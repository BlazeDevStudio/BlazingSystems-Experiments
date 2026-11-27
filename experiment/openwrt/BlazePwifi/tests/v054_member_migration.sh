#!/bin/sh
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
T="$(mktemp -d)"
trap 'rm -rf "$T"' EXIT
mkdir -p "$T/bin" "$T/state" "$T/run"

cat > "$T/bin/uci" <<'UCI'
#!/bin/sh
case "$*" in
  *'get blazepwifi.main.vendo_key') echo vendokey;;
  *'get blazepwifi.main.durable_sync') echo 0;;
  *'get blazepwifi.main.member_kdf_rounds') echo 1024;;
  *'get blazepwifi.main.member_event_history') echo 512;;
  *) exit 1;;
esac
UCI
chmod +x "$T/bin/uci"

export PATH="$T/bin:$PATH"
export BP_STATE="$T/state" BP_RUN="$T/run"
export BP_LIB="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/common.sh"
export BP_AUTH_LIB="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/auth.sh"
export BP_MEMBER_LIB="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/member.sh"
export BP_MEMBER_MIGRATION_LIB="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/member_migration.sh"
export REMOTE_ADDR=192.0.2.40
export BP_AUTH_TOKEN=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
export BP_AUTH_USER=admin BP_AUTH_ROLE=admin BP_AUTH_MUST_CHANGE=0

. "$BP_LIB"
. "$BP_AUTH_LIB"
. "$BP_MEMBER_LIB"
. "$BP_MEMBER_MIGRATION_LIB"
bp_member_init

bp_member_lock
bp_member_create alice "" 'alpha1234' seed >/dev/null
bp_member_create bob "Bob Existing" 'beta12345' seed >/dev/null
bp_member_balance_change alice add 300 seed "" >/dev/null
bp_member_unlock

ALICE_HASH="$(printf '%s' "$(bp_member_line alice)" | cut -f6)"
ALICE_SALT="$(printf '%s' "$(bp_member_line alice)" | cut -f5)"
EXPORT="$T/export.blazemembers"
bp_member_migration_export > "$EXPORT"
[ "$(sed -n '1p' "$EXPORT")" = BLAZE_MEMBER_METADATA_V1 ]
grep -q '^global_revision[[:space:]]' "$EXPORT"
grep -q '^member[[:space:]]alice[[:space:]]' "$EXPORT"
[ "$(awk -F '\t' '$1=="member"{if(NF!=7)bad=1} END{print bad+0}' "$EXPORT")" -eq 0 ]
! grep -Fq "$ALICE_HASH" "$EXPORT"
! grep -Fq "$ALICE_SALT" "$EXPORT"
! grep -Fq 'sha256i' "$EXPORT"
! grep -Fq 'alpha1234' "$EXPORT"

enc() { bp_member_migration_b64_encode "$1"; }
make_import() {
  file="$1"
  shift
  {
    printf 'BLAZE_MEMBER_METADATA_V1\n'
    printf 'exported_at\t%s\n' "$(bp_now)"
    printf 'global_revision\t%s\n' "$(bp_member_global_revision)"
    while [ "$#" -gt 0 ]; do
      printf '%b\n' "$1"
      shift
    done
  } > "$file"
}
payload() { base64 < "$1" | tr -d '\r\n'; }

IMPORT1="$T/import1.blazemembers"
make_import "$IMPORT1" \
  "member\talice\t0\t120\t$(bp_now)\t$(enc "Imported Alice")\t$(enc "legacy-local")" \
  "member\tcarol\t1\t900\t$(bp_now)\t$(enc "")\t$(enc "softtimer-local")"
TOKEN1="$(bp_member_migration_preview_create "$(payload "$IMPORT1")")"
[ "$(bp_member_migration_preview_meta "$TOKEN1" count)" -eq 2 ]
[ "$(bp_member_migration_preview_meta "$TOKEN1" creates)" -eq 1 ]
[ "$(bp_member_migration_preview_meta "$TOKEN1" collisions)" -eq 1 ]
[ "$(bp_member_migration_preview_meta "$TOKEN1" requested_enabled)" -eq 1 ]
PREVIEW="$(bp_member_migration_preview_json "$TOKEN1")"
printf '%s' "$PREVIEW" | grep -q '"username":"alice".*"status":"collision"'
printf '%s' "$PREVIEW" | grep -q '"username":"carol".*"status":"create"'

# Preview tokens are bound to the authenticated admin session/IP.
OLD_IP="$REMOTE_ADDR"
export REMOTE_ADDR=192.0.2.41
set +e
bp_member_migration_preview_validate "$TOKEN1"
RC=$?
set -e
[ "$RC" -eq 3 ]
export REMOTE_ADDR="$OLD_IP"

# Member state changes after preview invalidate apply.
bp_member_lock
bp_member_balance_change bob add 1 seed "" >/dev/null
bp_member_unlock
set +e
bp_member_migration_apply "$TOKEN1" skip admin:test >/dev/null
RC=$?
set -e
[ "$RC" -eq 6 ]

# Re-preview against current revision. Abort policy must fail before mutation.
TOKEN2="$(bp_member_migration_preview_create "$(payload "$IMPORT1")")"
REV_BEFORE="$(bp_member_global_revision)"
set +e
bp_member_migration_apply "$TOKEN2" abort admin:test >/dev/null
RC=$?
set -e
[ "$RC" -eq 7 ]
[ "$(bp_member_global_revision)" = "$REV_BEFORE" ]

