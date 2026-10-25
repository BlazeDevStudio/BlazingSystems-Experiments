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
LOG_PROCESSES = []


def start_continuous_call_logs():
    """Stream just app/native call tags from both emulators before dialing.

    Dumping the last N Android logcat lines at failure loses the decisive
    incoming offer on noisy Android 35 emulator images.
    """
    for serial in (CALLER, RECEIVER):
        # Do not accept a stale transport marker from a previous call.
        adb(serial, "logcat", "-c", check=False)
        target = open(OUT / f"{serial}-call-signaling-stream.txt", "wb")
        process = subprocess.Popen([
            "adb", "-s", serial, "logcat", "-v", "threadtime",
            "flutter:I", "LANCallTrace:I", "AndroidRuntime:E", "*:S"
        ], stdout=target, stderr=subprocess.DEVNULL)
        LOG_PROCESSES.append((process, target))
    note("logging", "Streaming filtered signaling/native logs from BOTH devices")


def stop_continuous_call_logs():
    for process, target in LOG_PROCESSES:
        process.terminate()
        try:
            process.wait(timeout=4)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=3)
        target.close()
    LOG_PROCESSES.clear()


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


def transport_connected_in_log(serial):
    """Read this endpoint's WebRTC connection callback from its own log."""
    path = OUT / f"{serial}-call-signaling-stream.txt"
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except FileNotFoundError:
        return False
    return any("LAN_CALL_TRACE webrtc_transport_connected" in line
               for line in lines)


def wait_both_connected(timeout_seconds=85):
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        for serial in (CALLER, RECEIVER):
            pid = adb(serial, "shell", "pidof", "com.example.lan_messenger",
                      check=False).strip()
            if not pid:
                raise RuntimeError(f"{serial} process exited during call")
        caller = snapshot(CALLER, "connected")
        receiver = snapshot(RECEIVER, "connected")
        caller_labels = " ".join(labels(n) for n in caller.iter("node")) if caller is not None else ""
        receiver_labels = " ".join(labels(n) for n in receiver.iter("node")) if receiver is not None else ""
        # Caller: only its WebRTC Connected state is accepted.
        # Receiver: when a native system-overlay call surface is in use,
        # it displays "Live" while the underlying call page displays the
        # active call. It does not mirror the caller's status header.
        caller_connected = "Connected • Local LAN" in caller_labels
        receiver_connected = (
            "Connected • Local LAN" in receiver_labels or
            ("Call active • Use your microphone to talk" in receiver_labels
             and "Live" in receiver_labels)
        )
        caller_transport = transport_connected_in_log(CALLER)
        receiver_transport = transport_connected_in_log(RECEIVER)
        if caller_connected and receiver_connected and caller_transport and receiver_transport:
            note("media", "PASS: BOTH WebRTC endpoints reported Connected; caller and receiver live UI confirmed")
            (OUT / "webrtc-two-endpoint-transport-proof.json").write_text(
                json.dumps({"caller": CALLER, "receiver": RECEIVER,
                            "caller_transport_connected": caller_transport,
                            "receiver_transport_connected": receiver_transport,
                            "caller_connected_ui": caller_connected,
                            "receiver_live_ui": receiver_connected}, indent=2),
                encoding="utf-8")
            return
        time.sleep(3)
    raise RuntimeError("BOTH WebRTC transport-connected events and both call interfaces were not confirmed")


def expand_notification_shade(serial, label):
    """System UI can ignore the first shade request while Launcher is busy."""
    adb(serial, "shell", "cmd", "statusbar", "expand-notifications", check=False)
    time.sleep(1)
    root = snapshot(serial, label + "-first-shade")
    found = root is not None and any(
        "LAN Messenger" in labels(n) and "notification" not in labels(n).lower()
        for n in root.iter("node"))
    if not found:
        adb(serial, "shell", "input", "swipe", "540", "1", "540", "1450", "460",
            timeout=12, check=False)
        time.sleep(1)
        root = snapshot(serial, label + "-swipe-shade")
    return root


