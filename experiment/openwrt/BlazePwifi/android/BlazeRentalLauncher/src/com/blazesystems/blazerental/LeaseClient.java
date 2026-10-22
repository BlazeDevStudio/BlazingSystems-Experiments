package com.blazesystems.blazerental;

import android.content.Context;
import org.json.JSONObject;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.cert.Certificate;
import java.security.cert.CertificateException;
import java.security.cert.X509Certificate;
import java.util.List;
import javax.net.ssl.HostnameVerifier;
import javax.net.ssl.HttpsURLConnection;
import javax.net.ssl.SSLContext;
import javax.net.ssl.SSLSession;
import javax.net.ssl.TrustManager;
import javax.net.ssl.X509TrustManager;

public final class LeaseClient {
    private LeaseClient() {}

    public static synchronized boolean sync(Context context) {
        try {
            String base = RentalLeaseStore.server(context);
            if (base.length() == 0) return false;
            String deviceSecret = RentalLeaseStore.deviceSecret(context);
            String enrollment = RentalLeaseStore.enrollment(context);
            boolean enrolling = deviceSecret.length() == 0;
            String nonce = enrolling
                    ? RentalLeaseStore.enrollmentRequestNonce(context) : Hmac.nonce();
            if (nonce.length() == 0) return false;
            String action = enrolling ? "enroll" : "status";
            String authSecret = enrolling ? enrollment : deviceSecret;
            if (authSecret.length() == 0) return false;

            StringBuilder body = new StringBuilder();
            body.append("action=").append(enc(action))
                    .append("&nonce=").append(enc(nonce));

            if (enrolling) {
                int dot = enrollment.indexOf('.');
                if (dot <= 0) return false;
                body.append("&enroll_id=").append(enc(enrollment.substring(0, dot)))
                        .append("&protocol=2");
            } else {
                body.append("&device_id=").append(enc(RentalLeaseStore.deviceId(context)));
                body.append("&inventory=").append(enc(inventoryCsv(context)));
            }

            String canonicalAuth = enrolling
                    ? "enroll_v2|" + nonce + "|" + authSecret
                    : action + "|" + nonce + "|" + authSecret;
            body.append("&sig=").append(enc(Hmac.sha256Hex(authSecret, canonicalAuth)));

            JSONObject response = post(context, base, body.toString());
            if (response == null || !response.optBoolean("ok", false)) return false;

            String deviceId = response.optString("device_id", RentalLeaseStore.deviceId(context));
            long serverNow = response.optLong("server_time_ms", 0L);
            long leaseUntil = response.optLong("lease_until_ms", 0L);
            if (serverNow <= 0L || leaseUntil < serverNow) return false;

            String newSecret = deviceSecret;
            if (enrolling) {
                if (response.optInt("enrollment_protocol", 0) != 2) return false;
                if (deviceId.length() != 24) return false;
                String kdf = response.optString("identity_kdf", "");
                if (!"hmac-sha256-v1".equals(kdf)) return false;
                String responseSig = response.optString("enroll_sig", "");
                String responseCanonical = "enroll-response-v2|" + nonce + "|" + deviceId
                        + "|" + serverNow + "|" + leaseUntil + "|" + kdf;
                if (responseSig.length() == 0
                        || !responseSig.equals(Hmac.sha256Hex(authSecret, responseCanonical))) {
                    return false;
                }
                newSecret = Hmac.sha256Hex(authSecret,
                        "device-secret-v2|" + nonce + "|" + deviceId);
                if (newSecret.length() != 64) return false;
                if (!RentalLeaseStore.setDeviceIdentity(context, deviceId, newSecret)) {
                    return false;
                }
            }
            // Do not mutate lease state before the authenticated status policy
            // is verified. Enrollment itself is authenticated above by the
            // enroll-response-v2 MAC.

            if (!enrolling) {
                if (!deviceId.equals(RentalLeaseStore.deviceId(context))) return false;
                String allowed = response.optString("allowed_packages", "*");
                String hidden = response.optString("hidden_packages", "");
                String mode = response.optString("launcher_mode", RentalPolicy.MODE_RENTAL);
                String salt = response.optString("admin_salt", "");
                String hash = response.optString("admin_hash", "");
                int rounds = response.optInt("admin_rounds", 4096);
                String preferred = response.optString("preferred_vendo", "");
                int secondsPerPulse = response.optInt("rental_seconds_per_pulse", 600);
                String timerMode = response.optString("timer_mode", "overlay");
                boolean timerUserToggle = response.optInt("timer_user_toggle", 1) != 0;
                String quickControls = response.optString("quick_controls", "");
                boolean notificationsEnabled = response.optInt("notifications_enabled", 1) != 0;
                String gestureType = response.optString("admin_gesture_type", "hold");
                long gestureValue = response.optLong("admin_gesture_value", 4000L);
                long offlineGrace = response.optLong("offline_grace", 0L);
                String policySignature = response.optString("policy_sig", "");
                String policySignatureV2 = response.optString("policy_sig_v2", "");
                String policySignatureV3 = response.optString("policy_sig_v3", "");

                String legacyCanonical = deviceId + "|" + nonce + "|" + serverNow + "|"
                        + leaseUntil + "|" + allowed + "|" + salt + "|" + hash + "|"
                        + rounds + "|" + preferred + "|" + secondsPerPulse;
                boolean versioned = response.has("policy_revision");
                long previousRevision = AndroidRentalPolicyRepository.revision(context);
                long revision = versioned
                        ? response.optLong("policy_revision", -1L)
                        : 0L;
                if (!LeaseSyncStateGuard.acceptRevision(versioned, revision,
                        previousRevision)) return false;

                String acceptedCanonical = legacyCanonical;
                String acceptedSignature = policySignature;
                boolean fullPolicyVerified = false;
                if (response.has("policy_revision")) {
                    String v2Canonical = "v2|" + deviceId + "|" + nonce + "|" + serverNow + "|"
                            + leaseUntil + "|" + revision + "|" + mode + "|" + allowed + "|"
                            + hidden + "|" + salt + "|" + hash + "|" + rounds + "|"
                            + preferred + "|" + secondsPerPulse;
                    String v3Canonical = "v3|" + deviceId + "|" + nonce + "|" + serverNow + "|"
                            + leaseUntil + "|" + revision + "|" + mode + "|" + allowed + "|"
                            + hidden + "|" + salt + "|" + hash + "|" + rounds + "|"
                            + preferred + "|" + secondsPerPulse + "|" + timerMode + "|"
                            + (timerUserToggle ? "1" : "0") + "|" + quickControls + "|"
                            + (notificationsEnabled ? "1" : "0") + "|" + gestureType + "|"
                            + gestureValue + "|" + offlineGrace;
                    if (policySignatureV3.length() > 0) {
                        if (!policySignatureV3.equals(Hmac.sha256Hex(newSecret, v3Canonical))) {
                            return false;
                        }
                        acceptedCanonical = v3Canonical;
                        acceptedSignature = policySignatureV3;
                        fullPolicyVerified = true;
                    } else {
                        if (policySignatureV2.length() == 0
                                || !policySignatureV2.equals(Hmac.sha256Hex(newSecret, v2Canonical))) {
                            return false;
                        }
                        acceptedCanonical = v2Canonical;
                        acceptedSignature = policySignatureV2;
                    }
                } else if (policySignature.length() == 0
                        || !policySignature.equals(Hmac.sha256Hex(newSecret, legacyCanonical))) {
                    return false;
                }

                String effectiveAllowed = allowed;
                if ("*".equals(allowed)) effectiveAllowed = inventoryCsv(context);

                boolean applyNewRevision = LeaseSyncStateGuard.shouldApplyRevision(
                        versioned, revision, previousRevision);
                if (applyNewRevision) {
                    if (!AndroidRentalPolicyRepository.applyVerified(context, revision, mode,
                            effectiveAllowed, hidden, "", acceptedCanonical, acceptedSignature)) {
                        return false;
                    }
                    if (fullPolicyVerified) {
                        RentalUiPolicy.applyVerified(context, timerMode, timerUserToggle,
                                quickControls, notificationsEnabled, gestureType,
                                gestureValue, offlineGrace);
                    }
                    if (salt.length() > 0 && hash.length() > 0) {
                        RentalLeaseStore.recordAdminVerifier(context, salt, hash, rounds);
                    }
                }

                JSONObject update = response.optJSONObject("update");
                if (update != null && update.optBoolean("available", false)) {
                    BlazeRentalUpdateManager.recordAvailable(context,
                            update.optString("version", ""),
                            update.optInt("version_code", 0),
                            update.optString("apk_url", ""),
                            update.optString("apk_sha256", ""),
                            update.optString("rollback_version", ""),
                            update.optInt("rollback_version_code", 0),
                            update.optString("rollback_url", ""),
                            update.optString("rollback_sha256", ""));
                }
            }

            // This is the first lease mutation for an authenticated status
            // response: signature + revision gate + durable policy storage
            // must all pass first. A rejected response cannot extend credit.
            RentalLeaseStore.recordLease(context, serverNow, leaseUntil);
            ManagedPolicyController.apply(context);
            return true;
        } catch (Exception ignored) {
            return false;
        }
    }

