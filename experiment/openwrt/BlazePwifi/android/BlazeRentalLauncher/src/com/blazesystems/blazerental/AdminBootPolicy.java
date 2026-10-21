package com.blazesystems.blazerental;

/**
 * Boot boundaries invalidate elapsed-realtime-based privileges.
 * The outstanding failed-login lockout starts fresh after reboot rather
 * than becoming a stale uptime timestamp from the previous boot.
 */
public final class AdminBootPolicy {
    public static final long LOCKOUT_MS = 15L * 60L * 1000L;

    private AdminBootPolicy() {}

    public static long lockedUntilAfterReboot(long previousLockedUntilMs,
                                              long currentElapsedRealtimeMs) {
        if (previousLockedUntilMs <= 0L) return 0L;
        long now = Math.max(0L, currentElapsedRealtimeMs);
        return now > Long.MAX_VALUE - LOCKOUT_MS
                ? Long.MAX_VALUE : now + LOCKOUT_MS;
    }
}
