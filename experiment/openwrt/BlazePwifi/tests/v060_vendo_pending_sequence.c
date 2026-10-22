#define _GNU_SOURCE
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#ifdef __linux__
#include <sys/mman.h>
#include <unistd.h>
#endif
#include "../esp/libraries/BlazePendingSequence/src/v060_pending_sequence.h"


/* Native guard-page fixture: a corrupt fixed-size flash token must never make
 * the validator inspect bytes beyond the maximum storage length.
 * ESP firmware uses the same shared header without host OS dependencies. */
#ifdef __linux__
static void check_token_page_boundary(size_t max_len) {
    long page = sysconf(_SC_PAGESIZE);
    assert(page > 0 && max_len + 1 < (size_t)page);
    void *mem = mmap(NULL, (size_t)page * 2, PROT_READ | PROT_WRITE,
                     MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    assert(mem != MAP_FAILED);
    assert(mprotect((char *)mem + page, (size_t)page, PROT_NONE) == 0);
    char *token = (char *)mem + page - (max_len + 1);
    memset(token, 'a', max_len + 1); /* deliberately NO NUL */
    assert(bp_pending_sequence_hex_token(token, 8, max_len) == 0);
    token[max_len] = '\0';
    assert(bp_pending_sequence_hex_token(token, 8, max_len) == 1);
    assert(munmap(mem, (size_t)page * 2) == 0);
}
#endif

int main(void) {
    BpPendingSequence s;
    BpPendingSequence recovered;
    bp_pending_sequence_init(&s);
    assert(bp_pending_sequence_valid(&s));

    assert(bp_pending_sequence_reserve(&s, 3, "abcdef0102030405", "abcdef0102030405") == 1);
    assert(s.acked_sequence == 0 && s.sequence == 1);
    recovered = s; /* power loss after durable reservation, before ACK */
    assert(bp_pending_sequence_valid(&recovered));
    assert(bp_pending_sequence_reserve(&recovered, 3, "abcdef0102030405", "abcdef0102030405") == 1);
    assert(recovered.sequence == 1); /* retry/lost ACK reuses exact sequence */
    assert(bp_pending_sequence_reserve(&recovered, 4, "abcdef0102030405", "abcdef0102030405") == 1);
    assert(recovered.sequence == 1 && recovered.pulses == 4);
    assert(bp_pending_sequence_reserve(&recovered, 4, "abcdef0102030406", "abcdef0102030405") == 0);
    assert(bp_pending_sequence_commit(&recovered) == 1);
    assert(recovered.acked_sequence == 1 && recovered.sequence == 0);

    assert(bp_pending_sequence_reserve(&recovered, 2, "abcdef0102030406", "abcdef0102030406") == 1);
    assert(recovered.sequence == 2);
    assert(bp_pending_sequence_abandon(&recovered) == 1);
    assert(recovered.acked_sequence == 1 && recovered.sequence == 0);
    assert(bp_pending_sequence_reserve(&recovered, 2, "abcdef0102030407", "abcdef0102030407") == 1);
    assert(recovered.sequence == 2); /* rejected request may safely reuse sequence */

    recovered.checksum ^= 1;
    assert(!bp_pending_sequence_valid(&recovered)); /* corrupt state is rejected */

    /* Badly corrupted but checksum-consistent flash records fail closed. */
    bp_pending_sequence_init(&s);
    assert(bp_pending_sequence_reserve(&s, 1, "0102030405060708", "0102030405060708"));
    memset(s.nonce, 'a', sizeof(s.nonce));
    bp_pending_sequence_seal(&s);
    assert(!bp_pending_sequence_valid(&s));
    bp_pending_sequence_init(&s);
    assert(bp_pending_sequence_reserve(&s, 1, "0102030405060708", "0102030405060708"));
    memset(s.target, 'a', sizeof(s.target));
    bp_pending_sequence_seal(&s);
    assert(!bp_pending_sequence_valid(&s));
#ifdef __linux__
    check_token_page_boundary(16); /* ESP nonce[17] */
    check_token_page_boundary(32); /* ESP target[33] */
#endif
    puts("Vendo pending sequence contract passed");
    return 0;
}
