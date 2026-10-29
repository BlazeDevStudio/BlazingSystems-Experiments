// Executes the actual firmware header with system mbedTLS (not a Python model).
// Synthetic lab key; no device provisioning or coin/relay admission.
#include "../esp32/BlazePwifiVendo32/ControllerAuthV1Lab.h"
#include <cassert>
#include <cstdio>
#include <cstring>
#include <string>
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
  const char key[]="synthetic-controller-v1-key";
  const std::string policy="{\"enabled\":0,\"coin_enabled\":0,\"config_revision\":7}";
  const char *digest=""; // use vetted SHA256 to derive the literal policy digest.
  (void)digest;
  unsigned char hash[32]; char hashhex[65];
  mbedtls_sha256_context ctx; mbedtls_sha256_init(&ctx);
  assert(mbedtls_sha256_starts_ret(&ctx,0)==0);
  assert(mbedtls_sha256_update_ret(&ctx,(const unsigned char*)policy.data(),policy.size())==0);
  assert(mbedtls_sha256_finish_ret(&ctx,hash)==0);
  mbedtls_sha256_free(&ctx);
  for(size_t i=0;i<32;i++) snprintf(hashhex+i*2,3,"%02x",hash[i]);
  hashhex[64]=0;
  assert(matches_policy_digest(policy.data(),policy.size(),hashhex));
  assert(!matches_policy_digest((policy+" ").data(),policy.size()+1,hashhex));
  const std::string prefix="blazepwifi-controller-response-v1|poll|";
  const std::string suffix=std::string("|7|")+hashhex+"|0||0|DENY";
  const std::string good=prefix+"vendo-01|0011223344556677"+suffix;
  const std::string signature=mac(good);
  assert(verify_mac(key,strlen(key),good.c_str(),signature.c_str()));
  assert(!may_admit_coin_even_if_mac_valid());
  assert(!may_energize_relay_even_if_mac_valid());
  std::puts("PHX-HW-CFG case 1 signed response, admission DENIED PASS");
  std::string badsig=signature; badsig[0]=badsig[0]=='0'?'1':'0';
  assert(!verify_mac(key,strlen(key),good.c_str(),badsig.c_str()));
  std::puts("PHX-HW-CFG case 2 tampered signature DENIED PASS");
  const std::string wrong_device=prefix+"vendo-02|0011223344556677"+suffix;
  assert(!verify_mac(key,strlen(key),wrong_device.c_str(),signature.c_str()));
  std::puts("PHX-HW-CFG case 3 wrong device DENIED PASS");
  const std::string wrong_nonce=prefix+"vendo-01|8899aabbccddeeff"+suffix;
  assert(!verify_mac(key,strlen(key),wrong_nonce.c_str(),signature.c_str()));
  std::puts("PHX-HW-CFG case 4 wrong nonce DENIED PASS");
  assert(!verify_mac(key,strlen(key),good.c_str(),"invalid"));
  assert(!verify_mac("",0,good.c_str(),signature.c_str()));
  std::puts("PHX-HW-CFG case 5 invalid signature/empty key DENIED PASS");
  std::puts("PHX-HW-CFG 5/5 header-executed synthetic checks PASS; protected witness UNPROVEN");
}
