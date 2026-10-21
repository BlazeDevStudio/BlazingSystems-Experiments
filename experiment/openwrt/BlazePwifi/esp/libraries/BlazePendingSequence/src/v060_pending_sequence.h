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

static inline int bp_pending_sequence_hex_token(const char *s, size_t min_len,
                                                size_t max_len) {
    size_t i, n = s ? strlen(s) : 0;
    if (n < min_len || n > max_len) return 0;
    for (i = 0; i < n; ++i)
        if (!((s[i] >= '0' && s[i] <= '9') ||
              (s[i] >= 'a' && s[i] <= 'f') ||
              (s[i] >= 'A' && s[i] <= 'F'))) return 0;
    return 1;
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

#endif
