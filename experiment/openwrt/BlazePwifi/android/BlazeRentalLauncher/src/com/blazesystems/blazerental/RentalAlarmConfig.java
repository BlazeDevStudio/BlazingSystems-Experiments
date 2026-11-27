package com.blazesystems.blazerental;

import android.content.Context;
import android.content.SharedPreferences;
import android.os.Build;

public final class RentalAlarmConfig {
    public static final int KIND_NEAR_END = 1;
    public static final int KIND_URGENT = 2;
    public static final int KIND_TIME_UP = 3;

    public static final String MODE_BUILTIN = "builtin";
    public static final String MODE_DEVICE = "device";
    public static final String MODE_CUSTOM = "custom";

    private static final String PREFS = "blaze_rental_alarm_v052";

    private RentalAlarmConfig() {}

    private static Context storage(Context context) {
        return Build.VERSION.SDK_INT >= 24
                ? context.createDeviceProtectedStorageContext() : context;
    }

    private static SharedPreferences prefs(Context context) {
        return storage(context).getSharedPreferences(PREFS, Context.MODE_PRIVATE);
    }

    private static String prefix(int kind) {
        switch (kind) {
            case KIND_URGENT: return "urgent";
            case KIND_TIME_UP: return "timeup";
            default: return "near";
        }
    }

    public static String title(int kind) {
        switch (kind) {
            case KIND_URGENT: return "Urgent add-credit alarm";
            case KIND_TIME_UP: return "Time's Up alarm";
            default: return "Near End alarm";
        }
    }

    public static boolean enabled(Context c, int kind) {
        return prefs(c).getBoolean(prefix(kind) + "_enabled", true);
    }

    public static void setEnabled(Context c, int kind, boolean enabled) {
        prefs(c).edit().putBoolean(prefix(kind) + "_enabled", enabled).apply();
    }

    public static long thresholdMs(Context c, int kind) {
        if (kind == KIND_TIME_UP) return 0L;
        long def = kind == KIND_URGENT ? 180L : 600L;
        long sec = prefs(c).getLong(prefix(kind) + "_threshold_sec", def);
        long min = kind == KIND_URGENT ? 30L : 60L;
        long max = kind == KIND_URGENT ? 3600L : 86400L;
        sec = Math.max(min, Math.min(max, sec));
        return sec * 1000L;
    }

    public static long thresholdSeconds(Context c, int kind) {
        return thresholdMs(c, kind) / 1000L;
    }

    public static void setThresholdSeconds(Context c, int kind, long seconds) {
        if (kind == KIND_TIME_UP) return;
        long min = kind == KIND_URGENT ? 30L : 60L;
        long max = kind == KIND_URGENT ? 3600L : 86400L;
        prefs(c).edit().putLong(prefix(kind) + "_threshold_sec",
                Math.max(min, Math.min(max, seconds))).apply();
    }

    public static long durationMs(Context c, int kind) {
        long def = kind == KIND_URGENT ? 10L : kind == KIND_TIME_UP ? 15L : 5L;
        long sec = prefs(c).getLong(prefix(kind) + "_duration_sec", def);
        return Math.max(1L, Math.min(60L, sec)) * 1000L;
    }

    public static long durationSeconds(Context c, int kind) {
        return durationMs(c, kind) / 1000L;
    }

    public static void setDurationSeconds(Context c, int kind, long seconds) {
        prefs(c).edit().putLong(prefix(kind) + "_duration_sec",
                Math.max(1L, Math.min(60L, seconds))).apply();
    }

    public static int volumePercent(Context c, int kind) {
        int def = kind == KIND_URGENT ? 85 : kind == KIND_TIME_UP ? 100 : 70;
        int value = prefs(c).getInt(prefix(kind) + "_volume", def);
        return Math.max(25, Math.min(100, value));
    }

    public static void setVolumePercent(Context c, int kind, int percent) {
        prefs(c).edit().putInt(prefix(kind) + "_volume",
                Math.max(25, Math.min(100, percent))).apply();
    }

    public static String soundMode(Context c, int kind) {
        String mode = prefs(c).getString(prefix(kind) + "_sound_mode", MODE_BUILTIN);
        if (!MODE_DEVICE.equals(mode) && !MODE_CUSTOM.equals(mode)) return MODE_BUILTIN;
        return mode;
    }

    public static String soundUri(Context c, int kind) {
        return prefs(c).getString(prefix(kind) + "_sound_uri", "");
    }

    public static void setSound(Context c, int kind, String mode, String uri) {
        if (!MODE_DEVICE.equals(mode) && !MODE_CUSTOM.equals(mode)) {
            mode = MODE_BUILTIN;
            uri = "";
        }
        prefs(c).edit()
                .putString(prefix(kind) + "_sound_mode", mode)
                .putString(prefix(kind) + "_sound_uri", uri == null ? "" : uri)
                .apply();
    }

    public static boolean wasTriggered(Context c, int kind, long leaseId) {
        return leaseId > 0L
                && prefs(c).getLong(prefix(kind) + "_fired_lease", -1L) == leaseId;
    }

    public static void markTriggered(Context c, int kind, long leaseId) {
        if (leaseId <= 0L) return;
        prefs(c).edit().putLong(prefix(kind) + "_fired_lease", leaseId).apply();
    }

    public static String soundDescription(Context c, int kind) {
        String mode = soundMode(c, kind);
        if (MODE_DEVICE.equals(mode)) return "Device alarm tone";
        if (MODE_CUSTOM.equals(mode)) return "Custom audio file";
        switch (kind) {
            case KIND_URGENT: return "Built-in urgent alert";
            case KIND_TIME_UP: return "Built-in loud Time's Up alarm";
            default: return "Built-in near-end alert";
        }
    }

    public static String summary(Context c, int kind) {
        String trigger = kind == KIND_TIME_UP
                ? "at 00:00"
                : (thresholdSeconds(c, kind) >= 60L
                    ? (thresholdSeconds(c, kind) / 60L) + " min remaining"
                    : thresholdSeconds(c, kind) + " sec remaining");
        return (enabled(c, kind) ? "ON" : "OFF") + " · " + trigger
                + " · rings " + durationSeconds(c, kind) + " sec"
                + " · " + volumePercent(c, kind) + "% minimum alarm volume"
                + " · " + soundDescription(c, kind);
    }
}
