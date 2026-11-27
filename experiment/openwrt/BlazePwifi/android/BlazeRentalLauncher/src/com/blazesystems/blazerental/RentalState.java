package com.blazesystems.blazerental;

/**
 * Monotonic rental lease state. Wall-clock time is intentionally not used here.
 */
public final class RentalState {
    private final long leaseUntilElapsedRealtimeMs;

    public RentalState(long leaseUntilElapsedRealtimeMs) {
        if (leaseUntilElapsedRealtimeMs < 0L) {
            throw new IllegalArgumentException("leaseUntilElapsedRealtimeMs must be >= 0");
        }
        this.leaseUntilElapsedRealtimeMs = leaseUntilElapsedRealtimeMs;
    }

    public long getLeaseUntilElapsedRealtimeMs() {
        return leaseUntilElapsedRealtimeMs;
    }

    public boolean isPaid(long monotonicNowMs) {
        if (monotonicNowMs < 0L) {
            throw new IllegalArgumentException("monotonicNowMs must be >= 0");
        }
        return leaseUntilElapsedRealtimeMs > monotonicNowMs;
    }

    public long remainingMs(long monotonicNowMs) {
        if (monotonicNowMs < 0L) {
            throw new IllegalArgumentException("monotonicNowMs must be >= 0");
        }
        long remaining = leaseUntilElapsedRealtimeMs - monotonicNowMs;
        return remaining > 0L ? remaining : 0L;
    }
}
