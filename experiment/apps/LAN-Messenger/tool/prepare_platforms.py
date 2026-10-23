"""Patch only generated Flutter platform runners; never touches application source."""
from pathlib import Path
import re

root = Path(__file__).resolve().parents[1]
manifest = root / 'android/app/src/main/AndroidManifest.xml'
if manifest.exists():
    text = manifest.read_text(encoding='utf-8')
    permissions = [
        'android.permission.INTERNET',
        'android.permission.ACCESS_WIFI_STATE',
        'android.permission.ACCESS_NETWORK_STATE',
        'android.permission.CHANGE_WIFI_MULTICAST_STATE',
        'android.permission.RECORD_AUDIO',
        'android.permission.CAMERA',
        'android.permission.FOREGROUND_SERVICE',
        'android.permission.FOREGROUND_SERVICE_CONNECTED_DEVICE',
        'android.permission.POST_NOTIFICATIONS',
    ]
    missing = ''.join(f'    <uses-permission android:name="{p}" />\n' for p in permissions
                      if f'android:name="{p}"' not in text)
    text = text.replace('<application', missing + '    <application', 1)
    text = re.sub(r'android:label="[^"]*"', 'android:label="LAN Messenger"', text, count=1)
    text = text.replace('<application', '<application android:usesCleartextTraffic="true"', 1)
    service = ('        <service android:name="de.julianassmann.flutter_background.IsolateHolderService" '
               'android:exported="false" android:foregroundServiceType="connectedDevice" />\n')
    if 'de.julianassmann.flutter_background.IsolateHolderService' not in text:
        text = text.replace('</application>', service + '    </application>', 1)
    manifest.write_text(text, encoding='utf-8')
    print(f'Patched {manifest}')

    main_activity = root / 'android/app/src/main/kotlin/com/example/lan_messenger/MainActivity.kt'
    main_activity.parent.mkdir(parents=True, exist_ok=True)
    # Native NotificationManager is intentionally used instead of a heavy plugin:
    # heads-up notifications need no network, account or background polling SDK.
    main_activity.write_text(r'''package com.example.lan_messenger

import android.Manifest
import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.media.AudioAttributes
import android.net.Uri
import android.net.wifi.WifiManager
import android.os.Build
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel

class MainActivity : FlutterActivity() {
    private var lock: WifiManager.MulticastLock? = null
    private var nextNotification = 1000
    private val notifications by lazy {
        getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
    }
    private fun channel(kind: String): String = "lan_v023_" + kind
    private fun enableNotifications() {
        if (Build.VERSION.SDK_INT >= 33 && checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS)
              != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(arrayOf(Manifest.permission.POST_NOTIFICATIONS), 7811)
        }
    }
    private fun showNotification(kind: String, title: String, body: String) {
        if (Build.VERSION.SDK_INT >= 33 && checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS)
              != PackageManager.PERMISSION_GRANTED) return
        val event = if (kind in listOf("call", "video_call", "message", "file")) kind else "message"
        val name = when(event) {
            "call" -> "Voice calls"
            "video_call" -> "Video calls"
            "file" -> "Files"
            else -> "Messages"
        }
        val id = channel(event)
        val tone = resources.getIdentifier(event, "raw", packageName)
        val intent = Intent(this, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_CLEAR_TOP or Intent.FLAG_ACTIVITY_SINGLE_TOP
        }
        val pending = PendingIntent.getActivity(this, 0, intent,
              PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)
        val builder = if (Build.VERSION.SDK_INT >= 26) {
            val ch = NotificationChannel(id, "LAN Messenger $name", NotificationManager.IMPORTANCE_HIGH)
            ch.description = "Offline local network $name"
            if (tone != 0) {
                ch.setSound(Uri.parse("android.resource://$packageName/$tone"),
                    AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_NOTIFICATION).build())
            }
            notifications.createNotificationChannel(ch)
            Notification.Builder(this, id)
        } else {
            @Suppress("DEPRECATION")
            Notification.Builder(this).setPriority(Notification.PRIORITY_HIGH)
        }
        builder.setContentTitle(title).setContentText(body).setSmallIcon(android.R.drawable.stat_notify_chat)
            .setContentIntent(pending).setAutoCancel(true)
        notifications.notify(++nextNotification, builder.build())
    }

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, "lan_messenger/notifications")
          .setMethodCallHandler { call, result ->
            try {
                when (call.method) {
                  "setup" -> { enableNotifications(); result.success(null) }
                  "show" -> {
                    showNotification(call.argument<String>("kind") ?: "message",
                        call.argument<String>("title") ?: "LAN Messenger",
                        call.argument<String>("body") ?: "Local network notification")
                    result.success(null)
                  }
                  else -> result.notImplemented()
                }
            } catch (e: Exception) { result.error("NOTIFY", e.message, null) }
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
                } catch (e: Exception) {
                    result.error("MULTICAST_LOCK", e.message, null)
                }
            }
    }
    override fun onDestroy() {
        lock?.let { if (it.isHeld) it.release() }
        lock = null
        super.onDestroy()
    }
}
''', encoding='utf-8')

    # Audio tones are generated original assets; Android plays these through
    # high-priority notification channels even when Flutter is not foregrounded.
    import shutil
    raw = root / 'android/app/src/main/res/raw'
    raw.mkdir(parents=True, exist_ok=True)
    for key in ('call','video_call','message','file'):
        source = root / 'assets/sounds' / (key+'.wav')
        if source.exists():
            shutil.copy2(source, raw / (key+'.wav'))

window = root / 'windows/runner/main.cpp'
if window.exists():
    text = window.read_text(encoding='utf-8')
    text = text.replace('L"lan_messenger"', 'L"LAN Messenger"')
    window.write_text(text, encoding='utf-8')
    print(f'Patched {window}')

# Flutter create may scaffold a demo widget_test referencing MyApp. This is
# not our application and must not replace the real protocol/crypto tests.
demo = root / 'test/widget_test.dart'
if demo.exists() and 'pumpWidget(const MyApp())' in demo.read_text(encoding='utf-8'):
    demo.unlink()
    print(f'Removed default template test {demo}')