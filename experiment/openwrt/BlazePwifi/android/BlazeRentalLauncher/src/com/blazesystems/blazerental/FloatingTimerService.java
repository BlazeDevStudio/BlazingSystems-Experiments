package com.blazesystems.blazerental;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.Service;
import android.content.Context;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.PixelFormat;
import android.os.Build;
import android.os.Handler;
import android.os.IBinder;
import android.provider.Settings;
import android.view.Gravity;
import android.view.MotionEvent;
import android.view.View;
import android.view.WindowManager;
import android.widget.TextView;

public class FloatingTimerService extends Service {
    private static final String CHANNEL = "blaze_rental_timer";
    private static final int NOTIFICATION_ID = 94040;

    private WindowManager windowManager;
    private TextView timerView;
    private WindowManager.LayoutParams params;
    private final Handler handler = new Handler();

    private final Runnable tick = new Runnable() {
        @Override public void run() {
            long remaining = RentalLeaseStore.remainingMs(FloatingTimerService.this);
            boolean enabled = RentalUiPolicy.floatingTimerEnabled(FloatingTimerService.this);
            if (remaining <= 0L || !enabled) {
                ManagedPolicyController.apply(FloatingTimerService.this);
                if (remaining <= 0L
                        && LauncherAccessController.isRentalRestricted(FloatingTimerService.this)) {
                    ManagedPolicyController.openHome(FloatingTimerService.this);
                }
                stopSelf();
                return;
            }
            if (timerView != null) timerView.setText(format(remaining));
            handler.postDelayed(this, 1000L);
        }
    };

    public static void ensure(Context context) {
        boolean enabled = RentalUiPolicy.floatingTimerEnabled(context);
        boolean operatorAllowed = RentalUiPolicy.floatingTimerOperatorAllowed(context);
        boolean overlay = Build.VERSION.SDK_INT < 23 || Settings.canDrawOverlays(context);
        if (!FloatingTimerPolicy.shouldShow(
                RentalLeaseStore.isLeaseValid(context), enabled, operatorAllowed, overlay)) {
            stop(context);
            return;
        }
        Intent intent = new Intent(context, FloatingTimerService.class);
        try {
            if (Build.VERSION.SDK_INT >= 26) context.startForegroundService(intent);
            else context.startService(intent);
        } catch (Exception ignored) {}
    }

    public static void stop(Context context) {
        try { context.stopService(new Intent(context, FloatingTimerService.class)); }
        catch (Exception ignored) {}
    }

    @Override public void onCreate() {
        super.onCreate();
        createForegroundNotification();
        if (Build.VERSION.SDK_INT >= 23 && !Settings.canDrawOverlays(this)) {
            stopSelf();
            return;
        }
        windowManager = (WindowManager) getSystemService(WINDOW_SERVICE);
        timerView = new TextView(this);
        timerView.setTextColor(Color.WHITE);
        timerView.setTextSize(12f);
        timerView.setGravity(Gravity.CENTER);
        timerView.setPadding(dp(8), dp(4), dp(8), dp(4));
        timerView.setBackgroundColor(0xcc101827);

        int type = Build.VERSION.SDK_INT >= 26
                ? WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY
                : WindowManager.LayoutParams.TYPE_PHONE;
        params = new WindowManager.LayoutParams(
                WindowManager.LayoutParams.WRAP_CONTENT,
                WindowManager.LayoutParams.WRAP_CONTENT,
                type,
                WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE
                        | WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS,
                PixelFormat.TRANSLUCENT);
        params.gravity = Gravity.TOP | Gravity.END;
        params.x = dp(10);
        params.y = dp(42);

        timerView.setOnTouchListener(new View.OnTouchListener() {
            private float startX;
            private float startY;
            private int originalX;
            private int originalY;

            @Override public boolean onTouch(View v, MotionEvent e) {
                if (e.getAction() == MotionEvent.ACTION_DOWN) {
                    startX = e.getRawX();
                    startY = e.getRawY();
                    originalX = params.x;
                    originalY = params.y;
                    return true;
                }
                if (e.getAction() == MotionEvent.ACTION_MOVE) {
                    params.x = Math.max(0, originalX - Math.round(e.getRawX() - startX));
                    params.y = Math.max(0, originalY + Math.round(e.getRawY() - startY));
                    try { windowManager.updateViewLayout(timerView, params); } catch (Exception ignored) {}
                    return true;
                }
                return true;
            }
        });

        try { windowManager.addView(timerView, params); }
        catch (Exception e) { stopSelf(); return; }
        handler.post(tick);
    }

    private void createForegroundNotification() {
        NotificationManager nm = (NotificationManager) getSystemService(NOTIFICATION_SERVICE);
        if (Build.VERSION.SDK_INT >= 26 && nm != null) {
            NotificationChannel channel = new NotificationChannel(
                    CHANNEL, "BlazeRental timer", NotificationManager.IMPORTANCE_MIN);
            channel.setShowBadge(false);
            nm.createNotificationChannel(channel);
        }
        Notification.Builder builder = Build.VERSION.SDK_INT >= 26
                ? new Notification.Builder(this, CHANNEL) : new Notification.Builder(this);
        builder.setContentTitle("BlazeRental active")
                .setContentText("Rental timer enforcement is running")
                .setSmallIcon(com.android.launcher3.R.drawable.ic_launcher_home)
                .setOngoing(true);
        startForeground(NOTIFICATION_ID, builder.build());
    }

    @Override public void onDestroy() {
        handler.removeCallbacks(tick);
        if (windowManager != null && timerView != null) {
            try { windowManager.removeView(timerView); } catch (Exception ignored) {}
        }
        timerView = null;
        super.onDestroy();
    }

    @Override public IBinder onBind(Intent intent) { return null; }

    private String format(long ms) {
        long total = Math.max(0L, ms / 1000L);
        long h = total / 3600L;
        long m = (total % 3600L) / 60L;
        long s = total % 60L;
        return h > 0L ? String.format("%d:%02d:%02d", h, m, s)
                : String.format("%02d:%02d", m, s);
    }

    private int dp(int value) {
        return Math.round(value * getResources().getDisplayMetrics().density);
    }
}
