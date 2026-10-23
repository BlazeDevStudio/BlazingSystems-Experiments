package com.example.lan_messenger

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Intent
import android.content.pm.ServiceInfo
import android.os.Build
import android.os.IBinder

/** Required user-visible foreground service for Android screen projection.
 * Never starts unless the user granted system MediaProjection consent in app.
 */
class ScreenProjectionService : Service() {
    override fun onBind(intent: Intent?): IBinder? = null

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        if (intent?.action == "STOP") {
            stopForeground(STOP_FOREGROUND_REMOVE)
            stopSelf()
            return START_NOT_STICKY
        }
        val manager = getSystemService(NOTIFICATION_SERVICE) as NotificationManager
        val id = "lan_messenger_projection"
        if (Build.VERSION.SDK_INT >= 26) {
            manager.createNotificationChannel(NotificationChannel(
                id, "LAN Messenger screen sharing", NotificationManager.IMPORTANCE_LOW))
        }
        val notification = if (Build.VERSION.SDK_INT >= 26) {
            Notification.Builder(this, id)
        } else {
            @Suppress("DEPRECATION")
            Notification.Builder(this).setPriority(Notification.PRIORITY_LOW)
        }.setSmallIcon(android.R.drawable.ic_menu_view)
            .setContentTitle("LAN Messenger is sharing your screen")
            .setContentText("Return to the active call to stop sharing")
            .setOngoing(true).build()
        if (Build.VERSION.SDK_INT >= 29) {
            startForeground(7025, notification,
                ServiceInfo.FOREGROUND_SERVICE_TYPE_MEDIA_PROJECTION)
        } else {
            startForeground(7025, notification)
        }
        return START_NOT_STICKY
    }
}
