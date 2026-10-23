#ifndef BLAZEPWIFI_V060_PENDING_SEQUENCE_H
#define BLAZEPWIFI_V060_PENDING_SEQUENCE_H

#include <stddef.h>
#include <stdint.h>
#include <string.h>

#define BP_PENDING_SEQUENCE_MAGIC 0x42505632UL
#define BP_PENDING_SEQUENCE_VERSION 2U
#define BP_PENDING_SEQUENCE_MAX 100000000ULL

typedef struct {
    uint32_t magic;
    uint16_t version;
    uint16_t reserved;
    uint64_t acked_sequence;
    uint64_t sequence;
    uint8_t pulses;
    char nonce[17];
    char target[33];
    uint32_t checksum;
} BpPendingSequence;

static inline uint32_t bp_pending_sequence_checksum(const BpPendingSequence *s) {
    const uint8_t *p = (const uint8_t *)s;
    uint32_t h = 2166136261UL;
    size_t i;
    for (i = 0; i < offsetof(BpPendingSequence, checksum); ++i) {
        h ^= p[i];
        h *= 16777619UL;
    }
    return h;
}

/* The persisted nonce[17] / target[33] fields may be corrupt and lack NUL.
 * Read at most max_len+1 bytes (including the final terminator slot) so a
 * forged checksum cannot make validation scan beyond the fixed-size field. */
static inline int bp_pending_sequence_hex_token(const char *s, size_t min_len,
                                                size_t max_len) {
    size_t i;
    if (!s || min_len > max_len) return 0;
    for (i = 0; i < max_len; ++i) {
        unsigned char c = (unsigned char)s[i];
        if (c == 0) return i >= min_len;
        if (!((c >= '0' && c <= '9') ||
              (c >= 'a' && c <= 'f') ||
              (c >= 'A' && c <= 'F'))) return 0;
    }
    return s[max_len] == '\0';
}

static inline void bp_pending_sequence_seal(BpPendingSequence *s) {
    s->magic = BP_PENDING_SEQUENCE_MAGIC;
    s->version = BP_PENDING_SEQUENCE_VERSION;
    s->reserved = 0;
    s->checksum = bp_pending_sequence_checksum(s);
}

static inline void bp_pending_sequence_init(BpPendingSequence *s) {
    memset(s, 0, sizeof(*s));
    bp_pending_sequence_seal(s);
}

static inline int bp_pending_sequence_valid(const BpPendingSequence *s) {
    if (!s || s->magic != BP_PENDING_SEQUENCE_MAGIC ||
        s->version != BP_PENDING_SEQUENCE_VERSION || s->reserved != 0 ||
        s->acked_sequence > BP_PENDING_SEQUENCE_MAX ||
        s->checksum != bp_pending_sequence_checksum(s)) return 0;
    if (s->sequence == 0)
        return s->pulses == 0 && s->nonce[0] == '\0' && s->target[0] == '\0';
    return s->acked_sequence < BP_PENDING_SEQUENCE_MAX &&
        s->sequence == s->acked_sequence + 1 && s->pulses > 0 &&
        s->pulses <= 20 && bp_pending_sequence_hex_token(s->nonce, 8, 16) &&
        bp_pending_sequence_hex_token(s->target, 8, 32);
}

/* Reserve once, then only permit pulse growth for the same pending event. */
static inline int bp_pending_sequence_reserve(BpPendingSequence *s,
        uint8_t pulses, const char *nonce, const char *target) {
    size_t nn, tn;
    if (!bp_pending_sequence_valid(s) || pulses == 0 || pulses > 20 ||
        !bp_pending_sequence_hex_token(nonce, 8, 16) ||
        !bp_pending_sequence_hex_token(target, 8, 32)) return 0;
    nn = strlen(nonce); tn = strlen(target);
    if (s->sequence != 0) {
        if (strcmp(s->nonce, nonce) || strcmp(s->target, target) ||
            pulses < s->pulses) return 0;
    } else {
        if (s->acked_sequence >= BP_PENDING_SEQUENCE_MAX) return 0;
        s->sequence = s->acked_sequence + 1;
        memcpy(s->nonce, nonce, nn + 1);
        memcpy(s->target, target, tn + 1);
    }
    s->pulses = pulses;
    bp_pending_sequence_seal(s);
    return 1;
}

/* Call only after a success acknowledgment; persistence must finish first. */
static inline int bp_pending_sequence_commit(BpPendingSequence *s) {
    if (!bp_pending_sequence_valid(s) || s->sequence == 0) return 0;
    s->acked_sequence = s->sequence;
    s->sequence = 0;
    s->pulses = 0;
    memset(s->nonce, 0, sizeof(s->nonce));
    memset(s->target, 0, sizeof(s->target));
    bp_pending_sequence_seal(s);
    return 1;
}

/* A known pre-commit rejection releases the slot without consuming sequence. */
static inline int bp_pending_sequence_abandon(BpPendingSequence *s) {
    if (!bp_pending_sequence_valid(s) || s->sequence == 0) return 0;
    s->sequence = 0;
    s->pulses = 0;
    memset(s->nonce, 0, sizeof(s->nonce));
    memset(s->target, 0, sizeof(s->target));
    bp_pending_sequence_seal(s);
    return 1;
}


#ifdef __cplusplus
/* Recovery of a validated /pending.new or /pending.bak must not claim success
 * if the LittleFS promotion fails. The previous source file remains on disk
 * after a failed rename, to be retried or inspected with the coin relay off.
 * Store supplies exists(), remove(), rename(); tested with a failing fake FS.
 * Never erase a readable canonical record before validating the replacement.
 */
template <typename Store>
static inline bool bp_pending_promote_recovered(Store &store,
                                                  const char *chosen) {
    if (!chosen) return false;
    if (!strcmp(chosen, "/pending.dat")) return store.exists("/pending.dat");
    if (strcmp(chosen, "/pending.new") && strcmp(chosen, "/pending.bak"))
        return false;
    if (!store.exists(chosen)) return false;
    if (store.exists("/pending.dat") && !store.remove("/pending.dat"))
        return false;
    return store.rename(chosen, "/pending.dat");
}
#endif

#endif
