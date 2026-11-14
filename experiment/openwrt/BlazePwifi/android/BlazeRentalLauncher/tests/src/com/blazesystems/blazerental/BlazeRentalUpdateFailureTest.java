package com.blazesystems.blazerental;

import android.content.Context;
import android.content.ContextWrapper;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageInstaller;
import android.os.Build;
import android.support.test.InstrumentationRegistry;
import android.support.test.runner.AndroidJUnit4;

import org.junit.After;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;

import static org.junit.Assert.*;
import static org.junit.Assume.assumeTrue;

/**
 * Isolated installer-result regression. No APK is downloaded, installed or
 * signed; no production app preferences or Device Owner controls are touched.
 */
@RunWith(AndroidJUnit4.class)
public final class BlazeRentalUpdateFailureTest {
    private static final String PREFS = "blaze_rental_update_v051";
    private static final String PREFIX = "rental_update_failure_test_";
    private Context isolated;
    private boolean confirmationRequested;

    @Before public void setUp() {
        assumeTrue(Build.VERSION.SDK_INT >= 24);
        confirmationRequested = false;
        isolated = new ContextWrapper(InstrumentationRegistry.getTargetContext()) {
            @Override public Context createDeviceProtectedStorageContext() {
                return this;
            }
            @Override public SharedPreferences getSharedPreferences(String name, int mode) {
                return super.getSharedPreferences(PREFIX + name, mode);
            }
            @Override public void startActivity(Intent intent) {
                confirmationRequested = true; // Do not actually launch UI.
            }
        };
        resetState();
    }

    @After public void tearDown() {
        if (isolated != null) resetState();
    }

    private void resetState() {
        isolated.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
                .edit().clear().commit();
    }

    private void markPending() {
        BlazeRentalUpdateManager.markInstallPending(isolated,
                "test-candidate", 999999, "/isolated/test-previous.apk", false);
        assertTrue(BlazeRentalUpdateManager.isPending(isolated));
    }

    @Test public void failedInstallerClearsPendingButPreservesDiagnosis() {
        markPending();
        Intent failure = new Intent(BlazeRentalPackageUpdater.ACTION_INSTALL_RESULT);
        failure.putExtra(PackageInstaller.EXTRA_STATUS, PackageInstaller.STATUS_FAILURE);
        failure.putExtra(PackageInstaller.EXTRA_STATUS_MESSAGE, "synthetic install failure");
        new BlazeRentalUpdateReceiver().onReceive(isolated, failure);

        assertFalse(BlazeRentalUpdateManager.isPending(isolated));
        assertEquals("synthetic install failure", BlazeRentalUpdateManager.lastError(isolated));
        assertEquals("/isolated/test-previous.apk",
                BlazeRentalUpdateManager.previousApk(isolated));
        assertFalse(confirmationRequested);
        SharedPreferences p = isolated.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        assertFalse(p.contains("pending_started_wall"));
        assertFalse(p.contains("pending_boots"));
        assertFalse(p.contains("pending_rescue"));
    }

    @Test public void validUserConfirmationDoesNotClearPending() {
        markPending();
        Intent waiting = new Intent(BlazeRentalPackageUpdater.ACTION_INSTALL_RESULT);
        waiting.putExtra(PackageInstaller.EXTRA_STATUS,
                PackageInstaller.STATUS_PENDING_USER_ACTION);
        waiting.putExtra(Intent.EXTRA_INTENT, new Intent("isolated.confirm"));
        new BlazeRentalUpdateReceiver().onReceive(isolated, waiting);

        assertTrue(confirmationRequested);
        assertTrue(BlazeRentalUpdateManager.isPending(isolated));
        assertEquals("", BlazeRentalUpdateManager.lastError(isolated));
    }

    @Test public void missingConfirmationIntentTerminatesPending() {
        markPending();
        Intent broken = new Intent(BlazeRentalPackageUpdater.ACTION_INSTALL_RESULT);
        broken.putExtra(PackageInstaller.EXTRA_STATUS,
                PackageInstaller.STATUS_PENDING_USER_ACTION);
        new BlazeRentalUpdateReceiver().onReceive(isolated, broken);

        assertFalse(BlazeRentalUpdateManager.isPending(isolated));
        assertFalse(confirmationRequested);
        assertTrue(BlazeRentalUpdateManager.lastError(isolated).length() > 0);
    }
}
