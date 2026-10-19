#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include "../esp/libraries/BlazePendingSequence/src/v060_pending_sequence.h"

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
    puts("Vendo pending sequence contract passed");
    return 0;
}
