package com.blazesystems.blazerental;

import org.junit.Test;
import static org.junit.Assert.*;

public class RentalPolicyStoreTest {
    private static final class MemoryStorage implements RentalPolicyStore.Storage {
        RentalPolicyStore.StoredPolicy value;
        @Override public RentalPolicyStore.StoredPolicy load() { return value; }
        @Override public void save(RentalPolicyStore.StoredPolicy storedPolicy) { value = storedPolicy; }
    }

    private static RentalPolicyStore.StoredPolicy stored(long revision) {
        RentalPolicy policy = new RentalPolicy(revision, RentalPolicy.MODE_RENTAL, null, null, null);
        return new RentalPolicyStore.StoredPolicy(policy, "payload-" + revision, "sig-" + revision);
    }

    @Test public void rejectsUnverifiedPolicy() {
        MemoryStorage storage = new MemoryStorage();
        RentalPolicyStore store = new RentalPolicyStore(storage);
        assertFalse(store.applyVerified(stored(1L), false));
        assertNull(store.getCurrent());
    }

    @Test public void persistsNewerVerifiedPolicy() {
        MemoryStorage storage = new MemoryStorage();
        RentalPolicyStore store = new RentalPolicyStore(storage);
        assertTrue(store.applyVerified(stored(1L), true));
        assertEquals(1L, store.getCurrent().policy.getRevision());
        assertSame(storage.value, store.getCurrent());
    }

    @Test public void stalePolicyCannotReplaceNewerRevision() {
        MemoryStorage storage = new MemoryStorage();
        storage.value = stored(5L);
        RentalPolicyStore store = new RentalPolicyStore(storage);
        assertFalse(store.applyVerified(stored(4L), true));
        assertFalse(store.applyVerified(stored(5L), true));
        assertEquals(5L, store.getCurrent().policy.getRevision());
    }
}
