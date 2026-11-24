#!/usr/bin/env python3
"""Guard the current CGI register/poll envelope boundary.

The current server's register and poll replies are unsigned. The member_snapshot
response_sig is domain-separated and is not a controller poll authorization.
This lab keeps the firmware consumer deny-only until CORE/QA approve a canonical
register/poll contract. Host compilation is simulated control-flow evidence.
"""
from pathlib import Path
import subprocess
import tempfile


def _action_block(source: str, label: str) -> str:
    marker = f"  {label})"
    start = source.find(marker)
    if start < 0:
        raise AssertionError(f"CGI action block missing: {label}")
    end = source.find("\n    ;;", start)
    if end < 0:
        raise AssertionError(f"CGI action block unterminated: {label}")
    return source[start:end]


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


CPP_MAIN = r"""
int verifyDenied(const String &payload, const String &signature,
                 const String &target, bool insert) {
  insertMode=true;
  activeTarget="stale-target";
  responseSignature=signature;
  responseTarget=target;
  responseInsert=insert;
  applyRemoteConfigCalls=0;
  remoteRevision=7;
  runRelayPin=26;
  runCoinActiveLow=true;
  runRelayActiveHigh=true;
  runDebounceMs=70;
  pollIntakeSuspended=true;
  relayOn=true;
  ledOn=true;
  applyOutputs();
  if(relayOn || ledOn) return 1;

  const bool accepted=acceptPollResponse(payload);
  pollIntakeSuspended=false;
  applyOutputs();
  if(accepted || insertMode || !activeTarget.empty() || relayOn || ledOn ||
     applyRemoteConfigCalls!=0 || remoteRevision!=7 || runRelayPin!=26 ||
     !runCoinActiveLow || !runRelayActiveHigh || runDebounceMs!=70) return 2;
  return 0;
}
int main() {
  int result=verifyDenied(
    String(R"PHX({"ok":true,"server_time":1700000000,"controller":{"enabled":1,"coin_enabled":1}})PHX"),
    String(""), String(""), false);
  if(result) return 10+result;
  std::cout<<"CURRENT_CGI_REGISTER_NO_SIGNATURE_DENY_PASS\n";

  result=verifyDenied(
    String(R"PHX({"ok":true,"insert":1,"target_nonce":"target-05","expires":1700000000,"controller":{"enabled":1,"coin_enabled":1}})PHX"),
    String(""), String("target-05"), true);
  if(result) return 20+result;
  std::cout<<"CURRENT_CGI_POLL_NO_SIGNATURE_DENY_PASS\n";

  // This endpoint has a response_sig, but its signed domain is member_snapshot,
  // and its payload contains no insert/target authorization fields.
  result=verifyDenied(
    String(R"PHX({"ok":true,"member_revision":7,"payload_sha256":"0123456789abcdef","members":[],"response_sig":"member-snapshot-signature"})PHX"),
    String("valid-signature"), String(""), false);
  if(result) return 30+result;
  std::cout<<"MEMBER_SNAPSHOT_SIGNATURE_NOT_POLL_AUTHORITY_PASS\n";
  std::cout<<"CURRENT_CGI_ENVELOPE_DENY_PASS 3/3\n";
  return 0;
}
"""


def verify(boards, extract, stubs):
    root = Path(__file__).resolve().parents[2]
    cgi_path = root / "openwrt/rootfs/www/blazepwifi/cgi-bin/vendo"
    if not cgi_path.is_file():
        raise SystemExit(f"CURRENT_CGI_SOURCE_MISSING: {cgi_path}")
    cgi = cgi_path.read_text(encoding="utf-8")

    register = _action_block(cgi, "register|ping")
    poll = _action_block(cgi, "poll")
    snapshot = _action_block(cgi, "member_snapshot")
    snapshot_sig_start = cgi.find("member_snapshot_sig() {")
    if snapshot_sig_start < 0:
        raise SystemExit("MEMBER_SNAPSHOT_SIGNATURE_FUNCTION_MISSING")
    snapshot_sig_end = cgi.find("\n}", snapshot_sig_start)
    if snapshot_sig_end < 0:
        raise SystemExit("MEMBER_SNAPSHOT_SIGNATURE_FUNCTION_UNTERMINATED")
    snapshot_sig = cgi[snapshot_sig_start:snapshot_sig_end]

    _require("response_sig" not in register,
             "REGISTER_RESPONSE_UNEXPECTEDLY_HAS_RESPONSE_SIG")
    _require("response_sig" not in poll,
             "POLL_RESPONSE_UNEXPECTEDLY_HAS_RESPONSE_SIG")
    _require('"server_time":%s' in register and '"controller":%s' in register,
             "REGISTER_RESPONSE_TEMPLATE_CHANGED")
    _require('"target_nonce":"%s"' in poll and '"expires":%s' in poll and '"controller":%s' in poll,
             "POLL_RESPONSE_TEMPLATE_CHANGED")
    _require("member_snapshot_sig" in snapshot and "response_sig" in snapshot,
             "MEMBER_SNAPSHOT_RESPONSE_SIGNATURE_MISSING")
    _require("|member_snapshot|" in snapshot_sig,
             "MEMBER_SNAPSHOT_SIGNATURE_DOMAIN_CHANGED")

    for board, sketch_path in boards.items():
        source = sketch_path.read_text(encoding="utf-8")
        code = ("#define TARGET_ESP32\n" if board == "ESP32" else "")
        code += stubs
        code += extract(source, "acceptPollResponse")
        code += extract(source, "coinIngressConfigurationAllows")
        code += extract(source, "applyOutputs")
        code += CPP_MAIN
        with tempfile.TemporaryDirectory(prefix="phx-current-cgi-envelope-") as folder:
            cpp = Path(folder) / "current_cgi_envelope.cpp"
            binary = Path(folder) / "current_cgi_envelope"
            cpp.write_text(code, encoding="utf-8")
            built = subprocess.run(
                ["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror",
                 "-Wno-unused-parameter", str(cpp), "-o", str(binary)],
                capture_output=True, text=True, timeout=30,
            )
            if built.returncode:
                raise RuntimeError(f"{board}: compile failed:\n{built.stderr[-3000:]}")
            ran = subprocess.run([str(binary)], capture_output=True, text=True, timeout=10)
            if ran.returncode:
                raise RuntimeError(
                    f"{board}: current CGI envelope deny failed ({ran.returncode}): "
                    f"{ran.stdout}\n{ran.stderr}"
                )
            if "CURRENT_CGI_ENVELOPE_DENY_PASS 3/3" not in ran.stdout:
                raise RuntimeError(f"{board}: missing 3/3 pass marker: {ran.stdout}")
            print(f"{board}: {ran.stdout.strip().replace(chr(10), '; ')}")

    print("SIMULATED_ONLY=1")
    print("PHYSICAL_COIN_ACCEPTOR_VERIFIED=0")
