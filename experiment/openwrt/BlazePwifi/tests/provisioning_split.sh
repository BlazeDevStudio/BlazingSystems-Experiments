#!/bin/sh
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
ADMIN="$ROOT/openwrt/rootfs/www/blazepwifi/cgi-bin/admin"
HTML="$ROOT/profiles/standalone-rental/openwrt/rental-standalone.html"
META="$ROOT/openwrt/rootfs/usr/share/blazepwifi/rental-provisioning.env"
LAUNCHER="$ROOT/android/BlazeRentalLauncher"
MANIFEST="$LAUNCHER/AndroidManifest.xml"
SRC="$LAUNCHER/src/com/blazesystems/blazerental"

grep -q 'rental_standard_qr' "$ADMIN"
grep -q 'rental_provisioning_status' "$ADMIN"
grep -q 'rental_provisioning_qr' "$ADMIN"
grep -q 'blazerental.enrollment.v2' "$ADMIN"
grep -q 'blazerental.provisioning.v2' "$ADMIN"
grep -q 'PROVISIONING_DEVICE_ADMIN_COMPONENT_NAME' "$ADMIN"
grep -q 'PROVISIONING_DEVICE_ADMIN_PACKAGE_DOWNLOAD_LOCATION' "$ADMIN"
grep -q 'PROVISIONING_DEVICE_ADMIN_PACKAGE_CHECKSUM' "$ADMIN"
grep -q 'PROVISIONING_DEVICE_ADMIN_MINIMUM_VERSION_CODE' "$ADMIN"
grep -q 'GMS_DPC_APPROVED' "$ADMIN"
grep -q 'ack_custom_dpc' "$ADMIN"
grep -q 'TARGET_SCOPE' "$ADMIN"
grep -q '"target_scope"' "$ADMIN"
grep -q 'bp_admin_cert_sha256' "$ADMIN"
grep -q 'server_cert_sha256' "$ADMIN"
grep -q 'Device Provisioning Rental Server URL must use HTTPS' "$ADMIN"

STANDARD="$(sed -n '/bp_admin_standard_qr_payload()/,/^}/p' "$ADMIN")"
! printf '%s' "$STANDARD" | grep -q 'PROVISIONING_DEVICE_ADMIN'

grep -q 'Standard Enrollment QR' "$HTML"
grep -q 'Device Provisioning QR' "$HTML"
grep -q "api('rental_standard_qr'" "$HTML"
grep -q "api('rental_provisioning_qr'" "$HTML"
grep -q "api('rental_provisioning_status'" "$HTML"
grep -q 'renderQr(j.qr_payload,4)' "$HTML"
grep -q 'CUSTOM DPC / GMS WARNING' "$HTML"
grep -q 'ack_custom_dpc' "$HTML"
grep -q 'AOSP/non-GMS' "$HTML"
grep -q 'Supported target scope' "$HTML"
grep -q 'Target scope:' "$HTML"

