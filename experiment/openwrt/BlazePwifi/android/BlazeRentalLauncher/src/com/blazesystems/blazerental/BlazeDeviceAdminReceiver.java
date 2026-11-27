package com.blazesystems.blazerental;

import android.app.admin.DeviceAdminReceiver;
import android.app.admin.DevicePolicyManager;
import android.content.Context;
import android.content.Intent;
import android.os.PersistableBundle;

public class BlazeDeviceAdminReceiver extends DeviceAdminReceiver {
    @Override
    public void onProfileProvisioningComplete(Context context, Intent intent) {
        PersistableBundle extras = intent.getParcelableExtra(
                DevicePolicyManager.EXTRA_PROVISIONING_ADMIN_EXTRAS_BUNDLE);
        RentalLeaseStore.acceptProvisioningExtras(context, extras);
        ManagedPolicyController.apply(context);
        final Context app = context.getApplicationContext();
        new Thread(new Runnable() {
            @Override public void run() {
                if (RentalLeaseStore.hasEnrollmentConfig(app)) LeaseClient.sync(app);
            }
        }).start();
        ManagedPolicyController.openHome(context);
    }

    @Override
    public void onEnabled(Context context, Intent intent) {
        ManagedPolicyController.apply(context);
    }
}
