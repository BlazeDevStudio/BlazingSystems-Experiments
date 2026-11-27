#!/bin/sh
# PAY-0737: execute real signed Full Vendo CGI with synthetic paid member state.
# No customer money, physical router or production signing key is ever used.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
T="$(mktemp -d /tmp/blaze-pay0737-XXXXXX)" || exit 1
trap 'touch "$T/release" 2>/dev/null || :; rm -rf "$T"' EXIT HUP INT TERM
chmod 700 "$T"
printf 'BLAZE-PAY-0737-SYNTHETIC-ONLY\n' > "$T/.lab-only"
mkdir -m 700 "$T/bin" "$T/state" "$T/run"
cat > "$T/bin/uci" <<'UCI'
#!/bin/sh
case "$*" in
  *'get blazepwifi.main.vendo_key') echo pay0737-test-vendo-secret;;
  *'get blazepwifi.main.vendo_port') echo 4455;;
  *'get blazepwifi.main.durable_sync') echo 0;;
  *) exit 1;;
esac
UCI
chmod 700 "$T/bin/uci"
export PATH="$T/bin:$PATH" BP_STATE="$T/state" BP_RUN="$T/run"
export BP_LIB="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/common.sh"
export BP_RENTAL_LIB="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/rental.sh"
export BP_CONTROLLER_LIB="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/controller.sh"
export BP_MEMBER_LIB="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/member.sh"
export REQUEST_METHOD=POST SERVER_PORT=4455 REMOTE_ADDR=10.0.0.9
VENDO="$ROOT/openwrt/rootfs/www/blazepwifi/cgi-bin/vendo"
NONCE=0102030405060708
CTL=vendolab
KEY=pay0737-test-vendo-secret
ROW="$(printf 'alice\tAlice\t1\tsha256i\tsalt\tstoredhash\t4096\t100\t1\t123456\tfixture')"
mkdir -p "$BP_STATE/targets"
printf '%s\n' "$ROW" > "$BP_STATE/members.tsv"
printf '1\n' > "$BP_STATE/member-revision"
: > "$BP_STATE/member-events.tsv"
chmod 600 "$BP_STATE/members.tsv" "$BP_STATE/member-revision" "$BP_STATE/member-events.tsv"
send() {
  act="$1"; target="$2"
  sign="$(printf '%s|%s|%s|%s|0|%s|%s' "$KEY" "$act" "$CTL" "$NONCE" "$target" "$KEY" | sha256sum | cut -d' ' -f1)"
  printf 'action=%s&id=%s&nonce=%s&pulses=0&target=%s&sig=%s' "$act" "$CTL" "$NONCE" "$target" "$sign" | sh "$VENDO"
}
PROOF="$(printf '%s|%s|%s|%s' storedhash "$NONCE" "$CTL" "$KEY" | sha256sum | cut -d' ' -f1)"
AUTH_TARGET="alice:$PROOF"
snapshot="$(send member_snapshot '')"
printf '%s' "$snapshot" | grep -Fq '"ok":true'
printf '%s' "$snapshot" | grep -Fq '"member_revision":1'
printf '%s' "$snapshot" | grep -Fq '"banked_seconds":100'
auth="$(send member_auth "$AUTH_TARGET")"
printf '%s' "$auth" | grep -Fq '"ok":true'
printf '%s' "$auth" | grep -Fq '"banked_seconds":100'
printf '%s' "$auth" | grep -Fq '"member_revision":1'

paid_hashes() {
  sha256sum "$BP_STATE/members.tsv" "$BP_STATE/member-events.tsv" 2>/dev/null |
    awk '{print $1}'
  if [ -e "$BP_STATE/member-revision" ]; then
    sha256sum "$BP_STATE/member-revision" | awk '{print $1}'
  else
    printf 'MISSING_REVISION\n'
  fi
}
deny() {
  label="$1"
  before="$(paid_hashes)"
  for act in member_snapshot member_auth; do
    if [ "$act" = member_snapshot ]; then tgt=; else tgt="$AUTH_TARGET"; fi
    out="$(send "$act" "$tgt")"
    if ! printf '%s' "$out" | grep -Fq '"ok":false' ||
       printf '%s' "$out" | grep -Fq '"response_sig"'; then
      echo "PAY-0737 unsafe signed $act response at $label: $out" >&2; exit 1
    fi
  done
  [ "$(paid_hashes)" = "$before" ] || {
    echo "PAY-0737 $label mutated member money or receipt" >&2; exit 1
  }
}

printf 'invalid-revision\n' > "$BP_STATE/member-revision"
deny malformed-revision
printf '0\n' > "$BP_STATE/member-revision"
deny revision-rollback-behind-existing-member
rm "$BP_STATE/member-revision"
deny missing-revision
printf '1\n' > "$BP_STATE/member-revision"
sed 's/\t100\t1\t/\t100X\t1\t/' "$BP_STATE/members.tsv" > "$T/corrupt"
mv "$T/corrupt" "$BP_STATE/members.tsv"
chmod 600 "$BP_STATE/members.tsv"
deny corrupted-balance
printf '%s\n' "$ROW" > "$BP_STATE/members.tsv"
chmod 600 "$BP_STATE/members.tsv"
printf 'PENDING\t123\n' > "$BP_STATE/paid-state-uncertain"
deny pending-paid-quarantine
rm "$BP_STATE/paid-state-uncertain"
printf 'CUTOVER\n' > "$BP_STATE/paid-v2-cutover-intent"
deny v2-cutover-in-progress
rm "$BP_STATE/paid-v2-cutover-intent"
ln -s "$T/not-present" "$BP_STATE/paid-v2-cutover-intent"
deny dangling-cutover-marker
rm "$BP_STATE/paid-v2-cutover-intent"

(
  exec 8>"$BP_RUN/paid-financial.lock"
  flock -x 8
  : > "$T/held"
  while [ ! -f "$T/release" ]; do sleep 0.05; done
) &
pid=$!
i=0
while [ ! -f "$T/held" ] && [ "$i" -lt 80 ]; do sleep 0.05; i=$((i+1)); done
[ -f "$T/held" ] || { echo "PAY-0737 writer lock setup failed" >&2; exit 1; }
deny writer-lock-before-quarantine-marker
: > "$T/release"
wait "$pid"
snapshot="$(send member_snapshot '')"
printf '%s' "$snapshot" | grep -Fq '"ok":true'
[ ! -e "$BP_STATE/paid-state-uncertain" ]
echo 'PAY-0737 PASS: real signed member snapshot/auth reject corrupt/rolled-back/missing revision, corrupt bank, held writer, quarantine and cutover without emitting signed success'
echo 'NOT PRODUCTION v2: crash-atomic paid authority, independent witness and real hardware/signer gates remain BLOCKED'
