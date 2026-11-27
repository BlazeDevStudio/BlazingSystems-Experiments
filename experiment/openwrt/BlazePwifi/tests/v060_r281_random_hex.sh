#!/bin/sh
# RNG-0657 — no truncated or predictable R281 private rental device keys.
# All tokens are fictional and never used with customer devices.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
T="$(mktemp -d /tmp/blaze-r281-rng-XXXXXX)"
trap 'rm -rf "$T"' EXIT HUP INT TERM
# Independently exercise both rootfs and standalone profiles; subshells
# isolate the sourced auth function, test shims and PATH command hash.
for profile in r281 full; do
(
  T="$T/$profile"
  mkdir -p "$T/bin" "$T/state" "$T/run"
  export BP_STATE="$T/state" BP_RUN="$T/run"
  case "$profile" in
    r281) LIB="$ROOT/profiles/r281-rental/root/usr/lib/blazepwifi" ;;
    full) LIB="$ROOT/openwrt/rootfs/usr/lib/blazepwifi" ;;
  esac
  . "$LIB/auth.sh"
for size in 6 12 18 24 32; do
  i=0
  : > "$T/seen"
  while [ "$i" -lt 12 ]; do
    token="$(bp_auth_random_hex "$size")" || {
      echo "R281 RNG refused healthy size $size" >&2; exit 1;
    }
    [ "$(printf '%s' "$token" | wc -c | tr -d '[:space:]')" -eq $((size*2)) ]
    printf '%s' "$token" | LC_ALL=C grep -Eq "^[a-f0-9]{$((size*2))}$"
    printf '%s\n' "$token" >> "$T/seen"
    i=$((i+1))
  done
  [ "$(sort -u "$T/seen" | wc -l | tr -d '[:space:]')" -eq 12 ] || {
    echo "duplicate R281 random token at size $size" >&2; exit 1;
  }
done
for invalid in 0 -1 65 abc 9999999999; do
  if bp_auth_random_hex "$invalid" > "$T/bad-secret" 2>/dev/null; then
    echo "invalid R281 RNG byte request was accepted: $invalid" >&2; exit 1
  fi
  [ ! -s "$T/bad-secret" ]
done

# Simulate BusyBox hexdump returning a short hex fragment.
cat > "$T/bin/hexdump" <<'SHIM'
#!/bin/sh
printf ff
SHIM
chmod 700 "$T/bin/hexdump"
PATH="$T/bin:$PATH"
export PATH
hash -r 2>/dev/null || true
out="$(bp_auth_random_hex 24)"
[ "$(printf '%s' "$out" | wc -c | tr -d '[:space:]')" -eq 48 ]
printf '%s' "$out" | LC_ALL=C grep -Eq '^[a-f0-9]{48}$'

# Both basic BusyBox readers fail: OpenSSL is permitted only when it emits
# exactly the full requested CSPRNG bytes.
cat > "$T/bin/od" <<'SHIM'
#!/bin/sh
exit 74
SHIM
chmod 700 "$T/bin/od"
hash -r 2>/dev/null || true
out="$(bp_auth_random_hex 24)"
[ "$(printf '%s' "$out" | wc -c | tr -d '[:space:]')" -eq 48 ]
printf '%s' "$out" | LC_ALL=C grep -Eq '^[a-f0-9]{48}$'

# No working secure random backend may NEVER mint a secret using clock/PID.
cat > "$T/bin/openssl" <<'SHIM'
#!/bin/sh
exit 74
SHIM
chmod 700 "$T/bin/openssl"
hash -r 2>/dev/null || true
if bp_auth_random_hex 24 > "$T/bad-secret" 2>/dev/null; then
  echo 'R281 RNG minted a token with no valid random source' >&2; exit 1
fi
[ ! -s "$T/bad-secret" ]
  echo "RNG-0657/0659 PASS $profile: full-length private crypto tokens, short entropy backend failover, no deterministic fallback"
)
done
echo 'RNG-0659 PASS BOTH full OpenWrt and standalone R281 CSPRNG profiles; NO production signer or Device Owner acceptance proven'
