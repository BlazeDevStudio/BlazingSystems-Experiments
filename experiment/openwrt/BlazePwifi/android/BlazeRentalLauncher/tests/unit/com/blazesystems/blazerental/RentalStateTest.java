package com.blazesystems.blazerental;

import org.junit.Test;
import static org.junit.Assert.*;

public class RentalStateTest {
    @Test public void paidBeforeMonotonicExpiry() {
        RentalState state = new RentalState(10_000L);
        assertTrue(state.isPaid(9_999L));
        assertEquals(1L, state.remainingMs(9_999L));
    }

    @Test public void expiredAtExactExpiry() {
        RentalState state = new RentalState(10_000L);
        assertFalse(state.isPaid(10_000L));
        assertEquals(0L, state.remainingMs(10_001L));
    }

    @Test(expected = IllegalArgumentException.class)
    public void rejectsNegativeLease() {
        new RentalState(-1L);
    }
}
