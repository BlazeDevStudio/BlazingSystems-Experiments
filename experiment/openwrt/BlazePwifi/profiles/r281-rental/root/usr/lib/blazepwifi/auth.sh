#!/bin/sh
# BlazePwifi v0.3 administrative authentication/session library.
# Source after common.sh, or execute with --set-password.

BP_ADMIN_USERS=${BP_ADMIN_USERS:-$BP_STATE/admin-users.tsv}
BP_ADMIN_SESSIONS=${BP_ADMIN_SESSIONS:-$BP_RUN/admin-sessions.tsv}
BP_AUTH_FAILURES=${BP_AUTH_FAILURES:-$BP_RUN/auth-failures.tsv}
BP_AUDIT=${BP_AUDIT:-$BP_STATE/audit.tsv}

bp_auth_cfg() {
	v="$(bp_cfg "$1" 2>/dev/null || true)"
	[ -n "$v" ] && printf '%s' "$v" || printf '%s' "$2"
}

bp_auth_now() {
	[ -n "${BP_AUTH_NOW:-}" ] && printf '%s\n' "$BP_AUTH_NOW" || bp_now
}

bp_auth_init() {
	bp_init_dirs
	touch "$BP_ADMIN_USERS" "$BP_ADMIN_SESSIONS" "$BP_AUTH_FAILURES" "$BP_AUDIT"
	chmod 600 "$BP_ADMIN_USERS" "$BP_ADMIN_SESSIONS" "$BP_AUTH_FAILURES" "$BP_AUDIT"
}

bp_auth_lock() {
	mkdir -p "$BP_RUN"
	exec 8>"$BP_RUN/auth.lock"
	flock -w 5 8 || { exec 8>&-; return 1; }
}

bp_auth_unlock() {
	flock -u 8 2>/dev/null || true
	exec 8>&-
}

# Signed rental enrollment, admin tokens and device secrets require full
# CSPRNG output. Never substitute PID/time-derived SHA256 for random bytes.
bp_auth_random_hex() {
  rng_bytes="$1"
  case "$rng_bytes" in ''|*[!0-9]*) return 8;; esac
  [ "$rng_bytes" -ge 1 ] 2>/dev/null &&
    [ "$rng_bytes" -le 64 ] 2>/dev/null || return 8
  rng_need=$((rng_bytes*2))

  rng_out=""
  if command -v hexdump >/dev/null 2>&1; then
    rng_out="$(hexdump -n "$rng_bytes" -e '1/1 "%02x"' /dev/urandom 2>/dev/null |
      tr -cd '0-9a-fA-F' | tr 'A-F' 'a-f' || true)"
  fi
  [ "$(printf '%s' "$rng_out" | wc -c | tr -d '[:space:]')" -eq "$rng_need" ] 2>/dev/null ||
    rng_out=""
  if [ -z "$rng_out" ] && command -v od >/dev/null 2>&1; then
    rng_out="$(od -An -v -N "$rng_bytes" -tx1 /dev/urandom 2>/dev/null |
      tr -cd '0-9a-fA-F' | tr 'A-F' 'a-f' || true)"
  fi
  [ "$(printf '%s' "$rng_out" | wc -c | tr -d '[:space:]')" -eq "$rng_need" ] 2>/dev/null ||
    rng_out=""
  if [ -z "$rng_out" ] && command -v openssl >/dev/null 2>&1; then
    rng_out="$(openssl rand -hex "$rng_bytes" 2>/dev/null |
      tr -cd '0-9a-fA-F' | tr 'A-F' 'a-f' || true)"
  fi
  [ "$(printf '%s' "$rng_out" | wc -c | tr -d '[:space:]')" -eq "$rng_need" ] 2>/dev/null &&
    printf '%s' "$rng_out" | LC_ALL=C grep -Eq '^[a-f0-9]+$' || return 8
  printf '%s' "$rng_out"
}

bp_auth_clean_field() {
	printf '%s' "$1" | tr '\t\r\n' '   '
}

