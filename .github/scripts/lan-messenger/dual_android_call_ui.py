#!/usr/bin/env python3
"""Real UI automation for two LAN Messenger Android emulator instances.

Required: both APKs already running and peer discovery confirmed. This test
uses ADB UiAutomator to tap the same controls as a person. It never reports a
successful call merely because a process stayed alive or an offer was sent.
Saves XML and screenshots when any step fails for reproducible diagnosis.
"""
import json
import os
import pathlib
import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

OUT = pathlib.Path(os.environ.get("GITHUB_WORKSPACE", ".")) / "android-lan-evidence"
OUT.mkdir(parents=True, exist_ok=True)
CALLER, RECEIVER = "emulator-5554", "emulator-5556"
EVENTS = []


def adb(serial, *args, timeout=45, check=True):
    p = subprocess.run(["adb", "-s", serial, *args], capture_output=True,
                       timeout=timeout)
    if check and p.returncode != 0:
        raise RuntimeError(f"adb {serial} {' '.join(args)} failed: "
                           f"{p.stderr.decode(errors='replace')[-1000:]}")
    return p.stdout


def note(stage, message):
    line = f"{stage}: {message}"
    EVENTS.append(line)
    print(line, flush=True)


def snapshot(serial, stage):
    try:
        xml_path = "/sdcard/lan_messenger_cloud_ui.xml"
        adb(serial, "shell", "uiautomator", "dump", xml_path,
            timeout=35, check=False)
        data = adb(serial, "exec-out", "cat", xml_path, timeout=15)
        (OUT / f"{serial}-{stage}.xml").write_bytes(data)
        image = adb(serial, "exec-out", "screencap", "-p", timeout=25)
        (OUT / f"{serial}-{stage}.png").write_bytes(image)
        root = ET.fromstring(data)
        return root
    except Exception as exc:
        note(stage, f"{serial} UI snapshot unavailable: {exc}")
        return None


def labels(node):
    return (node.attrib.get("text", "") + " " +
            node.attrib.get("content-desc", "")).strip()


def choose(root, criterion):
    parent = {child: item for item in root.iter() for child in item}
    candidates = [item for item in root.iter("node")
                  if criterion(labels(item))]
    for item in candidates:
        candidate = item
        while candidate is not None:
            if candidate.attrib.get("clickable") == "true" and re.match(
                r"\[\d+,\d+\]\[\d+,\d+\]",
                candidate.attrib.get("bounds", "")
            ):
                return candidate
            candidate = parent.get(candidate)
        if item.attrib.get("bounds"):
            return item
    return None


def tap(serial, node, stage):
    bounds = node.attrib.get("bounds", "")
    points = [int(i) for i in re.findall(r"\d+", bounds)]
    if len(points) != 4:
        raise RuntimeError(f"{stage}: no tappable bounds ({bounds})")
    x, y = (points[0] + points[2]) // 2, (points[1] + points[3]) // 2
    note(stage, f"tap {serial} ({x},{y}) label={labels(node)!r}")
    adb(serial, "shell", "input", "tap", str(x), str(y))


def tap_label(serial, stage, criterion, timeout_seconds=35):
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        root = snapshot(serial, stage)
        if root is not None:
            item = choose(root, criterion)
            if item is not None:
                tap(serial, item, stage)
                return
        time.sleep(2)
    raise RuntimeError(f"{stage}: expected interactive UI action absent")


def contains(serial, stage, needle):
    root = snapshot(serial, stage)
    if root is None:
        return False
    return needle.lower() in " ".join(labels(n) for n in root.iter("node")).lower()


def wait_both_connected(timeout_seconds=85):
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        for serial in (CALLER, RECEIVER):
            pid = adb(serial, "shell", "pidof", "com.example.lan_messenger",
                      check=False).strip()
            if not pid:
                raise RuntimeError(f"{serial} process exited during call")
        success = [
            contains(serial, "connected", "Connected • Local LAN")
            for serial in (CALLER, RECEIVER)
        ]
        if all(success):
            note("media", "PASS: both peers display Connected • Local LAN")
            return
        time.sleep(3)
    raise RuntimeError("Two-device call did not reach Connected state on both UIs")


