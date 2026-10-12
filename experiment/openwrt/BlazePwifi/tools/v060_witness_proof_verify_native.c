/*
 * WITNESS-0734: read-only verifier for ONE cryptographically signed external
 * witness statement. NOT an actual monotonic witness or production admission.
 * The caller MUST pin the owner's P-256 PUBLIC identity in a protected domain,
 * derive nonce securely (never reuse), and verify actual independent witness
 * counter/storage/advancement separately. Never turn a valid proof into ACK.
 * No private key I/O, paid writes, network I/O, or customer installation.
 */
#ifndef _GNU_SOURCE
#define _GNU_SOURCE 1
#endif
#include <errno.h>
#include <fcntl.h>
#include <limits.h>
#include <openssl/core_names.h>
#include <openssl/evp.h>
#include <openssl/pem.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>

#if OPENSSL_VERSION_NUMBER < 0x30000000L
#error "WITNESS-0734 requires OpenSSL 3 strict public-key group validation"
#endif
#ifdef BLAZE_PAID_RUNTIME_ENABLED
#error "Proof verification alone MUST NOT enable a v2 payment authority"
#endif
#define MAX_LEDGER 2097152
static void deny(const char *msg) {
  fprintf(stderr,"WITNESS-0734 REJECT: %s (NO PAID ACK)\n",msg);
  exit(9);
}
static int digits(const char *s) {
  size_t i,n=strlen(s);
  if(!n||n>12||(n>1&&s[0]=='0')||s[0]=='0')return 0;
  for(i=0;i<n;i++)if(s[i]<'0'||s[i]>'9')return 0;
  return 1;
}
static int device_id(const char *s) {
  size_t i,n=strlen(s);
  if(n<2||n>32)return 0;
  for(i=0;i<n;i++) {
    char c=s[i];
    if(!((c>='a'&&c<='z')||(c>='A'&&c<='Z')||
         (c>='0'&&c<='9')||c=='-'))return 0;
  }
  return 1;
}
static int nonce_hex(const char *s) {
  size_t i;
  if(strlen(s)!=64)return 0;
  for(i=0;i<64;i++)if(!((s[i]>='0'&&s[i]<='9')||
                         (s[i]>='a'&&s[i]<='f')))return 0;
  return 1;
}
static int protected_fd(const char *path) {
  int fd;struct stat st;
  fd=open(path,O_RDONLY|O_CLOEXEC|O_NOFOLLOW|O_NONBLOCK);
  if(fd<0||fstat(fd,&st)!=0||!S_ISREG(st.st_mode)||
     st.st_uid!=geteuid()||st.st_nlink!=1)deny("unsafe signed proof input");
  return fd;
}
static size_t fixed_read(const char *path,unsigned char *buf,size_t cap) {
  int fd=protected_fd(path);size_t n=0;ssize_t got;
  struct stat start,end;
  if(fstat(fd,&start)!=0||start.st_size<1||
     (unsigned long long)start.st_size>cap)
      deny("invalid protected input size");
  for(;;) {
    if(n==cap) {
      unsigned char extra;
      got=read(fd,&extra,1);
      if(got==0)break;
      if(got<0&&errno==EINTR)continue;
      deny("oversized protected input");
    }
    got=read(fd,buf+n,cap-n);
    if(got==0)break;
    if(got<0&&errno==EINTR)continue;
    if(got<0)deny("read failed");
    n+=(size_t)got;
  }
  if(fstat(fd,&end)!=0||start.st_size!=end.st_size||
     start.st_mtim.tv_sec!=end.st_mtim.tv_sec||
     start.st_mtim.tv_nsec!=end.st_mtim.tv_nsec||
     (size_t)start.st_size!=n||close(fd)!=0)deny("changed signed proof input");
  return n;
}
static void ledger_digest(const char *path,char out[65]) {
  int fd=protected_fd(path),i;unsigned char buf[8192],hash[32];
  EVP_MD_CTX *md=EVP_MD_CTX_new();ssize_t n;size_t total=0;
  struct stat start,end;
  if(!md||fstat(fd,&start)!=0||start.st_size<1||
     start.st_size>MAX_LEDGER||EVP_DigestInit_ex(md,EVP_sha256(),NULL)!=1)
      deny("invalid ledger digest start");
  while((n=read(fd,buf,sizeof(buf)))!=0) {
    if(n<0){if(errno==EINTR)continue;deny("ledger read failed");}
    total+=(size_t)n;
    if(total>MAX_LEDGER||EVP_DigestUpdate(md,buf,(size_t)n)!=1)
      deny("ledger cap/digest failure");
  }
  if(total!=(size_t)start.st_size||fstat(fd,&end)!=0||
     start.st_size!=end.st_size||
     start.st_mtim.tv_sec!=end.st_mtim.tv_sec||
     start.st_mtim.tv_nsec!=end.st_mtim.tv_nsec||
     close(fd)!=0||EVP_DigestFinal_ex(md,hash,NULL)!=1)
      deny("ledger changed during digest");
  EVP_MD_CTX_free(md);
  for(i=0;i<32;i++)sprintf(out+i*2,"%02x",hash[i]);
  out[64]=0;
  OPENSSL_cleanse(hash,sizeof(hash));
}
int main(int argc,char **argv) {
  char digest[65],expected[350],group[80];
  unsigned char payload[512],signature[256];
  size_t pn,sn,groupsize=0;int n,fd;
  FILE *pubfile;EVP_PKEY *key=NULL;EVP_MD_CTX *ctx=NULL;
  if(argc!=9)deny("usage: PUBKEY SNAPSHOT PROOF SIGNATURE DEVICE EPOCH REVISION CHALLENGE_NONCE");
  if(!device_id(argv[5])||!digits(argv[6])||!digits(argv[7])||
     !nonce_hex(argv[8]))deny("malformed expected witness fields");
  ledger_digest(argv[2],digest);
  n=snprintf(expected,sizeof(expected),
      "BLAZE-V2-WITNESS-CHALLENGE/1\t%s\t%s\t%s\t%s\t%s\n",
      argv[5],argv[6],argv[7],digest,argv[8]);
  if(n<=0||(size_t)n>=sizeof(expected))deny("canonical statement overflow");
  pn=fixed_read(argv[3],payload,sizeof(payload));
  if(pn!=(size_t)n||memcmp(payload,expected,pn)!=0)
      deny("witness statement not bound to expected snapshot/challenge");
  sn=fixed_read(argv[4],signature,sizeof(signature));
  /* Public identity is selected by a privileged caller; a caller-provided
     arbitrary key is not a pinned trust root. This executable cannot attest
     how its caller provisioned/trusted a key or a fresh challenge. */
  fd=protected_fd(argv[1]);
  pubfile=fdopen(fd,"rb");
  if(!pubfile)deny("public key open failed");
  key=PEM_read_PUBKEY(pubfile,NULL,NULL,NULL);
  fclose(pubfile);
  if(!key||EVP_PKEY_base_id(key)!=EVP_PKEY_EC||
     EVP_PKEY_bits(key)!=256||
     EVP_PKEY_get_utf8_string_param(key,OSSL_PKEY_PARAM_GROUP_NAME,
                                    group,sizeof(group),&groupsize)!=1||
     strcmp(group,"prime256v1")!=0)deny("untrusted non-P256 proof key");
  ctx=EVP_MD_CTX_new();
  if(!ctx||EVP_DigestVerifyInit(ctx,NULL,EVP_sha256(),NULL,key)!=1||
     EVP_DigestVerifyUpdate(ctx,payload,pn)!=1||
     EVP_DigestVerifyFinal(ctx,signature,sn)!=1)
      deny("invalid detached P-256 witness signature");
  EVP_MD_CTX_free(ctx);EVP_PKEY_free(key);
  OPENSSL_cleanse(signature,sizeof(signature));
  OPENSSL_cleanse(payload,sizeof(payload));
  /* Deliberately NO 'admitted' status: independent monotonic storage,
     key pinning, challenge freshness and advance-before-ACK unproven. */
  puts("WITNESS_STATEMENT_CRYPTO_VALID=1");
  puts("INDEPENDENT_MONOTONIC_WITNESS_VERIFIED=0");
  puts("PAID_ACK_AUTHORIZED=0");
  puts("FINANCIAL_MIGRATION_AUTHORIZED=0");
  puts("CUSTOMER_INSTALL_AUTHORIZED=0");
  return 0;
}
