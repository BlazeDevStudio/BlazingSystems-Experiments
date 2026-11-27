package com.blazesystems.blazerental;

public final class FloatingTimerPolicy {
    private FloatingTimerPolicy() {}

    public static boolean shouldShow(boolean paid, boolean userEnabled,
                                     boolean operatorAllowed, boolean overlayGranted) {
        return paid && userEnabled && operatorAllowed && overlayGranted;
    }
}