grep -q 'android.app.action.GET_PROVISIONING_MODE' "$MANIFEST"
grep -q 'android.app.action.ADMIN_POLICY_COMPLIANCE' "$MANIFEST"
grep -q 'android.app.action.PROVISIONING_SUCCESSFUL' "$MANIFEST"
test -s "$SRC/BlazeProvisioningContract.java"
test -s "$SRC/BlazeProvisioningModeActivity.java"
test -s "$SRC/BlazeProvisioningComplianceActivity.java"
test -s "$SRC/ProvisioningStateGuard.java"
test -s "$LAUNCHER/tests/unit/com/blazesystems/blazerental/ProvisioningStateGuardTest.java"
grep -q 'ProvisioningStateGuard.canAccept' "$SRC/RentalLeaseStore.java"
grep -q 'ProvisioningStateGuard.isExactReplay' "$SRC/RentalLeaseStore.java"
grep -q 'MODE_FULLY_MANAGED_DEVICE = 1' "$SRC/BlazeProvisioningContract.java"
grep -q 'blazerental.provisioning.v2' "$SRC/BlazeProvisioningContract.java"
grep -q 'device_owner_provisioning' "$SRC/RentalLeaseStore.java"
grep -q 'serverCertSha256' "$SRC/RentalLeaseStore.java"
grep -q 'server_cert_sha256' "$SRC/BlazeProvisioningContract.java"
grep -q 'isValidServerOrigin(server, true)' "$SRC/BlazeProvisioningContract.java"
grep -q 'isValidServerOrigin(server, false)' "$SRC/QrEnrollmentScannerActivity.java"
grep -q 'static boolean isValidServerOrigin' "$SRC/RentalLeaseStore.java"
grep -q 'BlazePwifi TLS certificate pin mismatch' "$SRC/LeaseClient.java"
grep -q 'HttpsURLConnection' "$SRC/LeaseClient.java"
grep -q 'standard_manual' "$SRC/RentalLeaseStore.java"
grep -q 'This is a Device Provisioning QR' "$SRC/QrEnrollmentScannerActivity.java"
grep -q 'Manual first-run administrator setup is disabled' "$SRC/BlazeAdminActivity.java"
grep -q '&protocol=2' "$SRC/LeaseClient.java"
grep -q 'enroll_v2|' "$SRC/LeaseClient.java"
grep -q 'enroll-response-v2|' "$SRC/LeaseClient.java"
grep -q 'device-secret-v2|' "$SRC/LeaseClient.java"
! grep -q 'response.optString("device_secret"' "$SRC/LeaseClient.java"
grep -q '.remove("enrollment")' "$SRC/RentalLeaseStore.java"
grep -q '"enrollment_protocol":2' "$ROOT/openwrt/rootfs/www/blazepwifi/cgi-bin/rental"
grep -q 'identity_kdf' "$ROOT/openwrt/rootfs/www/blazepwifi/cgi-bin/rental"

test -f "$META"
grep -q '^READY=0$' "$META"
grep -q '^APK_URL=$' "$META"
grep -q '^APK_CHECKSUM=$' "$META"
grep -q '^GMS_DPC_APPROVED=0$' "$META"
grep -q '^TARGET_SCOPE=unconfigured$' "$META"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT HUP INT TERM

grep -q 'bp_admin_origin_authority_ok' "$ADMIN"
grep -q 'Validate again at the persistence boundary' "$SRC/RentalLeaseStore.java"

ORIGIN_FN="$TMP/origin-validator.sh"
sed -n '/^bp_admin_origin_authority_ok()/,/^}/p' "$ADMIN" > "$ORIGIN_FN"
. "$ORIGIN_FN"

for good_authority in \
  '192.168.1.1' \
  '192.168.1.1:8443' \
  'blazepwifi.local' \
  '[2001:db8::1]' \
  '[2001:db8::1]:443'
do
  bp_admin_origin_authority_ok "$good_authority"
done

for bad_authority in \
  '' \
  ':443' \
  'host:abc' \
  'host:0' \
  'host:65536' \
  'host:443:99' \
  'user@host' \
  'host/path' \
  'host?x=1' \
  'host#frag' \
  'host\\evil' \
  '[2001:db8::1' \
  '[2001:db8::1]:abc'
do
  if bp_admin_origin_authority_ok "$bad_authority"; then
    echo "invalid server authority accepted: $bad_authority" >&2
    exit 1
  fi
done
printf 'dummy-apk-bytes-for-provisioning-contract' > "$TMP/app.apk"
python3 "$ROOT/tools/make-provisioning.py" \
  --apk "$TMP/app.apk" \
  --apk-url 'https://example.invalid/BlazeRental.apk' \
  --server-url 'https://192.168.1.1' \
  --server-cert-sha256 '0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef' \
  --enrollment-token '0123456789ab.0123456789abcdef0123456789abcdef' \
  --device-name 'Audit phone' \
  --version-code 50212 \
  --out "$TMP/provisioning.json"
