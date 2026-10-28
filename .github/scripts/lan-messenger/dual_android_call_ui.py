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


def tap_notification_answer(serial, stage, timeout_seconds=32):
    """Expand a collapsed Android notification group, then tap REAL Answer.

    Emulator 35 can group "LAN Messenger is ready" with the CallStyle alert.
    A collapsed group shows an "Expand" node but hides its child actions.
    Never invent an Answer or issue an intent in place of a user tap.
    """
    deadline = time.monotonic() + timeout_seconds
    expanded_once = False
    while time.monotonic() < deadline:
        root = expand_notification_shade(serial, stage + "-shade")
        if root is not None:
            candidate = choose(root, lambda t: t.strip().lower() == "answer"
                               or "answer" in t.lower() and "decline" not in t.lower())
            if candidate is not None:
                tap(serial, candidate, stage)
                return
            all_labels = " ".join(labels(n) for n in root.iter("node"))
            if "LAN Messenger" in all_labels:
                expander = choose(root, lambda t: t.strip().lower() == "expand")
                if expander is not None and not expanded_once:
                    tap(serial, expander, stage + "-expand-group")
                    expanded_once = True
                    time.sleep(1)
                    continue
        time.sleep(1)
    (OUT / f"{serial}-{stage}-notification-dumpsys.txt").write_bytes(
        adb(serial, "shell", "dumpsys", "notification", "--noredact",
            timeout=20, check=False))
    raise RuntimeError(f"{stage}: Android notification never exposed an actionable Answer after group expansion")


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
    # Even with SYSTEM_ALERT_WINDOW granted, a successfully posted CallStyle
    # notification must NOT create a duplicate app-owned Answer/Decline HUD.
    before_shade = snapshot(RECEIVER, "ringing-overlay-suppressed")
    if before_shade is not None:
        leaked = [n for n in before_shade.iter("node")
                  if n.attrib.get("package") == "com.example.lan_messenger"
                  and labels(n).strip().lower() in ("answer", "decline")]
        if leaked:
            raise RuntimeError("Duplicate application-owned Answer/Decline overlay while system notification is visible")
    note("ringing-surface", "PASS: no app-owned duplicate incoming buttons over HOME")
    root = expand_notification_shade(RECEIVER, "background-first-3seconds")
    if root is not None:
        note("notification-early", "UI labels: " +
             repr([labels(n) for n in root.iter("node") if labels(n)][:40]))
    (OUT / "android-first-background-notification.txt").write_bytes(
        adb(RECEIVER, "shell", "dumpsys", "notification", "--noredact",
            timeout=20, check=False))
    tap_notification_answer(RECEIVER, "notification-answer", timeout_seconds=30)
    wait_both_connected()
    note("background-first-connected", "PASS: first native Answer connected WebRTC")
    tap_label(RECEIVER, "hangup",
              lambda text: text.lower().strip() == "end call", timeout_seconds=28)
    for serial in (CALLER, RECEIVER):
        if not adb(serial, "shell", "pidof", "com.example.lan_messenger",
                   check=False).strip():
            raise RuntimeError(f"{serial} exited during notification Answer")
    note("done", "PASS: background-first Answer -> WebRTC -> hangup, no crash")


