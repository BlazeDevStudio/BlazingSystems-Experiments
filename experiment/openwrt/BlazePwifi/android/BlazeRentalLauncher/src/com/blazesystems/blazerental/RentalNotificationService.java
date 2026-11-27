package com.blazesystems.blazerental;

import android.app.Notification;
import android.app.PendingIntent;
import android.content.Context;
import android.service.notification.NotificationListenerService;
import android.service.notification.StatusBarNotification;
import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

public class RentalNotificationService extends NotificationListenerService {
    public static final class Entry {
        public final String key;
        public final String packageName;
        public final String title;
        public final String text;
        public final long postedAt;

        Entry(String key, String packageName, String title, String text, long postedAt) {
            this.key = key;
            this.packageName = packageName;
            this.title = title;
            this.text = text;
            this.postedAt = postedAt;
        }
    }

    private static final Map<String, StatusBarNotification> ACTIVE =
            Collections.synchronizedMap(new LinkedHashMap<String, StatusBarNotification>());
    private static volatile RentalNotificationService instance;

    @Override public void onListenerConnected() {
        instance = this;
        try {
            StatusBarNotification[] active = getActiveNotifications();
            if (active != null) for (StatusBarNotification sbn : active) ACTIVE.put(sbn.getKey(), sbn);
        } catch (Exception ignored) {}
    }

    @Override public void onListenerDisconnected() {
        if (instance == this) instance = null;
    }

    @Override public void onNotificationPosted(StatusBarNotification sbn) {
        ACTIVE.put(sbn.getKey(), sbn);
    }

    @Override public void onNotificationRemoved(StatusBarNotification sbn) {
        ACTIVE.remove(sbn.getKey());
    }

    public static List<Entry> snapshot() {
        ArrayList<Entry> out = new ArrayList<Entry>();
        synchronized (ACTIVE) {
            for (StatusBarNotification sbn : ACTIVE.values()) {
                Notification n = sbn.getNotification();
                CharSequence title = n.extras.getCharSequence(Notification.EXTRA_TITLE, "");
                CharSequence text = n.extras.getCharSequence(Notification.EXTRA_TEXT, "");
                out.add(new Entry(sbn.getKey(), sbn.getPackageName(),
                        title == null ? "" : title.toString(),
                        text == null ? "" : text.toString(), sbn.getPostTime()));
            }
        }
        return out;
    }

    public static boolean open(Context context, String key) {
        StatusBarNotification sbn = ACTIVE.get(key);
        if (sbn == null || !LauncherAccessController.isPackageVisible(
                context, sbn.getPackageName())) return false;
        PendingIntent intent = sbn.getNotification().contentIntent;
        if (intent == null) return false;
        try {
            intent.send();
            return true;
        } catch (PendingIntent.CanceledException ignored) {
            return false;
        }
    }

    public static boolean dismiss(String key) {
        RentalNotificationService current = instance;
        if (current == null || key == null) return false;
        try {
            current.cancelNotification(key);
            ACTIVE.remove(key);
            return true;
        } catch (Exception ignored) {
            return false;
        }
    }

    public static boolean dismissAll() {
        RentalNotificationService current = instance;
        if (current == null) return false;
        try {
            current.cancelAllNotifications();
            ACTIVE.clear();
            return true;
        } catch (Exception ignored) {
            return false;
        }
    }
}
