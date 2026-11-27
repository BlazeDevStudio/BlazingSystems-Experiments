package com.blazesystems.blazerental;

import android.content.Context;
import android.content.SharedPreferences;
import java.util.HashSet;
import java.util.Set;

public final class RentalUiPolicy {
    private static final String PREFS = "blaze_rental_ui";
    private static final String DEFAULT_QUICK =
            "volume_down,volume_up,floating_timer,network_status,battery_status,bluetooth_status,flashlight";

    private RentalUiPolicy() {}

    private static SharedPreferences prefs(Context context) {
        return context.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
    }

    public static void applyVerified(Context context, String timerMode,
                                     boolean timerUserToggleAllowed, String quickControls,
                                     boolean notificationsEnabled, String gestureType,
                                     long gestureValue, long offlineGraceSeconds) {
        String mode = normalizeTimerMode(timerMode);
        long hold = Math.max(1500L, Math.min(15000L, gestureValue > 0L ? gestureValue : 4000L));
        prefs(context).edit()
                .putString("operator_timer_mode", mode)
                .putBoolean("operator_timer_toggle_allowed", timerUserToggleAllowed)
                .putString("operator_quick_controls",
                        quickControls == null ? DEFAULT_QUICK : quickControls.trim())
                .putBoolean("operator_notifications_enabled", notificationsEnabled)
                .putString("admin_gesture_type",
                        gestureType == null || gestureType.length() == 0 ? "hold" : gestureType)
                .putLong("admin_hold_ms", hold)
                .putLong("offline_grace_seconds", Math.max(0L, offlineGraceSeconds))
                .apply();
    }

    public static boolean floatingTimerOperatorAllowed(Context context) {
        return !"off".equals(prefs(context).getString("operator_timer_mode", "overlay"));
    }

    public static boolean floatingTimerForcedOn(Context context) {
        return "always".equals(prefs(context).getString("operator_timer_mode", "overlay"));
    }

    public static boolean floatingTimerUserToggleAllowed(Context context) {
        return floatingTimerOperatorAllowed(context)
                && !floatingTimerForcedOn(context)
                && prefs(context).getBoolean("operator_timer_toggle_allowed", true)
                && quickControlAllowed(context, "floating_timer");
    }

    public static boolean floatingTimerEnabled(Context context) {
        if (!floatingTimerOperatorAllowed(context)) return false;
        if (floatingTimerForcedOn(context)) return true;
        return prefs(context).getBoolean("floating_timer", true);
    }

    public static boolean quickControlAllowed(Context context, String key) {
        String csv = prefs(context).contains("operator_quick_controls")
                ? prefs(context).getString("operator_quick_controls", "")
                : DEFAULT_QUICK;
        Set<String> values = new HashSet<String>();
        for (String part : csv.split(",")) {
            String value = part.trim();
            if (value.length() > 0) values.add(value);
        }
        if ("bluetooth".equals(key)) {
            return values.contains("bluetooth") || values.contains("bluetooth_status")
                    || values.contains("bluetooth_toggle");
        }
        return values.contains(key);
    }

    public static boolean notificationsEnabled(Context context) {
        return prefs(context).getBoolean("operator_notifications_enabled", true);
    }

    public static long adminHoldMs(Context context) {
        long hold = prefs(context).getLong("admin_hold_ms", 4000L);
        return Math.max(1500L, Math.min(15000L, hold));
    }

    private static String normalizeTimerMode(String value) {
        if ("off".equals(value) || "always".equals(value) || "overlay".equals(value)) {
            return value;
        }
        return "overlay";
    }
}
