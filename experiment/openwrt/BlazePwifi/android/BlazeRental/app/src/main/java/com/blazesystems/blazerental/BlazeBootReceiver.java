package com.blazesystems.blazerental;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

public class BlazeBootReceiver extends BroadcastReceiver {
    @Override public void onReceive(Context context, Intent intent) {
        Policy.applyManagedPolicy(context);
        LeaseStore.invalidateCachedLeaseAfterBoot(context);
        Policy.openHome(context);
    }
}
