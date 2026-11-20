#pragma once
// PHX-HW-H: ESP32 lab-only primitive. Input must first come from a STRICT,
// duplicate-rejecting JSON parser. This file never admits coins or touches GPIO.
// CORE producer: PR252 at 7f613affd60fe8b1c19f2f8187077ec4aa2463bb.
// No protected reboot freshness, signer custody, or monetary authority.
#include <stddef.h>
#include <stdint.h>
#include <mbedtls/version.h>

// This lab uses the legacy SHA-256 API. Fail with a clear diagnostic before
// including legacy headers on unsupported or unversioned Mbed TLS targets.
#if !defined(MBEDTLS_VERSION_MAJOR)
#error "ControllerAuthV1Lab requires an explicit Mbed TLS major version."
#elif MBEDTLS_VERSION_MAJOR < 2 || MBEDTLS_VERSION_MAJOR >= 4
#error "ControllerAuthV1Lab supports Mbed TLS 2.x/3.x only; Mbed TLS 4 requires a separately reviewed PSA Crypto adapter."
#endif

#include <mbedtls/md.h>
#include <mbedtls/sha256.h>

namespace phx_controller_auth_v1 {

// Validate an exact parser-owned byte span. No terminator scan is performed;
// the caller must supply at least length readable bytes.
inline bool hex64(const char *p, size_t length) {
  if (!p || length != 64) return false;
  for (size_t i = 0; i < length; ++i) {
    const char c = p[i];
    if (!((c >= '0' && c <= '9') || (c >= 'a' && c <= 'f'))) return false;
  }
  return true;
}
inline bool equal_fixed(const unsigned char *a,const unsigned char *b,size_t n) {
  unsigned char diff=0;
  for(size_t i=0;i<n;i++) diff|=(unsigned char)(a[i]^b[i]);
  return diff==0;
}
// Deterministic rendering of a 32-byte digest. Shared by SHA256 and HMAC
// so both checks use one auditable lowercase-hex implementation.
inline void encode_sha256_hex(const unsigned char digest[32], char out[65]) {
  static const char kHex[] = "0123456789abcdef";
  for (size_t i = 0; i < 32; ++i) {
    out[2 * i] = kHex[digest[i] >> 4];
    out[2 * i + 1] = kHex[digest[i] & 0x0f];
  }
  out[64] = '\0';
}
inline bool matches_policy_digest(const char *raw_policy,size_t len,
                                  const char *digest,size_t digest_len) {
  if (!raw_policy || !hex64(digest,digest_len)) return false;
  unsigned char hash[32]; char hex[65];
  mbedtls_sha256_context ctx; mbedtls_sha256_init(&ctx);
  bool ok=mbedtls_sha256_starts_ret(&ctx,0)==0 &&
          mbedtls_sha256_update_ret(&ctx,reinterpret_cast<const unsigned char*>(raw_policy),len)==0 &&
          mbedtls_sha256_finish_ret(&ctx,hash)==0;
  mbedtls_sha256_free(&ctx);
  if(!ok) return false;
  encode_sha256_hex(hash, hex);
  return equal_fixed(reinterpret_cast<const unsigned char*>(hex),
                     reinterpret_cast<const unsigned char*>(digest),64);
}
// Caller MUST separately verify strict JSON schema, duplicate-free parsing,
// action, device, original outstanding nonce, full raw-policy bytes, revision
// against accepted local policy and all signed insert/window fields.
// This verifies the exact CORE canonical message only; never grants authority.
inline bool verify_mac(const char *key,size_t key_len,
                       const char *canonical,size_t canonical_len,
                       const char *signature,size_t signature_len) {
  if(!key || !key_len || !canonical || !hex64(signature,signature_len)) return false;
  unsigned char out[32]; char hex[65];
  const mbedtls_md_info_t *md=mbedtls_md_info_from_type(MBEDTLS_MD_SHA256);
  if(!md || mbedtls_md_hmac(md,reinterpret_cast<const unsigned char*>(key),
              key_len,reinterpret_cast<const unsigned char*>(canonical),
              canonical_len,out)!=0) return false;
  encode_sha256_hex(out, hex);
  return equal_fixed(reinterpret_cast<const unsigned char*>(hex),
                     reinterpret_cast<const unsigned char*>(signature),64);
}
inline bool may_admit_coin_even_if_mac_valid() { return false; }
inline bool may_energize_relay_even_if_mac_valid() { return false; }
} // namespace phx_controller_auth_v1
