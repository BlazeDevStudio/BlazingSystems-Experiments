package com.blazesystems.blazerental;

public final class AdminSession {
    public interface Clock { long nowMs(); }

    private final Clock clock;
    private final long durationMs;
    private long unlockedUntilMs;

    public AdminSession(Clock clock, long durationMs) {
        if (clock == null || durationMs <= 0L) throw new IllegalArgumentException();
        this.clock = clock;
        this.durationMs = durationMs;
    }

    public void unlock() { unlockedUntilMs = clock.nowMs() + durationMs; }
    public void clear() { unlockedUntilMs = 0L; }
    public boolean isActive() { return clock.nowMs() < unlockedUntilMs; }
    public long remainingMs() { return Math.max(0L, unlockedUntilMs - clock.nowMs()); }
}
