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
        saveEnrollment(context,
                extras.getString("server_url"),
                extras.getString("enrollment_token"),
                extras.getString("device_name"),
                extras.getString("server_cert_sha256"));
    }

    public static void saveManualEnrollment(Context context, String server, String token, String name) {
        saveManualEnrollment(context, server, token, name, "");
    }

    public static void saveManualEnrollment(Context context, String server, String token,
                                            String name, String certPin) {
        saveEnrollment(context, server, token, name, certPin);
    }

    private static void saveEnrollment(Context context, String server, String token,
                                       String name, String certPin) {
        prefs(context).edit()
                .putString("server", safe(server))
                .putString("enrollment", safe(token))
                .putString("device_name", safe(name))
                .putString("server_cert_sha256", normalizePin(certPin))
                .putBoolean("setup_complete", false)
                .remove("enrollment_request_nonce")
                .remove("device_id")
                .remove("device_secret")
                .remove("lease_duration_ms")
                .remove("lease_sync_elapsed")
                .remove("server_time_ms")
                .remove("lease_until_ms")
                .commit();
        AndroidRentalPolicyRepository.clear(context);
    }

    public static boolean setDeviceIdentity(Context context, String id, String secret) {
        return prefs(context).edit()
                .putString("device_id", safe(id))
                .putString("device_secret", safe(secret))
                .remove("enrollment")
                .remove("enrollment_request_nonce")
                .commit();
    }

    public static synchronized String enrollmentRequestNonce(Context context) {
        SharedPreferences p = prefs(context);
        String nonce = p.getString("enrollment_request_nonce", "");
        if (nonce.length() > 0) return nonce;
        nonce = Hmac.nonce();
        if (!p.edit().putString("enrollment_request_nonce", nonce).commit()) return "";
        return nonce;
    }

    public static void recordLease(Context context, long serverNowMs, long leaseUntilMs) {
        long previousLeaseUntil = prefs(context).getLong("lease_until_ms", 0L);
        long duration = Math.max(0L, leaseUntilMs - serverNowMs);
        if (duration <= 0L || (previousLeaseUntil > 0L
                && leaseUntilMs > previousLeaseUntil + 1000L)) {
            BlazeAlarmPlayer.stop(context);
        }
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

    public static long leaseUntilMs(Context context) {
        return prefs(context).getLong("lease_until_ms", 0L);
    }

    public static void invalidateLeaseAfterBoot(Context context) {
        prefs(context).edit().putLong("lease_sync_elapsed", 0L).apply();
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
        BlazeAlarmPlayer.stop(context);
        prefs(context).edit()
                .putBoolean("setup_complete", false)
                .remove("server")
                .remove("enrollment")
                .remove("enrollment_request_nonce")
                .remove("server_cert_sha256")
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

    private static long adminLockDurationMs(int level) {
        switch (Math.max(1, level)) {
            case 1: return 60000L;
            case 2: return 300000L;
            case 3: return 1800000L;
            case 4: return 21600000L;
            default: return 86400000L;
        }
    }

    public static boolean verifyAdminPassword(Context context, String password) {
        SharedPreferences p = prefs(context);
        long now = SystemClock.elapsedRealtime();
        int lockLevel = p.getInt("admin_lock_level", 0);
        long previousElapsed = p.getLong("admin_last_elapsed", 0L);
        long lockedUntil = p.getLong("admin_locked_until", 0L);

        // elapsedRealtime resets at boot. Rebuild an active penalty after a
        // reboot instead of letting repeated reboots clear brute-force delay.
        if (lockLevel > 0 && previousElapsed > 0L && now < previousElapsed) {
            lockedUntil = now + adminLockDurationMs(lockLevel);
            p.edit().putLong("admin_locked_until", lockedUntil).apply();
        }
        p.edit().putLong("admin_last_elapsed", now).apply();
        if (now < lockedUntil) return false;

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
                    .putInt("admin_lock_level", 0)
                    .putLong("admin_locked_until", 0L)
                    .putLong("admin_last_elapsed", now)
                    .putLong("admin_unlock_until", now + 300000L).apply();
            return true;
        }

        int failures = p.getInt("admin_failures", 0) + 1;
        if (failures >= 5) {
            lockLevel = Math.min(5, lockLevel + 1);
            edit.putInt("admin_failures", 0)
                    .putInt("admin_lock_level", lockLevel)
                    .putLong("admin_locked_until", now + adminLockDurationMs(lockLevel))
                    .putLong("admin_last_elapsed", now)
                    .apply();
        } else {
            edit.putInt("admin_failures", failures)
                    .putLong("admin_last_elapsed", now)
                    .apply();
        }
        return false;
    }

    public static boolean isAdminWindowActive(Context context) {
        return prefs(context).getLong("admin_unlock_until", 0L) > SystemClock.elapsedRealtime();
    }

    public static String server(Context c) { return prefs(c).getString("server", ""); }
    public static String serverCertSha256(Context c) {
        return normalizePin(prefs(c).getString("server_cert_sha256", ""));
    }
    public static String enrollment(Context c) { return prefs(c).getString("enrollment", ""); }
    public static String deviceId(Context c) { return prefs(c).getString("device_id", ""); }
    public static String deviceSecret(Context c) { return prefs(c).getString("device_secret", ""); }
    public static String deviceName(Context c) { return prefs(c).getString("device_name", "Rental phone"); }
    public static boolean isEnrolled(Context c) { return deviceSecret(c).length() > 0; }

    private static String safe(String value) { return value == null ? "" : value.trim(); }

    private static String normalizePin(String value) {
        String pin = safe(value).replace(":", "").toLowerCase();
        if (pin.length() != 64) return "";
        for (int i = 0; i < pin.length(); i++) {
            char ch = pin.charAt(i);
            if (!((ch >= '0' && ch <= '9') || (ch >= 'a' && ch <= 'f'))) return "";
        }
        return pin;
    }
}