def video_call_test():
    """Never mistake signaling for video: require decoded frames at both ends."""
    note("video", "Testing video camera frames, Android foreground UI and Home PiP")
    tap_label(CALLER, "video-call", lambda text: "video call" in text.lower(),
              timeout_seconds=40)
    tap_label(RECEIVER, "video-answer",
              lambda text: text.lower().strip() == "answer", timeout_seconds=50)
    wait_both_connected()
    deadline = time.monotonic() + 70
    while time.monotonic() < deadline:
        if all("LAN_CALL_TRACE remote_video_frame_decoded" in
               (OUT / f"{serial}-call-signaling-stream.txt").read_text(
                   encoding="utf-8", errors="replace")
               for serial in (CALLER, RECEIVER)):
            note("video", "PASS: both Android peers decoded remote camera frames")
            break
        time.sleep(2)
    else:
        raise RuntimeError("Video call connected but both decoded-frame callbacks were not observed")
    # In-app mini view must NOT cover the screen. Navigation back to call is
    # handled by a small titlebar action, not a video overlay over Settings.
    tap_label(RECEIVER, "video-minimize",
              lambda text: "minimize; call stays connected" in text.lower())
    if contains(RECEIVER, "video-in-app-mini", "Expand call controls"):
        raise RuntimeError("Legacy floating video mini-view still visible inside Messenger")
    tap_label(RECEIVER, "return-to-call",
              lambda text: "return to active call" in text.lower())
    adb(RECEIVER, "shell", "input", "keyevent", "KEYCODE_HOME")
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        pip_events = (OUT / f"{RECEIVER}-call-signaling-stream.txt").read_text(
            encoding="utf-8", errors="replace")
        if "pip_state_changed active=true" in pip_events:
            note("pip", "PASS: Android native OS confirmed real PiP after HOME")
            break
        time.sleep(2)
    else:
        raise RuntimeError("Home did not enter Android native PiP even though a live video call exists")
    # Expand the real OS PiP and require the live CALL surface, not the
    # conversation page. The native PiP state callback must restore it.
    adb(RECEIVER, "shell", "am", "start", "-W",
        "-n", "com.example.lan_messenger/.MainActivity", timeout=30)
    if not contains(RECEIVER, "pip-expanded-call-screen", "End call"):
        raise RuntimeError("Expanding PiP returned to conversation, not active call")

    # Put the receiver in PiP again; the remote peer now ends the call.
    # Old Android code disabled future PiP entry but left this PiP alive.
    adb(RECEIVER, "shell", "input", "keyevent", "KEYCODE_HOME")
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        logs = (OUT / f"{RECEIVER}-call-signaling-stream.txt").read_text(
            encoding="utf-8", errors="replace")
        if logs.count("pip_state_changed active=true") >= 2:
            break
        time.sleep(1)
    else:
        raise RuntimeError("Expanded video call could not return to OS PiP")
    tap_label(CALLER, "remote-hangup-while-receiver-pip",
              lambda text: text.lower().strip() == "end call",
              timeout_seconds=30)
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        logs = (OUT / f"{RECEIVER}-call-signaling-stream.txt").read_text(
            encoding="utf-8", errors="replace")
        if "ended_call_pip_dismissed" in logs:
            note("pip", "PASS: remote Hangup explicitly dismissed live OS PiP")
            break
        time.sleep(1)
    else:
        raise RuntimeError("Android PiP stayed open after remote call ended")
    # PiP close may finish the Flutter Activity, but reopening from launcher
    # must remain possible without a stuck call or process crash.
    adb(RECEIVER, "shell", "am", "start", "-W",
        "-n", "com.example.lan_messenger/.MainActivity", timeout=30)
    if not adb(RECEIVER, "shell", "pidof", "com.example.lan_messenger",
               check=False).strip():
        raise RuntimeError("Receiver could not reopen after closed PiP")
    note("video", "PASS: two decoded video feeds, PiP expand, remote hangup and PiP close")



