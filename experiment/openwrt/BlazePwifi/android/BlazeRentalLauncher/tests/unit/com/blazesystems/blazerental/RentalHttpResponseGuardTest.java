package com.blazesystems.blazerental;

import org.junit.Test;
import static org.junit.Assert.*;
import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;

public final class RentalHttpResponseGuardTest {
    private static final class TrackedStream extends ByteArrayInputStream {
        boolean closed;
        TrackedStream(byte[] content) { super(content); }
        @Override public void close() {
            closed = true;
            super.close();
        }
    }

    @Test public void redirectsAreNeverValidResponses() {
        assertTrue(RentalHttpResponseGuard.isRedirect(301));
        assertTrue(RentalHttpResponseGuard.isRedirect(302));
        assertTrue(RentalHttpResponseGuard.isRedirect(303));
        assertTrue(RentalHttpResponseGuard.isRedirect(307));
        assertTrue(RentalHttpResponseGuard.isRedirect(308));
        assertFalse(RentalHttpResponseGuard.isRedirect(200));
        assertFalse(RentalHttpResponseGuard.isRedirect(400));
        assertFalse(RentalHttpResponseGuard.isRedirect(500));
    }

    @Test public void acceptsSmallJsonAndClosesStream() throws Exception {
        TrackedStream in = new TrackedStream("{\"ok\":true}".getBytes(StandardCharsets.UTF_8));
        assertEquals("{\"ok\":true}", RentalHttpResponseGuard.readLimited(in));
        assertTrue(in.closed);
    }

    @Test public void acceptsExactlyTheMaximum() throws Exception {
        byte[] bytes = new byte[RentalHttpResponseGuard.MAX_BODY_BYTES];
        java.util.Arrays.fill(bytes, (byte) 'a');
        TrackedStream in = new TrackedStream(bytes);
        assertEquals(bytes.length, RentalHttpResponseGuard.readLimited(in).length());
        assertTrue(in.closed);
    }

    @Test public void refusesOversizeAndClosesStream() throws Exception {
        byte[] bytes = new byte[RentalHttpResponseGuard.MAX_BODY_BYTES + 1];
        TrackedStream in = new TrackedStream(bytes);
        try {
            RentalHttpResponseGuard.readLimited(in);
            fail("Oversized Rental JSON must fail closed");
        } catch (IOException expected) {
            assertTrue(expected.getMessage().contains("exceeds maximum"));
        }
        assertTrue(in.closed);
    }
}