def main():
    note("setup", "Starting actual Android↔Android foreground voice call UI test")
    for serial in (CALLER, RECEIVER):
        if not adb(serial, "shell", "pidof", "com.example.lan_messenger",
                   check=False).strip():
            raise RuntimeError(f"{serial} is not running")
    tap_label(CALLER, "choose-peer",
              lambda text: "online" in text.lower() and
              "looking for nearby" not in text.lower())
    tap_label(CALLER, "call", lambda text: "voice call" in text.lower())
    tap_label(RECEIVER, "answer", lambda text: text.lower().strip() == "answer",
              timeout_seconds=55)
    wait_both_connected()
    adb(RECEIVER, "shell", "input", "keyevent", "KEYCODE_HOME")
    time.sleep(3)
    if not adb(RECEIVER, "shell", "pidof", "com.example.lan_messenger",
               check=False).strip():
        raise RuntimeError("Android Answer succeeded but app died after backgrounding")
    note("background", "PASS: connected Android receiver remains alive after HOME")
    # Return to the running Activity before ending the call, no new call.
    adb(RECEIVER, "shell", "am", "start", "-W",
        "-n", "com.example.lan_messenger/.MainActivity", timeout=30)
    tap_label(RECEIVER, "hangup", lambda text: text.lower().strip() == "end call")
    for serial in (CALLER, RECEIVER):
        if not adb(serial, "shell", "pidof", "com.example.lan_messenger",
                   check=False).strip():
            raise RuntimeError(f"{serial} exited during hangup")
    note("foreground-call", "PASS: foreground Answer, connected, backgrounded, hung up")
    # Regression for the original Answer crash: receiver must be backgrounded
    # BEFORE a new incoming offer, without an OS overlay grant. Use Android's
    # system notification action, not the in-app Answer button.
    adb(RECEIVER, "shell", "input", "keyevent", "KEYCODE_HOME")
    time.sleep(3)
    foreground = adb(RECEIVER, "shell", "dumpsys", "activity", "activities",
                     check=False).decode(errors="replace")
    if re.search(r"topResumedActivity=.*com\\.example\\.lan_messenger", foreground):
        raise RuntimeError("Receiver did not background before incoming call")
    note("background-incoming", "Receiver moved to Android HOME before call")
    tap_label(CALLER, "call-again", lambda text: "voice call" in text.lower(),
              timeout_seconds=40)
    # Native CallStyle/heads-up notification fallback for apps that are
    # backgrounded without SYSTEM_ALERT_WINDOW permission.
    adb(RECEIVER, "shell", "cmd", "statusbar", "expand-notifications",
        check=False)
    tap_label(RECEIVER, "notification-answer",
              lambda text: text.strip().lower() == "answer",
              timeout_seconds=55)
    wait_both_connected()
    note("background-answer", "PASS: native Android notification Answer connected both peers")
    tap_label(RECEIVER, "hangup-background-call",
              lambda text: text.strip().lower() == "end call",
              timeout_seconds=25)
    for serial in (CALLER, RECEIVER):
        if not adb(serial, "shell", "pidof", "com.example.lan_messenger",
                   check=False).strip():
            raise RuntimeError(f"{serial} died during background-Answer hangup")
    note("done", "PASS: foreground and background notification Answer calls, WebRTC connected and hung up without app crash")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        note("FAILED", str(exc))
        for serial in (CALLER, RECEIVER):
            snapshot(serial, "failure")
        raise
    finally:
        (OUT / "voice-call-report.json").write_text(
            json.dumps({"events": EVENTS}, indent=2), encoding="utf-8")
