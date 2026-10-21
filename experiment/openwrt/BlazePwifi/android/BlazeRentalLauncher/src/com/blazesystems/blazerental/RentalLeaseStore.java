package com.blazesystems.blazerental;

import android.content.Context;
import android.content.SharedPreferences;
import android.os.Build;
import android.os.PersistableBundle;
import android.os.SystemClock;

public final class RentalLeaseStore {
    private static final String PREFS = "blaze_rental_v04";
    private RentalLeaseStore() {}

    private static Context storage(Context context) {
        return Build.VERSION.SDK_INT >= 24
                ? context.createDeviceProtectedStorageContext() : context;
    }

    private static SharedPreferences prefs(Context context) {
        return storage(context).getSharedPreferences(PREFS, Context.MODE_PRIVATE);
    }

    public static void acceptProvisioningExtras(Context context, PersistableBundle extras) {
        if (extras == null) return;
        prefs(context).edit()
                .putString("server", safe(extras.getString("server_url")))
                .putString("enrollment", safe(extras.getString("enrollment_token")))
                .putString("device_name", safe(extras.getString("device_name")))
                .apply();
    }

    public static void saveManualEnrollment(Context context, String server, String token, String name) {
        prefs(context).edit()
                .putString("server", safe(server))
                .putString("enrollment", safe(token))
                .putString("device_name", safe(name))
                .putBoolean("setup_complete", false)
                .remove("device_id")
                .remove("device_secret")
                .remove("lease_duration_ms")
                .remove("lease_sync_elapsed")
                .apply();
        AndroidRentalPolicyRepository.clear(context);
    }

    public static void setDeviceIdentity(Context context, String id, String secret) {
        prefs(context).edit()
                .putString("device_id", safe(id))
                .putString("device_secret", safe(secret))
                .apply();
    }

    public static void recordLease(Context context, long serverNowMs, long leaseUntilMs) {
        long duration = Math.max(0L, leaseUntilMs - serverNowMs);
        prefs(context).edit()
                .putLong("lease_duration_ms", duration)
                .putLong("lease_sync_elapsed", SystemClock.elapsedRealtime())
                .putLong("server_time_ms", serverNowMs)
                .putLong("lease_until_ms", leaseUntilMs)
                .apply();
        RentalAlarmReceiver.schedule(context, duration);
    }

    public static RentalState rentalState(Context context) {
        SharedPreferences p = prefs(context);
        long sync = p.getLong("lease_sync_elapsed", 0L);
        long duration = p.getLong("lease_duration_ms", 0L);
        if (sync <= 0L || duration <= 0L || SystemClock.elapsedRealtime() < sync) {
            return new RentalState(0L);
        }
        return new RentalState(sync + duration);
    }

    public static boolean isLeaseValid(Context context) {
        return rentalState(context).isPaid(SystemClock.elapsedRealtime());
    }

    public static long remainingMs(Context context) {
        return rentalState(context).remainingMs(SystemClock.elapsedRealtime());
    }

    public static void invalidateLeaseAfterBoot(Context context) {
        // elapsedRealtime() starts over after every boot. A persisted deadline
        // for an unlocked administrator session must never survive that reset.
        SharedPreferences p = prefs(context);
        long previousLockout = p.getLong("admin_locked_until", 0L);
        long nextLockout = AdminBootPolicy.lockedUntilAfterReboot(
                previousLockout, SystemClock.elapsedRealtime());
        p.edit()
                .putLong("lease_sync_elapsed", 0L)
                .remove("admin_unlock_until")
                .putLong("admin_locked_until", nextLockout)
                .apply();
    }

    public static void recordAdminVerifier(Context context, String salt, String hash, int rounds) {
        String safeSalt = safe(salt);
        String safeHash = safe(hash);
        if (safeSalt.length() == 0 || safeHash.length() == 0) return;
        prefs(context).edit()
                .putString("admin_salt", safeSalt)
                .putString("admin_hash", safeHash)
                .putInt("admin_rounds", Math.max(1, rounds))
                .apply();
    }

