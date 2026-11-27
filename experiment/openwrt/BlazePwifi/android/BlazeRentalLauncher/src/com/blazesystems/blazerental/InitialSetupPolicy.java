package com.blazesystems.blazerental;

public final class InitialSetupPolicy {
    private InitialSetupPolicy() {}

    public static boolean needsInitialSetup(boolean enrolled, boolean hasAdminVerifier) {
        return !enrolled || !hasAdminVerifier;
    }
}
