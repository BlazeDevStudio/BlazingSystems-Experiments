"""Android emulator-only UI check: native reply -> fixture DOM -> native confirmation.
No Meta account, backend or live Facebook messages are involved.
"""
import re
import subprocess
import sys
import time
from xml.etree import ElementTree as ET

PACKAGE = "com.blazesystems.threadharbor"
PROBE = "THRPROBE20261026"

def adb(*arguments):
    return subprocess.check_output(["adb", *arguments], text=True, stderr=subprocess.STDOUT)

launcher_anr_recoveries = 0
uiautomator_recoveries = 0

def dump():
    global launcher_anr_recoveries, uiautomator_recoveries
    for _ in range(4):
        try:
            adb("shell", "uiautomator", "dump", "/sdcard/window.xml")
        except subprocess.CalledProcessError as exc:
            # Android's own low-memory killer can kill the short-lived UIAutomator
            # instrumentation process (exit 137). Do not confuse it with an
            # application crash or silently treat an invalid dump as a pass.
            if exc.returncode != 137:
                raise
            uiautomator_recoveries += 1
            if uiautomator_recoveries == 1:
                try:
                    with open("threadharbor-uiautomator-killed.png", "wb") as out:
                        subprocess.run(["adb", "exec-out", "screencap", "-p"],
                                       stdout=out, check=True)
                except Exception:
                    pass
            assert uiautomator_recoveries <= 2, "INCONCLUSIVE: repeated low-memory UIAutomator kills"
            assert adb("shell", "pidof", PACKAGE).strip(), "Application process died during UIAutomator failure"
            print("INFRA: UIAutomator exit 137 while application process lives; bounded retry")
            time.sleep(2)
            continue
        raw = adb("shell", "cat", "/sdcard/window.xml")
        start = raw.find("<?xml")
        if start < 0:
            raise AssertionError("No Android accessibility XML")
        tree = ET.fromstring(raw[start:])
        visible = [n.get("text", "") for n in tree.iter("node")]
        stalled = [value for value in visible if "isn't responding" in value]
        if not stalled:
            return tree
        # Don't hide an app ANR: explicitly allow only the Google Pixel Launcher
        # in the emulator, and preserve the screen before acknowledging it.
        if stalled != ["Pixel Launcher isn't responding"]:
            raise AssertionError("Non-launcher ANR shown: " + repr(stalled))
        launcher_anr_recoveries += 1
        if launcher_anr_recoveries > 2:
            raise AssertionError("Repeated Pixel Launcher ANRs; emulator not reliable")
        if launcher_anr_recoveries == 1:
            try:
                with open("threadharbor-launcher-anr.png", "wb") as out:
                    subprocess.run(["adb", "exec-out", "screencap", "-p"],
                                   stdout=out, check=True)
            except Exception as exc:
                print("Could not capture launcher ANR: " + str(exc), file=sys.stderr)
        options = [n for n in tree.iter("node") if n.get("text") == "Wait"]
        if len(options) != 1:
            raise AssertionError("Pixel Launcher ANR cannot be dismissed safely")
        tap(options[0])
        print("INFRA: dismissed Pixel Launcher ANR, preserving fail-on-app-ANR")
        time.sleep(1)
    raise AssertionError("System overlay persisted after permitted recovery")

def nodes(tree, **attributes):
    return [
        item for item in tree.iter("node")
        if all(item.get(key) == val for key, val in attributes.items())
    ]

