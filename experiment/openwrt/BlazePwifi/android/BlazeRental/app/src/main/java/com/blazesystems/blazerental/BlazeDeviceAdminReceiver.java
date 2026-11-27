package com.blazesystems.blazerental;

import android.app.admin.DeviceAdminReceiver;
import android.content.Context;
import android.content.Intent;
import android.os.PersistableBundle;

public class BlazeDeviceAdminReceiver extends DeviceAdminReceiver {
    @Override public void onProfileProvisioningComplete(Context context, Intent intent) {
        PersistableBundle extras = intent.getParcelableExtra(
                android.app.admin.DevicePolicyManager.EXTRA_PROVISIONING_ADMIN_EXTRAS_BUNDLE);
        LeaseStore.acceptProvisioningExtras(context, extras);
        Policy.applyManagedPolicy(context);
        Policy.openHome(context);
    }

    @Override public void onEnabled(Context context, Intent intent) {
        Policy.applyManagedPolicy(context);
    }
}
