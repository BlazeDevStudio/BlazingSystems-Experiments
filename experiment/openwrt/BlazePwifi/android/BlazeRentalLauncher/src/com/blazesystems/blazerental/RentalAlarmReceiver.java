package com.blazesystems.blazerental;

import android.app.AlarmManager;
import android.app.PendingIntent;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.os.SystemClock;
import android.os.Build;
import android.widget.Toast;

public class RentalAlarmReceiver extends BroadcastReceiver {
    private static final int REQUEST_HEALTH = 9404;
    private static final int REQUEST_NEAR = 9405;
    private static final int REQUEST_URGENT = 9406;
    private static final int REQUEST_TIMEUP = 9407;

    private static final String EXTRA_KIND = "alarm_kind";
    private static final String EXTRA_LEASE_ID = "lease_id";

    public static void schedule(Context context, long remainingMs) {
        AlarmManager manager = (AlarmManager) context.getSystemService(Context.ALARM_SERVICE);
        if (manager == null) return;

        scheduleHealth(context, manager, remainingMs);

        long leaseId = RentalLeaseStore.leaseUntilMs(context);
        if (remainingMs <= 0L || leaseId <= 0L) {
            cancelWarning(context, manager, RentalAlarmConfig.KIND_NEAR_END);
            cancelWarning(context, manager, RentalAlarmConfig.KIND_URGENT);
            cancelWarning(context, manager, RentalAlarmConfig.KIND_TIME_UP);
            return;
        }

        scheduleWarning(context, manager, RentalAlarmConfig.KIND_NEAR_END,
                remainingMs, leaseId);
        scheduleWarning(context, manager, RentalAlarmConfig.KIND_URGENT,
                remainingMs, leaseId);
        scheduleWarning(context, manager, RentalAlarmConfig.KIND_TIME_UP,
                remainingMs, leaseId);
    }