    public static boolean setLocalAdminPassword(Context context, String password) {
        if (password == null || password.length() < 8) return false;
        try {
            String salt = Hmac.nonce();
            int rounds = 4096;
            String hash = Hmac.sha256Iter(password, salt, rounds);
            recordAdminVerifier(context, salt, hash, rounds);
            return true;
        } catch (Exception ignored) {
            return false;
        }
    }

    public static boolean hasAdminVerifier(Context context) {
        SharedPreferences p = prefs(context);
        return p.getString("admin_salt", "").length() > 0
                && p.getString("admin_hash", "").length() > 0;
    }

    public static boolean hasEnrollmentConfig(Context context) {
        return server(context).length() > 0
                && (enrollment(context).length() > 0 || isEnrolled(context));
    }

    public static boolean isInitialSetupComplete(Context context) {
        return prefs(context).getBoolean("setup_complete", false);
    }

    public static void markInitialSetupComplete(Context context, boolean complete) {
        SharedPreferences.Editor edit = prefs(context).edit().putBoolean("setup_complete", complete);
        if (complete) edit.remove("admin_unlock_until");
        edit.apply();
    }

    public static void beginInitialSetupWindow(Context context) {
        if (isInitialSetupComplete(context)) return;
        prefs(context).edit()
                .putLong("admin_unlock_until", SystemClock.elapsedRealtime() + 600000L)
                .apply();
    }

    public static void endAdminWindow(Context context) {
        prefs(context).edit().remove("admin_unlock_until").apply();
    }

    public static void prepareTransfer(Context context) {
        prefs(context).edit()
                .putBoolean("setup_complete", false)
                .remove("server")
                .remove("enrollment")
                .remove("device_id")
                .remove("device_secret")
                .remove("lease_duration_ms")
                .remove("lease_sync_elapsed")
                .remove("server_time_ms")
                .remove("lease_until_ms")
                .remove("admin_unlock_until")
                .apply();
        AndroidRentalPolicyRepository.clear(context);
    }

    public static boolean verifyAdminPassword(Context context, String password) {
        SharedPreferences p = prefs(context);
        long now = SystemClock.elapsedRealtime();
        if (now < p.getLong("admin_locked_until", 0L)) return false;
        String salt = p.getString("admin_salt", "");
        String expected = p.getString("admin_hash", "");
        if (salt.length() == 0 || expected.length() == 0) return false;
        boolean ok = false;
        try {
            ok = expected.equals(Hmac.sha256Iter(password, salt, p.getInt("admin_rounds", 4096)));
        } catch (Exception ignored) {}
        SharedPreferences.Editor edit = p.edit();
        if (ok) {
            edit.putInt("admin_failures", 0)
                    .putLong("admin_locked_until", 0L)
                    .putLong("admin_unlock_until", now + 300000L).apply();
            return true;
        }
        int failures = p.getInt("admin_failures", 0) + 1;
        if (failures >= 5) {
            edit.putInt("admin_failures", 0)
                    .putLong("admin_locked_until", now + AdminBootPolicy.LOCKOUT_MS).apply();
        } else {
            edit.putInt("admin_failures", failures).apply();
        }
        return false;
    }

    public static boolean isAdminWindowActive(Context context) {
        return prefs(context).getLong("admin_unlock_until", 0L) > SystemClock.elapsedRealtime();
    }

    public static String server(Context c) { return prefs(c).getString("server", ""); }
    public static String enrollment(Context c) { return prefs(c).getString("enrollment", ""); }
    public static String deviceId(Context c) { return prefs(c).getString("device_id", ""); }
    public static String deviceSecret(Context c) { return prefs(c).getString("device_secret", ""); }
    public static String deviceName(Context c) { return prefs(c).getString("device_name", "Rental phone"); }
    public static boolean isEnrolled(Context c) { return deviceSecret(c).length() > 0; }

    private static String safe(String value) { return value == null ? "" : value.trim(); }
}