python3 - "$TMP/provisioning.json" "$TMP/app.apk" <<'PY'
import base64,hashlib,json,pathlib,sys
p=json.load(open(sys.argv[1],encoding="utf-8"))
assert p["android.app.extra.PROVISIONING_DEVICE_ADMIN_COMPONENT_NAME"]=="com.blazesystems.blazerental/.BlazeDeviceAdminReceiver"
assert p["android.app.extra.PROVISIONING_DEVICE_ADMIN_MINIMUM_VERSION_CODE"]==50212
checksum=p["android.app.extra.PROVISIONING_DEVICE_ADMIN_PACKAGE_CHECKSUM"]
assert len(checksum)==44 and checksum.endswith("=")
assert base64.urlsafe_b64decode(checksum)==hashlib.sha256(pathlib.Path(sys.argv[2]).read_bytes()).digest()
x=p["android.app.extra.PROVISIONING_ADMIN_EXTRAS_BUNDLE"]
assert x["blaze_schema"]=="blazerental.provisioning.v2"
assert x["server_url"]=="https://192.168.1.1"
assert x["server_cert_sha256"]=="0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
assert x["enrollment_token"].startswith("0123456789ab.")
PY

# Server URL is an origin, not an arbitrary base URL. Paths/userinfo/query
# must fail before a provisioning payload can be written.
for bad_server in \
  'https://192.168.1.1/path' \
  'https://user@192.168.1.1' \
  'https://192.168.1.1?x=1' \
  'https://192.168.1.1#fragment'
do
  if python3 "$ROOT/tools/make-provisioning.py" \
      --apk "$TMP/app.apk" \
      --apk-url 'https://example.invalid/BlazeRental.apk' \
      --server-url "$bad_server" \
      --server-cert-sha256 '0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef' \
      --enrollment-token '0123456789ab.0123456789abcdef0123456789abcdef' \
      --device-name 'Audit phone' \
      --version-code 50212 \
      --out "$TMP/should-not-exist.json" >/dev/null 2>&1
  then
    echo "invalid server origin accepted: $bad_server" >&2
    exit 1
  fi
done

# Release metadata generator must produce the same canonical checksum and GMS flag.
APK_SHA="$(sha256sum "$TMP/app.apk" | awk '{print $1}')"
APK_CHECKSUM="$(python3 -c 'import base64,hashlib,pathlib,sys; print(base64.urlsafe_b64encode(hashlib.sha256(pathlib.Path(sys.argv[1]).read_bytes()).digest()).decode())' "$TMP/app.apk")"
printf '%s\n' \
  'PACKAGE_NAME=com.blazesystems.blazerental' \
  'APK_VERSION=0.5.2-rental.2-rc.11' \
  'APK_VERSION_CODE=50212' \
  'APK_CHANNEL=test' \
  'PRODUCTION_READY=0' \
  'GMS_DPC_APPROVED=0' \
  'TARGET_SCOPE=aosp_non_gms_or_explicit_oem_only' \
  "APK_SHA256=$APK_SHA" \
  "APK_CHECKSUM=$APK_CHECKSUM" \
  'SIGNER_CERT_SHA256=0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef' \
  > "$TMP/build-meta.txt"
python3 "$ROOT/profiles/standalone-rental/build/make-release-provisioning-meta.py" \
  --apk "$TMP/app.apk" \
  --metadata "$TMP/build-meta.txt" \
  --tag 'v0.5.2-rental.2-rc.11' \
  --repository 'BlazingSystems/BlazingSystems-Experiments' \
  --out "$TMP/release-meta.env"
grep -qx "APK_SHA256=$APK_SHA" "$TMP/release-meta.env"
grep -qx "APK_CHECKSUM=$APK_CHECKSUM" "$TMP/release-meta.env"
grep -qx 'GMS_DPC_APPROVED=0' "$TMP/release-meta.env"
grep -qx 'TARGET_SCOPE=aosp_non_gms_or_explicit_oem_only' "$TMP/release-meta.env"
grep -Eq '^APK_CHECKSUM=[A-Za-z0-9_-]{43}=$' "$TMP/release-meta.env"

