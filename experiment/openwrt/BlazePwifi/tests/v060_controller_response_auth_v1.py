#!/usr/bin/env python3
"""PHX-G bounded HMAC controller CONFIG reply only, NO coin/relay admission."""
import copy
import hashlib
import hmac
import json
import os
import pathlib
import subprocess
import tempfile
import time
import urllib.parse

ROOT = pathlib.Path(__file__).resolve().parents[1]
COMMON = ROOT / "openwrt/rootfs/usr/lib/blazepwifi/common.sh"
CONTROLLER = ROOT / "openwrt/rootfs/usr/lib/blazepwifi/controller.sh"
VENDO = ROOT / "openwrt/rootfs/www/blazepwifi/cgi-bin/vendo"
KEY = "synthetic-controller-v1-key"
ID = "vendo-01"
TARGET = "1122334455667788"
PREFIX = "blazepwifi-controller-response-v1"

def check(condition, label):
    if not condition:
        raise AssertionError(label)

def valid(reply, action, nonce):
    auth = reply["config_auth"]
    check(auth["version"] == 1 and auth["action"] == action, "version/action")
    check(auth["controller_id"] == ID and auth["request_nonce"] == nonce, "binding")
    check(auth["admission_allowed"] is False, "admission unexpectedly granted")
    policy = json.dumps(reply["controller"], separators=(",", ":"), ensure_ascii=False)
    check(auth["policy_sha256"] == hashlib.sha256(policy.encode()).hexdigest(), "policy SHA")
    check(auth["revision"] == reply["controller"]["config_revision"], "revision match")
    if action == "poll":
        check(auth["insert"] == reply["insert"], "legacy insert binding")
        check(auth["target_nonce"] == reply["target_nonce"], "target binding")
        check(auth["expires"] == reply["expires"], "expiry binding")
    parts = [PREFIX, action, ID, nonce, str(auth["revision"]), auth["policy_sha256"],
             str(auth["insert"]), auth["target_nonce"], str(auth["expires"]), "DENY"]
    expected = hmac.new(KEY.encode(), "|".join(parts).encode(), hashlib.sha256).hexdigest()
    check(hmac.compare_digest(auth["signature"], expected), "signature HMAC")
    return auth

with tempfile.TemporaryDirectory(prefix="phx-controller-auth-v1-") as d:
    t = pathlib.Path(d)
    (t / "bin").mkdir()
    (t / "state/targets").mkdir(parents=True)
    (t / "run").mkdir()
    uci = t / "bin/uci"
    uci.write_text("""#!/bin/sh
case "$*" in
 *'get blazepwifi.main.vendo_key') echo synthetic-controller-v1-key;;
 *'get blazepwifi.main.vendo_port') echo 4455;;
 *'get blazepwifi.main.durable_sync') echo 0;;
 *) exit 1;;
esac
""")
    uci.chmod(0o700)
    env = dict(os.environ, PATH=str(t / "bin")+":"+os.environ["PATH"],
               BP_STATE=str(t / "state"), BP_RUN=str(t / "run"),
               BP_LIB=str(COMMON), BP_CONTROLLER_LIB=str(CONTROLLER),
               BP_RENTAL_LIB=str(ROOT / "openwrt/rootfs/usr/lib/blazepwifi/rental.sh"),
               BP_MEMBER_LIB=str(ROOT / "openwrt/rootfs/usr/lib/blazepwifi/member.sh"),
               REQUEST_METHOD="POST", SERVER_PORT="4455", REMOTE_ADDR="10.0.0.50")
    def request(action, nonce):
        sig = hashlib.sha256(f"{KEY}|{action}|{ID}|{nonce}|0||{KEY}".encode()).hexdigest()
        body = urllib.parse.urlencode(dict(action=action,id=ID,nonce=nonce,pulses="0",target="",sig=sig))
        p = subprocess.run(["sh", str(VENDO)], input=body, text=True, capture_output=True,
                           env=env, check=True, timeout=15)
        # subprocess(text=True) normalizes HTTP CRLF to LF on Linux.
        # Parse either platform without altering CGI response bytes.
        normalized = p.stdout.replace("\r\n", "\n")
        check("\n\n" in normalized, "JSON headers")
        return json.loads(normalized.split("\n\n", 1)[1])
    nr = "0011223344556677"
    reg = request("register", nr)
    check(reg["ok"] is True, "register response")
    valid(reg, "register", nr)
    check(reg["controller"]["enabled"] == 0, "unknown controller not disabled")
    print("PHX-G-CFG-AUTH case 1 register HMAC + unknown deny PASS")
    exp = int(time.time()) + 240
    (t/"state/targets"/(ID+".tsv")).write_text(
        f"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\taa:bb:cc:dd:ee:ff\t{TARGET}\t{exp}\t{ID}\thotspot\n")
    np = "1122334455667788"
    inactive = request("poll", np)
    valid(inactive, "poll", np)
    check(inactive["insert"] == 0, "unknown poll granted insert")
    print("PHX-G-CFG-AUTH case 2 poll disabled + HMAC PASS")
    admin = dict(env, REQUEST_METHOD="GET")
    cmd = f'. "{COMMON}"; . "{CONTROLLER}"; bp_controller_set {ID} 1 1 1 1 -1 -1 -1 1 1 1 40 400 6'
    subprocess.run(["sh","-c",cmd],env=admin,check=True,timeout=15)
    na = "2233445566778899"
    active = request("poll", na)
    valid(active, "poll", na)
    check(active["insert"] == 1 and active["config_auth"]["admission_allowed"] is False,
          "legacy insert must never grant protected admission")
    print("PHX-G-CFG-AUTH case 3 legacy insert independently denied PASS")
    tampered = copy.deepcopy(active)
    tampered["controller"]["coin_enabled"] = 0
    try: valid(tampered, "poll", na)
    except AssertionError: pass
    else: raise AssertionError("tampered policy accepted")
    print("PHX-G-CFG-AUTH case 4 policy tamper denied PASS")
    tampered = copy.deepcopy(active)
    tampered["config_auth"]["request_nonce"] = "0011001100110011"
    try: valid(tampered, "poll", na)
    except AssertionError: pass
    else: raise AssertionError("nonce tamper accepted")
    print("PHX-G-CFG-AUTH case 5 nonce tamper denied PASS")
    tampered = copy.deepcopy(active)
    tampered["config_auth"]["target_nonce"] = "ffeeddccbbaa9988"
    try: valid(tampered, "poll", na)
    except AssertionError: pass
    else: raise AssertionError("target tamper accepted")
    print("PHX-G-CFG-AUTH case 6 target tamper denied PASS")
    different = request("poll", "33445566778899aa")
    valid(different, "poll", "33445566778899aa")
    try: valid(active, "poll", "33445566778899aa")
    except AssertionError: pass
    else: raise AssertionError("replayed response accepted for new nonce")
    print("PHX-G-CFG-AUTH case 7 replay-to-new-nonce denied PASS")
    fake = t/"bin/openssl"
    fake.write_text("#!/bin/sh\nexit 74\n")
    fake.chmod(0o700)
    broken = request("poll", "445566778899aabb")
    check(broken["ok"] is False and "authentication unavailable" in broken["error"],
          "openssl failure must deny, never unsigned fallback")
    print("PHX-G-CFG-AUTH case 8 missing signer denies response PASS")
    print("PHX-G-CFG-AUTH 8/8 synthetic host cases PASS; protected reboot highwater=UNPROVEN; physical admission=DENY")
