package com.example.lan_messenger

import android.Manifest
import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Person
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.media.AudioAttributes
import android.net.Uri
import android.net.wifi.WifiManager
import android.os.Build
import android.os.Bundle
import android.provider.Settings
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel

/**
 * Explicit non-exported call controls. Only the active peer callId can be
 * answered/declined in Dart; actions from stale Android notifications are ignored.
 */
class CallActionReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        val action = intent.getStringExtra("action") ?: return
        val callId = intent.getStringExtra("callId") ?: return
        if (action != "answer" && action != "decline") return
        (context.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager).cancel(7024)
        MainActivity.deliverCallAction(context, action, callId)
    }
}

class MainActivity : FlutterActivity() {
    companion object {
        @Volatile private var active: MainActivity? = null
        fun deliverCallAction(context: Context, action: String, callId: String) {
            val running = active
            if (running != null) {
                running.runOnUiThread { running.callBridge?.invokeMethod("callAction",
                    mapOf("action" to action, "callId" to callId)) }
            } else {
                // This only reopens the UI; there is no unattended microphone start.
                val intent = Intent(context, MainActivity::class.java).apply {
                    addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP or Intent.FLAG_ACTIVITY_SINGLE_TOP)
                    putExtra("action", action)
                    putExtra("callId", callId)
                }
                context.startActivity(intent)
            }
        }
    }
    private var lock: WifiManager.MulticastLock? = null
    private var nextNotification = 1100
    private var callBridge: MethodChannel? = null
    private val notifications by lazy {
        getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        active = this
        consumeAction(intent)
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        consumeAction(intent)
    }

    private fun consumeAction(intent: Intent?) {
        val action = intent?.getStringExtra("action") ?: return
        val callId = intent.getStringExtra("callId") ?: return
        callBridge?.invokeMethod("callAction", mapOf("action" to action, "callId" to callId))
    }

    private fun requestNotificationPermission() {
        if (Build.VERSION.SDK_INT >= 33 &&
            checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(arrayOf(Manifest.permission.POST_NOTIFICATIONS), 7811)
        }
    }

    private fun canNotify(): Boolean {
        return Build.VERSION.SDK_INT < 33 ||
            checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) == PackageManager.PERMISSION_GRANTED
    }

    private fun eventChannel(event: String): String = "lan_v026_" + event

    private fun createChannel(event: String) {
        if (Build.VERSION.SDK_INT < 26) return
        val name = when(event) {
            "call" -> "Incoming voice calls"
            "video_call" -> "Incoming video calls"
            "file" -> "File transfers"
            else -> "Chat messages"
        }
        val id = eventChannel(event)
        if (notifications.getNotificationChannel(id) != null) return
        val channel = NotificationChannel(id, "LAN Messenger $name", NotificationManager.IMPORTANCE_HIGH)
        channel.description = "Offline LAN Messenger $name"
        channel.enableVibration(event == "call" || event == "video_call")
        val tone = resources.getIdentifier(event, "raw", packageName)
        if (tone != 0) {
            val usage = if (event == "call" || event == "video_call")
                AudioAttributes.USAGE_NOTIFICATION_RINGTONE else AudioAttributes.USAGE_NOTIFICATION
            channel.setSound(Uri.parse("android.resource://$packageName/$tone"),
                AudioAttributes.Builder().setUsage(usage).build())
        }
        notifications.createNotificationChannel(channel)
    }

    private fun builder(event: String): Notification.Builder {
        createChannel(event)
        return if (Build.VERSION.SDK_INT >= 26) {
            Notification.Builder(this, eventChannel(event))
        } else {
            @Suppress("DEPRECATION")
            Notification.Builder(this).setPriority(Notification.PRIORITY_MAX)
        }
    }

    private fun openApp(): PendingIntent {
        val intent = Intent(this, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_CLEAR_TOP or Intent.FLAG_ACTIVITY_SINGLE_TOP
        }
        return PendingIntent.getActivity(this, 0, intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)
    }

    private fun callAction(action: String, callId: String): PendingIntent {
        val intent = Intent(this, CallActionReceiver::class.java).apply {
            putExtra("action", action)
            putExtra("callId", callId)
        }
        return PendingIntent.getBroadcast(this, (action + callId).hashCode(), intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)
    }

    private fun showIncomingCall(caller: String, callId: String, video: Boolean): Boolean {
        if (!canNotify() || callId.isEmpty() || caller.isBlank()) return false
        val event = if (video) "video_call" else "call"
        val answer = callAction("answer", callId)
        val decline = callAction("decline", callId)
        val b = builder(event)
            .setSmallIcon(android.R.drawable.ic_menu_call)
            .setContentTitle(caller)
            .setContentText(if (video) "Incoming LAN video call" else "Incoming LAN voice call")
            .setContentIntent(openApp())
            .setCategory(Notification.CATEGORY_CALL)
            .setVisibility(Notification.VISIBILITY_PUBLIC)
            .setAutoCancel(false)
            .setOngoing(true)
            .setOnlyAlertOnce(true)
        // Full screen intents are restricted by Android 14's user-controlled
        // Special App Access, but enable a heads-up call banner when allowed.
        if (Build.VERSION.SDK_INT < 34 || notifications.canUseFullScreenIntent()) {
            b.setFullScreenIntent(openApp(), true)
        }
        if (Build.VERSION.SDK_INT >= 31) {
            b.setStyle(Notification.CallStyle.forIncomingCall(
                Person.Builder().setName(caller).build(), decline, answer))
        } else {
            @Suppress("DEPRECATION")
            b.setPriority(Notification.PRIORITY_MAX)
            b.addAction(android.R.drawable.ic_menu_close_clear_cancel, "Decline", decline)
            b.addAction(android.R.drawable.ic_menu_call, "Answer", answer)
        }
        notifications.notify(7024, b.build())
        return true
    }

    private fun showEvent(event: String, title: String, body: String): Boolean {
        if (!canNotify()) return false
        val kind = if (event in listOf("message", "file")) event else "message"
        notifications.notify(++nextNotification, builder(kind)
            .setContentTitle(title)
            .setContentText(body)
            .setSmallIcon(android.R.drawable.stat_notify_chat)
            .setCategory(Notification.CATEGORY_MESSAGE)
            .setContentIntent(openApp())
            .setAutoCancel(true).build())
        return true
    }

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        callBridge = MethodChannel(flutterEngine.dartExecutor.binaryMessenger, "lan_messenger/notifications")
        callBridge?.setMethodCallHandler { call, result ->
            try {
                when (call.method) {
                    "setup" -> { requestNotificationPermission(); result.success(null) }
                    "incoming" -> result.success(showIncomingCall(
                        call.argument<String>("caller") ?: "LAN Messenger",
                        call.argument<String>("callId") ?: "",
                        call.argument<Boolean>("video") ?: false))
                    "dismissIncoming" -> { notifications.cancel(7024); result.success(null) }
                    "show" -> result.success(showEvent(
                        call.argument<String>("kind") ?: "message",
                        call.argument<String>("title") ?: "LAN Messenger",
                        call.argument<String>("body") ?: "Local message"))
                    else -> result.notImplemented()
                }
            } catch (e: Exception) { result.error("LAN_NOTIFY", e.message, null) }
        }
        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, "lan_messenger/remote")
            .setMethodCallHandler { call, result ->
                try {
                    when (call.method) {
                        "available" -> result.success(RemoteTouchService.active != null)
                        "openAccessibilitySettings" -> {
                            startActivity(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS))
                            result.success(null)
                        }
                        "tap" -> result.success(RemoteTouchService.tap(
                            (call.argument<Number>("x") ?: 0.0).toDouble(),
                            (call.argument<Number>("y") ?: 0.0).toDouble()))
                        "openCallSettings" -> {
                            if (Build.VERSION.SDK_INT >= 26) {
                                startActivity(Intent(Settings.ACTION_CHANNEL_NOTIFICATION_SETTINGS)
                                    .putExtra(Settings.EXTRA_APP_PACKAGE, packageName)
                                    .putExtra(Settings.EXTRA_CHANNEL_ID, eventChannel("call")))
                            } else {
                                startActivity(Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS,
                                    Uri.parse("package:$packageName")))
                            }
                            result.success(null)
                        }
                        "openFullScreenSettings" -> {
                            if (Build.VERSION.SDK_INT >= 34) {
                                startActivity(Intent("android.settings.MANAGE_APP_USE_FULL_SCREEN_INTENT",
                                    Uri.parse("package:$packageName")))
                            } else {
                                startActivity(Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS,
                                    Uri.parse("package:$packageName")))
                            }
                            result.success(null)
                        }
                        else -> result.notImplemented()
                    }
                } catch (e: Exception) { result.error("LAN_REMOTE", e.message, null) }
            }
        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, "lan_messenger/projection")
            .setMethodCallHandler { call, result ->
                try {
                    when (call.method) {
                        "start" -> {
                            val service = Intent(this, ScreenProjectionService::class.java)
                            if (Build.VERSION.SDK_INT >= 26) startForegroundService(service)
                            else startService(service)
                            result.success(null)
                        }
                        "stop" -> {
                            stopService(Intent(this, ScreenProjectionService::class.java))
                            result.success(null)
                        }
                        else -> result.notImplemented()
                    }
                } catch (e: Exception) { result.error("PROJECTION", e.message, null) }
            }
        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, "lan_messenger/multicast")
            .setMethodCallHandler { call, result ->
                try {
                    when (call.method) {
                        "acquire" -> {
                            if (lock == null) {
                                val wifi = applicationContext.getSystemService(
                                    Context.WIFI_SERVICE) as WifiManager
                                lock = wifi.createMulticastLock("LANMessengerDiscovery").apply {
                                    setReferenceCounted(false)
                                    acquire()
                                }
                            }
                            result.success(null)
                        }
                        "release" -> {
                            lock?.let { if (it.isHeld) it.release() }
                            lock = null
                            result.success(null)
                        }
                        else -> result.notImplemented()
                    }
                } catch (e: Exception) { result.error("MULTICAST_LOCK", e.message, null) }
            }
    }

    override fun onDestroy() {
        if (active === this) active = null
        callBridge = null
        lock?.let { if (it.isHeld) it.release() }
        lock = null
        super.onDestroy()
    }
}
