package com.blazesystems.blazerental;

import android.content.Context;
import android.content.SharedPreferences;
import android.content.pm.PackageInfo;
import android.content.pm.PackageManager;
import android.os.Build;

public final class BlazeRentalUpdateManager {
    private static final String PREFS = "blaze_rental_update_v051";
    private BlazeRentalUpdateManager() {}

    private static Context storage(Context c) {
        return Build.VERSION.SDK_INT >= 24 ? c.createDeviceProtectedStorageContext() : c;
    }

    private static SharedPreferences prefs(Context c) {
        return storage(c).getSharedPreferences(PREFS, Context.MODE_PRIVATE);
    }

    public static int currentCode(Context c) {
        try { return c.getPackageManager().getPackageInfo(c.getPackageName(), 0).versionCode; }
        catch (Exception ignored) { return 0; }
    }

    public static String currentVersion(Context c) {
        try {
            PackageInfo p = c.getPackageManager().getPackageInfo(c.getPackageName(), 0);
            return p.versionName == null ? "" : p.versionName;
        } catch (Exception ignored) { return ""; }
    }

    public static void recordAvailable(Context c, String version, int code, String url, String sha,
                                       String rollbackVersion, int rollbackCode,
                                       String rollbackUrl, String rollbackSha) {
        SharedPreferences.Editor e = prefs(c).edit();
        if (code <= 0 || url == null || url.length() == 0) {
            e.remove("available_version").remove("available_code").remove("available_url")
                    .remove("available_sha").apply();
            return;
        }
        e.putString("available_version", safe(version))
                .putInt("available_code", code)
                .putString("available_url", safe(url))
                .putString("available_sha", safe(sha).toLowerCase())
                .putString("rollback_version", safe(rollbackVersion))
                .putInt("rollback_code", Math.max(0, rollbackCode))
                .putString("rollback_url", safe(rollbackUrl))
                .putString("rollback_sha", safe(rollbackSha).toLowerCase())
                .apply();
    }

    public static boolean hasAvailableUpdate(Context c) {
        return availableCode(c) > currentCode(c) && availableUrl(c).length() > 0;
    }

    public static int availableCode(Context c) { return prefs(c).getInt("available_code", 0); }
    public static String availableVersion(Context c) { return prefs(c).getString("available_version", ""); }
    public static String availableUrl(Context c) { return prefs(c).getString("available_url", ""); }
    public static String availableSha(Context c) { return prefs(c).getString("available_sha", ""); }
    public static int rollbackCode(Context c) { return prefs(c).getInt("rollback_code", 0); }
    public static String rollbackVersion(Context c) { return prefs(c).getString("rollback_version", ""); }
    public static String rollbackUrl(Context c) { return prefs(c).getString("rollback_url", ""); }
    public static String rollbackSha(Context c) { return prefs(c).getString("rollback_sha", ""); }

    public static boolean hasRollbackRescue(Context c) {
        return rollbackCode(c) > currentCode(c)
                && rollbackUrl(c).length() > 0 && rollbackSha(c).length() == 64;
    }

    public static void markInstallPending(Context c, String targetVersion, int targetCode,
                                          String backupPath, boolean rescue) {
        prefs(c).edit()
                .putString("previous_version", currentVersion(c))
                .putInt("previous_code", currentCode(c))
                .putString("previous_apk", safe(backupPath))
                .putString("pending_version", safe(targetVersion))
                .putInt("pending_code", targetCode)
                .putBoolean("pending_rescue", rescue)
                .putInt("pending_boots", 0)
                .putLong("pending_started_wall", System.currentTimeMillis())
                .remove("last_error")
                .apply();
    }

    public static boolean isPending(Context c) {
        return prefs(c).getInt("pending_code", 0) > 0;
    }

    public static void markLaunchHealthy(Context c) {
        SharedPreferences p = prefs(c);
        int pending = p.getInt("pending_code", 0);
        if (pending <= 0 || currentCode(c) != pending) return;
        p.edit()
                .putString("stable_version", currentVersion(c))
                .putInt("stable_code", currentCode(c))
                .putLong("stable_since_wall", System.currentTimeMillis())
                .remove("pending_version").remove("pending_code").remove("pending_rescue")
                .remove("pending_boots").remove("pending_started_wall").remove("last_error")
                .apply();
    }

    public static boolean noteBootAndShouldAutoRollback(Context c) {
        SharedPreferences p = prefs(c);
        int pending = p.getInt("pending_code", 0);
        if (pending <= 0 || currentCode(c) != pending) return false;
        int boots = p.getInt("pending_boots", 0) + 1;
        p.edit().putInt("pending_boots", boots).apply();
        return boots >= 2 && hasRollbackRescue(c);
    }

    public static void recordInstallFailure(Context c, String message) {
        prefs(c).edit().putString("last_error", safe(message)).apply();
    }

    public static String lastError(Context c) { return prefs(c).getString("last_error", ""); }
    public static String previousVersion(Context c) { return prefs(c).getString("previous_version", ""); }
    public static int previousCode(Context c) { return prefs(c).getInt("previous_code", 0); }
    public static String previousApk(Context c) { return prefs(c).getString("previous_apk", ""); }

    public static String statusLine(Context c) {
        StringBuilder s = new StringBuilder();
        s.append("Current ").append(currentVersion(c)).append(" (").append(currentCode(c)).append(")");
        if (hasAvailableUpdate(c)) s.append(" • available ").append(availableVersion(c))
                .append(" (").append(availableCode(c)).append(")");
        if (isPending(c)) s.append(" • health check pending");
        if (hasRollbackRescue(c)) s.append(" • rescue ").append(rollbackVersion(c))
                .append(" (").append(rollbackCode(c)).append(")");
        return s.toString();
    }

    private static String safe(String v) { return v == null ? "" : v.trim(); }
}
