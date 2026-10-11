/*
 * PAY-0721 — target libcrypto P-256 primitive compatibility PROBE ONLY.
 * Built for host and official target SDKs with a LAB-ONLY macro.
 * No persistent private keys, no production signer, no network/payments,
 * no PKCS#11/TPM claims, no ACKP1 issuer, no v1 import or ledger writes.
 * The one ephemeral test key exists in memory until EVP_PKEY_free.
 * A successful host run or target ELF compile is NOT physical hardware proof.
 */
#ifndef BLAZE_V2_P256_CAPABILITY_LAB_ONLY
#error PAY-0721 refuses builds without explicit LAB-ONLY compile guard
#endif
#include <openssl/evp.h>
#include <openssl/x509.h>
#include <openssl/crypto.h>
#include <stdio.h>
#include <string.h>

static int probe(void) {
    static const unsigned char msg[] = "BLAZE-P256-TARGET-LIBCRYPTO-PROBE/1\n";
    static const unsigned char tampered[] = "BLAZE-P256-TARGET-LIBCRYPTO-PROBE/0\n";
    EVP_PKEY_CTX *gen = NULL;
    EVP_PKEY *private_key = NULL, *public_key = NULL;
    EVP_MD_CTX *signer = NULL, *verifier = NULL;
    unsigned char *sig = NULL, *spki = NULL;
    const unsigned char *cursor;
    int result = 1, der_len, verified;
    size_t sig_len = 0;
    gen = EVP_PKEY_CTX_new_from_name(NULL, "EC", NULL);
    if (gen == NULL || EVP_PKEY_keygen_init(gen) != 1 ||
        EVP_PKEY_CTX_set_group_name(gen, "prime256v1") != 1 ||
        EVP_PKEY_keygen(gen, &private_key) != 1) goto done;
    /* Key generation alone proves no signature or verifier capability. */
    signer = EVP_MD_CTX_new();
    if (signer == NULL ||
        EVP_DigestSignInit(signer, NULL, EVP_sha256(), NULL, private_key) != 1 ||
        EVP_DigestSignUpdate(signer, msg, sizeof(msg)-1) != 1 ||
        EVP_DigestSignFinal(signer, NULL, &sig_len) != 1 ||
        sig_len < 8 || sig_len > 512) goto done;
    sig = OPENSSL_malloc(sig_len);
    if (sig == NULL ||
        EVP_DigestSignFinal(signer, sig, &sig_len) != 1) goto done;
    /* Parse a PUBLIC-ONLY DER SubjectPublicKeyInfo (client-side trust form). */
    der_len = i2d_PUBKEY(private_key, &spki);
    if (der_len <= 0 || der_len > 2048 || spki == NULL) goto done;
    cursor = spki;
    public_key = d2i_PUBKEY(NULL, &cursor, der_len);
    if (public_key == NULL || cursor != spki+der_len) goto done;
    /* Drop the private key BEFORE evaluating the public-only verifier. */
    EVP_PKEY_free(private_key);
    private_key = NULL;
    verifier = EVP_MD_CTX_new();
    if (verifier == NULL ||
        EVP_DigestVerifyInit(verifier, NULL, EVP_sha256(), NULL, public_key) != 1 ||
        EVP_DigestVerifyUpdate(verifier, msg, sizeof(msg)-1) != 1) goto done;
    verified = EVP_DigestVerifyFinal(verifier, sig, sig_len);
    if (verified != 1) goto done;
    if (EVP_DigestVerifyInit(verifier, NULL, EVP_sha256(), NULL, public_key) != 1 ||
        EVP_DigestVerifyUpdate(verifier, tampered, sizeof(tampered)-1) != 1) goto done;
    if (EVP_DigestVerifyFinal(verifier, sig, sig_len) == 1) goto done;
    result = 0;
done:
    EVP_MD_CTX_free(verifier);
    EVP_MD_CTX_free(signer);
    EVP_PKEY_free(public_key);
    EVP_PKEY_free(private_key);
    EVP_PKEY_CTX_free(gen);
    OPENSSL_clear_free(sig, sig_len);
    OPENSSL_free(spki);
    return result;
}
int main(int argc, char **argv) {
    (void)argv;
    if (argc != 1) {
        fputs("PAY-0721 usage: capability probe takes no arguments\n", stderr);
        return 2;
    }
    if (probe() != 0) {
        fputs("PAY-0721 BLOCKED: libcrypto P-256 signing/verifying primitive failed\n",stderr);
        return 3;
    }
    puts("PAY-0721 EPHEMERAL_SIGN_VERIFY_TEST=PASS");
    puts("ALGORITHM=ECDSA-P256-SHA256");
    puts("PUBLIC_VERIFY=SPKI-DER");
    puts("PRIVATE_KEY_PERSISTED=0");
    puts("PRODUCTION_SIGNER_AVAILABLE=0");
    puts("PHYSICAL_TARGET_TESTED=0");
    puts("CUSTOMER_PAID_ACK_AUTHORIZED=0");
    return 0;
}