# Skip collisions creates only the new member. New account is disabled/reset-required.
RESULT="$(bp_member_migration_apply "$TOKEN2" skip admin:test)"
[ "$(printf '%s' "$RESULT" | cut -f1)" -eq 1 ]
[ "$(printf '%s' "$RESULT" | cut -f2)" -eq 0 ]
[ "$(printf '%s' "$RESULT" | cut -f3)" -eq 1 ]
CAROL="$(bp_member_line carol)"
[ "$(printf '%s' "$CAROL" | cut -f2)" = "" ]
[ "$(printf '%s' "$CAROL" | cut -f3)" = 0 ]
[ "$(printf '%s' "$CAROL" | cut -f4)" = reset_required ]
[ "$(printf '%s' "$CAROL" | cut -f5)" = "-" ]
[ "$(printf '%s' "$CAROL" | cut -f6)" = "-" ]
[ "$(printf '%s' "$CAROL" | cut -f8)" -eq 900 ]
! bp_member_verify_password carol 'anything123'
set +e
bp_member_migration_preview_validate "$TOKEN2"
RC=$?
set -e
[ "$RC" -eq 1 ]

# Normal admin password reset then enable makes an imported member usable.
bp_member_lock
bp_member_set_password carol 'carol-new99' admin:test >/dev/null
bp_member_patch carol @keep 1 admin:test >/dev/null
bp_member_unlock
bp_member_verify_password carol 'carol-new99'
CAROL_HASH="$(printf '%s' "$(bp_member_line carol)" | cut -f6)"

# Explicit metadata-only update preserves verifier material on collisions.
IMPORT2="$T/import2.blazemembers"
make_import "$IMPORT2" \
  "member\talice\t0\t120\t$(bp_now)\t$(enc "Imported Alice")\t$(enc "legacy-local")" \
  "member\tcarol\t1\t600\t$(bp_now)\t$(enc "Carol Central")\t$(enc "legacy-local")"
TOKEN3="$(bp_member_migration_preview_create "$(payload "$IMPORT2")")"
[ "$(bp_member_migration_preview_meta "$TOKEN3" collisions)" -eq 2 ]
RESULT="$(bp_member_migration_apply "$TOKEN3" update admin:test)"
[ "$(printf '%s' "$RESULT" | cut -f1)" -eq 0 ]
[ "$(printf '%s' "$RESULT" | cut -f2)" -eq 2 ]
[ "$(printf '%s' "$(bp_member_line alice)" | cut -f6)" = "$ALICE_HASH" ]
[ "$(printf '%s' "$(bp_member_line carol)" | cut -f6)" = "$CAROL_HASH" ]
[ "$(printf '%s' "$(bp_member_line alice)" | cut -f2)" = "Imported Alice" ]
[ "$(printf '%s' "$(bp_member_line alice)" | cut -f3)" = 0 ]
[ "$(printf '%s' "$(bp_member_line alice)" | cut -f8)" -eq 120 ]
[ "$(printf '%s' "$(bp_member_line carol)" | cut -f2)" = "Carol Central" ]
[ "$(printf '%s' "$(bp_member_line carol)" | cut -f8)" -eq 600 ]
bp_member_verify_password carol 'carol-new99'

# Duplicate usernames are rejected during preview.
DUP="$T/duplicate.blazemembers"
make_import "$DUP" \
  "member\tdave\t0\t0\t$(bp_now)\t$(enc "Dave")\t$(enc "legacy")" \
  "member\tdave\t0\t0\t$(bp_now)\t$(enc "Dave again")\t$(enc "legacy")"
set +e
bp_member_migration_preview_create "$(payload "$DUP")" >/dev/null
RC=$?
set -e
[ "$RC" -eq 12 ]

# Inject failure after one collision update; records/events/revision must roll back together.
ROLL="$T/rollback.blazemembers"
make_import "$ROLL" \
  "member\talice\t1\t999\t$(bp_now)\t$(enc "Should Roll Back")\t$(enc "legacy")" \
  "member\tdave\t1\t60\t$(bp_now)\t$(enc "Dave")\t$(enc "legacy")"
TOKEN4="$(bp_member_migration_preview_create "$(payload "$ROLL")")"
cp -p "$BP_MEMBERS" "$T/before.members"
cp -p "$BP_MEMBER_EVENTS" "$T/before.events"
cp -p "$BP_MEMBER_REVISION" "$T/before.revision"
bp_member_migration_import_new() { return 1; }
set +e
bp_member_migration_apply "$TOKEN4" update admin:test >/dev/null
RC=$?
set -e
[ "$RC" -eq 14 ]
cmp -s "$T/before.members" "$BP_MEMBERS"
cmp -s "$T/before.events" "$BP_MEMBER_EVENTS"
cmp -s "$T/before.revision" "$BP_MEMBER_REVISION"
[ -z "$(bp_member_line dave)" ]
[ "$(printf '%s' "$(bp_member_line alice)" | cut -f2)" = "Imported Alice" ]

grep -Fq 'member_export)' "$ROOT/openwrt/rootfs/www/blazepwifi/cgi-bin/admin"
grep -Fq 'member_import_preview)' "$ROOT/openwrt/rootfs/www/blazepwifi/cgi-bin/admin"
grep -Fq 'member_import_apply)' "$ROOT/openwrt/rootfs/www/blazepwifi/cgi-bin/admin"
grep -Fq 'Member metadata migration' "$ROOT/openwrt/rootfs/www/blazepwifi/admin.html"
grep -Fq "let importPreviewToken=''" "$ROOT/openwrt/rootfs/www/blazepwifi/admin/members.js"
! grep -Fq 'localStorage' "$ROOT/openwrt/rootfs/www/blazepwifi/admin/members.js"
! grep -Fq 'sessionStorage' "$ROOT/openwrt/rootfs/www/blazepwifi/admin/members.js"

echo 'BlazePwifi v0.5.3-dev.4 member metadata migration checks passed'
