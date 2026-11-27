package com.blazesystems.blazerental;

import android.content.Context;
import android.content.SharedPreferences;
import java.util.Collections;
import java.util.HashSet;
import java.util.Set;

public final class AndroidRentalPolicyRepository {
    private static final String PREFS = "blaze_rental_policy_v04";
    private AndroidRentalPolicyRepository() {}

    public static long revision(Context context) {
        return prefs(context).getLong("revision", -1L);
    }

    public static RentalPolicy load(Context context) {
        SharedPreferences p = prefs(context);
        long revision = Math.max(0L, p.getLong("revision", 0L));
        String mode = p.getString("launcher_mode", RentalPolicy.MODE_RENTAL);
        return new RentalPolicy(revision, mode,
                parseCsv(p.getString("allowed", "")),
                parseCsv(p.getString("hidden", "")),
                parseCsv(p.getString("sensitive", "")));
    }

    public static boolean applyVerified(Context context, long revision, String mode,
                                        String allowedCsv, String hiddenCsv, String sensitiveCsv,
                                        String signedPayload, String signature) {
        if (signedPayload == null || signedPayload.length() == 0
                || signature == null || signature.length() == 0) return false;
        long current = prefs(context).getLong("revision", -1L);
        if (revision <= current) return false;
        RentalPolicy validated = new RentalPolicy(revision, mode,
                parseCsv(allowedCsv), parseCsv(hiddenCsv), parseCsv(sensitiveCsv));
        prefs(context).edit()
                .putLong("revision", validated.getRevision())
                .putString("launcher_mode", validated.getLauncherMode())
                .putString("allowed", join(validated.getAllowedPackages()))
                .putString("hidden", join(validated.getHiddenPackages()))
                .putString("sensitive", join(validated.getSensitivePackages()))
                .putString("signed_payload", signedPayload)
                .putString("signature", signature)
                .apply();
        return true;
    }

    public static void setLocalLauncherMode(Context context, String mode) {
        String normalized = RentalPolicy.MODE_UNRESTRICTED.equals(mode)
                ? RentalPolicy.MODE_UNRESTRICTED : RentalPolicy.MODE_RENTAL;
        SharedPreferences p = prefs(context);
        p.edit()
                .putLong("revision", Math.max(0L, p.getLong("revision", 0L)))
                .putString("launcher_mode", normalized)
                .apply();
    }

    public static void clear(Context context) {
        prefs(context).edit().clear().apply();
    }

    private static SharedPreferences prefs(Context context) {
        return context.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
    }

    public static Set<String> parseCsv(String csv) {
        if (csv == null || csv.trim().length() == 0 || "*".equals(csv.trim())) {
            return Collections.emptySet();
        }
        Set<String> out = new HashSet<String>();
        String[] parts = csv.split(",");
        for (String part : parts) {
            String value = part.trim();
            if (value.length() > 0) out.add(value);
        }
        return out;
    }

    private static String join(Set<String> values) {
        StringBuilder out = new StringBuilder();
        for (String value : values) {
            if (out.length() > 0) out.append(',');
            out.append(value);
        }
        return out.toString();
    }
}