    public static String coinStart(Context context, String preferredVendo) {
        try {
            String base = RentalLeaseStore.server(context);
            String secret = RentalLeaseStore.deviceSecret(context);
            String deviceId = RentalLeaseStore.deviceId(context);
            if (base.length() == 0 || secret.length() == 0 || deviceId.length() == 0) {
                return "Rental phone is not enrolled.";
            }
            String nonce = Hmac.nonce();
            String body = "action=coin_start&nonce=" + enc(nonce)
                    + "&device_id=" + enc(deviceId)
                    + "&sig=" + enc(Hmac.sha256Hex(secret,
                    "coin_start|" + nonce + "|" + secret));
            if (preferredVendo != null && preferredVendo.trim().length() > 0) {
                body += "&vendo=" + enc(preferredVendo.trim());
            }
            JSONObject response = post(context, base, body);
            if (response == null) return "Server unavailable.";
            if (!response.optBoolean("ok", false)) {
                return response.optString("error", "Unable to start coin slot.");
            }
            return "Insert coin at " + response.optString("vendo", "selected controller") + ".";
        } catch (Exception ignored) {
            return "Unable to start coin slot.";
        }
    }

    static String inventoryCsv(Context context) {
        List<String> packages = ManagedPolicyController.installedLaunchablePackages(context);
        StringBuilder out = new StringBuilder();
        for (String pkg : packages) {
            if (out.length() > 0) out.append(',');
            out.append(pkg);
        }
        return out.toString();
    }

