package com.blazesystems.blazerental;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;

/**
 * Network response boundaries for the authenticated Rental Server protocol.
 * This intentionally has no Android dependencies so its limits can be tested
 * using an ordinary Java/JUnit runner.
 */
final class RentalHttpResponseGuard {
    static final int MAX_BODY_BYTES = 256 * 1024;

    private RentalHttpResponseGuard() {}

    static boolean isRedirect(int code) {
        return code >= 300 && code < 400;
    }

    static String readLimited(InputStream input) throws IOException {
        if (input == null) throw new IOException("Missing Rental Server response");
        try {
            ByteArrayOutputStream output = new ByteArrayOutputStream();
            byte[] buffer = new byte[4096];
            int total = 0;
            int count;
            while ((count = input.read(buffer)) != -1) {
                if (count <= 0) continue;
                if (count > MAX_BODY_BYTES - total) {
                    throw new IOException("Rental Server response exceeds maximum JSON size");
                }
                output.write(buffer, 0, count);
                total += count;
            }
            return output.toString("UTF-8");
        } finally {
            input.close();
        }
    }
}