    private static void scheduleHealth(Context context, AlarmManager manager, long remainingMs) {
        long delay = Math.max(1000L,
                Math.min(remainingMs > 0L ? remainingMs : 15000L, 60000L));
        Intent intent = new Intent(context, RentalAlarmReceiver.class);
        intent.putExtra(EXTRA_KIND, 0);
        PendingIntent pending = PendingIntent.getBroadcast(context, REQUEST_HEALTH, intent,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        setExactCompat(manager, SystemClock.elapsedRealtime() + delay, pending);
    }

    private static void scheduleWarning(Context context, AlarmManager manager,
                                        int kind, long remainingMs, long leaseId) {
        if (!RentalAlarmConfig.enabled(context, kind)
                || RentalAlarmConfig.wasTriggered(context, kind, leaseId)) {
            cancelWarning(context, manager, kind);
            return;
        }

        long delay;
        if (kind == RentalAlarmConfig.KIND_TIME_UP) {
            delay = Math.max(1000L, remainingMs);
        } else if (kind == RentalAlarmConfig.KIND_URGENT) {
            long threshold = RentalAlarmConfig.thresholdMs(context, kind);
            delay = remainingMs > threshold ? remainingMs - threshold : 1000L;
        } else {
            long near = RentalAlarmConfig.thresholdMs(context, kind);
            long urgent = RentalAlarmConfig.thresholdMs(
                    context, RentalAlarmConfig.KIND_URGENT);
            if (remainingMs <= urgent) {
                cancelWarning(context, manager, kind);
                return;
            }
            delay = remainingMs > near ? remainingMs - near : 1000L;
        }

        Intent intent = new Intent(context, RentalAlarmReceiver.class);
        intent.putExtra(EXTRA_KIND, kind);
        intent.putExtra(EXTRA_LEASE_ID, leaseId);
        PendingIntent pending = PendingIntent.getBroadcast(context, requestCode(kind), intent,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        setExactCompat(manager,
                SystemClock.elapsedRealtime() + Math.max(1000L, delay), pending);
    }

    private static void setExactCompat(AlarmManager manager, long when,
                                       PendingIntent pending) {
        if (Build.VERSION.SDK_INT >= 23) {
            manager.setExactAndAllowWhileIdle(AlarmManager.ELAPSED_REALTIME_WAKEUP,
                    when, pending);
        } else if (Build.VERSION.SDK_INT >= 19) {
            manager.setExact(AlarmManager.ELAPSED_REALTIME_WAKEUP, when, pending);
        } else {
            manager.set(AlarmManager.ELAPSED_REALTIME_WAKEUP, when, pending);
        }
    }

    private static void cancelWarning(Context context, AlarmManager manager, int kind) {
        Intent intent = new Intent(context, RentalAlarmReceiver.class);
        PendingIntent pending = PendingIntent.getBroadcast(context, requestCode(kind), intent,
                PendingIntent.FLAG_NO_CREATE | PendingIntent.FLAG_IMMUTABLE);
        if (pending != null) {
            manager.cancel(pending);
            pending.cancel();
        }
    }

    private static int requestCode(int kind) {
        switch (kind) {
            case RentalAlarmConfig.KIND_URGENT: return REQUEST_URGENT;
            case RentalAlarmConfig.KIND_TIME_UP: return REQUEST_TIMEUP;
            default: return REQUEST_NEAR;
        }
    }

    @Override
    public void onReceive(final Context context, final Intent intent) {
        final int kind = intent == null ? 0 : intent.getIntExtra(EXTRA_KIND, 0);
        if (kind != 0) {
            handleWarning(context, kind,
                    intent.getLongExtra(EXTRA_LEASE_ID, 0L));
            return;
        }

        final PendingResult pending = goAsync();
        new Thread(new Runnable() {
            @Override public void run() {
                try {
                    if (RentalLeaseStore.hasEnrollmentConfig(context)) LeaseClient.sync(context);
                    ManagedPolicyController.apply(context);
                    if (!RentalLeaseStore.isLeaseValid(context)
                            && !AndroidRentalPolicyRepository.load(context).isUnrestricted()) {
                        ManagedPolicyController.openHome(context);
                    }
                    schedule(context, RentalLeaseStore.remainingMs(context));
                } finally {
                    pending.finish();
                }
            }
        }, "BlazeRental-lease-health").start();
    }

    private static void handleWarning(Context context, int kind, long expectedLeaseId) {
        long currentLeaseId = RentalLeaseStore.leaseUntilMs(context);
        if (expectedLeaseId <= 0L || currentLeaseId != expectedLeaseId
                || RentalAlarmConfig.wasTriggered(context, kind, expectedLeaseId)
                || !RentalAlarmConfig.enabled(context, kind)) {
            return;
        }

        long remaining = RentalLeaseStore.remainingMs(context);
        if (kind == RentalAlarmConfig.KIND_NEAR_END) {
            long near = RentalAlarmConfig.thresholdMs(context, kind);
            long urgent = RentalAlarmConfig.thresholdMs(
                    context, RentalAlarmConfig.KIND_URGENT);
            if (remaining <= 0L || remaining > near + 5000L || remaining <= urgent) return;
        } else if (kind == RentalAlarmConfig.KIND_URGENT) {
            long urgent = RentalAlarmConfig.thresholdMs(context, kind);
            if (remaining <= 0L || remaining > urgent + 5000L) return;
        } else if (kind == RentalAlarmConfig.KIND_TIME_UP) {
            if (remaining > 1500L) return;
        } else {
            return;
        }

        RentalAlarmConfig.markTriggered(context, kind, expectedLeaseId);
        BlazeAlarmPlayer.play(context, kind);

        if (kind == RentalAlarmConfig.KIND_NEAR_END) {
            Toast.makeText(context, "Rental time is nearing the end. Save your work soon.",
                    Toast.LENGTH_LONG).show();
        } else if (kind == RentalAlarmConfig.KIND_URGENT) {
            Toast.makeText(context, "URGENT: Add credit now. Save your game or work.",
                    Toast.LENGTH_LONG).show();
        } else {
            Toast.makeText(context, "TIME'S UP. Add credit to continue.",
                    Toast.LENGTH_LONG).show();
            ManagedPolicyController.apply(context);
            if (!AndroidRentalPolicyRepository.load(context).isUnrestricted()) {
                ManagedPolicyController.openHome(context);
            }
        }

        schedule(context, RentalLeaseStore.remainingMs(context));
    }
}