bp_auth_audit() {
	now="$(bp_auth_now)"; event="$(bp_auth_clean_field "$1")"; user="$(bp_auth_clean_field "${2:-}")"; ip="$(bp_auth_clean_field "${3:-}")"; detail="$(bp_auth_clean_field "${4:-}")"
	printf '%s\t%s\t%s\t%s\t%s\n' "$now" "$event" "$user" "$ip" "$detail" >> "$BP_AUDIT" || return 8
	chmod 600 "$BP_AUDIT" || return 8
}

bp_auth_sha256i() {
	pass="$1"; salt="$2"; rounds="$3"
	case "$rounds" in ''|*[!0-9]*) rounds=2048;; esac
	[ "$rounds" -ge 1 ] 2>/dev/null || rounds=1
	v="$(printf '%s|%s|%s' "$salt" "$pass" "$salt" | bp_sha256)"
	i=1
	while [ "$i" -lt "$rounds" ]; do
		v="$(printf '%s|%s|%s' "$v" "$pass" "$salt" | bp_sha256)"
		i=$((i+1))
	done
	printf '%s' "$v"
}

bp_auth_user_line() {
	awk -F '\t' -v u="$1" '$1==u {print; exit}' "$BP_ADMIN_USERS"
}

bp_auth_set_password() {
	user="$1"; role="$2"; pass="$3"; must_change="${4:-0}"
	printf '%s' "$user" | grep -Eq '^[A-Za-z0-9_.-]{1,32}$' || { echo "invalid username" >&2; return 2; }
	case "$role" in admin|operator|viewer) ;; *) echo "invalid role" >&2; return 2;; esac
	case "$must_change" in 0|1) ;; *) must_change=0;; esac
	[ "${#pass}" -ge 12 ] || { echo "password must be at least 12 characters" >&2; return 2; }
	salt="$(bp_auth_random_hex 8)" || return 8
	printf '%s' "$salt" | LC_ALL=C grep -Eq '^[a-f0-9]{16}$' || return 8
	if command -v openssl >/dev/null 2>&1 && openssl passwd -6 -salt "$salt" "$pass" >/dev/null 2>&1; then
		scheme=openssl6; rounds=0
		hash="$(openssl passwd -6 -salt "$salt" "$pass" 2>/dev/null)" || return 8
	else
		scheme=sha256i; rounds="$(bp_auth_cfg auth_kdf_rounds 2048)"
		hash="$(bp_auth_sha256i "$pass" "$salt" "$rounds")" || return 8
	fi
	[ -n "$hash" ] || return 8
	[ -f "$BP_ADMIN_USERS" ] && [ ! -L "$BP_ADMIN_USERS" ] || return 8
	# Existing administrator/operator passwords are security-critical.
	# Never replace with an incomplete/malformed/duplicated copied snapshot.
	tmp="$BP_STATE/.admin-users.$(bp_tmp_suffix)"
	umask 077
	if ! awk -F '\t' -v OFS='\t' -v u="$user" '
		{
			if (NF!=7 || $1 !~ /^[A-Za-z0-9_.-]+$/ || length($1)>32 ||
			    $2 !~ /^(admin|operator|viewer)$/ ||
			    $3 !~ /^(openssl6|sha256i)$/ || $4=="" || $5=="" ||
			    $6 !~ /^[0-9]+$/ || $7 !~ /^[01]$/ ||
			    ++seen[$1]>1) bad=1
			if ($1!=u) print
		}
		END{if(bad) exit 8}
	' "$BP_ADMIN_USERS" > "$tmp"; then
		rm -f "$tmp" 2>/dev/null || true
		return 8
	fi
	if ! printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "$user" "$role" "$scheme" "$salt" "$hash" "$rounds" "$must_change" >> "$tmp" ||
	   ! chmod 600 "$tmp" ||
	   ! mv "$tmp" "$BP_ADMIN_USERS"; then
		rm -f "$tmp" 2>/dev/null || true
		return 8
	fi
	bp_durable_sync || return 8
	bp_auth_audit password_set "$user" "${REMOTE_ADDR:-local}" "$role" || return 8
	return 0
}