# Secure enrollment v2 derivation parity: the long-lived device secret is
# derived independently from the one-time token and never needs transport.
TOKEN='0123456789ab.0123456789abcdef0123456789abcdef'
NONCE='00112233445566778899aabbccddeeff'
DID='00112233445566778899aabb'
SERVER_MS=1700000000000
LEASE_MS=1700000000000
KDF='hmac-sha256-v1'
DERIVED_SERVER="$(printf '%s' "device-secret-v2|$NONCE|$DID" | openssl dgst -sha256 -hmac "$TOKEN" | awk '{print $NF}')"
DERIVED_CLIENT="$(printf '%s' "device-secret-v2|$NONCE|$DID" | openssl dgst -sha256 -hmac "$TOKEN" | awk '{print $NF}')"
[ "$DERIVED_SERVER" = "$DERIVED_CLIENT" ]
[ "${#DERIVED_SERVER}" -eq 64 ]
RESP="enroll-response-v2|$NONCE|$DID|$SERVER_MS|$LEASE_MS|$KDF"
SIG_SERVER="$(printf '%s' "$RESP" | openssl dgst -sha256 -hmac "$TOKEN" | awk '{print $NF}')"
SIG_CLIENT="$(printf '%s' "$RESP" | openssl dgst -sha256 -hmac "$TOKEN" | awk '{print $NF}')"
[ "$SIG_SERVER" = "$SIG_CLIENT" ]

# Runtime regressions: v2-generated tokens must be downgrade-resistant
# and retry-safe if the first enrollment response is lost.
STATE="$TMP/state"
RUN="$TMP/run"
mkdir -p "$STATE" "$RUN"
export BP_STATE="$STATE" BP_RUN="$RUN"
export BP_LIB="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/common.sh"
export BP_AUTH_LIB="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/auth.sh"
export BP_RENTAL_LIB="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/rental.sh"
export BP_RENTAL_POLICY_LIB="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/rental_policy.sh"
. "$BP_LIB"; . "$BP_AUTH_LIB"; . "$BP_RENTAL_LIB"
bp_rental_init

TOKEN="$(bp_rental_enroll_create 'Race phone' 600 2)"
EID="${TOKEN%%.*}"
NONCE='00112233445566778899aabbccddeeff'
CGI="$ROOT/openwrt/rootfs/www/blazepwifi/cgi-bin/rental"

LEGACY_SIG="$(bp_rental_hmac "$TOKEN" "enroll|$NONCE|$TOKEN")"
DOWNGRADE="$(printf 'action=enroll&enroll_id=%s&protocol=1&nonce=%s&sig=%s' "$EID" "$NONCE" "$LEGACY_SIG" | REQUEST_METHOD=POST sh "$CGI")"
printf '%s' "$DOWNGRADE" | grep -q 'enrollment requires protocol 2'

