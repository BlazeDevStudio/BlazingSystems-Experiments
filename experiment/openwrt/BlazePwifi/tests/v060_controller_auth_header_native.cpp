// Executes the actual firmware header with system mbedTLS (not a Python model).
// Synthetic lab key; no device provisioning or coin/relay admission.
#include "../esp32/BlazePwifiVendo32/ControllerAuthV1Lab.h"
#include <cassert>
#include <cstdio>
#include <cstring>
#include <string>
#include <vector>
using namespace phx_controller_auth_v1;
static std::string mac(const std::string &body) {
  const char key[]="synthetic-controller-v1-key";
  const mbedtls_md_info_t *md=mbedtls_md_info_from_type(MBEDTLS_MD_SHA256);
  unsigned char out[32]; char hex[65];
  assert(md && mbedtls_md_hmac(md,(const unsigned char*)key,strlen(key),
    (const unsigned char*)body.data(),body.size(),out)==0);
  for(size_t i=0;i<32;i++) snprintf(hex+i*2,3,"%02x",out[i]);
  hex[64]=0; return hex;
}
int main() {
  // Exact byte spans need no trailing NUL and must never be scanned past.
  char raw_digest[64];
  memset(raw_digest, 'a', sizeof(raw_digest));
  assert(hex64(raw_digest, sizeof(raw_digest)));
  assert(!hex64(raw_digest, 0));
  assert(!hex64(raw_digest, sizeof(raw_digest) - 1));
  char oversized_digest[65];
  memset(oversized_digest, 'a', sizeof(oversized_digest));
  assert(!hex64(oversized_digest, sizeof(oversized_digest)));
  char uppercase_digest[64];
  memset(uppercase_digest, 'A', sizeof(uppercase_digest));
  assert(!hex64(uppercase_digest, sizeof(uppercase_digest)));
  assert(!hex64(nullptr, 64));
  assert(!hex64(nullptr, 0));

  // The fixed-span comparator is a public header helper: invalid pointers and
  // empty spans must fail closed before any dereference or equality result.
  const unsigned char compare_byte = 0x5a;
  const unsigned char other_compare_byte = 0xa5;
  assert(!equal_fixed(nullptr, &compare_byte, 1));
  assert(!equal_fixed(&compare_byte, nullptr, 1));
  assert(!equal_fixed(nullptr, nullptr, 1));
  assert(!equal_fixed(nullptr, nullptr, 0));
  assert(!equal_fixed(&compare_byte, &compare_byte, 0));
  assert(equal_fixed(&compare_byte, &compare_byte, 1));
  assert(!equal_fixed(&compare_byte, &other_compare_byte, 1));
  std::puts("PHX-HW fixed comparator null/empty spans fail closed PASS");

  unsigned char sample[32];
  for (size_t i = 0; i < sizeof(sample); ++i) sample[i] = (unsigned char)i;
  char rendered[65];
  encode_sha256_hex(sample, rendered);
  assert(strcmp(rendered, "000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f") == 0);
  std::puts("PHX-HW-CFG length-aware hex span and lowercase renderer PASS");

  const char key[]="synthetic-controller-v1-key";
  const std::string policy="{\\"enabled\\":0,\\"coin_enabled\\":0,\\"config_revision\\":7}";
  unsigned char hash[32]; char hashhex[65];
  mbedtls_sha256_context ctx; mbedtls_sha256_init(&ctx);
  assert(mbedtls_sha256_starts_ret(&ctx,0)==0);
  assert(mbedtls_sha256_update_ret(&ctx,(const unsigned char*)policy.data(),policy.size())==0);
  assert(mbedtls_sha256_finish_ret(&ctx,hash)==0);
  mbedtls_sha256_free(&ctx);
  for(size_t i=0;i<32;i++) snprintf(hashhex+i*2,3,"%02x",hash[i]);
  hashhex[64]=0;
  assert(matches_policy_digest(policy.data(),policy.size(),hashhex,64));
  assert(!matches_policy_digest(policy.data(),policy.size(),hashhex,0));
  assert(!matches_policy_digest(nullptr,policy.size(),hashhex,64));
  assert(!matches_policy_digest(policy.data(),policy.size(),nullptr,64));
  assert(!matches_policy_digest(policy.data(),policy.size(),hashhex,63));
  assert(!matches_policy_digest((policy+" ").data(),policy.size()+1,hashhex,64));
  // Empty policy bytes are invalid even when their digest is correct.
  const char emptySha256[] = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855";
  assert(!matches_policy_digest("",0,emptySha256,sizeof(emptySha256)-1));
  std::puts("PHX-HW empty policy span denied PASS");

  const std::string prefix="blazepwifi-controller-response-v1|poll|";
  const std::string suffix=std::string("|7|")+hashhex+"|0||0|DENY";
  const std::string good=prefix+"vendo-01|0011223344556677"+suffix;
  const std::string signature=mac(good);
  assert(!verify_mac(key,strlen(key),good.data(),good.size(),
                     signature.data(),0));
  std::puts("PHX-HW zero-length digest and signature spans denied PASS");
  // An empty message cannot be a canonical controller response.
  const std::string emptyCanonical;
  const std::string emptyCanonicalMac=mac(emptyCanonical);
  assert(!verify_mac(key,strlen(key),emptyCanonical.data(),emptyCanonical.size(),
                     emptyCanonicalMac.data(),emptyCanonicalMac.size()));
  std::puts("PHX-HW empty canonical span denied PASS");
  const std::vector<char> raw_canonical(good.begin(),good.end());
  const std::vector<char> raw_signature(signature.begin(),signature.end());
  assert(!verify_mac(nullptr,strlen(key),raw_canonical.data(),raw_canonical.size(),
                     raw_signature.data(),raw_signature.size()));
  assert(!verify_mac(key,strlen(key),nullptr,good.size(),
                     raw_signature.data(),raw_signature.size()));
  assert(!verify_mac(key,strlen(key),raw_canonical.data(),raw_canonical.size(),
                     nullptr,64));
  std::puts("PHX-HW null parser-span pointers denied PASS");
  assert(verify_mac(key,strlen(key),raw_canonical.data(),raw_canonical.size(),
                    raw_signature.data(),raw_signature.size()));
  assert(!may_admit_coin_even_if_mac_valid());
  assert(!may_energize_relay_even_if_mac_valid());
  std::puts("PHX-HW-CFG case 1 signed response, admission DENIED PASS");

  std::vector<char> badsig(raw_signature);
  badsig[0]=badsig[0]=='0'?'1':'0';
  assert(!verify_mac(key,strlen(key),raw_canonical.data(),raw_canonical.size(),
                     badsig.data(),badsig.size()));
  std::puts("PHX-HW-CFG case 2 tampered signature DENIED PASS");
  const std::string wrong_device=prefix+"vendo-02|0011223344556677"+suffix;
  assert(!verify_mac(key,strlen(key),wrong_device.data(),wrong_device.size(),
                     raw_signature.data(),raw_signature.size()));
  std::puts("PHX-HW-CFG case 3 wrong device DENIED PASS");
  const std::string wrong_nonce=prefix+"vendo-01|8899aabbccddeeff"+suffix;
  assert(!verify_mac(key,strlen(key),wrong_nonce.data(),wrong_nonce.size(),
                     raw_signature.data(),raw_signature.size()));
  std::puts("PHX-HW-CFG case 4 wrong nonce DENIED PASS");
  const char invalid_signature[]="invalid";
  assert(!verify_mac(key,strlen(key),raw_canonical.data(),raw_canonical.size(),
                     invalid_signature,sizeof(invalid_signature)-1));
  assert(!verify_mac("",0,raw_canonical.data(),raw_canonical.size(),
                     raw_signature.data(),raw_signature.size()));
  std::puts("PHX-HW-CFG case 5 invalid signature/empty key DENIED PASS");
  std::puts("PHX-HW-CFG 5/5 header-executed synthetic checks PASS; protected witness UNPROVEN");
}
