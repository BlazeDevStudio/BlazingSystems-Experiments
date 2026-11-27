package com.blazesystems.blazerental;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

public class BlazeBootReceiver extends BroadcastReceiver {
    @Override
    public void onReceive(final Context context, Intent intent) {
        RentalLeaseStore.invalidateLeaseAfterBoot(context);
        ManagedPolicyController.apply(context);
        ManagedPolicyController.openHome(context);
        RentalAlarmReceiver.schedule(context, 1000L);

        // Only the fully unlocked BOOT_COMPLETED path attempts network recovery.
        // Two boots while an update remains un-promoted indicates the new build
        // is not reaching its normal health window.
        if (Intent.ACTION_BOOT_COMPLETED.equals(intent.getAction())
                && BlazeRentalUpdateManager.noteBootAndShouldAutoRollback(context)) {
            final PendingResult pending = goAsync();
            new Thread(new Runnable() {
                @Override public void run() {
                    try {
                        String result = BlazeRentalPackageUpdater.installRollbackRescue(context);
                        if (result == null || result.indexOf("staged") < 0) {
                            BlazeRentalUpdateManager.recordInstallFailure(context, result);
                        }
                    } finally {
                        pending.finish();
                    }
                }
            }, "BlazeRental-rescue").start();
        }
    }
}