def first_background_incoming_test():
    """One fresh background-incoming call, with no prior WebRTC teardown."""
    note("background-setup", "Receiver is HOME before the FIRST call")
    adb(RECEIVER, "shell", "input", "keyevent", "KEYCODE_HOME")
    time.sleep(3)
    activity = adb(RECEIVER, "shell", "dumpsys", "activity", "activities",
                   check=False).decode(errors="replace")
    if re.search(r"topResumedActivity=.*com\.example\.lan_messenger", activity):
        raise RuntimeError("Receiver still foreground before background call")
    tap_label(CALLER, "background-first-call",
              lambda text: "voice call" in text.lower())
    time.sleep(3)
    root = expand_notification_shade(RECEIVER, "background-first-3seconds")
    if root is not None:
        note("notification-early", "UI labels: " +
             repr([labels(n) for n in root.iter("node") if labels(n)][:40]))
    (OUT / "android-first-background-notification.txt").write_bytes(
        adb(RECEIVER, "shell", "dumpsys", "notification", "--noredact",
            timeout=20, check=False))
    tap_label(RECEIVER, "notification-answer",
              lambda text: "answer" in text.lower(), timeout_seconds=30)
    wait_both_connected()
    note("background-first-connected", "PASS: first native Answer connected WebRTC")
    tap_label(RECEIVER, "hangup",
              lambda text: text.lower().strip() == "end call", timeout_seconds=28)
    for serial in (CALLER, RECEIVER):
        if not adb(serial, "shell", "pidof", "com.example.lan_messenger",
                   check=False).strip():
            raise RuntimeError(f"{serial} exited during notification Answer")
    note("done", "PASS: background-first Answer -> WebRTC -> hangup, no crash")


def main():
    note("setup", "Starting actual Android↔Android voice call UI test")
    for serial in (CALLER, RECEIVER):
        if not adb(serial, "shell", "pidof", "com.example.lan_messenger",
                   check=False).strip():
            raise RuntimeError(f"{serial} is not running")
    tap_label(CALLER, "choose-peer",
              lambda text: "online" in text.lower() and
              "looking for nearby" not in text.lower())
    if os.environ.get("LAN_MESSENGER_SCENARIO") == "background-first":
        first_background_incoming_test()
        return
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
    if re.search(r"topResumedActivity=.*com\.example\.lan_messenger", foreground):
        raise RuntimeError("Receiver did not background before incoming call")
    note("background-incoming", "Receiver moved to Android HOME before call")
    # An old call leaves both RTCPeerConnection objects disposing after the
    # visible End Call control disappears. Wait for both peers to finish
    # teardown, otherwise the next offer may legitimately be rejected as BUSY.
    note("redial-gate", "Allowing 18 seconds for two-device WebRTC teardown")
    time.sleep(18)
    tap_label(CALLER, "call-again", lambda text: "voice call" in text.lower(),
              timeout_seconds=40)
    # Capture the *first* notification state before the incoming decision
    # timeout clears it. Previously only the last (~55-second) snapshot
    # survived, which cannot prove what Android showed at ring time.
    time.sleep(3)
    adb(RECEIVER, "shell", "cmd", "statusbar", "expand-notifications",
        check=False)
    root = snapshot(RECEIVER, "incoming-3-seconds")
    if root is not None:
        note("notification-3-seconds", "Visible labels: " +
             repr([labels(n) for n in root.iter("node") if labels(n)][:35]))
    (OUT / "android-notification-state.txt").write_bytes(
        adb(RECEIVER, "shell", "dumpsys", "notification", "--noredact",
            timeout=20, check=False))
    # Android CallStyle actions vary in accessible wording between API levels.
    # Never turn a timeout into a pass; retain UI, system notification,
    # caller/receiver logs if a real Answer control cannot be found.
    tap_label(RECEIVER, "notification-answer",
              lambda text: "answer" in text.lower(),
              timeout_seconds=26)
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
        start_continuous_call_logs()
        main()
    except Exception as exc:
        note("FAILED", str(exc))
        for serial in (CALLER, RECEIVER):
            snapshot(serial, "failure")
            # Capture logs AFTER the failed offer, not the discovery-only logs.
            try:
                log = adb(serial, "logcat", "-d", "-t", "9000",
                          timeout=30, check=False)
                (OUT / f"{serial}-call-failure-logcat.txt").write_bytes(log)
                markers = [line for line in log.decode(errors="replace").splitlines()
                           if "LAN_CALL_TRACE" in line or "LANCallTrace" in line]
                note("signaling-trace", f"{serial} last trace markers: {markers[-18:]}")
                (OUT / f"{serial}-call-failure-activity.txt").write_bytes(
                    adb(serial, "shell", "dumpsys", "activity", "activities",
                        timeout=25, check=False))
            except Exception as capture_error:
                note("evidence", f"{serial}: {capture_error}")
        raise
    finally:
        stop_continuous_call_logs()
        (OUT / "voice-call-report.json").write_text(
            json.dumps({"events": EVENTS}, indent=2), encoding="utf-8")
