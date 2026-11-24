#!/usr/bin/env python3
"""Guard the current CGI register/poll envelope boundary.

The current server's register and poll replies are unsigned. The member_snapshot
response_sig is domain-separated and is not a controller poll authorization.
This lab keeps the firmware consumer deny-only until CORE/QA approve a canonical
register/poll contract. Candidate signature state is adversarial input, not a
verified signature. Host compilation is simulated control-flow evidence.
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


def _validate_cgi_envelope(register: str, poll: str, snapshot: str,
                           snapshot_sig: str) -> None:
    _require("response_sig" not in register,
             "REGISTER_RESPONSE_UNEXPECTEDLY_HAS_RESPONSE_SIG")
    _require("response_sig" not in poll,
             "POLL_RESPONSE_UNEXPECTEDLY_HAS_RESPONSE_SIG")
    _require('"server_time":%s' in register and '"controller":%s' in register,
             "REGISTER_RESPONSE_TEMPLATE_CHANGED")
    _require('"target_nonce":"%s"' in poll and '"expires":%s' in poll and
             '"controller":%s' in poll,
             "POLL_RESPONSE_TEMPLATE_CHANGED")
    _require("member_snapshot_sig" in snapshot and "response_sig" in snapshot,
             "MEMBER_SNAPSHOT_RESPONSE_SIGNATURE_MISSING")
    _require("|member_snapshot|" in snapshot_sig,
             "MEMBER_SNAPSHOT_SIGNATURE_DOMAIN_CHANGED")


CPP_MAIN = r"""
int verifyDenied(const String &payload, const String &candidateSignature,
                 const String &target, bool insert) {
  insertMode=true;
  activeTarget="stale-target";
  // Adversarial preloaded state only; this is not a verified payload signature.
  responseSignature=candidateSignature;
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
    String("unverified-candidate-signature"), String(""), false);
  if(result) return 30+result;
  std::cout<<"MEMBER_SNAPSHOT_SHAPED_RESPONSE_REMAINS_DENIED_PASS\n";
  std::cout<<"CURRENT_CGI_ENVELOPE_DENY_PASS 3/3\n";
  return 0;
}
"""


def _compile_and_run(board: str, code: str, label: str):
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
            raise RuntimeError(
                f"{board} {label}: compile failed:\n{built.stderr[-3000:]}"
            )
        return subprocess.run(
            [str(binary)], capture_output=True, text=True, timeout=10
        )


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

    _validate_cgi_envelope(register, poll, snapshot, snapshot_sig)

    source_mutations = (
        ("register-response-sig-injection",
         register + "\nresponse_sig=unapproved", poll, snapshot, snapshot_sig),
        ("poll-response-sig-injection",
         register, poll + "\nresponse_sig=unapproved", snapshot, snapshot_sig),
        ("member-snapshot-signature-removal",
         register, poll, snapshot.replace("response_sig", "missing_sig"), snapshot_sig),
        ("member-snapshot-domain-confusion",
         register, poll, snapshot,
         snapshot_sig.replace("|member_snapshot|", "|poll|", 1)),
    )
    for label, mutant_register, mutant_poll, mutant_snapshot, mutant_sig in source_mutations:
        if label == "member-snapshot-domain-confusion" and mutant_sig == snapshot_sig:
            raise SystemExit("CGI_DOMAIN_MUTATION_ANCHOR_MISSING")
        try:
            _validate_cgi_envelope(
                mutant_register, mutant_poll, mutant_snapshot, mutant_sig
            )
        except (AssertionError, SystemExit):
            print(f"CGI_SOURCE_MUTATION_REJECTED {label}")
        else:
            raise SystemExit(f"CGI_SOURCE_MUTATION_SURVIVED: {label}")
    print("CURRENT_CGI_SOURCE_MUTATION_REJECTION_PASS 4/4")

    for board, sketch_path in boards.items():
        source = sketch_path.read_text(encoding="utf-8")
        target_define = "#define TARGET_ESP32\n" if board == "ESP32" else ""
        accept = extract(source, "acceptPollResponse")
        ingress = extract(source, "coinIngressConfigurationAllows")
        outputs = extract(source, "applyOutputs")
        if accept.count("return false;") != 1:
            raise SystemExit(f"{board}: ACCEPT_POLL_DENY_ANCHOR_CHANGED")
        suspend_gate = "!pollIntakeSuspended &&"
        if outputs.count(suspend_gate) != 1:
            raise SystemExit(f"{board}: POLL_INTAKE_SUSPEND_GATE_CHANGED")

        prefix = target_define + stubs
        suffix = ingress + outputs + CPP_MAIN
        code = prefix + accept + suffix
        ran = _compile_and_run(board, code, "deny baseline")
        if ran.returncode:
            raise RuntimeError(
                f"{board}: current CGI envelope deny failed ({ran.returncode}): "
                f"{ran.stdout}\n{ran.stderr}"
            )
        if "CURRENT_CGI_ENVELOPE_DENY_PASS 3/3" not in ran.stdout:
            raise RuntimeError(f"{board}: missing 3/3 pass marker: {ran.stdout}")
        print(f"{board}: {ran.stdout.strip().replace(chr(10), '; ')}")

        accept_mutant = accept.replace("return false;", "return true;", 1)
        accept_mutant_run = _compile_and_run(
            board, prefix + accept_mutant + suffix, "acceptPollResponse fail-open mutation"
        )
        if accept_mutant_run.returncode == 0:
            raise SystemExit(f"{board}: ACCEPT_POLL_FAIL_OPEN_MUTATION_SURVIVED")
        print(
            f"{board}: MUTATION_REJECTED acceptPollResponse-return-true "
            f"(exit={accept_mutant_run.returncode})"
        )

        outputs_mutant = outputs.replace(suspend_gate, "true &&", 1)
        outputs_mutant_run = _compile_and_run(
            board, prefix + accept + ingress + outputs_mutant + CPP_MAIN,
            "pollIntakeSuspended bypass mutation",
        )
        if outputs_mutant_run.returncode == 0:
            raise SystemExit(f"{board}: POLL_INTAKE_SUSPEND_BYPASS_MUTATION_SURVIVED")
        print(
            f"{board}: MUTATION_REJECTED pollIntakeSuspended-bypass "
            f"(exit={outputs_mutant_run.returncode})"
        )

    print("CURRENT_CGI_CONSUMER_MUTATION_REJECTION_PASS 2/2 per board")
    print("SIMULATED_ONLY=1")
    print("PHYSICAL_COIN_ACCEPTOR_VERIFIED=0")
