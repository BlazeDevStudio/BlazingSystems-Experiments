package com.blazesystems.blazerental;

import android.app.NotificationManager;
import android.content.Context;
import android.media.AudioManager;
import android.media.MediaPlayer;
import android.media.RingtoneManager;
import android.media.ToneGenerator;
import android.net.Uri;
import android.os.Build;
import android.os.Handler;
import android.os.Looper;
import android.os.PowerManager;

public final class BlazeAlarmPlayer {
    private static final Handler HANDLER = new Handler(Looper.getMainLooper());

    private static MediaPlayer media;
    private static ToneGenerator tone;
    private static Runnable stopRunnable;
    private static Runnable volumeGuardRunnable;
    private static PowerManager.WakeLock wakeLock;
    private static int activeKind;
    private static Context appContext;
    private static AudioManager audio;
    private static NotificationManager notificationManager;
    private static int previousAlarmVolume = -1;
    private static int previousRingerMode = -1;
    private static int previousFilter = -1;

    private BlazeAlarmPlayer() {}

    public static synchronized void play(Context context, int kind) {
        stopInternal(true);
        appContext = context.getApplicationContext();
        long duration = RentalAlarmConfig.durationMs(appContext, kind);
        activeKind = kind;

        audio = (AudioManager) appContext.getSystemService(Context.AUDIO_SERVICE);
        notificationManager = (NotificationManager)
                appContext.getSystemService(Context.NOTIFICATION_SERVICE);

        forceAudible(kind);
        startVolumeGuard(kind, duration);
        acquireWakeLock(duration + 5000L);

        boolean started = false;
        String mode = RentalAlarmConfig.soundMode(appContext, kind);
        if (!RentalAlarmConfig.MODE_BUILTIN.equals(mode)) {
            String value = RentalAlarmConfig.soundUri(appContext, kind);
            if (value != null && value.length() > 0) {
                started = startMedia(Uri.parse(value));
            }
        }
        if (!started && !RentalAlarmConfig.MODE_BUILTIN.equals(mode)) {
            Uri fallback = RingtoneManager.getDefaultUri(RingtoneManager.TYPE_ALARM);
            if (fallback != null) started = startMedia(fallback);
        }
        if (!started) startBuiltIn(kind, duration);

        final long stopAfter = duration;
        stopRunnable = new Runnable() {
            @Override public void run() {
                synchronized (BlazeAlarmPlayer.class) {
                    stopInternal(true);
                }
            }
        };
        HANDLER.postDelayed(stopRunnable, stopAfter);
    }

    public static synchronized void stop(Context context) {
        stopInternal(true);
    }

    public static synchronized boolean isPlaying() {
        return media != null || tone != null;
    }

    private static boolean startMedia(Uri uri) {
        try {
            media = new MediaPlayer();
            media.setAudioStreamType(AudioManager.STREAM_ALARM);
            media.setDataSource(appContext, uri);
            media.setLooping(true);
            media.prepare();
            media.start();
            return true;
        } catch (Exception ignored) {
            if (media != null) {
                try { media.release(); } catch (Exception ignored2) {}
                media = null;
            }
            return false;
        }
    }

    private static void startBuiltIn(int kind, long duration) {
        try {
            int streamPercent = Math.max(50, RentalAlarmConfig.volumePercent(appContext, kind));
            tone = new ToneGenerator(AudioManager.STREAM_ALARM, streamPercent);
            int toneType;
            if (kind == RentalAlarmConfig.KIND_TIME_UP) {
                toneType = ToneGenerator.TONE_CDMA_EMERGENCY_RINGBACK;
            } else if (kind == RentalAlarmConfig.KIND_URGENT) {
                toneType = ToneGenerator.TONE_CDMA_ALERT_CALL_GUARD;
            } else {
                toneType = ToneGenerator.TONE_PROP_BEEP2;
            }
            int ms = (int) Math.min(Integer.MAX_VALUE, Math.max(1000L, duration));
            tone.startTone(toneType, ms);
        } catch (Exception ignored) {
            try {
                tone = new ToneGenerator(AudioManager.STREAM_ALARM, 100);
                tone.startTone(ToneGenerator.TONE_CDMA_ALERT_CALL_GUARD,
                        (int) Math.min(60000L, Math.max(1000L, duration)));
            } catch (Exception ignored2) {}
        }
    }