    static JSONObject post(Context context, String base, String body) throws Exception {
        URL url = new URL(base.replaceAll("/+$", "") + "/cgi-bin/rental");
        HttpURLConnection connection = (HttpURLConnection) url.openConnection();
        try {
            // A redirect must never move a signed enrollment/status request to
            // another origin. Redirects are not part of the Rental API protocol.
            connection.setInstanceFollowRedirects(false);
            applyPinnedTls(context, connection);
            connection.setConnectTimeout(3500);
            connection.setReadTimeout(3500);
            connection.setRequestMethod("POST");
            connection.setDoOutput(true);
            connection.setRequestProperty("Content-Type", "application/x-www-form-urlencoded");
            OutputStream output = connection.getOutputStream();
            try {
                output.write(body.getBytes(StandardCharsets.UTF_8));
            } finally {
                output.close();
            }

            int status = connection.getResponseCode();
            if (RentalHttpResponseGuard.isRedirect(status)
                    || connection.getContentLengthLong() > RentalHttpResponseGuard.MAX_BODY_BYTES) {
                return null;
            }
            // Preserve structured 4xx errors for the customer UI, but enforce
            // the same byte limit on both success and error JSON.
            InputStream input = status == HttpURLConnection.HTTP_OK
                    ? connection.getInputStream() : connection.getErrorStream();
            if (input == null) return null;
            return new JSONObject(RentalHttpResponseGuard.readLimited(input));
        } finally {
            connection.disconnect();
        }
    }

    private static void applyPinnedTls(Context context, HttpURLConnection connection)
            throws Exception {
        final String expectedPin = RentalLeaseStore.serverCertSha256(context);
        if (expectedPin.length() == 0) return;
        if (!(connection instanceof HttpsURLConnection)) {
            throw new CertificateException("Pinned BlazePwifi server requires HTTPS");
        }

        final X509TrustManager pinnedTrust = new X509TrustManager() {
            @Override public void checkClientTrusted(X509Certificate[] chain, String authType)
                    throws CertificateException {
                throw new CertificateException("Client certificate trust is not supported");
            }

            @Override public void checkServerTrusted(X509Certificate[] chain, String authType)
                    throws CertificateException {
                if (chain == null || chain.length == 0
                        || !certificateMatches(expectedPin, chain[0])) {
                    throw new CertificateException("BlazePwifi TLS certificate pin mismatch");
                }
            }

            @Override public X509Certificate[] getAcceptedIssuers() {
                return new X509Certificate[0];
            }
        };

        SSLContext tls = SSLContext.getInstance("TLS");
        tls.init(null, new TrustManager[]{pinnedTrust}, null);
        HttpsURLConnection https = (HttpsURLConnection) connection;
        https.setSSLSocketFactory(tls.getSocketFactory());
        https.setHostnameVerifier(new HostnameVerifier() {
            @Override public boolean verify(String hostname, SSLSession session) {
                try {
                    Certificate[] peer = session.getPeerCertificates();
                    return peer != null && peer.length > 0
                            && certificateMatches(expectedPin, peer[0]);
                } catch (Exception ignored) {
                    return false;
                }
            }
        });
    }

    private static boolean certificateMatches(String expectedPin, Certificate certificate) {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] bytes = digest.digest(certificate.getEncoded());
            StringBuilder hex = new StringBuilder(bytes.length * 2);
            for (byte value : bytes) {
                int v = value & 0xff;
                if (v < 16) hex.append('0');
                hex.append(Integer.toHexString(v));
            }
            return expectedPin.equals(hex.toString());
        } catch (Exception ignored) {
            return false;
        }
    }

    static String enc(String value) throws Exception {
        return URLEncoder.encode(value == null ? "" : value, "UTF-8");
    }

}
