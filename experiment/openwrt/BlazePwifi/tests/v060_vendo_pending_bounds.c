/* COIN-20261022: ASan proof of corruption-safe parsing of persisted
 * ESP8266/ESP32 pending coin event records. No real flash or network. */
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../esp/libraries/BlazePendingSequence/src/v060_pending_sequence.h"

int main(void) {
    BpPendingSequence *s = (BpPendingSequence *)malloc(sizeof(*s));
    assert(s != NULL);
    memset(s, 'a', sizeof(*s));
    s->magic = BP_PENDING_SEQUENCE_MAGIC;
    s->version = BP_PENDING_SEQUENCE_VERSION;
    s->reserved = 0;
    s->pulses = 1;
    /* A complete binary flash record with an internally correct checksum
     * but missing NUL in BOTH fixed-width token arrays. A weak checksum can
     * be recomputed after malformed writes; it is not authentication.
     */
    int found = 0;
    for (uint64_t i = 0; i < 10000; ++i) {
        s->acked_sequence = i;
        s->sequence = i + 1;
        bp_pending_sequence_seal(s);
        const unsigned char *p = (const unsigned char *)&s->checksum;
        if (p[0] && p[1] && p[2] && p[3]) {
            found = 1;
            break;
        }
    }
    assert(found && s->checksum == bp_pending_sequence_checksum(s));
    assert(!bp_pending_sequence_valid(s)); /* Reject safely, no strlen overread. */
    free(s);

    BpPendingSequence good;
    bp_pending_sequence_init(&good);
    assert(bp_pending_sequence_reserve(&good, 1, "abcdef1234567890",
                                      "0123456789abcdef0123456789abcdef"));
    assert(bp_pending_sequence_valid(&good));
    assert(bp_pending_sequence_commit(&good));
    assert(bp_pending_sequence_valid(&good));
    puts("COIN-20261022 PASS: malformed fully checksummed pending record rejected within fixed array bounds");
    return 0;
}