def center(item):
    value = item.get("bounds", "")
    groups = re.fullmatch(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", value)
    if not groups:
        raise AssertionError("No bounds: " + repr(value))
    x1, y1, x2, y2 = map(int, groups.groups())
    return ((x1 + x2) // 2, (y1 + y2) // 2)

def tap(item):
    x, y = center(item)
    adb("shell", "input", "tap", str(x), str(y))

def run():
    deadline = time.monotonic() + 40
    start = dump()
    while time.monotonic() < deadline and not nodes(start, text="Tabs: 1"):
        time.sleep(2)
        start = dump()
    assert nodes(start, text="Tabs: 1"), "Real browser did not become ready as home"
    assert nodes(start, text="Back"), "Primary browser controls missing"
    more = nodes(start, text="More")
    assert len(more) == 1, "Compact browser actions menu missing"
    tap(more[0])
    menu = dump()
    for action in ("Home", "Bookmarks", "History", "Native Reader", "Open externally"):
        assert nodes(menu, text=action), "Missing browser action: " + action
    # Close the menu using its valid Home action, avoiding BACK (which can
    # navigate Android itself if the soft-keyboard/window owns focus).
    home = nodes(menu, text="Home")
    tap(home[0])
    start = dump()
    add = nodes(start, text="+ Tab")
    assert len(add) == 1, "Browser tab creation unavailable"
    tap(add[0])
    time.sleep(0.6)
    assert nodes(dump(), text="Tabs: 2"), "Second browser tab not created"
    chat = nodes(dump(), text="Chats")
    assert len(chat) == 1, "Native Chats tab inaccessible"
    tap(chat[0])
    time.sleep(0.6)
    status = dump()
    assert nodes(status, text="No compatible messaging site adapter is connected."), "Chats must not fake a real account"
    diagnostic = nodes(status, text="Open controlled adapter diagnostics")
    assert len(diagnostic) == 1, "Fixture must only be reachable by explicit diagnostic action"
    tap(diagnostic[0])
    fixture_deadline = time.monotonic() + 30
    fixture_view = dump()
    while time.monotonic() < fixture_deadline and not nodes(fixture_view, text="Observed 2 fixture messages"):
        active_packages = {n.get("package") for n in fixture_view.iter("node")}
        if PACKAGE not in active_packages:
            raise AssertionError(
                "App lost the foreground during diagnostic navigation; probable crash. "
                "Inspect FATAL EXCEPTION in uploaded logcat, packages=" + repr(active_packages)
            )
        time.sleep(2)
        fixture_view = dump()
    assert nodes(fixture_view, text="Developer adapter diagnostics"), "Diagnostic lab was not displayed"
    assert nodes(fixture_view, text="Observed 2 fixture messages"), "Bridge did not load initial fixture DOM"
    # The browser address bar is on the START snapshot, but this screen is
    # the diagnostic lab. Selecting from start would tap stale browser coords.
    fields = nodes(fixture_view, **{"class":"android.widget.EditText"})
    assert len(fields) == 1, "Expected exactly one native compose reply input"
    tap(fields[0])
    focused = dump()
    focused_fields = nodes(focused, **{"class":"android.widget.EditText"})
    assert len(focused_fields) == 1 and focused_fields[0].get("focused") == "true", (
        "Native reply field did not obtain keyboard focus; inspect hidden WebView focus")
    adb("shell", "input", "text", PROBE)
    time.sleep(1.5)
    typed = dump()
    assert nodes(typed, text=PROBE), "Keyboard input did not update the Compose text field"
    # Never send BACK during this test: on this emulator it exits the app.
    # Assert the Compose Send control stays available while input is focused.
    ready = dump()
    assert nodes(ready, text=PROBE), "Draft changed unexpectedly before send"
    send = nodes(ready, text="Send")
    assert len(send) == 1, "Send control unavailable while composing"
    tap(send[0])
    time.sleep(0.7)
    immediate = dump()
    immediate_text = [n.get("text","") for n in immediate.iter("node")]
    print("After Send tap:", repr([v for v in immediate_text if PROBE in v or "fixture" in v.lower() or "unverified" in v.lower()]))
    deadline = time.monotonic() + 18
    last_text = []
    while time.monotonic() < deadline:
        time.sleep(1)
        current = dump()
        rendered = [n.get("text", "") for n in current.iter("node")]
        last_text = [v for v in rendered if v and (PROBE in v or
                     "fixture" in v.lower() or "unverified" in v.lower())]
        if any(value == "Last action: OBSERVED_IN_FIXTURE" for value in rendered):
            assert any(value == PROBE for value in rendered), "Action observed but no message bubble"
            print("PASS: Native reply resulted in observed fixture DOM mutation and UI confirmation")
            browser = nodes(current, text="Browser")
            assert len(browser) == 1, "Could not return to the real browser"
            tap(browser[0])
            time.sleep(0.7)
            assert nodes(dump(), text="Tabs: 2"), "Browser tabs lost across native tool navigation"
            print("PASS: Browser tabs survive a switch to the native messaging lab")
            return
    print("Last visible post-submit UI entries: " + repr(last_text), file=sys.stderr)
    raise AssertionError("No visible verified pending action despite observed fixture reply")
def save_evidence():
    try:
        with open("threadharbor-native-reply.png", "wb") as dest:
            subprocess.run(["adb", "exec-out", "screencap", "-p"], stdout=dest, check=True)
        with open("threadharbor-native-hierarchy.xml", "w", encoding="utf-8") as dest:
            dest.write(adb("shell", "cat", "/sdcard/window.xml"))
    except Exception as exc:
        print("Evidence capture failure: " + str(exc), file=sys.stderr)

if __name__ == "__main__":
    try:
        run()
    except Exception as exc:
        print("FAIL: " + str(exc), file=sys.stderr)
        raise
    finally:
        save_evidence()
