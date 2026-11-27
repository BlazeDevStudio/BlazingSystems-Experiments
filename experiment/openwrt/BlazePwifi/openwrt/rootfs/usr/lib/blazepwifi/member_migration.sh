#!/bin/sh
# BlazePwifi Pisonet member metadata export/import.
# Source after common.sh, auth.sh, member.sh, and console_ops.sh.
#
# Portable file format:
#   BLAZE_MEMBER_METADATA_V1
#   exported_at<TAB>UNIX_EPOCH
#   global_revision<TAB>REV
#   member<TAB>USERNAME<TAB>ENABLED<TAB>BANKED_SECONDS<TAB>UPDATED<TAB>LABEL_B64<TAB>SOURCE_B64
#
# Password verifier fields are deliberately absent.

BP_MEMBER_IMPORT_DIR=${BP_MEMBER_IMPORT_DIR:-$BP_RUN/member-imports}
BP_MEMBER_IMPORT_TTL=${BP_MEMBER_IMPORT_TTL:-600}
BP_MEMBER_IMPORT_MAX_BYTES=${BP_MEMBER_IMPORT_MAX_BYTES:-262144}
BP_MEMBER_IMPORT_MAX_MEMBERS=${BP_MEMBER_IMPORT_MAX_MEMBERS:-5000}

bp_member_migration_init() {
  bp_member_init
  mkdir -p "$BP_MEMBER_IMPORT_DIR"
  chmod 700 "$BP_MEMBER_IMPORT_DIR"
}

bp_member_migration_b64_encode() {
  # Prefix every text value so even an empty string has a non-empty encoded field.
  printf 'v1:%s' "$1" | base64 | tr -d '\r\n'
}

bp_member_migration_decode_text() {
  encoded="$1"; max="$2"
  [ "$(printf '%s' "$encoded" | wc -c)" -le 512 ] || return 1
  case "$encoded" in *[!A-Za-z0-9+/=]*) return 1;; esac
  tmp="$BP_RUN/.member-import-field.$(bp_tmp_suffix)"
  if ! printf '%s' "$encoded" | base64 -d > "$tmp" 2>/dev/null; then
    rm -f "$tmp"; return 1
  fi
  [ "$(wc -c < "$tmp" 2>/dev/null)" -le $((max+3)) ] || { rm -f "$tmp"; return 1; }
  prefix="$(head -c 3 "$tmp" 2>/dev/null)"
  [ "$prefix" = "v1:" ] || { rm -f "$tmp"; return 1; }
  dd if="$tmp" of="$tmp.value" bs=1 skip=3 2>/dev/null || { rm -f "$tmp" "$tmp.value"; return 1; }
  if LC_ALL=C grep -q '[[:cntrl:]]' "$tmp.value" 2>/dev/null; then
    rm -f "$tmp" "$tmp.value"; return 1
  fi
  cat "$tmp.value"
  rm -f "$tmp" "$tmp.value"
}

bp_member_migration_export() {
  bp_member_migration_init
  now="$(bp_now)"; rev="$(bp_member_global_revision)"
  printf 'BLAZE_MEMBER_METADATA_V1\n'
  printf 'exported_at\t%s\n' "$now"
  printf 'global_revision\t%s\n' "$rev"
  while IFS= read -r line || [ -n "$line" ]; do
    user="$(printf '%s' "$line" | cut -f1)"; [ -n "$user" ] || continue
    label="$(printf '%s' "$line" | cut -f2)"
    enabled="$(printf '%s' "$line" | cut -f3)"
    banked="$(printf '%s' "$line" | cut -f8)"
    updated="$(printf '%s' "$line" | cut -f10)"
    source="$(printf '%s' "$line" | cut -f11)"
    printf 'member\t%s\t%s\t%s\t%s\t%s\t%s\n' \
      "$user" "${enabled:-0}" "${banked:-0}" "${updated:-0}" \
      "$(bp_member_migration_b64_encode "$label")" "$(bp_member_migration_b64_encode "$source")"
  done < "$BP_MEMBERS"
}

