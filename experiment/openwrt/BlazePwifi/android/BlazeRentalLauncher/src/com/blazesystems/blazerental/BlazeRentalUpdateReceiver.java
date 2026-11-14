package com.blazesystems.blazerental;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageInstaller;

public class BlazeRentalUpdateReceiver extends BroadcastReceiver {
    @Override public void onReceive(Context context, Intent intent) {
        if (intent == null) return;
        String token = intent.getStringExtra(BlazeRentalPackageUpdater.EXTRA_INSTALL_TOKEN);
        // Old or unbound results must never mutate a newer installation.
        if (!BlazeRentalUpdateManager.isPendingInstallToken(context, token)) return;
        int status = intent.getIntExtra(PackageInstaller.EXTRA_STATUS,
                PackageInstaller.STATUS_FAILURE);
        if (status == PackageInstaller.STATUS_SUCCESS) {
            ManagedPolicyController.apply(context);
            ManagedPolicyController.openHome(context);
            return;
        }
        if (status == PackageInstaller.STATUS_PENDING_USER_ACTION) {
            Intent confirm = (Intent) intent.getParcelableExtra(Intent.EXTRA_INTENT);
            if (confirm != null) {
                confirm.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                context.startActivity(confirm);
                return;
            }
        }
        String msg = intent.getStringExtra(PackageInstaller.EXTRA_STATUS_MESSAGE);
        // A terminal failure cannot leave an update that never installed
        // marked as still awaiting its boot-time health check.
        BlazeRentalUpdateManager.recordTerminalInstallFailure(context, token,
                msg == null ? "PackageInstaller status " + status : msg);
    }
}