bp_auth_verify_password() {
	user="$1"; pass="$2"; line="$(bp_auth_user_line "$user")"
	[ -n "$line" ] || return 1
	oldifs="$IFS"; IFS="$(printf '\t')"; set -- $line; IFS="$oldifs"
	role="$2"; scheme="$3"; salt="$4"; stored="$5"; rounds="$6"
	case "$scheme" in
		openssl6)
		command -v openssl >/dev/null 2>&1 || return 1
		got="$(openssl passwd -6 -salt "$salt" "$pass" 2>/dev/null || true)"
		;;
		sha256i) got="$(bp_auth_sha256i "$pass" "$salt" "$rounds")" ;;
		*) return 1 ;;
	esac
	[ -n "$got" ] && [ "$got" = "$stored" ]
}

bp_auth_failure_line() {
	awk -F '\t' -v k="$1" '$1==k {print; exit}' "$BP_AUTH_FAILURES"
}

bp_auth_failure_write() {
	key="$1"; count="$2"; start="$3"; lock_until="$4"; level="$5"
	tmp="$BP_RUN/.auth-failures.$(bp_tmp_suffix)"
	awk -F '\t' -v OFS='\t' -v k="$key" '$1!=k {print}' "$BP_AUTH_FAILURES" > "$tmp"
	printf '%s\t%s\t%s\t%s\t%s\n' "$key" "$count" "$start" "$lock_until" "$level" >> "$tmp"
	chmod 600 "$tmp" && mv "$tmp" "$BP_AUTH_FAILURES"
}

bp_auth_fail_update() {
	key="$1"; max="$2"; now="$3"; window="$4"; base_lock="$5"; user="$6"; ip="$7"
	line="$(bp_auth_failure_line "$key")"
	count=0; start="$now"; lock_until=0; level=0
	if [ -n "$line" ]; then
		oldifs="$IFS"; IFS="$(printf '\t')"; set -- $line; IFS="$oldifs"
		count="${2:-0}"; start="${3:-$now}"; lock_until="${4:-0}"; level="${5:-0}"
	fi
	if [ "$now" -ge "$lock_until" ] 2>/dev/null && [ $((now-start)) -gt "$window" ] 2>/dev/null; then
		count=0; start="$now"
	fi
	count=$((count+1))
	if [ "$count" -ge "$max" ]; then
		level=$((level+1)); [ "$level" -le 3 ] || level=3
		mult=1; [ "$level" -ge 2 ] && mult=2; [ "$level" -ge 3 ] && mult=4
		lock_until=$((now + base_lock*mult)); count=0; start="$now"
		bp_auth_audit lockout "$user" "$ip" "$key:$lock_until"
	fi
	bp_auth_failure_write "$key" "$count" "$start" "$lock_until" "$level"
}

bp_auth_is_locked() {
	user="$1"; ip="$2"; now="$(bp_auth_now)"
	for key in "ip:$ip" "user:$user" global; do
		line="$(bp_auth_failure_line "$key")"; [ -n "$line" ] || continue
		lock_until="$(printf '%s' "$line" | cut -f4)"
		[ "${lock_until:-0}" -gt "$now" ] 2>/dev/null && return 0
	done
	return 1
}

bp_auth_record_failure() {
	user="$1"; ip="$2"; now="$(bp_auth_now)"
	max="$(bp_auth_cfg auth_max_attempts 5)"; global_max="$(bp_auth_cfg auth_global_max_attempts 30)"
	window="$(bp_auth_cfg auth_window_seconds 300)"; base_lock="$(bp_auth_cfg auth_lock_seconds 900)"
	bp_auth_audit login_failure "$user" "$ip" "invalid_credentials"
	bp_auth_fail_update "ip:$ip" "$max" "$now" "$window" "$base_lock" "$user" "$ip"
	bp_auth_fail_update "user:$user" "$max" "$now" "$window" "$base_lock" "$user" "$ip"
	bp_auth_fail_update global "$global_max" "$now" "$window" "$base_lock" "$user" "$ip"
}

bp_auth_clear_failures() {
	user="$1"; ip="$2"; tmp="$BP_RUN/.auth-failures.$(bp_tmp_suffix)"
	awk -F '\t' -v a="ip:$ip" -v b="user:$user" '$1!=a && $1!=b {print}' "$BP_AUTH_FAILURES" > "$tmp"
	chmod 600 "$tmp" && mv "$tmp" "$BP_AUTH_FAILURES"
}

