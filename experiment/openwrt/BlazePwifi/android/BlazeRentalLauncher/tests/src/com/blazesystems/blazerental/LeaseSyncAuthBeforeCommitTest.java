package com.blazesystems.blazerental;

import android.app.AlarmManager;
import android.app.PendingIntent;
import android.content.Context;
import android.content.ContextWrapper;
import android.content.SharedPreferences;
import android.os.Build;
import android.os.SystemClock;
import android.support.test.InstrumentationRegistry;
import android.support.test.runner.AndroidJUnit4;

import org.json.JSONObject;
import org.junit.After;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.InetAddress;
import java.net.ServerSocket;
import java.net.Socket;
import java.net.URLDecoder;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;

import static org.junit.Assert.*;
import static org.junit.Assume.assumeTrue;
import static org.mockito.Matchers.*;
import static org.mockito.Mockito.*;

/**
 * Real LeaseClient.sync + RentalLeaseStore instrumentation; localhost serves
 * nonce-bound test responses. No Device Owner, payments or production endpoint.
 * Requires API >= 23 (exact AlarmManager instrumentation).
 */
@RunWith(AndroidJUnit4.class)
public final class LeaseSyncAuthBeforeCommitTest {
    private static final String ID = "0123456789abcdef01234567";
    private static final String KEY = "local-test-only-device-key";
    private static final String FORGED_KEY = "attacker-controlled-test-key";
    private static final long NOW = 1800000000000L;
    private static final long OLD_UNTIL = NOW + 300000L;
    private static final long NEW_UNTIL = NOW + 900000L;
    private static final String PREFIX = "rental_auth_isolated_";

    private final AlarmManager alarms = mock(AlarmManager.class);
    private Context scoped;

    @Before public void setUp() {
        assumeTrue(Build.VERSION.SDK_INT >= 23);
        scoped = new ContextWrapper(InstrumentationRegistry.getTargetContext()) {
            @Override public Context createDeviceProtectedStorageContext() {
                return this; // Keep the fixture out of real device-protected app prefs.
            }
            @Override public SharedPreferences getSharedPreferences(String name, int mode) {
                return super.getSharedPreferences(PREFIX + name, mode);
            }
            @Override public Object getSystemService(String name) {
                return Context.ALARM_SERVICE.equals(name)
                        ? alarms : super.getSystemService(name);
            }
        };
        clearFixture();
        LeaseClient.clearCoinWindow();
    }

    @After public void tearDown() {
        if (scoped != null) {
            clearFixture();
            LeaseClient.clearCoinWindow();
        }
    }

    private void clearFixture() {
        for (String name : new String[]{
                "blaze_rental_v04", "blaze_rental_policy_v04", "blaze_rental_ui"}) {
            scoped.getSharedPreferences(name, Context.MODE_PRIVATE)
                    .edit().clear().commit();
        }
    }

    @Test public void invalidCoinSignatureCannotAlterPaidLease() throws Exception {
        try (ServerSocket server = openServer()) {
            setupPaidLease(server);
            Map<String, ?> before = leasePrefs();
            long remaining = RentalLeaseStore.remainingMs(scoped);
            long start = SystemClock.elapsedRealtime();

            assertFalse(syncWithResponse(server, false, false));
            long elapsed = SystemClock.elapsedRealtime() - start;
            assertEquals(before, leasePrefs());
            assertEquals(OLD_UNTIL, RentalLeaseStore.leaseUntilMs(scoped));
            assertTrue(Math.abs(RentalLeaseStore.remainingMs(scoped)
                    - Math.max(0L, remaining - elapsed)) < 2000L);
            verifyZeroInteractions(alarms);
        }
    }

    @Test public void responseSuppliedSigningKeyCannotAuthorizeStatus() throws Exception {
        try (ServerSocket server = openServer()) {
            setupPaidLease(server);
            Map<String, ?> before = leasePrefs();

            // Both signatures are valid under the ATTACKER'S response-supplied
            // key, but NOT under the installed key.
            assertFalse(syncWithResponse(server, true, true));
            assertEquals(before, leasePrefs());
            verifyZeroInteractions(alarms);
        }
    }

    @Test public void legitimateSignedStatusStillExtendsLease() throws Exception {
        try (ServerSocket server = openServer()) {
            setupPaidLease(server);
            assertTrue(syncWithResponse(server, true, false));
            assertEquals(NEW_UNTIL, RentalLeaseStore.leaseUntilMs(scoped));
            assertTrue(RentalLeaseStore.remainingMs(scoped) > 600000L);
            verify(alarms, atLeastOnce()).setExactAndAllowWhileIdle(
                    eq(AlarmManager.ELAPSED_REALTIME_WAKEUP),
                    anyLong(), any(PendingIntent.class));
        }
    }