    private static void startVolumeGuard(final int kind, long duration) {
        if (volumeGuardRunnable != null) HANDLER.removeCallbacks(volumeGuardRunnable);
        final long until = android.os.SystemClock.elapsedRealtime() + duration;
        volumeGuardRunnable = new Runnable() {
            @Override public void run() {
                synchronized (BlazeAlarmPlayer.class) {
                    if (activeKind != kind || (!isPlaying())) return;
                    if (audio != null) {
                        try {
                            int max = Math.max(1,
                                    audio.getStreamMaxVolume(AudioManager.STREAM_ALARM));
                            int percent = RentalAlarmConfig.volumePercent(appContext, kind);
                            int minimum = Math.max(1, Math.round(max * percent / 100f));
                            if (audio.getStreamVolume(AudioManager.STREAM_ALARM) < minimum) {
                                audio.setStreamVolume(AudioManager.STREAM_ALARM, minimum, 0);
                            }
                        } catch (Exception ignored) {}
                    }
                    if (android.os.SystemClock.elapsedRealtime() < until) {
                        HANDLER.postDelayed(this, 350L);
                    }
                }
            }
        };
        HANDLER.postDelayed(volumeGuardRunnable, 350L);
    }

    private static void forceAudible(int kind) {
        if (audio != null) {
            try {
                previousAlarmVolume = audio.getStreamVolume(AudioManager.STREAM_ALARM);
                int max = Math.max(1, audio.getStreamMaxVolume(AudioManager.STREAM_ALARM));
                int percent = RentalAlarmConfig.volumePercent(appContext, kind);
                int desired = Math.max(1, Math.round(max * percent / 100f));
                audio.setStreamVolume(AudioManager.STREAM_ALARM, desired, 0);
            } catch (Exception ignored) {}
            try {
                previousRingerMode = audio.getRingerMode();
                audio.setRingerMode(AudioManager.RINGER_MODE_NORMAL);
            } catch (Exception ignored) {}
        }

        if (Build.VERSION.SDK_INT >= 23 && notificationManager != null) {
            try {
                if (notificationManager.isNotificationPolicyAccessGranted()) {
                    previousFilter = notificationManager.getCurrentInterruptionFilter();
                    notificationManager.setInterruptionFilter(
                            NotificationManager.INTERRUPTION_FILTER_ALL);
                }
            } catch (Exception ignored) {}
        }
    }

    private static void restoreAudio() {
        if (audio != null) {
            if (previousAlarmVolume >= 0) {
                try {
                    audio.setStreamVolume(AudioManager.STREAM_ALARM,
                            previousAlarmVolume, 0);
                } catch (Exception ignored) {}
            }
            if (previousRingerMode >= 0) {
                try { audio.setRingerMode(previousRingerMode); }
                catch (Exception ignored) {}
            }
        }

        if (Build.VERSION.SDK_INT >= 23 && notificationManager != null
                && previousFilter >= 0) {
            try {
                if (notificationManager.isNotificationPolicyAccessGranted()) {
                    notificationManager.setInterruptionFilter(previousFilter);
                }
            } catch (Exception ignored) {}
        }
        previousAlarmVolume = -1;
        previousRingerMode = -1;
        previousFilter = -1;
    }

    private static void acquireWakeLock(long duration) {
        try {
            PowerManager pm = (PowerManager)
                    appContext.getSystemService(Context.POWER_SERVICE);
            if (pm == null) return;
            wakeLock = pm.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK,
                    "BlazeRental:TimeAlarm");
            wakeLock.setReferenceCounted(false);
            wakeLock.acquire(Math.max(5000L, duration));
        } catch (Exception ignored) {}
    }

    private static void stopInternal(boolean restore) {
        if (stopRunnable != null) {
            HANDLER.removeCallbacks(stopRunnable);
            stopRunnable = null;
        }
        if (volumeGuardRunnable != null) {
            HANDLER.removeCallbacks(volumeGuardRunnable);
            volumeGuardRunnable = null;
        }
        activeKind = 0;
        if (media != null) {
            try { if (media.isPlaying()) media.stop(); } catch (Exception ignored) {}
            try { media.release(); } catch (Exception ignored) {}
            media = null;
        }
        if (tone != null) {
            try { tone.stopTone(); } catch (Exception ignored) {}
            try { tone.release(); } catch (Exception ignored) {}
            tone = null;
        }
        if (wakeLock != null) {
            try { if (wakeLock.isHeld()) wakeLock.release(); } catch (Exception ignored) {}
            wakeLock = null;
        }
        if (restore) restoreAudio();
        appContext = null;
        audio = null;
        notificationManager = null;
    }
}