bp_auth_role_rank() {
	case "$1" in admin) echo 3;; operator) echo 2;; viewer) echo 1;; *) echo 0;; esac
}

bp_auth_session_create_unlocked() {
	user="$1"; role="$2"; ip="$3"; now="$(bp_auth_now)"
	uline="$(bp_auth_user_line "$user")"; must_change="$(printf '%s' "$uline" | cut -f7)"; [ -n "$must_change" ] || must_change=0
	token="$(bp_auth_random_hex 32)" || return 8
	csrf="$(bp_auth_random_hex 24)" || return 8
	printf '%s' "$token" | LC_ALL=C grep -Eq '^[a-f0-9]{64}$' || return 8
	printf '%s' "$csrf" | LC_ALL=C grep -Eq '^[a-f0-9]{48}$' || return 8
	abs="$(bp_auth_cfg auth_absolute_seconds 28800)"; absolute=$((now+abs))
	printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "$token" "$user" "$role" "$csrf" "$now" "$now" "$absolute" "$ip" "$must_change" >> "$BP_ADMIN_SESSIONS" || return 8
	chmod 600 "$BP_ADMIN_SESSIONS" || return 8
	printf '%s\t%s\t%s\t%s\n' "$token" "$csrf" "$role" "$user"
}

bp_auth_login() {
	user="$1"; pass="$2"; ip="$3"
	bp_auth_init
	bp_auth_lock || return 3
	if bp_auth_is_locked "$user" "$ip"; then
		bp_auth_audit locked_attempt "$user" "$ip" "active_lock"
		bp_auth_unlock; return 2
	fi
	if ! bp_auth_verify_password "$user" "$pass"; then
		bp_auth_record_failure "$user" "$ip"
		bp_auth_unlock; return 1
	fi
	line="$(bp_auth_user_line "$user")"; role="$(printf '%s' "$line" | cut -f2)"
	bp_auth_clear_failures "$user" "$ip"
	if ! out="$(bp_auth_session_create_unlocked "$user" "$role" "$ip")"; then
		bp_auth_audit session_create_failed "$user" "$ip" "entropy_or_storage_unavailable"
		bp_auth_unlock
		return 8
	fi
	bp_auth_audit login_success "$user" "$ip" "$role"
	bp_auth_unlock
	printf '%s\n' "$out"
}

bp_auth_cookie_token() {
	printf '%s' "${HTTP_COOKIE:-}" | tr ';' '\n' | sed -n 's/^[[:space:]]*blaze_admin=//p' | head -n1
}

bp_auth_session_lookup() {
	token="$1"; ip="$2"; now="$(bp_auth_now)"; idle="$(bp_auth_cfg auth_idle_seconds 900)"; bind="$(bp_auth_cfg auth_bind_ip 1)"
	[ -f "$BP_ADMIN_SESSIONS" ] && [ ! -L "$BP_ADMIN_SESSIONS" ] || return 8
	line="$(awk -F '\t' -v t="$token" '$1==t {print; exit}' "$BP_ADMIN_SESSIONS")" || return 8
	[ -n "$line" ] || return 1
	last="$(printf '%s' "$line" | cut -f6)"; absolute="$(printf '%s' "$line" | cut -f7)"; sip="$(printf '%s' "$line" | cut -f8)"
	[ "$absolute" -gt "$now" ] 2>/dev/null || return 1
	[ $((now-last)) -le "$idle" ] 2>/dev/null || return 1
	[ "$bind" != 1 ] || [ "$sip" = "$ip" ] || return 1
	tmp="$BP_RUN/.admin-sessions.$(bp_tmp_suffix)"
	if ! awk -F '\t' -v OFS='\t' -v t="$token" -v n="$now" '$1==t {$6=n} {print}' "$BP_ADMIN_SESSIONS" > "$tmp" ||
	   ! chmod 600 "$tmp" || ! mv "$tmp" "$BP_ADMIN_SESSIONS"; then
		rm -f "$tmp" 2>/dev/null || true
		return 8
	fi
	printf '%s\n' "$line"
}

