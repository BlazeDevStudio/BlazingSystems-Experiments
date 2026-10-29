#!/usr/bin/env python3
"""Return tap coordinates ONLY for Android's Pixel Launcher ANR close button.

CI test helper: close the *launcher*, not LAN Messenger, so the original
two-emulator UI discovery assertion can be rerun with no system overlay.
No app success is inferred from this helper's result.
"""
import re
import sys
import xml.etree.ElementTree as ET


def close_launcher_button(xml_file):
    try:
        root = ET.parse(xml_file).getroot()
    except (ET.ParseError, OSError):
        return None

    nodes = list(root.iter("node"))
    if not any(
        node.get("text") == "Pixel Launcher isn't responding"
        and node.get("package") == "android"
        and node.get("resource-id") == "android:id/alertTitle"
        for node in nodes
    ):
        return None

    candidates = [
        node for node in nodes
        if node.get("resource-id") == "android:id/aerr_close"
        and node.get("text") == "Close app"
        and node.get("package") == "android"
        and node.get("enabled") == "true"
    ]
    if len(candidates) != 1:
        return None
    bounds = re.fullmatch(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]",
                          candidates[0].get("bounds", ""))
    if bounds is None:
        return None
    left, top, right, bottom = map(int, bounds.groups())
    if right <= left or bottom <= top:
        return None
    return ((left + right) // 2, (top + bottom) // 2)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(2)
    target = close_launcher_button(sys.argv[1])
    if target is None:
        sys.exit(2)
    print(f"{target[0]} {target[1]}")
