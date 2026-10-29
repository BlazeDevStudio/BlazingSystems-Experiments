#!/bin/bash
set -euo pipefail
DIR="${1:?usage: esp_v04_audit.sh ARTIFACT_DIR esp8266|esp32 [OUT]}"
KIND="${2:?missing controller kind}"
OUT="${3:-esp-v04-audit}"
mkdir -p "$OUT"

SUMS="$(find "$DIR" -type f -name SHA256SUMS -print -quit)"
test -n "$SUMS"
(cd "$(dirname "$SUMS")" && sha256sum -c "$(basename "$SUMS")") | tee "$OUT/checksums.txt"

case "$KIND" in
  esp8266) BIN="$(find "$DIR" -type f -name '*BlazePwifiVendo*.bin' ! -name '*elf*' -print | sort | head -n1)" ;;
  esp32) BIN="$(find "$DIR" -type f -name '*BlazePwifiVendo32*.bin' ! -name '*bootloader*' ! -name '*partitions*' -print | sort | head -n1)" ;;
  *) echo "unsupported kind: $KIND" >&2; exit 2;;
esac
test -n "$BIN" -a -s "$BIN"
file "$BIN" | tee "$OUT/file.txt"
python3 -m esptool image_info "$BIN" > "$OUT/esptool.txt" 2>&1 || {
  python3 -m esptool image-info "$BIN" > "$OUT/esptool.txt" 2>&1
}
grep -Eqi 'Image|ESP|Segment|Entry' "$OUT/esptool.txt"

strings "$BIN" > "$OUT/strings.txt"
grep -Fq 'BlazePwifi' "$OUT/strings.txt"
# The original v0.4 path requires the live endpoint marker in compiled bytes.
# Phase A intentionally disables all endpoint callers at compile time, so LTO
# may omit the dead string. Admit this variant ONLY when the exact checksummed
# source shipped beside the binary proves every admission gate remains false.
ENDPOINT_MODE=runtime
if ! grep -Fq 'cgi-bin/vendo' "$OUT/strings.txt"; then
  case "$KIND" in
    esp8266) SKETCH=BlazePwifiVendo ;;
    esp32) SKETCH=BlazePwifiVendo32 ;;
  esac
  SOURCE="$DIR/source/$SKETCH/$SKETCH.ino"
  test -s "$SOURCE" || { echo "missing checksummed Phase A source $SOURCE" >&2; exit 1; }
  for gate in \
    'static constexpr bool kCoinAdmissionEnabled=false;' \
    'bool accepting=kCoinAdmissionEnabled &&' \
    'if(kCoinAdmissionEnabled && insertMode && fsReady &&' \
    'if(kCoinAdmissionEnabled && pendingPulses && pendingReady &&' \
    'if(kCoinAdmissionEnabled && WiFi.status()==WL_CONNECTED'; do
    grep -Fq "$gate" "$SOURCE" || {
      echo "binary missing endpoint and source missing fail-closed gate: $gate" >&2
      exit 1
    }
  done
  ENDPOINT_MODE=phase_a_denied
  echo "$KIND: compiled endpoint optimized out; exact shipped source confirms Phase A denial"
fi
grep -Fq 'Wi-Fi verification failed' "$OUT/strings.txt"

python3 - "$OUT/audit.json" "$KIND" "$BIN" "$ENDPOINT_MODE" <<'PY'
import hashlib,json,sys,os
out,kind,path,mode=sys.argv[1:]
h=hashlib.sha256(open(path,'rb').read()).hexdigest()
json.dump({"target":kind,"release":"0.4.0",
           "validation_level":("compiled-binary-parse-and-protocol-strings" if mode=="runtime"
                               else "compiled-binary-parse-and-source-verified-phase-a-denial"),
           "binary":os.path.basename(path),"sha256":h,
           "checks":{"sha256_manifest":True,"esptool_parse":True,"blazepwifi_marker":True,
                     "vendo_endpoint_marker":mode=="runtime","phase_a_lockdown":mode=="phase_a_denied",
                      "wifi_verification_marker":True}},
          open(out,'w'),indent=2)
PY
echo "$KIND v0.4 binary audit passed ($ENDPOINT_MODE)"
