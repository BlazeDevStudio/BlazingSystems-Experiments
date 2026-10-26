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
    groups = re.fullmatch(r"\\[(\\d+),(\\d+)\\]\\[(\\d+),(\\d+)\\]", value)
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
    send = nodes(typed, text="Send")
    assert len(send) == 1, "Send button missing after text input"
    tap(send[0])
    deadline = time.monotonic() + 18
    while time.monotonic() < deadline:
        time.sleep(1)
        current = dump()
        rendered = [n.get("text", "") for n in current.iter("node")]
        if any("OBSERVED_IN_FIXTURE: " + PROBE in value for value in rendered):
            assert any(value == PROBE for value in rendered), "Action observed but no message bubble"
            print("PASS: Native reply resulted in observed fixture DOM mutation and UI confirmation")
            return
    raise AssertionError("No observed fixture confirmation within 18 seconds")
if __name__ == "__main__":
    try:
        run()
    except Exception as exc:
        print("FAIL: " + str(exc), file=sys.stderr)
        raise
