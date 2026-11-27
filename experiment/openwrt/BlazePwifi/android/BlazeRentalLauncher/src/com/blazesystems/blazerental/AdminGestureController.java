package com.blazesystems.blazerental;

public final class AdminGestureController {
    private final long holdMs;
    private long pressedAt = -1L;

    public AdminGestureController(long holdMs) {
        if (holdMs < 1500L || holdMs > 15000L) throw new IllegalArgumentException("invalid hold");
        this.holdMs = holdMs;
    }

    public void onDown(long nowMs) { pressedAt = nowMs; }

    public boolean onUp(long nowMs) {
        if (pressedAt < 0L) return false;
        long elapsed = nowMs - pressedAt;
        pressedAt = -1L;
        return elapsed >= holdMs;
    }

    public boolean shouldTrigger(long nowMs) {
        return pressedAt >= 0L && nowMs - pressedAt >= holdMs;
    }

    public void cancel() { pressedAt = -1L; }
}
