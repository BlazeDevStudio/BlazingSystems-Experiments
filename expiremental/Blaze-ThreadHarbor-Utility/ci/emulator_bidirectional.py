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

def dump():
    adb("shell", "uiautomator", "dump", "/sdcard/window.xml")
    raw = adb("shell", "cat", "/sdcard/window.xml")
    start = raw.find("<?xml")
    if start < 0:
        raise AssertionError("No Android accessibility XML")
    return ET.fromstring(raw[start:])

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
    start = dump()
    assert nodes(start, text="Observed 2 fixture messages"), "Bridge did not load initial fixture DOM"
    fields = nodes(start, **{"class":"android.widget.EditText"})
    assert len(fields) == 1, "Expected exactly one native compose reply input"
    tap(fields[0])
    adb("shell", "input", "text", PROBE)
    time.sleep(1.5)
    typed = dump()
    assert nodes(typed, text=PROBE), "Keyboard input did not update the Compose text field"
    # The previous RED left the draft untouched: a tap while the IME was open
    # could hit keyboard content instead of the Compose button. Close IME FIRST.
    adb("shell", "input", "keyevent", "KEYCODE_BACK")
    time.sleep(1)
    ready = dump()
    assert nodes(ready, text=PROBE), "Draft lost when closing software keyboard"
    send = nodes(ready, text="Send")
    assert len(send) == 1, "Send button missing after keyboard dismissed"
    tap(send[0])
    deadline = time.monotonic() + 18
    last_text = []
    while time.monotonic() < deadline:
        time.sleep(1)
        current = dump()
        rendered = [n.get("text", "") for n in current.iter("node")]
        last_text = [v for v in rendered if v and (PROBE in v or
                     "fixture" in v.lower() or "unverified" in v.lower())]
        if any("OBSERVED_IN_FIXTURE: " + PROBE in value for value in rendered):
            assert any(value == PROBE for value in rendered), "Action observed but no message bubble"
            print("PASS: Native reply resulted in observed fixture DOM mutation and UI confirmation")
            return
    print("Last visible post-submit UI entries: " + repr(last_text), file=sys.stderr)
    raise AssertionError("No observed fixture confirmation within 18 seconds")
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
