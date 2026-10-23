package com.example.lan_messenger

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Intent
import android.content.pm.ServiceInfo
import android.os.Build
import android.os.IBinder

/**
 * Starts ONLY after WebRTC's standard MediaProjection consent UI was accepted.
 * Its persistent notification makes capture obvious and revocable by the owner.
 */
class ScreenCaptureForegroundService : Service() {
    private val channelId = "lan_messenger_active_screen_capture"

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        val manager = getSystemService(NotificationManager::class.java)
        if (Build.VERSION.SDK_INT >= 26) {
            manager.createNotificationChannel(NotificationChannel(channelId,
                "LAN Messenger screen sharing", NotificationManager.IMPORTANCE_LOW))
        }
        val notification = if (Build.VERSION.SDK_INT >= 26) {
            Notification.Builder(this, channelId)
        } else {
            @Suppress("DEPRECATION")
            Notification.Builder(this)
        }.setSmallIcon(android.R.drawable.ic_menu_share)
            .setContentTitle("LAN Messenger — sharing your screen")
            .setContentText("Open LAN Messenger to stop sharing")
            .setOngoing(true)
            .setCategory(Notification.CATEGORY_SERVICE)
            .build()
        if (Build.VERSION.SDK_INT >= 29) {
            startForeground(7045, notification,
                ServiceInfo.FOREGROUND_SERVICE_TYPE_MEDIA_PROJECTION)
        } else {
            startForeground(7045, notification)
        }
        return START_NOT_STICKY
    }
    override fun onDestroy() {
        stopForeground(STOP_FOREGROUND_REMOVE)
        super.onDestroy()
    }
}
