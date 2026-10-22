package com.blazesystems.blazerental;

import android.app.Activity;
import android.graphics.Color;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.Gravity;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;

public class BlazeProvisioningComplianceActivity extends Activity {
    private TextView status;
    private Button retry;
    private volatile boolean running;

    @Override protected void onCreate(Bundle state) {
        super.onCreate(state);
        buildUi();
        boolean callbackHasExtras = getIntent() != null
                && getIntent().hasExtra(BlazeProvisioningContract.EXTRA_ADMIN_EXTRAS);
        boolean captured = BlazeProvisioningContract.capture(this, getIntent());
        if ((callbackHasExtras && !captured)
                || !ProvisioningStateGuard.isProvisioningSource(
                        RentalLeaseStore.enrollmentSource(this))) {
            showFailure("Device Provisioning identity is invalid, changed, or missing. "
                    + "Do not complete Android setup with a Standard Enrollment identity.");
            return;
        }
        attempt();
    }

    private void buildUi() {
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setGravity(Gravity.CENTER);
        root.setPadding(40, 60, 40, 60);
        root.setBackgroundColor(Color.rgb(7, 17, 31));

        TextView title = new TextView(this);
        title.setText("BlazeRental Device Provisioning");
        title.setTextColor(Color.rgb(82, 228, 255));
        title.setTextSize(24f);
        title.setGravity(Gravity.CENTER);
        root.addView(title, new LinearLayout.LayoutParams(-1, -2));

        status = new TextView(this);
        status.setText("Verifying Device Owner and binding this phone to the Rental Server...");
        status.setTextColor(Color.WHITE);
        status.setTextSize(16f);
        status.setGravity(Gravity.CENTER);
        status.setPadding(0, 30, 0, 30);
        root.addView(status, new LinearLayout.LayoutParams(-1, -2));

        retry = new Button(this);
        retry.setText("Retry secure enrollment");
        retry.setVisibility(View.GONE);
        retry.setOnClickListener(new View.OnClickListener() {
            @Override public void onClick(View view) { attempt(); }
        });
        root.addView(retry, new LinearLayout.LayoutParams(-1, -2));
        setContentView(root);
    }

    private synchronized void attempt() {
        if (running) return;
        running = true;
        retry.setVisibility(View.GONE);
        status.setText("Verifying Device Owner and binding this phone to the Rental Server...");
        final Activity self = this;
        new Thread(new Runnable() {
            @Override public void run() {
                boolean success = false;
                String reason = "Unable to bind to the Rental Server.";
                for (int attempt = 1; attempt <= 8 && !success; attempt++) {
                    if (!ProvisioningStateGuard.isProvisioningSource(
                            RentalLeaseStore.enrollmentSource(self))) {
                        reason = "Device Owner provisioning identity was not accepted.";
                        break;
                    } else if (!ManagedPolicyController.isDeviceOwner(self)) {
                        reason = "Android has not granted Device Owner yet.";
                    } else if (!RentalLeaseStore.hasEnrollmentConfig(self)
                            && !RentalLeaseStore.isEnrolled(self)) {
                        // ACTION_PROVISIONING_SUCCESSFUL can arrive before the
                        // provisioning-complete receiver on older Android. Wait
                        // briefly for the receiver to persist admin extras.
                        reason = "Waiting for Android provisioning data.";
                    } else {
                        ManagedPolicyController.apply(self);
                        boolean synced = LeaseClient.sync(self);
                        if (synced && RentalLeaseStore.isEnrolled(self)) {
                            // Server enrollment alone is insufficient. Require a
                            // second authenticated status sync and a persisted
                            // verified policy before completing Setup Wizard.
                            boolean policySynced = LeaseClient.sync(self);
                            boolean policyStored =
                                    AndroidRentalPolicyRepository.revision(self) >= 0L;
                            if (policySynced && policyStored) {
                                ManagedPolicyController.apply(self);
                                success = true;
                                break;
                            }
                            reason = "Enrollment succeeded, but verified policy synchronization failed.";
                        }
                        reason = "The Rental Server rejected enrollment or is unreachable.";
                    }
                    try { Thread.sleep(Math.min(5000L, 750L * attempt)); }
                    catch (InterruptedException ignored) {}
                }
                final boolean ok = success;
                final String error = reason;
                new Handler(Looper.getMainLooper()).post(new Runnable() {
                    @Override public void run() {
                        running = false;
                        if (ok) {
                            status.setText("Device Owner provisioning and Rental Server enrollment completed.");
                            setResult(RESULT_OK);
                            finish();
                        } else {
                            showFailure(error + " Check Wi-Fi/server reachability, then retry. Do not continue using this phone as a managed rental device until enrollment succeeds.");
                        }
                    }
                });
            }
        }).start();
    }

    private void showFailure(String message) {
        running = false;
        status.setText(message);
        retry.setVisibility(View.VISIBLE);
        setResult(RESULT_CANCELED);
    }
}