bp_auth_require_role() {
	need="$1"; ip="${REMOTE_ADDR:-unknown}"; token="${HTTP_X_BLAZE_SESSION:-$(bp_auth_cookie_token)}"
	[ -n "$token" ] || return 1
	bp_auth_init
	bp_auth_lock || return 1
	if line="$(bp_auth_session_lookup "$token" "$ip")"; then rc=0; else rc=1; fi
	bp_auth_unlock
	[ "$rc" -eq 0 ] || return 1
	user="$(printf '%s' "$line" | cut -f2)"; role="$(printf '%s' "$line" | cut -f3)"; csrf="$(printf '%s' "$line" | cut -f4)"; must_change="$(printf '%s' "$line" | cut -f9)"
	[ "$(bp_auth_role_rank "$role")" -ge "$(bp_auth_role_rank "$need")" ] || return 2
	BP_AUTH_TOKEN="$token"; BP_AUTH_USER="$user"; BP_AUTH_ROLE="$role"; BP_AUTH_CSRF="$csrf"; BP_AUTH_MUST_CHANGE="${must_change:-0}"
	export BP_AUTH_TOKEN BP_AUTH_USER BP_AUTH_ROLE BP_AUTH_CSRF BP_AUTH_MUST_CHANGE
	return 0
}

bp_auth_csrf_ok() {
	got="${HTTP_X_BLAZE_CSRF:-$(bp_param csrf)}"
	[ -n "${BP_AUTH_CSRF:-}" ] && [ "$got" = "$BP_AUTH_CSRF" ]
}


bp_auth_invalidate_user_sessions() {
	user="$1"; tmp="$BP_RUN/.admin-sessions.$(bp_tmp_suffix)"
	[ -f "$BP_ADMIN_SESSIONS" ] && [ ! -L "$BP_ADMIN_SESSIONS" ] || return 8
	if ! awk -F '\t' -v u="$user" '$2!=u {print}' "$BP_ADMIN_SESSIONS" > "$tmp" ||
	   ! chmod 600 "$tmp" || ! mv "$tmp" "$BP_ADMIN_SESSIONS"; then
		rm -f "$tmp" 2>/dev/null || true
		return 8
	fi
	return 0
}

bp_auth_logout() {
	token="$1"; user="$2"; ip="$3"
	tmp="$BP_RUN/.admin-sessions.$(bp_tmp_suffix)"
	[ -f "$BP_ADMIN_SESSIONS" ] && [ ! -L "$BP_ADMIN_SESSIONS" ] || return 8
	if ! awk -F '\t' -v t="$token" '$1!=t {print}' "$BP_ADMIN_SESSIONS" > "$tmp" ||
	   ! chmod 600 "$tmp" || ! mv "$tmp" "$BP_ADMIN_SESSIONS"; then
		rm -f "$tmp" 2>/dev/null || true
		return 8
	fi
	bp_auth_audit logout "$user" "$ip" "" || return 8
	return 0
}

case "${1:-}" in
--set-password|--set-bootstrap)
	[ "$#" -eq 4 ] || { echo "usage: $0 --set-password|--set-bootstrap USER ROLE PASSWORD" >&2; exit 2; }
	mode="$1"; . "${BP_LIB:-/usr/lib/blazepwifi/common.sh}"
	bp_auth_init
	bp_auth_lock || { echo "authentication state busy" >&2; exit 1; }
	must=0; [ "$mode" = "--set-bootstrap" ] && must=1
	printf '%s' "$2" | LC_ALL=C grep -Eq '^[A-Za-z0-9_.-]{1,32}$' || { bp_auth_unlock; echo "invalid admin username" >&2; exit 2; }
	case "$3" in admin|operator|viewer) ;; *) bp_auth_unlock; echo "invalid admin role" >&2; exit 2;; esac
	[ "${#4}" -ge 12 ] || { bp_auth_unlock; echo "password must be at least 12 characters" >&2; exit 2; }
	# CLI reset/bootstrap also revokes pre-change sessions under auth lock.
	if ! bp_auth_invalidate_user_sessions "$2"; then
		bp_auth_unlock
		echo "session revocation failed; admin password was not changed" >&2
		exit 8
	fi
	if bp_auth_set_password "$2" "$3" "$4" "$must"; then rc=0; else rc=$?; fi
	bp_auth_unlock
	exit "$rc"
	;;
esac
