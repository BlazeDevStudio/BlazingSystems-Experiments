package com.blazesystems.blazerental;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.SecureRandom;
import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;

public final class Hmac {
    private static final SecureRandom RANDOM = new SecureRandom();
    private Hmac() {}

    public static String sha256Hex(String secret, String message) throws Exception {
        Mac mac = Mac.getInstance("HmacSHA256");
        mac.init(new SecretKeySpec(secret.getBytes(StandardCharsets.UTF_8), "HmacSHA256"));
        return hex(mac.doFinal(message.getBytes(StandardCharsets.UTF_8)));
    }

    public static String digestHex(String message) throws Exception {
        return hex(MessageDigest.getInstance("SHA-256").digest(message.getBytes(StandardCharsets.UTF_8)));
    }

    public static String sha256Iter(String password, String salt, int rounds) throws Exception {
        int count = Math.max(1, rounds);
        String value = digestHex(salt + "|" + password + "|" + salt);
        for (int i = 1; i < count; i++) {
            value = digestHex(value + "|" + password + "|" + salt);
        }
        return value;
    }

    public static String nonce() {
        byte[] bytes = new byte[16];
        RANDOM.nextBytes(bytes);
        return hex(bytes);
    }

    private static String hex(byte[] bytes) {
        StringBuilder out = new StringBuilder(bytes.length * 2);
        for (byte value : bytes) {
            out.append(String.format("%02x", value & 0xff));
        }
        return out.toString();
    }
}
