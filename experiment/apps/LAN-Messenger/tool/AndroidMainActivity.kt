package com.example.lan_messenger

import android.Manifest
import android.app.Notification
import android.app.NotificationChannel
import android.app.AppOpsManager
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Person
import android.app.PictureInPictureParams
import android.app.RemoteAction
import android.graphics.drawable.Icon
import android.content.res.Configuration
import android.util.Rational
import android.util.Log
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
        // An old notification action must not cancel the NEW call's shared
        // notification ID 7024. Validate against the currently live session
        // before changing notification state or forwarding anything to Dart.
        if (!MainActivity.isCurrentCallAction(action, callId)) return
        if (action == "answer" || action == "decline" || action == "end")
            (context.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager).cancel(7024)
        MainActivity.deliverCallAction(context, action, callId)
    }
}

class MainActivity : FlutterActivity() {
    companion object {
        @Volatile private var active: MainActivity? = null

        /**
         * Reject stale taps from earlier notification instances. Android
         * reuses ID 7024 for a newer call, so canceling before this test can
         * silently remove the current user's Answer and Decline buttons.
         */
        fun isCurrentCallAction(action: String, callId: String): Boolean {
            val running = active ?: return false
            if (callId.isEmpty() || callId != running.lastCallId) return false
            return when (action) {
                "answer", "decline" -> running.lastIncoming
                "end", "mute" -> !running.lastIncoming
                "open" -> true
                else -> false
            }
        }

        fun deliverCallAction(context: Context, action: String, callId: String) {
            if (!isCurrentCallAction(action, callId)) return
            val running = active
            if (running != null) {
                running.runOnUiThread {
                    if (action == "answer" && !running.activityForeground) {
                        // Android 14+ restricts starting a microphone/camera while
                        // backgrounded. Restore the Activity only on explicit
                        // Answer, defer capture until onResume, then Dart can
                        // minimize it to PiP after negotiation.
                        running.pendingAnswer = callId
                        val open = Intent(context, MainActivity::class.java).apply {
                            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or
                                Intent.FLAG_ACTIVITY_CLEAR_TOP or Intent.FLAG_ACTIVITY_SINGLE_TOP)
                        }
                        try {
                            context.startActivity(open)
                        } catch (_: Exception) {
                            // Android may forbid background launches. Keep the
                            // CallStyle notification instead of crashing.
                            running.pendingAnswer = null
                            running.updateOverlay()
                        }
                    } else {
                        running.callBridge?.invokeMethod("callAction",
                            mapOf("action" to action, "callId" to callId))
                    }
                }
            } else {
                // This only reopens the UI; there is no unattended microphone start.
                val intent = Intent(context, MainActivity::class.java).apply {
                    addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP or Intent.FLAG_ACTIVITY_SINGLE_TOP)
                    putExtra("action", action)
                    putExtra("callId", callId)
                }
                try {
                    context.startActivity(intent)
                } catch (_: Exception) {
                    // A broadcast from a terminated process cannot legitimately
                    // force-open an Activity on modern Android; never crash.
                }
            }
        }
    }
    private var lock: WifiManager.MulticastLock? = null
    // A separately keyed call notification must not be auto-bundled with
    // FlutterBackground's persistent "LAN Messenger is ready" notification.
    // Android 35 hid Answer/Decline behind that auto-group in actual CI.
    private val callNotificationGroup = "lan-messenger-call-actions"
    private var nextNotification = 1100
    private var callBridge: MethodChannel? = null
    private var activityForeground = true

    private var lastCaller: String? = null
    private var lastCallId: String? = null
    private var lastVideo = false
    private var lastMuted = false
    private var lastIncoming = false
    private var pendingAnswer: String? = null
    private var answerDispatching = false
    private var pipEnabledForCall = false
    private var incomingNotificationPosted = false

    private fun updateOverlay() {
        // Android has exactly ONE external call presentation surface:
        // a native CallStyle notification while ringing, then system PiP
        // for connected video. Never add our TYPE_APPLICATION_OVERLAY HUD,
        // including while the notification shade or settings are visible.
    }

    override fun onStart() {
        super.onStart()
        activityForeground = true
    }

    override fun onResume() {
        super.onResume()
        activityForeground = true
        if (lastIncoming) notifications.cancel(7024)
        window?.decorView?.post { deliverPendingAnswer() }
    }

    override fun onPause() {
        // Pause can occur for OS permissions, the shade, or transient system
        // overlays while Messenger remains visible. Do not show another HUD.
        super.onPause()
    }

    override fun onStop() {
        super.onStop()
        activityForeground = false
        if (Build.VERSION.SDK_INT >= 26 && isInPictureInPictureMode) {
            return
        }
        val id = lastCallId
        val caller = lastCaller
        if (lastIncoming && id != null && caller != null &&
            !incomingNotificationPosted) {
            showIncomingCall(caller, id, lastVideo)
        }
        updateOverlay()
    }
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
        // Activity restarts/rotation must never replay an old Answer.
        intent.removeExtra("action")
        intent.removeExtra("callId")
        if (action == "answer") {
            pendingAnswer = callId
            window?.decorView?.post { deliverPendingAnswer() }
        } else {
            callBridge?.invokeMethod("callAction",
                mapOf("action" to action, "callId" to callId))
        }
    }

    private fun deliverPendingAnswer() {
        // Do not consume an Answer until Flutter acknowledges that it has a
        // live matching incoming offer. Activity resume can precede Flutter
        // widget initialization or LAN signal delivery on slow Android phones.
        if (!activityForeground || answerDispatching) return
        val id = pendingAnswer ?: return
        if (!lastIncoming || id != lastCallId) return
        val bridge = callBridge ?: return
        answerDispatching = true
        bridge.invokeMethod("callAction",
            mapOf("action" to "answer", "callId" to id,
                "wasBackground" to true), object : MethodChannel.Result {
                override fun success(result: Any?) {
                    answerDispatching = false
                    if (result == true && pendingAnswer == id) pendingAnswer = null
                }
                override fun error(code: String, message: String?, details: Any?) {
                    answerDispatching = false
                }
                override fun notImplemented() {
                    answerDispatching = false
                }
            })
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
        if (action == "answer") {
            // Direct user-launched Activity PendingIntent: no Android 12+
            // notification broadcast -> background Activity trampoline.
            val open = Intent(this, MainActivity::class.java).apply {
                flags = Intent.FLAG_ACTIVITY_CLEAR_TOP or
                    Intent.FLAG_ACTIVITY_SINGLE_TOP
                putExtra("action", action)
                putExtra("callId", callId)
            }
            return PendingIntent.getActivity(this, (action + callId).hashCode(), open,
                PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)
        }
        val intent = Intent(this, CallActionReceiver::class.java).apply {
            putExtra("action", action)
            putExtra("callId", callId)
        }
        return PendingIntent.getBroadcast(this, (action + callId).hashCode(), intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)
    }

    private fun showIncomingCall(caller: String, callId: String, video: Boolean): Boolean {
        Log.i("LANCallTrace", "showIncoming invoked foreground=$activityForeground canNotify=${canNotify()}")
        if (callId.isEmpty() || caller.isBlank()) return false
        lastCaller = caller; lastCallId = callId
        lastVideo = video; lastMuted = false; lastIncoming = true
        if (activityForeground) {
            incomingNotificationPosted = false
            return false // Flutter shows the in-app buttons.
        }
        if (!canNotify()) {
            incomingNotificationPosted = false
            updateOverlay()
            return false
        }
        val event = if (video) "video_call" else "call"
        val answer = callAction("answer", callId)
        val decline = callAction("decline", callId)
        val b = builder(event)
            .setSmallIcon(android.R.drawable.ic_menu_call)
            .setContentTitle(caller)
            .setContentText(if (video) "Incoming LAN video call" else "Incoming LAN voice call")
            .setContentIntent(openApp())
            .setCategory(Notification.CATEGORY_CALL)
            .setGroup(callNotificationGroup)
            .setVisibility(Notification.VISIBILITY_PUBLIC)
            .setAutoCancel(false)
            .setOngoing(true)
            .setOnlyAlertOnce(true)
        // Intentionally do NOT use setFullScreenIntent. Incoming calls
        // display system-managed CallStyle/heads-up Answer + Decline buttons
        // without launching or stealing the screen of the busy user.
        if (Build.VERSION.SDK_INT >= 31) {
            b.setStyle(Notification.CallStyle.forIncomingCall(
                Person.Builder().setName(caller).build(), decline, answer)
                .setIsVideo(video))
        } else {
            @Suppress("DEPRECATION")
            b.setPriority(Notification.PRIORITY_MAX)
            b.addAction(android.R.drawable.ic_menu_close_clear_cancel, "Decline", decline)
            b.addAction(android.R.drawable.ic_menu_call, "Answer", answer)
        }
        var posted = false
        try {
            notifications.notify(7024, b.build())
            Log.i("LANCallTrace", "incoming CallStyle notification 7024 posted")
            posted = true
        } catch (error: Exception) {
            // Android 14+ can reject CallStyle notifications that are not
            // themselves the foreground-service notification, even though
            // LAN Messenger's separate FlutterBackground service is active.
            // Preserve OS-level Answer/Decline actions and user choice instead
            // of losing the incoming call entirely. Do not launch an Activity.
            Log.w("LANCallTrace", "CallStyle unavailable; posting actionable heads-up fallback: ${error.message}")
            try {
                val fallback = builder(event)
                    .setSmallIcon(android.R.drawable.ic_menu_call)
                    .setContentTitle(caller)
                    .setContentText(if (video) "Incoming LAN video call" else "Incoming LAN voice call")
                    .setContentIntent(openApp())
                    .setCategory(Notification.CATEGORY_CALL)
            .setGroup(callNotificationGroup)
                    .setVisibility(Notification.VISIBILITY_PUBLIC)
                    .setAutoCancel(false)
                    .setOngoing(true)
                    .setOnlyAlertOnce(false)
                    .addAction(android.R.drawable.ic_menu_close_clear_cancel, "Decline", decline)
                    .addAction(android.R.drawable.ic_menu_call, "Answer", answer)
                notifications.notify(7024, fallback.build())
                Log.i("LANCallTrace", "fallback Answer/Decline notification 7024 posted")
                posted = true
            } catch (fallbackError: Exception) {
                Log.e("LANCallTrace", "incoming notification fallback failed: ${fallbackError.message}")
            }
        }
        incomingNotificationPosted = posted
        // No second Answer/Decline UI. If notifications are unavailable,
        // a returning user can answer from the inline Messenger call controls.
        updateOverlay()
        return posted
    }

    private fun showOngoingCall(caller: String, callId: String,
                                video: Boolean, muted: Boolean): Boolean {
        if (callId.isBlank()) return false
        // PiP availability must never depend on notification permission.
        // Samsung/Android users can decline alerts and still use video PiP.
        lastCaller = caller; lastCallId = callId
        lastVideo = video; lastMuted = muted; lastIncoming = false
        incomingNotificationPosted = false
        pipEnabledForCall = video
        if (Build.VERSION.SDK_INT >= 31) {
            try {
                setPictureInPictureParams(PictureInPictureParams.Builder()
                    .setAspectRatio(Rational(16, 9))
                    .setActions(pictureActions(callId))
                    .setAutoEnterEnabled(video)
                    .build())
            } catch (e: Exception) {
                Log.w("LANCallTrace", "could not configure video PiP: ${e.message}")
            }
        }
        if (!canNotify()) return false
        // Active calls must not play the incoming ringtone again.
        // A separate low-importance channel preserves in-call actions without
        // silently overriding the owner's high-priority incoming-call settings.
        val b = if (Build.VERSION.SDK_INT >= 26) {
            val channelId = "lan_v028_ongoing"
            if (notifications.getNotificationChannel(channelId) == null) {
                val channel = NotificationChannel(channelId,
                    "LAN Messenger active calls", NotificationManager.IMPORTANCE_LOW)
                channel.setSound(null, null)
                notifications.createNotificationChannel(channel)
            }
            Notification.Builder(this, channelId)
        } else {
            @Suppress("DEPRECATION")
            Notification.Builder(this)
                .setPriority(Notification.PRIORITY_LOW)
                .setSound(null)
        }
        b.setSmallIcon(android.R.drawable.ic_menu_call)
            .setContentTitle(caller)
            .setContentText(if (muted) "Microphone muted" else
                if (video) "Video call in progress" else "Voice call in progress")
            .setContentIntent(openApp())
            .setCategory(Notification.CATEGORY_CALL)
            .setGroup(callNotificationGroup)
            .setOngoing(true)
            .setOnlyAlertOnce(true)
        val end = callAction("end", callId)
        if (Build.VERSION.SDK_INT >= 31) {
            b.setStyle(Notification.CallStyle.forOngoingCall(
                Person.Builder().setName(caller).build(), end).setIsVideo(video))
        } else {
            b.addAction(android.R.drawable.ic_menu_close_clear_cancel, "End call", end)
        }
        b.addAction(android.R.drawable.ic_lock_silent_mode,
            if (muted) "Unmute" else "Mute", callAction("mute", callId))
        b.addAction(android.R.drawable.ic_menu_view, "Return to live call",
            callAction("open", callId))
        notifications.notify(7024, b.build())
        if (Build.VERSION.SDK_INT >= 26 && isInPictureInPictureMode) {
            try {
                setPictureInPictureParams(PictureInPictureParams.Builder()
                    .setAspectRatio(Rational(16, 9))
                    .setActions(pictureActions(callId)).build())
            } catch (_: Exception) { }
        }
        updateOverlay()
        return true
    }

    private fun pictureActions(id: String): List<RemoteAction> {
        fun control(name: String, label: String, icon: Int): RemoteAction {
            return RemoteAction(Icon.createWithResource(this, icon),
                label, label, callAction(name, id))
        }
        // OS PiP already owns tap-to-expand. A custom "Open conversation"
        // action changed Flutter state but did not expand the Android PiP
        // task, leaving the last video tile floating over another app.
        // Keep only genuine in-PiP controls; user taps the system PiP tile
        // to expand the full active video call.
        return listOf(
            control("mute", if (lastMuted) "Unmute" else "Mute",
                android.R.drawable.ic_lock_silent_mode),
            control("end", "End call", android.R.drawable.ic_menu_close_clear_cancel),
        )
    }

    private fun pipFailureReason(): String {
        if (Build.VERSION.SDK_INT < 26) return "Android 8 or newer is required for video PiP."
        if (!packageManager.hasSystemFeature(PackageManager.FEATURE_PICTURE_IN_PICTURE))
            return "This Android device does not support picture-in-picture."
        try {
            val ops = getSystemService(Context.APP_OPS_SERVICE) as AppOpsManager
            @Suppress("DEPRECATION")
            val mode = ops.checkOpNoThrow(
                AppOpsManager.OPSTR_PICTURE_IN_PICTURE, applicationInfo.uid, packageName)
            if (mode == AppOpsManager.MODE_IGNORED || mode == AppOpsManager.MODE_ERRORED)
                return "Picture-in-picture is blocked in Android app settings. 'Appear on top' is a different permission."
        } catch (_: Exception) {
            // Device-specific AppOps failures do not imply disabled PiP.
        }
        if (lastIncoming || lastCallId == null || !pipEnabledForCall)
            return "PiP is available only after connecting an active video call."
        if (!activityForeground)
            return "Open LAN Messenger's active video call before starting PiP."
        return "Android did not enter PiP. Try Home from an active video call."
    }

    private fun openPipSettings() {
        // OEMs may expose a dedicated PiP settings screen. Fall back to the
        // app details page when the action is absent; never request overlay.
        val picture = Intent("android.settings.PICTURE_IN_PICTURE_SETTINGS").apply {
            data = Uri.parse("package:$packageName")
        }
        val destination = if (picture.resolveActivity(packageManager) != null) picture
                          else Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS,
                              Uri.parse("package:$packageName"))
        startActivity(destination)
    }

    private fun enterCallPictureInPicture(id: String): Boolean {
        if (Build.VERSION.SDK_INT < 26 || id.isEmpty() ||
            id != lastCallId || !activityForeground || !pipEnabledForCall) {
            Log.w("LANCallTrace", "PiP rejected: no foreground connected video call")
            return false
        }
        return try {
            val params = PictureInPictureParams.Builder()
                .setAspectRatio(Rational(16, 9))
                .setActions(pictureActions(id)).build()
            val entered = enterPictureInPictureMode(params)
            if (!entered) Log.w("LANCallTrace", "System refused PiP transition")
            entered
        } catch (e: Exception) {
            Log.w("LANCallTrace", "PiP transition rejected: ${e.message}")
            false
        }
    }

    override fun onUserLeaveHint() {
        super.onUserLeaveHint()
        // Android 8-11 does not support setAutoEnterEnabled.
        if (Build.VERSION.SDK_INT in 26..30 && pipEnabledForCall &&
            lastVideo && !lastIncoming && lastCallId != null) {
            enterCallPictureInPicture(lastCallId!!)
        }
    }

    override fun onPictureInPictureModeChanged(
        inPip: Boolean, configuration: Configuration
    ) {
        super.onPictureInPictureModeChanged(inPip, configuration)
        Log.i("LANCallTrace", "pip_state_changed active=$inPip")
        callBridge?.invokeMethod("pipState", mapOf("active" to inPip))
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
                    "retryPendingAnswer" -> {
                        // Dart calls this only after its incoming decision
                        // completer is installed; this closes the resume race.
                        val id = call.argument<String>("callId")
                        if (id != null && id == lastCallId) deliverPendingAnswer()
                        result.success(pendingAnswer == id)
                    }
                    "dismissIncoming" -> {
                        // Don't dismiss the accepted call's ongoing controls.
                        if (lastIncoming) {
                            lastCallId = null; lastCaller = null
                            pendingAnswer = null
                            incomingNotificationPosted = false
                            notifications.cancel(7024)
                        }
                        result.success(null)
                    }
                    "dismissCall" -> {
                        notifications.cancel(7024)
                        lastCallId = null; lastCaller = null
                        lastIncoming = false; pendingAnswer = null
                        pipEnabledForCall = false
                        incomingNotificationPosted = false
                        // Disabling future auto-enter does NOT dismiss an
                        // already-open PiP Activity. The call is fully ended:
                        // remove just this floating Activity/task. A new
                        // launcher activation creates a fresh app UI.
                        val closeExistingPip =
                            Build.VERSION.SDK_INT >= 26 && isInPictureInPictureMode
                        if (Build.VERSION.SDK_INT >= 31) {
                            try {
                                setPictureInPictureParams(PictureInPictureParams.Builder()
                                    .setAutoEnterEnabled(false).build())
                            } catch (_: Exception) { }
                        }
                        result.success(null)
                        if (closeExistingPip) {
                            window?.decorView?.post {
                                // Never finish an expanded foreground Activity.
                                if (Build.VERSION.SDK_INT >= 26 &&
                                    isInPictureInPictureMode && lastCallId == null) {
                                    Log.i("LANCallTrace", "ended_call_pip_dismissed")
                                    finish()
                                }
                            }
                        }
                    }
                    "foreground" -> {
                        // Flutter resumed/inactive/paused is NOT authoritative
                        // for the native Activity visibility. A notification
                        // shade or transient permission prompt must not change
                        // the native onStart/onStop state.
                        updateOverlay()
                        result.success(null)
                    }
                    "overlayEnabled" -> result.success(false)
                    "openOverlaySettings" -> {
                        // Historical API kept so prior Dart clients receive
                        // a safe destination. No longer request the unrelated
                        // draw-over-apps permission for video PiP.
                        startActivity(Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS,
                            Uri.parse("package:$packageName")))
                        result.success(null)
                    }
                    "pipDiagnostic" -> result.success(pipFailureReason())
                    "openPipSettings" -> {
                        openPipSettings()
                        result.success(null)
                    }
                    "enterPip" -> result.success(enterCallPictureInPicture(
                        call.argument<String>("callId") ?: ""))
                    "ongoing" -> result.success(showOngoingCall(
                        call.argument<String>("caller") ?: "LAN Messenger",
                        call.argument<String>("callId") ?: "",
                        call.argument<Boolean>("video") ?: false,
                        call.argument<Boolean>("muted") ?: false))
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
                        "openAppInfo" -> {
                            // Android 13+ sideloaded APKs may require the owner to
                            // choose "Allow restricted settings" in App info.
                            // There is no API for the app to grant itself this access.
                            startActivity(Intent(
                                Settings.ACTION_APPLICATION_DETAILS_SETTINGS,
                                Uri.parse("package:$packageName")))
                            result.success(null)
                        }
                        "tap" -> result.success(RemoteTouchService.tap(
                            (call.argument<Number>("x") ?: 0.0).toDouble(),
                            (call.argument<Number>("y") ?: 0.0).toDouble()))
                        "status" -> {
                            val active = call.argument<Boolean>("active") == true
                            val intent = Intent(this, ScreenProjectionService::class.java).apply {
                                action = if (active) "CONTROL_ON" else "CONTROL_OFF"
                            }
                            // The existing projection foreground service must already run.
                            startService(intent)
                            result.success(null)
                        }
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
