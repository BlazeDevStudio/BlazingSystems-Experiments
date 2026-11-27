package com.blazesystems.blazerental;

import org.junit.Test;
import static org.junit.Assert.*;

public class AdminSessionTest {
    private static final class FakeClock implements AdminSession.Clock {
        long now;
        @Override public long nowMs() { return now; }
    }

    @Test public void sessionExpiresAtConfiguredDeadline() {
        FakeClock clock = new FakeClock();
        AdminSession session = new AdminSession(clock, 300000L);
        session.unlock();
        clock.now = 299999L;
        assertTrue(session.isActive());
        clock.now = 300000L;
        assertFalse(session.isActive());
    }

    @Test public void clearEndsSessionImmediately() {
        FakeClock clock = new FakeClock();
        AdminSession session = new AdminSession(clock, 10000L);
        session.unlock();
        session.clear();
        assertFalse(session.isActive());
    }
}