def process_death_test():
    """Kill an active peer without signaling; survivor must end automatically.

    This is the missing acceptance path from the physical Windows freeze/exit.
    A graceful Hangup cannot prove the watchdog detects process death.
    """
    package = "com.example.lan_messenger"
    note("peer-death", "Dialing first real voice session before forced process exit")
    tap_label(CALLER, "peer-death-dial", lambda text: "voice call" in text.lower(),
              timeout_seconds=45)
    tap_label(RECEIVER, "peer-death-answer",
              lambda text: text.strip().lower() == "answer",
              timeout_seconds=55)
    wait_both_connected()
    before = snapshot(CALLER, "peer-death-before-kill")
    if before is None:
        raise RuntimeError("No caller UI evidence before peer termination")
    if "End call" not in " ".join(labels(n) for n in before.iter("node")):
        raise RuntimeError("No active call controls before peer termination")
    # Android force-stop is deliberately abrupt: no Dart dispose/hangup can
    # run. This simulates a desktop executable disappearing mid-call.
    started = time.monotonic()
    note("peer-death-kill", "Force-stopping receiver process without hangup")
    adb(RECEIVER, "shell", "am", "force-stop", package)
    time.sleep(2)
    if adb(RECEIVER, "shell", "pidof", package, check=False).strip():
        raise RuntimeError("Force-stopped peer is still running")

    saw_reconnecting = False
    saw_ended = False
    saw_offline = False
    # Default reconnect grace is 60s; 110s allows two 5-second probes,
    # bounded HTTP timeouts, media cleanup and UiAutomator overhead.
    # The session must NOT stay active indefinitely after a dead process.
    deadline = started + 110
    while time.monotonic() < deadline:
        if not adb(CALLER, "shell", "pidof", package, check=False).strip():
            raise RuntimeError("Surviving caller crashed after remote process death")
        if adb(RECEIVER, "shell", "pidof", package, check=False).strip():
            raise RuntimeError("Dead receiver unexpectedly restarted; invalid test")
        root = snapshot(CALLER, "peer-death-watchdog")
        if root is None:
            time.sleep(2)
            continue
        screen = " ".join(labels(n) for n in root.iter("node"))
        if "reconnecting" in screen.lower():
            if not saw_reconnecting:
                note("peer-death-grace", "Observed surviving caller reconnect countdown")
            saw_reconnecting = True
        has_end = any(labels(n).strip().lower() == "end call"
                      for n in root.iter("node"))
        offline = "Offline • Waiting for this device" in screen
        if offline:
            saw_offline = True
        if not has_end and offline:
            saw_ended = True
            elapsed = round(time.monotonic() - started, 1)
            note("peer-death-complete", f"PASS: orphan call ended and peer offline in {elapsed}s")
            break
        time.sleep(3)

    report = {
        "trigger": "adb shell am force-stop, no app hangup signal",
        "source": "same exact-head APK installed on two Android 35 emulators",
        "configured_grace_seconds": 60,
        "saw_reconnecting": saw_reconnecting,
        "call_ended": saw_ended,
        "peer_offline": saw_offline,
        "elapsed_seconds": round(time.monotonic() - started, 1),
        "receiver_remained_stopped": not bool(
            adb(RECEIVER, "shell", "pidof", package, check=False).strip()),
        "survivor_alive": bool(
            adb(CALLER, "shell", "pidof", package, check=False).strip()),
    }
    (OUT / "peer-process-death-acceptance.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8")
    if not saw_ended or not saw_offline or not report["survivor_alive"]:
        raise RuntimeError(
            "Orphan call did not auto-end with offline peer within "
            "110s of an unannounced remote process exit")
    # Immediate terminal WebRTC Failed/Closed is also safe and may bypass a
    # visible reconnect countdown. Report it rather than inventing a pass.
    if not saw_reconnecting:
        note("peer-death-grace",
             "No reconnect UI observed: connection may have ended immediately via ICE")

def main():
    note("setup", "Starting actual Android↔Android voice/video call UI test")
    for serial in (CALLER, RECEIVER):
        if not adb(serial, "shell", "pidof", "com.example.lan_messenger",
                   check=False).strip():
            raise RuntimeError(f"{serial} is not running")
    if os.environ.get("LAN_MESSENGER_SCENARIO") != "video" or not contains(
            CALLER, "video-peer-context", "Video call"):
        tap_label(CALLER, "choose-peer",
                  lambda text: "online" in text.lower() and
                  "looking for nearby" not in text.lower())
    if os.environ.get("LAN_MESSENGER_SCENARIO") == "peer-process-death":
        process_death_test()
        return
    if os.environ.get("LAN_MESSENGER_SCENARIO") == "background-first":
        first_background_incoming_test()
        return
    if os.environ.get("LAN_MESSENGER_SCENARIO") == "video":
        video_call_test()
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
    tap_notification_answer(RECEIVER, "notification-answer", timeout_seconds=26)
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
