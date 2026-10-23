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
    ]
    missing = ''.join(f'    <uses-permission android:name="{p}" />\n' for p in permissions
                      if f'android:name="{p}"' not in text)
    text = text.replace('<application', missing + '    <application', 1)
    text = re.sub(r'android:label="[^"]*"', 'android:label="LAN Messenger"', text, count=1)
    text = text.replace('<application', '<application android:usesCleartextTraffic="true"', 1)
    manifest.write_text(text, encoding='utf-8')
    print(f'Patched {manifest}')

    main_activity = root / 'android/app/src/main/kotlin/com/example/lan_messenger/MainActivity.kt'
    main_activity.parent.mkdir(parents=True, exist_ok=True)
    main_activity.write_text(r'''package com.example.lan_messenger

import android.content.Context
import android.net.wifi.WifiManager
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel

class MainActivity : FlutterActivity() {
    private var lock: WifiManager.MulticastLock? = null

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
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

window = root / 'windows/runner/main.cpp'
if window.exists():
    text = window.read_text(encoding='utf-8')
    text = text.replace('L"lan_messenger"', 'L"LAN Messenger"')
    window.write_text(text, encoding='utf-8')
    print(f'Patched {window}')