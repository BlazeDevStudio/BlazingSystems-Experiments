#pragma once
// PHX-HW-H: ESP32 lab-only primitive. Input must first come from a STRICT,
// duplicate-rejecting JSON parser. This file never admits coins or touches GPIO.
// CORE producer: PR252 at 7f613affd60fe8b1c19f2f8187077ec4aa2463bb.
// No protected reboot freshness, signer custody, or monetary authority.
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <mbedtls/md.h>
#include <mbedtls/sha256.h>

namespace phx_controller_auth_v1 {

inline bool hex64(const char *p) {
  if (!p || strlen(p) != 64) return false;
  for (unsigned i=0;i<64;i++)
    if (!((p[i]>='0'&&p[i]<='9')||(p[i]>='a'&&p[i]<='f'))) return false;
  return true;
}
inline bool equal_fixed(const unsigned char *a,const unsigned char *b,size_t n) {
  unsigned char diff=0;
  for(size_t i=0;i<n;i++) diff|=(unsigned char)(a[i]^b[i]);
  return diff==0;
}
inline bool matches_policy_digest(const char *raw_policy,size_t len,const char *digest) {
  if (!raw_policy || !hex64(digest)) return false;
  unsigned char hash[32]; char hex[65];
  mbedtls_sha256_context ctx; mbedtls_sha256_init(&ctx);
  bool ok=mbedtls_sha256_starts_ret(&ctx,0)==0 &&
          mbedtls_sha256_update_ret(&ctx,reinterpret_cast<const unsigned char*>(raw_policy),len)==0 &&
          mbedtls_sha256_finish_ret(&ctx,hash)==0;
  mbedtls_sha256_free(&ctx);
  if(!ok) return false;
  for(size_t i=0;i<32;i++) snprintf(hex+i*2,3,"%02x",hash[i]);
  hex[64]=0;
  return equal_fixed(reinterpret_cast<const unsigned char*>(hex),
                     reinterpret_cast<const unsigned char*>(digest),64);
}
// Caller MUST separately verify strict JSON schema, duplicate-free parsing,
// action, device, original outstanding nonce, full raw-policy bytes, revision
// against accepted local policy and all signed insert/window fields.
// This verifies the exact CORE canonical message only; never grants authority.
inline bool verify_mac(const char *key,size_t key_len,
                       const char *canonical,const char *signature) {
  if(!key || !key_len || !canonical || !hex64(signature)) return false;
  unsigned char out[32]; char hex[65];
  const mbedtls_md_info_t *md=mbedtls_md_info_from_type(MBEDTLS_MD_SHA256);
  if(!md || mbedtls_md_hmac(md,reinterpret_cast<const unsigned char*>(key),
              key_len,reinterpret_cast<const unsigned char*>(canonical),
              strlen(canonical),out)!=0) return false;
  for(size_t i=0;i<32;i++) snprintf(hex+i*2,3,"%02x",out[i]);
  hex[64]=0;
  return equal_fixed(reinterpret_cast<const unsigned char*>(hex),
                     reinterpret_cast<const unsigned char*>(signature),64);
}
inline bool may_admit_coin_even_if_mac_valid() { return false; }
inline bool may_energize_relay_even_if_mac_valid() { return false; }
} // namespace phx_controller_auth_v1
