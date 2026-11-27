#!/usr/bin/env python3
"""Real-Chromium smoke for the standalone edition's SELF-CONTAINED UI.
No real server, customer state or admin credential is used.
"""
import json
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = Path(__file__).resolve().parents[1]
HTML = BASE / "profiles" / "standalone-rental" / "openwrt" / "rental-standalone.html"
OUT = Path(sys.argv[1] if len(sys.argv) > 1 else "simulation-out/browser")
OUT.mkdir(parents=True, exist_ok=True)
mutations = []
external = []
errors = []

def fulfill(route):
    request = route.request
    url = request.url
    if not url.startswith("https://127.0.0.1/"):
        external.append(url)
        route.abort()
        return
    if url.startswith("https://127.0.0.1/rental/vendor/qrcode.js"):
        route.fulfill(status=200, content_type="application/javascript",
                      body="window.qrcode = function(){return {addData(){},make(){},createSvgTag(){return '<svg></svg>'}}};")
        return
    if url.startswith("https://127.0.0.1/rental/"):
        route.fulfill(status=200, content_type="text/html; charset=utf-8",
                      body=HTML.read_text(encoding="utf-8"))
        return
    if url.endswith("/cgi-bin/blaze-rental-session"):
        route.fulfill(status=200, content_type="application/json",
                      body=json.dumps({"ok": True, "username": "UI-TEST",
                                       "role": "admin", "csrf": "fake-ui-csrf",
                                       "must_change": 0}))
        return
    if url.endswith("/cgi-bin/blaze-rental-admin"):
        from urllib.parse import parse_qs
        action = parse_qs(request.post_data or "").get("action", [""])[0]
        mutations.append(action)
        payload = {"ok": True}
        if action == "rental_device_list":
            payload["devices"] = []
        elif action == "controller_list":
            payload["controllers"] = []
        else:
            payload["error"] = "Unexpected mock action"
            payload["ok"] = False
        route.fulfill(status=200, content_type="application/json",
                      body=json.dumps(payload))
        return
    if url.endswith("/cgi-bin/blaze-rental-profile"):
        route.fulfill(status=200, content_type="application/json",
                      body=json.dumps({"ok": True, "edition": "rental-standalone",
                                       "version": "UI-MOCK", "model": "Test only",
                                       "board": "Test only", "openwrt": "Test",
                                       "mem_available_kb": 64000, "uptime_seconds": 1000,
                                       "full_upgrade_available": False}))
        return
    route.abort()
    errors.append("unexpected request: " + url)

with sync_playwright() as playwright:
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context(ignore_https_errors=True, viewport={"width": 1365, "height": 850})
    page = context.new_page()
    page.on("pageerror", lambda err: errors.append("pageerror: " + str(err)))
    page.route("**/*", fulfill)
    page.goto("https://127.0.0.1/rental/", wait_until="networkidle")
    page.wait_for_selector("#app:not(.hidden)")
    assert page.locator("#blazeStyleStandalone").input_value() == "fusion"
    assert page.locator("body").get_attribute("data-blaze-style") == "fusion"
    assert page.locator("#mTotal").inner_text() == "0"
    page.select_option("#blazeStyleStandalone", "compact")
    assert page.locator("body").get_attribute("data-blaze-style") == "compact"
    assert page.evaluate("localStorage.getItem('blazepwifi.console.appearance.v1')") == "compact"
    page.reload(wait_until="networkidle")
    page.wait_for_selector("#app:not(.hidden)")
    assert page.locator("#blazeStyleStandalone").input_value() == "compact"
    page.select_option("#blazeStyleStandalone", "comfort")
    assert page.locator("body").get_attribute("data-blaze-style") == "comfort"
    page.select_option("#blazeStyleStandalone", "fusion")
    page.screenshot(path=str(OUT / "standalone-blazefusion-desktop.png"), full_page=True)
    for width in (390, 360):
        page.set_viewport_size({"width": width, "height": 844})
        page.wait_for_timeout(100)
        assert page.locator("#blazeStyleStandalone").is_visible()
        assert page.locator('button:has-text("Sign out")').is_visible()
        geometry = page.evaluate("""() => ({
            viewport: window.innerWidth,
            document: document.documentElement.scrollWidth,
            offenders: [...document.querySelectorAll('body *')]
              .filter(e => {
                const r = e.getBoundingClientRect();
                return r.width > 0 && r.right > window.innerWidth + 2 &&
                  getComputedStyle(e).display !== 'none';
              })
              .slice(0, 12).map(e => ({
                tag: e.tagName.toLowerCase(), id: e.id, className: String(e.className).slice(0, 90),
                right: Math.round(e.getBoundingClientRect().right)
              }))
          })""")
        assert geometry["document"] <= geometry["viewport"] + 2, (
            "Standalone rental mobile horizontal overflow: " + str(geometry))
        if width == 360:
            page.screenshot(path=str(OUT / "standalone-blazefusion-mobile.png"), full_page=True)
    assert set(mutations) == {"rental_device_list", "controller_list"}, mutations
    assert not external, external
    assert not errors, errors
    context.close()
    browser.close()
print("Standalone BlazeFusion Chrome: theme/reload/mobile layout + original read-only rental APIs passed")
