package com.blazesystems.blazerental;

import android.content.Context;
import org.json.JSONObject;

public final class RentalPolicyClient {
    private static final String KEEP = "@keep";
    private RentalPolicyClient() {}

    public static boolean sync(Context context) { return LeaseClient.sync(context); }

    public static JSONObject policyPatch(Context context, long expectedRevision, String patchJson) {
        try {
            String base = RentalLeaseStore.server(context);
            String secret = RentalLeaseStore.deviceSecret(context);
            String deviceId = RentalLeaseStore.deviceId(context);
            if (base.length() == 0 || secret.length() == 0 || deviceId.length() == 0) return null;

            JSONObject patch = new JSONObject(patchJson);
            String mode = value(patch, "launcher_mode");
            String allowed = listValue(patch, "allowed_packages");
            String hidden = listValue(patch, "hidden_packages");
            String preferred = value(patch, "preferred_vendo");
            String timer = value(patch, "timer_user_toggle");
            String notifications = value(patch, "notifications_enabled");
            String quick = listValue(patch, "quick_controls");
            String gesture = value(patch, "admin_gesture_value");
            String adminPassword = value(patch, "admin_password");

            String nonce = Hmac.nonce();
            String canonical = "policy_patch|" + nonce + "|" + deviceId + "|"
                    + expectedRevision + "|" + mode + "|" + allowed + "|" + hidden + "|"
                    + preferred + "|" + timer + "|" + notifications + "|" + quick + "|"
                    + gesture + "|" + adminPassword;
            String body = "action=policy_patch&nonce=" + LeaseClient.enc(nonce)
                    + "&device_id=" + LeaseClient.enc(deviceId)
                    + "&expected_revision=" + expectedRevision
                    + "&launcher_mode=" + LeaseClient.enc(mode)
                    + "&allowed_packages=" + LeaseClient.enc(allowed)
                    + "&hidden_packages=" + LeaseClient.enc(hidden)
                    + "&preferred_vendo=" + LeaseClient.enc(preferred)
                    + "&timer_user_toggle=" + LeaseClient.enc(timer)
                    + "&notifications_enabled=" + LeaseClient.enc(notifications)
                    + "&quick_controls=" + LeaseClient.enc(quick)
                    + "&admin_gesture_value=" + LeaseClient.enc(gesture)
                    + "&admin_password=" + LeaseClient.enc(adminPassword)
                    + "&sig=" + LeaseClient.enc(Hmac.sha256Hex(secret, canonical));
            return LeaseClient.post(context, base, body);
        } catch (Exception ignored) {
            return null;
        }
    }

    private static String listValue(JSONObject patch, String key) {
        String out = value(patch, key);
        if (KEEP.equals(out)) return out;
        return out.length() == 0 ? "-" : out;
    }

    private static String value(JSONObject patch, String key) {
        if (!patch.has(key)) return KEEP;
        Object value = patch.opt(key);
        if (value == null || value == JSONObject.NULL) return "";
        return String.valueOf(value);
    }
}