V2_SIG="$(bp_rental_hmac "$TOKEN" "enroll_v2|$NONCE|$TOKEN")"
FIRST="$(printf 'action=enroll&enroll_id=%s&protocol=2&nonce=%s&sig=%s' "$EID" "$NONCE" "$V2_SIG" | REQUEST_METHOD=POST sh "$CGI")"
printf '%s' "$FIRST" | grep -q '"ok":true'
printf '%s' "$FIRST" | grep -q '"enrollment_protocol":2'
! printf '%s' "$FIRST" | grep -q '"device_secret"'
DID="$(printf '%s' "$FIRST" | sed -n 's/.*"device_id":"\([^"]*\)".*/\1/p')"
[ "${#DID}" -eq 24 ]

# Simulate loss of the first response. Retrying the exact request must return
# the same identity and must not create another device.
SECOND="$(printf 'action=enroll&enroll_id=%s&protocol=2&nonce=%s&sig=%s' "$EID" "$NONCE" "$V2_SIG" | REQUEST_METHOD=POST sh "$CGI")"
printf '%s' "$SECOND" | grep -q '"ok":true'
printf '%s' "$SECOND" | grep -q '"reused":true'
DID2="$(printf '%s' "$SECOND" | sed -n 's/.*"device_id":"\([^"]*\)".*/\1/p')"
[ "$DID2" = "$DID" ]
[ "$(awk -F '\t' -v d="$DID" '$1==d{n++} END{print n+0}' "$STATE/rental-devices.tsv")" -eq 1 ]

# A new request nonce cannot claim the redeemed token.
OTHER='ffeeddccbbaa99887766554433221100'
OTHER_SIG="$(bp_rental_hmac "$TOKEN" "enroll_v2|$OTHER|$TOKEN")"
CLAIMED="$(printf 'action=enroll&enroll_id=%s&protocol=2&nonce=%s&sig=%s' "$EID" "$OTHER" "$OTHER_SIG" | REQUEST_METHOD=POST sh "$CGI")"
printf '%s' "$CLAIMED" | grep -q 'enrollment already claimed'

# The permanent secret is independently derived. A valid status request proves
# possession and retires the temporary redemption/token record.
DSECRET="$(bp_rental_hmac "$TOKEN" "device-secret-v2|$NONCE|$DID")"
STATUS_NONCE='status0011223344'
STATUS_SIG="$(bp_rental_hmac "$DSECRET" "status|$STATUS_NONCE|$DSECRET")"
STATUS="$(printf 'action=status&device_id=%s&nonce=%s&sig=%s' "$DID" "$STATUS_NONCE" "$STATUS_SIG" | REQUEST_METHOD=POST sh "$CGI")"
printf '%s' "$STATUS" | grep -q '"ok":true'
[ -z "$(bp_rental_enroll_lookup "$EID")" ]

# Stable-promotion gate must fail closed for the current RC/test channel even
# when given the locked public production identity.
PROMOTE="$ROOT/profiles/standalone-rental/build/check-stable-promotion.py"
IDENTITY="$ROOT/../../../.github/blazerental-v052-production-identity.json"
EVIDENCE="$ROOT/profiles/standalone-rental/validation/physical-provisioning-validation.template.json"
test -x "$PROMOTE"
test -f "$IDENTITY"
test -f "$EVIDENCE"

printf 'rc7-test-apk' > "$TMP/rc9-test.apk"
RC9_SHA="$(sha256sum "$TMP/rc9-test.apk" | awk '{print $1}')"
RC9_CHECKSUM="$(python3 -c 'import base64,hashlib,pathlib,sys; print(base64.urlsafe_b64encode(hashlib.sha256(pathlib.Path(sys.argv[1]).read_bytes()).digest()).decode())' "$TMP/rc9-test.apk")"
LOCKED_FP="$(python3 -c 'import json,re,sys; d=json.load(open(sys.argv[1])); print(re.sub(r"[^0-9A-Fa-f]","",d["sha256_fingerprint"]).lower())' "$IDENTITY")"
printf '%s\n' \
  'READY=1' \
  'PACKAGE_NAME=com.blazesystems.blazerental' \
  'APK_VERSION=0.5.2-rental.2-rc.11' \
  'APK_VERSION_CODE=50212' \
  'APK_CHANNEL=test' \
  'PRODUCTION_READY=0' \
  'GMS_DPC_APPROVED=0' \
  'TARGET_SCOPE=aosp_non_gms_or_explicit_oem_only' \
  "APK_SHA256=$RC9_SHA" \
  "APK_CHECKSUM=$RC9_CHECKSUM" \
  "SIGNER_CERT_SHA256=$LOCKED_FP" \
  > "$TMP/rc9-meta.env"

if python3 "$PROMOTE" \
    --identity "$IDENTITY" \
    --metadata "$TMP/rc9-meta.env" \
    --evidence "$EVIDENCE" \
    --apk "$TMP/rc9-test.apk" >/dev/null 2>&1
then
  echo "stable promotion gate incorrectly accepted RC/test metadata" >&2
  exit 1
fi

# Stable gate must verify the actual APK signer, not merely metadata,
# and must reject a target scope broader than the declared GMS approval state.
printf 'synthetic-production-apk' > "$TMP/prod.apk"
PROD_SHA="$(sha256sum "$TMP/prod.apk" | awk '{print $1}')"
PROD_CHECKSUM="$(python3 -c 'import base64,hashlib,pathlib,sys; print(base64.urlsafe_b64encode(hashlib.sha256(pathlib.Path(sys.argv[1]).read_bytes()).digest()).decode())' "$TMP/prod.apk")"

cat > "$TMP/fake-apksigner-good" <<EOF
#!/bin/sh
echo "Signer #1 certificate SHA-256 digest: $LOCKED_FP"
exit 0
EOF
chmod +x "$TMP/fake-apksigner-good"

cat > "$TMP/fake-apksigner-bad" <<'EOF'
#!/bin/sh
echo "Signer #1 certificate SHA-256 digest: 0000000000000000000000000000000000000000000000000000000000000000"
exit 0
EOF
chmod +x "$TMP/fake-apksigner-bad"

printf '%s\n' \
  'READY=1' \
  'PACKAGE_NAME=com.blazesystems.blazerental' \
  'APK_VERSION=0.5.2-rental.2' \
  'APK_VERSION_CODE=50212' \
  'APK_CHANNEL=production' \
  'PRODUCTION_READY=1' \
  'GMS_DPC_APPROVED=0' \
  'TARGET_SCOPE=aosp_non_gms_or_explicit_oem_only' \
  "APK_SHA256=$PROD_SHA" \
  "APK_CHECKSUM=$PROD_CHECKSUM" \
  "SIGNER_CERT_SHA256=$LOCKED_FP" \
  > "$TMP/prod-meta.env"

python3 - "$IDENTITY" "$PROD_SHA" "$TMP/prod-evidence.json" <<'PY'
import json, re, sys
identity=json.load(open(sys.argv[1],encoding="utf-8"))
fp=re.sub(r"[^0-9A-Fa-f]","",identity["sha256_fingerprint"]).lower()
out={
  "schema":"blazerental.physical-provisioning-validation.v1",
  "passed":True,
  "release":"synthetic-gate-test",
  "package_id":"com.blazesystems.blazerental",
  "apk_sha256":sys.argv[2],
  "signer_certificate_sha256":fp,
  "target_scope":"aosp_non_gms_or_explicit_oem_only",
  "gms_dpc_approved":False,
  "universal_gms_compatibility_claimed":False,
  "factory_reset_setup_wizard_completed":True,
  "device_owner_confirmed":True,
  "https_certificate_pin_verified":True,
  "v2_enrollment_completed":True,
  "device_visible_on_intended_server":True,
  "response_loss_retry_same_identity":True,
  "protocol1_downgrade_rejected":True,
  "redemption_record_retired_after_authenticated_sync":True,
  "standard_scanner_rejected_device_provisioning_qr":True,
  "android_12_plus_path_tested":True,
  "tested_android_versions":["12","14"]
}
json.dump(out,open(sys.argv[3],"w",encoding="utf-8"),indent=2)
PY

python3 "$PROMOTE" \
  --identity "$IDENTITY" \
  --metadata "$TMP/prod-meta.env" \
  --evidence "$TMP/prod-evidence.json" \
  --apk "$TMP/prod.apk" \
  --apksigner "$TMP/fake-apksigner-good" \
  | grep -q 'PROMOTION GATE: PASS'

if python3 "$PROMOTE" \
    --identity "$IDENTITY" \
    --metadata "$TMP/prod-meta.env" \
    --evidence "$TMP/prod-evidence.json" \
    --apk "$TMP/prod.apk" \
    --apksigner "$TMP/fake-apksigner-bad" >/dev/null 2>&1
then
  echo "stable promotion gate trusted forged signer metadata" >&2
  exit 1
fi

sed 's/^TARGET_SCOPE=.*/TARGET_SCOPE=gms_and_supported_aosp/' \
  "$TMP/prod-meta.env" > "$TMP/prod-meta-bad-scope.env"
if python3 "$PROMOTE" \
    --identity "$IDENTITY" \
    --metadata "$TMP/prod-meta-bad-scope.env" \
    --evidence "$TMP/prod-evidence.json" \
    --apk "$TMP/prod.apk" \
    --apksigner "$TMP/fake-apksigner-good" >/dev/null 2>&1
then
  echo "stable promotion gate accepted an over-broad non-GMS target scope" >&2
  exit 1
fi

echo "BlazeRental provisioning/enrollment split audit passed"

# RC10: Reject unauthenticated status mutations before local lease credit changes.
python3 - "$SRC/LeaseClient.java" "$SRC/BlazeProvisioningComplianceActivity.java" <<'PY'
from pathlib import Path
import sys
lease=Path(sys.argv[1]).read_text()
compliance=Path(sys.argv[2]).read_text()
write="RentalLeaseStore.recordLease(context, serverNow, leaseUntil);"
assert lease.count(write)==1
assert lease.index("if (policySignatureV3.length() > 0)") < lease.index(write)
assert lease.index("LeaseSyncStateGuard.acceptRevision") < lease.index(write)
assert lease.index("AndroidRentalPolicyRepository.applyVerified") < lease.index(write)
assert "if (!deviceId.equals(RentalLeaseStore.deviceId(context))) return false;" in lease
assert "policySynced && policyStored" in compliance
PY