    private static ServerSocket openServer() throws Exception {
        ServerSocket server = new ServerSocket(0, 1,
                InetAddress.getByName("127.0.0.1"));
        server.setSoTimeout(6000);
        return server;
    }

    private void setupPaidLease(ServerSocket server) {
        RentalLeaseStore.saveManualEnrollment(scoped,
                "http://127.0.0.1:" + server.getLocalPort(),
                "test-enroll.invalid", "Native test", "");
        assertTrue(RentalLeaseStore.setDeviceIdentity(scoped, ID, KEY));
        RentalLeaseStore.recordLease(scoped, NOW, OLD_UNTIL);
        reset(alarms); // Ignore setup scheduling; observe only status effects.
    }

    private Map<String, ?> leasePrefs() {
        return new HashMap<String, Object>(
                scoped.getSharedPreferences("blaze_rental_v04",
                        Context.MODE_PRIVATE).getAll());
    }

    private boolean syncWithResponse(final ServerSocket server,
                                     final boolean correctCoin,
                                     final boolean substitutedKey) throws Exception {
        ExecutorService executor = Executors.newSingleThreadExecutor();
        try {
            Future<?> served = executor.submit(new Runnable() {
                @Override public void run() {
                    try { serveSignedStatus(server, correctCoin, substitutedKey); }
                    catch (Exception e) { throw new RuntimeException(e); }
                }
            });
            boolean accepted = LeaseClient.sync(scoped);
            // A network failure must never be mistaken for an authentication
            // rejection: the response worker must have completed normally.
            served.get(8L, TimeUnit.SECONDS);
            return accepted;
        } finally {
            executor.shutdownNow();
        }
    }

    private static void serveSignedStatus(ServerSocket server,
                                          boolean correctCoin,
                                          boolean substitutedKey) throws Exception {
        try (Socket peer = server.accept()) {
            peer.setSoTimeout(5000);
            BufferedReader in = new BufferedReader(
                    new InputStreamReader(peer.getInputStream(), "UTF-8"));
            String startLine = in.readLine();
            if (startLine == null || !startLine.startsWith("POST /cgi-bin/rental")) {
                throw new IllegalStateException("Unexpected request");
            }
            int length = -1;
            String header;
            while ((header = in.readLine()) != null && header.length() > 0) {
                if (header.regionMatches(true, 0, "Content-Length:", 0, 15))
                    length = Integer.parseInt(header.substring(15).trim());
            }
            if (length < 0) throw new IllegalStateException("Missing body length");
            char[] request = new char[length];
            int n = 0;
            while (n < length) {
                int got = in.read(request, n, length - n);
                if (got < 0) throw new IllegalStateException("Truncated request");
                n += got;
            }
            String nonce = null;
            for (String field : new String(request).split("&")) {
                String[] pair = field.split("=", 2);
                if (pair.length == 2 && "nonce".equals(pair[0]))
                    nonce = URLDecoder.decode(pair[1], "UTF-8");
            }
            if (nonce == null || nonce.length() == 0)
                throw new IllegalStateException("Missing nonce");

            String signingKey = substitutedKey ? FORGED_KEY : KEY;
            long serverNow = NOW + 1000L;
            String coinCanonical = "coin_window|" + ID + "|" + serverNow
                    + "|0||0|0";
            String v3Canonical = "v3|" + ID + "|" + nonce + "|" + serverNow
                    + "|" + NEW_UNTIL + "|7|rental|*||||4096||600"
                    + "|overlay|1||1|hold|4000|0";

            JSONObject status = new JSONObject()
                    .put("ok", true)
                    .put("device_id", ID)
                    .put("server_time_ms", serverNow)
                    .put("lease_until_ms", NEW_UNTIL)
                    .put("policy_revision", 7)
                    .put("coin_window_sig", correctCoin
                            ? Hmac.sha256Hex(signingKey, coinCanonical)
                            : "deliberately-invalid-signature")
                    .put("policy_sig_v3", Hmac.sha256Hex(signingKey, v3Canonical));
            if (substitutedKey) status.put("device_secret", FORGED_KEY);

            byte[] bytes = status.toString().getBytes("UTF-8");
            OutputStream out = peer.getOutputStream();
            out.write(("HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n"
                    + "Content-Length: " + bytes.length
                    + "\r\nConnection: close\r\n\r\n").getBytes("UTF-8"));
            out.write(bytes);
            out.flush();
        }
    }
}