bp_member_migration_cleanup() {
  bp_member_migration_init
  now="$(bp_now)"
  for meta in "$BP_MEMBER_IMPORT_DIR"/*.meta; do
    [ -f "$meta" ] || continue
    expires="$(awk -F '\t' '$1=="expires"{print $2;exit}' "$meta")"
    case "$expires" in ''|*[!0-9]*) expires=0;; esac
    if [ "$expires" -lt "$now" ] 2>/dev/null; then
      base="${meta%.meta}"
      rm -f "$meta" "$base.members"
    fi
  done
}

bp_member_migration_session_hash() {
  [ -n "${BP_AUTH_TOKEN:-}" ] || return 1
  printf '%s' "$BP_AUTH_TOKEN" | bp_sha256
}

bp_member_migration_preview_meta() {
  token="$1"; key="$2"
  awk -F '\t' -v k="$key" '$1==k {sub(/^[^\t]*\t/,""); print; exit}' "$BP_MEMBER_IMPORT_DIR/$token.meta" 2>/dev/null
}

bp_member_migration_preview_validate() {
  token="$1"
  printf '%s' "$token" | grep -Eq '^[0-9a-f]{48}$' || return 1
  meta="$BP_MEMBER_IMPORT_DIR/$token.meta"
  members="$BP_MEMBER_IMPORT_DIR/$token.members"
  [ -r "$meta" ] && [ -r "$members" ] || return 1
  expires="$(bp_member_migration_preview_meta "$token" expires)"
  case "$expires" in ''|*[!0-9]*) return 1;; esac
  [ "$expires" -ge "$(bp_now)" ] 2>/dev/null || return 2
  expected_hash="$(bp_member_migration_preview_meta "$token" auth_hash)"
  got_hash="$(bp_member_migration_session_hash)" || return 1
  [ -n "$expected_hash" ] && [ "$expected_hash" = "$got_hash" ] || return 3
  expected_ip="$(bp_member_migration_preview_meta "$token" ip)"
  [ "$expected_ip" = "${REMOTE_ADDR:-unknown}" ] || return 3
  return 0
}

bp_member_migration_parse_file() {
  input="$1"; canonical="$2"
  : > "$canonical"; chmod 600 "$canonical"
  line_no=0; count=0; exported_at=0; export_revision=0
  while IFS= read -r line || [ -n "$line" ]; do
    line_no=$((line_no+1))
    case "$line_no" in
      1)
        [ "$line" = "BLAZE_MEMBER_METADATA_V1" ] || return 10
        ;;
      2)
        key="$(printf '%s' "$line" | cut -f1)"
        value="$(printf '%s' "$line" | cut -f2)"
        [ "$key" = exported_at ] || return 10
        case "$value" in ''|*[!0-9]*) return 10;; esac
        exported_at="$value"
        ;;
      3)
        key="$(printf '%s' "$line" | cut -f1)"
        value="$(printf '%s' "$line" | cut -f2)"
        [ "$key" = global_revision ] || return 10
        case "$value" in ''|*[!0-9]*) return 10;; esac
        export_revision="$value"
        ;;
      *)
        [ -n "$line" ] || continue
        [ "$(printf '%s\n' "$line" | awk -F '\t' '{print NF}')" -eq 7 ] || return 10
        kind="$(printf '%s' "$line" | cut -f1)"
        [ "$kind" = member ] || return 10
        user="$(bp_member_norm "$(printf '%s' "$line" | cut -f2)")" || return 11
        enabled="$(printf '%s' "$line" | cut -f3)"
        banked="$(printf '%s' "$line" | cut -f4)"
        updated="$(printf '%s' "$line" | cut -f5)"
        label64="$(printf '%s' "$line" | cut -f6)"
        source64="$(printf '%s' "$line" | cut -f7)"
        case "$enabled" in 0|1) ;; *) return 11;; esac
        case "$banked" in ''|*[!0-9]*) return 11;; esac
        [ "$banked" -le 31536000 ] 2>/dev/null || return 11
        case "$updated" in ''|*[!0-9]*) return 11;; esac
        label="$(bp_member_migration_decode_text "$label64" 96)" || return 11
        source="$(bp_member_migration_decode_text "$source64" 96)" || return 11
        [ "$(bp_member_clean "$label")" = "$label" ] || return 11
        [ "$(bp_member_clean "$source")" = "$source" ] || return 11
        awk -F '\t' -v u="$user" '$1==u {found=1} END{exit found?0:1}' "$canonical" && return 12
        printf '%s\t%s\t%s\t%s\t%s\t%s\n' "$user" "$enabled" "$banked" "$updated" "$label64" "$source64" >> "$canonical"
        count=$((count+1))
        [ "$count" -le "$BP_MEMBER_IMPORT_MAX_MEMBERS" ] || return 13
        ;;
    esac
  done < "$input"
  [ "$line_no" -ge 3 ] || return 10
  BP_MEMBER_IMPORT_COUNT="$count"
  BP_MEMBER_IMPORT_EXPORTED_AT="$exported_at"
  BP_MEMBER_IMPORT_EXPORT_REVISION="$export_revision"
  export BP_MEMBER_IMPORT_COUNT BP_MEMBER_IMPORT_EXPORTED_AT BP_MEMBER_IMPORT_EXPORT_REVISION
  return 0
}

bp_member_migration_preview_create() {
  payload_b64="$1"
  bp_member_migration_init
  bp_member_migration_cleanup
  [ -n "${BP_AUTH_TOKEN:-}" ] || return 3
  [ "$(printf '%s' "$payload_b64" | wc -c)" -le $((BP_MEMBER_IMPORT_MAX_BYTES*2)) ] || return 4

  raw="$BP_RUN/.member-import-raw.$(bp_tmp_suffix)"
  canonical="$BP_RUN/.member-import-canon.$(bp_tmp_suffix)"
  if ! printf '%s' "$payload_b64" | base64 -d > "$raw" 2>/dev/null; then
    rm -f "$raw" "$canonical"; return 4
  fi
  [ "$(wc -c < "$raw" 2>/dev/null)" -le "$BP_MEMBER_IMPORT_MAX_BYTES" ] || { rm -f "$raw" "$canonical"; return 4; }

  if bp_member_migration_parse_file "$raw" "$canonical"; then
    :
  else
    rc=$?; rm -f "$raw" "$canonical"; return "$rc"
  fi
  rm -f "$raw"

  token="$(bp_auth_random_hex 24)" || { rm -f "$canonical"; return 5; }
  base="$BP_MEMBER_IMPORT_DIR/$token"
  mv "$canonical" "$base.members" || { rm -f "$canonical"; return 5; }
  chmod 600 "$base.members"

  now="$(bp_now)"; expires=$((now+BP_MEMBER_IMPORT_TTL))
  auth_hash="$(bp_member_migration_session_hash)" || { rm -f "$base.members"; return 5; }
  base_revision="$(bp_member_global_revision)"
  creates=0; collisions=0; requested_enabled=0
  while IFS="$(printf '\t')" read -r user enabled banked updated label64 source64; do
    [ "$enabled" = 1 ] && requested_enabled=$((requested_enabled+1))
    if [ -n "$(bp_member_line "$user")" ]; then collisions=$((collisions+1)); else creates=$((creates+1)); fi
  done < "$base.members"
  payload_sha="$(cat "$base.members" | bp_sha256)"
  {
    printf 'created\t%s\n' "$now"
    printf 'expires\t%s\n' "$expires"
    printf 'auth_hash\t%s\n' "$auth_hash"
    printf 'ip\t%s\n' "${REMOTE_ADDR:-unknown}"
    printf 'base_revision\t%s\n' "$base_revision"
    printf 'export_revision\t%s\n' "$BP_MEMBER_IMPORT_EXPORT_REVISION"
    printf 'exported_at\t%s\n' "$BP_MEMBER_IMPORT_EXPORTED_AT"
    printf 'count\t%s\n' "$BP_MEMBER_IMPORT_COUNT"
    printf 'creates\t%s\n' "$creates"
    printf 'collisions\t%s\n' "$collisions"
    printf 'requested_enabled\t%s\n' "$requested_enabled"
    printf 'payload_sha256\t%s\n' "$payload_sha"
  } > "$base.meta"
  chmod 600 "$base.meta"
  printf '%s' "$token"
}

bp_member_migration_preview_json() {
  token="$1"
  bp_member_migration_preview_validate "$token" || return $?
  first=1; printf '['
  while IFS="$(printf '\t')" read -r user enabled banked updated label64 source64; do
    label="$(bp_member_migration_decode_text "$label64" 96)" || return 1
    source="$(bp_member_migration_decode_text "$source64" 96)" || return 1
    if [ -n "$(bp_member_line "$user")" ]; then status=collision; else status=create; fi
    [ "$first" = 1 ] || printf ','; first=0
    printf '{"username":"%s","label":"%s","requested_enabled":%s,"banked_seconds":%s,"updated":%s,"source":"%s","status":"%s"}' \
      "$(bp_json_escape "$user")" "$(bp_json_escape "$label")" "$enabled" "$banked" "$updated" "$(bp_json_escape "$source")" "$status"
  done < "$BP_MEMBER_IMPORT_DIR/$token.members"
  printf ']'
}

bp_member_migration_import_new() {
  user="$1"; label="$2"; banked="$3"; requested_enabled="$4"; actor="$5"; original_source="$6"
  [ -z "$(bp_member_line "$user")" ] || return 3
  rev="$(bp_member_next_revision)"; now="$(bp_now)"
  source="$(bp_member_clean "import:$actor")"
  # Keep non-secret sentinel fields populated so legacy tab parsing retains all columns.
  bp_member_write "$user" "$label" 0 reset_required "-" "-" 0 "$banked" "$rev" "$now" "$source" || return 1
  bp_member_event_record "import:$rev:$user" "$now" "$user" import_create "$banked" "$banked" "$source" \
    "password_reset_required:requested_enabled=$requested_enabled:source=$(bp_member_clean "$original_source")"
}

bp_member_migration_import_update() {
  user="$1"; label="$2"; enabled="$3"; banked="$4"; actor="$5"; original_source="$6"
  line="$(bp_member_line "$user")"; [ -n "$line" ] || return 3
  scheme="$(printf '%s' "$line" | cut -f4)"
  salt="$(printf '%s' "$line" | cut -f5)"
  hash="$(printf '%s' "$line" | cut -f6)"
  rounds="$(printf '%s' "$line" | cut -f7)"
  oldbank="$(printf '%s' "$line" | cut -f8)"
  rev="$(bp_member_next_revision)"; now="$(bp_now)"
  source="$(bp_member_clean "import:$actor")"
  bp_member_write "$user" "$label" "$enabled" "$scheme" "$salt" "$hash" "$rounds" "$banked" "$rev" "$now" "$source" || return 1
  delta=$((banked-oldbank))
  bp_member_event_record "import:$rev:$user" "$now" "$user" import_update "$delta" "$banked" "$source" \
    "metadata_only:source=$(bp_member_clean "$original_source")"
}

bp_member_migration_restore_snapshot() {
  snap="$1"
  cp -p "$snap/members" "$BP_MEMBERS" || return 1
  cp -p "$snap/events" "$BP_MEMBER_EVENTS" || return 1
  cp -p "$snap/revision" "$BP_MEMBER_REVISION" || return 1
  chmod 600 "$BP_MEMBERS" "$BP_MEMBER_EVENTS" "$BP_MEMBER_REVISION"
  bp_durable_sync
}

bp_member_migration_apply() {
  token="$1"; policy="$2"; actor="$3"
  case "$policy" in abort|skip|update) ;; *) return 8;; esac
  bp_member_migration_preview_validate "$token" || return $?
  expected_revision="$(bp_member_migration_preview_meta "$token" base_revision)"
  [ "$(bp_member_global_revision)" = "$expected_revision" ] || return 6

  bp_member_lock || return 9
  if [ "$(bp_member_global_revision)" != "$expected_revision" ]; then bp_member_unlock; return 6; fi

  members_file="$BP_MEMBER_IMPORT_DIR/$token.members"
  if [ "$policy" = abort ]; then
    while IFS="$(printf '\t')" read -r user enabled banked updated label64 source64; do
      if [ -n "$(bp_member_line "$user")" ]; then bp_member_unlock; return 7; fi
    done < "$members_file"
  fi

  snap="$BP_RUN/.member-import-snapshot.$(bp_tmp_suffix)"
  mkdir -p "$snap" || { bp_member_unlock; return 9; }
  chmod 700 "$snap"
  cp -p "$BP_MEMBERS" "$snap/members" || { rm -rf "$snap"; bp_member_unlock; return 9; }
  cp -p "$BP_MEMBER_EVENTS" "$snap/events" || { rm -rf "$snap"; bp_member_unlock; return 9; }
  cp -p "$BP_MEMBER_REVISION" "$snap/revision" || { rm -rf "$snap"; bp_member_unlock; return 9; }
  chmod 600 "$snap/members" "$snap/events" "$snap/revision"

  created=0; updated_count=0; skipped=0; rc=0
  while IFS="$(printf '\t')" read -r user enabled banked updated label64 source64; do
    label="$(bp_member_migration_decode_text "$label64" 96)" || { rc=10; break; }
    original_source="$(bp_member_migration_decode_text "$source64" 96)" || { rc=10; break; }
    if [ -n "$(bp_member_line "$user")" ]; then
      case "$policy" in
        skip) skipped=$((skipped+1)); continue ;;
        update)
          bp_member_migration_import_update "$user" "$label" "$enabled" "$banked" "$actor" "$original_source" || { rc=14; break; }
          updated_count=$((updated_count+1))
          ;;
        *) rc=7; break ;;
      esac
    else
      bp_member_migration_import_new "$user" "$label" "$banked" "$enabled" "$actor" "$original_source" || { rc=14; break; }
      created=$((created+1))
    fi
  done < "$members_file"

  if [ "$rc" -ne 0 ]; then
    bp_member_migration_restore_snapshot "$snap" || rc=15
    rm -rf "$snap"
    bp_member_unlock
    return "$rc"
  fi

  rm -rf "$snap"
  rm -f "$BP_MEMBER_IMPORT_DIR/$token.meta" "$BP_MEMBER_IMPORT_DIR/$token.members"
  bp_durable_sync
  final_revision="$(bp_member_global_revision)"
  bp_member_unlock
  printf '%s\t%s\t%s\t%s\n' "$created" "$updated_count" "$skipped" "$final_revision"
}
