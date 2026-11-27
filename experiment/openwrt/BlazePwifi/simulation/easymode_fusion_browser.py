#!/usr/bin/env python3
"""Offline Chromium visual smoke for an opt-in EasyMode R281 preview.
The browser never connects to a real router or uses live credentials.
"""
import http.server
import json
import socketserver
import subprocess
import sys
import tempfile
import threading
from pathlib import Path
from playwright.sync_api import sync_playwright

PROJECT = Path(__file__).resolve().parents[2] / "easymode-project"
BUILDER = PROJECT / "integrations" / "blazefusion" / "build-preview.py"
OUT = Path(sys.argv[1] if len(sys.argv) > 1 else "simulation-out/browser").resolve()
OUT.mkdir(parents=True, exist_ok=True)
errors, external, ubus_requests = [], [], []

class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *_): pass

with tempfile.TemporaryDirectory(prefix="easymode-fusion-ui-") as temp:
    stage = Path(temp) / "www"
    subprocess.run([sys.executable, str(BUILDER), "--output", str(stage)], check=True)
    class Handler(Quiet):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(stage), **kwargs)
    server = socketserver.TCPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    root_url = f"http://127.0.0.1:{server.server_address[1]}"
    try:
        with sync_playwright() as api:
            browser = api.chromium.launch(headless=True)
            ctx = browser.new_context(viewport={"width": 1365, "height": 900})
            page = ctx.new_page()
            page.on("pageerror", lambda e: errors.append(str(e)))
            def route(req):
                url = req.request.url
                if not url.startswith(root_url):
                    external.append(url)
                    req.abort()
                elif url.endswith("/ubus"):
                    ubus_requests.append(req.request.method)
                    req.fulfill(status=200, content_type="application/json",
                                body=json.dumps({"jsonrpc": "2.0", "result": [0, {}]}))
                else:
                    req.continue_()
            page.route("**/*", route)
            page.goto(root_url + "/", wait_until="domcontentloaded")
            page.wait_for_function("document.documentElement.dataset.blazeStyle === 'fusion'")
            # The existing UI requires OpenWrt RPC login; only show its shell
            # for presentation tests, without pretending to validate login.
            page.locator("#app").evaluate("(e) => {e.hidden = false}")
            page.locator("#login").evaluate("(e) => {e.hidden = true}")
            choice = page.locator("#blazefusion-appearance")
            assert choice.is_visible()
            assert page.locator("#logout").is_visible()
            page.select_option("#blazefusion-appearance", "compact")
            assert page.locator("html").get_attribute("data-blaze-style") == "compact"
            assert page.evaluate("localStorage.getItem('blazepwifi.console.appearance.v1')") == "compact"
            page.reload(wait_until="domcontentloaded")
            page.locator("#app").evaluate("(e) => {e.hidden = false}")
            page.locator("#login").evaluate("(e) => {e.hidden = true}")
            assert page.locator("#blazefusion-appearance").input_value() == "compact"
            page.select_option("#blazefusion-appearance", "comfort")
            assert page.locator("html").get_attribute("data-blaze-style") == "comfort"
            page.select_option("#blazefusion-appearance", "fusion")
            page.screenshot(path=str(OUT / "easymode-fusion-desktop.png"), full_page=True)
            for width in (390, 360):
                page.set_viewport_size({"width": width, "height": 844})
                page.wait_for_timeout(120)
                assert page.locator("#blazefusion-appearance").is_visible()
                assert page.locator("#logout").is_visible()
                geom = page.evaluate("""() => ({
                    viewport: innerWidth, total: document.documentElement.scrollWidth,
                    offenders: [...document.querySelectorAll('body *')]
                      .filter(e => getComputedStyle(e).display !== 'none' &&
                        e.getBoundingClientRect().right > innerWidth + 2)
                      .slice(0, 8).map(e => e.tagName + '#' + e.id)
                })""")
                assert geom["total"] <= geom["viewport"] + 2, geom
                if width == 360:
                    page.screenshot(path=str(OUT / "easymode-fusion-mobile.png"), full_page=True)
            # Existing EasyMode's light/dark and --accent are server-owned;
            # the appearance toggle must not replace these config values.
            assert page.locator("html").get_attribute("data-theme") in ("dark", "light")
            assert not external, external
            assert not errors, errors
            ctx.close()
            browser.close()
    finally:
        server.shutdown()
        server.server_close()
print("EasyMode Fusion off-device Chromium appearance/persistence/360px test passed; no actual login, network settings or router touched")
