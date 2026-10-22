package com.blazesystems.blazerental;

import android.app.admin.DeviceAdminReceiver;
import android.content.Context;
import android.content.Intent;
import android.os.Build;

public class BlazeDeviceAdminReceiver extends DeviceAdminReceiver {
    @Override
    public void onProfileProvisioningComplete(Context context, Intent intent) {
        boolean callbackHasExtras = intent != null
                && intent.hasExtra(BlazeProvisioningContract.EXTRA_ADMIN_EXTRAS);
        boolean captured = BlazeProvisioningContract.capture(context, intent);
        ManagedPolicyController.apply(context);
        // Android 8+ has a dedicated provisioning-success/compliance activity.
        // Do not race it from DeviceAdminReceiver for the same one-time token.
        if (Build.VERSION.SDK_INT >= 26) return;
        final Context app = context.getApplicationContext();
        final boolean accepted = (!callbackHasExtras || captured)
                && ProvisioningStateGuard.isProvisioningSource(
                        RentalLeaseStore.enrollmentSource(app));
        new Thread(new Runnable() {
            @Override public void run() {
                boolean ok = false;
                if (accepted && (RentalLeaseStore.hasEnrollmentConfig(app)
                        || RentalLeaseStore.isEnrolled(app))) {
                    boolean enrolled = LeaseClient.sync(app)
                            && RentalLeaseStore.isEnrolled(app);
                    if (enrolled) {
                        ok = LeaseClient.sync(app)
                                && AndroidRentalPolicyRepository.revision(app) >= 0L;
                    }
                }
                ManagedPolicyController.apply(app);
                // Android 8+ invokes ACTION_PROVISIONING_SUCCESSFUL and modern
                // Android invokes ADMIN_POLICY_COMPLIANCE. Older devices do not,
                // so only they need the receiver to launch home after verified bind.
                if (ok && Build.VERSION.SDK_INT < 26) {
                    ManagedPolicyController.openHome(app);
                }
            }
        }).start();
    }

    @Override
    public void onEnabled(Context context, Intent intent) {
        ManagedPolicyController.apply(context);
    }
}
