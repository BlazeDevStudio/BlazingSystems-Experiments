package com.example.lan_messenger

import android.accessibilityservice.AccessibilityService
import android.accessibilityservice.GestureDescription
import android.graphics.Path
import android.view.accessibility.AccessibilityEvent
import android.content.res.Resources
import android.os.Build

/**
 * Optional assistive touch bridge for owner-approved LAN Messenger screen sharing.
 * The phone owner must MANUALLY enable this service in Android Accessibility.
 * Only single taps are supported. The Dart call controller verifies encrypted
 * peer identity, explicit per-call consent, timeout, and active projection.
 */
class RemoteTouchService : AccessibilityService() {
    companion object {
        @Volatile var active: RemoteTouchService? = null
        fun tap(normalizedX: Double, normalizedY: Double): Boolean {
            val service = active ?: return false
            if (Build.VERSION.SDK_INT < 24 ||
                !normalizedX.isFinite() || !normalizedY.isFinite() ||
                normalizedX < 0.0 || normalizedX > 1.0 ||
                normalizedY < 0.0 || normalizedY > 1.0) return false
            val metrics = Resources.getSystem().displayMetrics
            val width = metrics.widthPixels
            val height = metrics.heightPixels
            if (width <= 1 || height <= 1) return false
            val x = (normalizedX * (width - 1)).toFloat()
            val y = (normalizedY * (height - 1)).toFloat()
            val path = Path().apply { moveTo(x, y) }
            val click = GestureDescription.StrokeDescription(path, 0, 70)
            return service.dispatchGesture(
                GestureDescription.Builder().addStroke(click).build(),
                null, null)
        }
    }

    override fun onServiceConnected() {
        super.onServiceConnected()
        active = this
    }
    override fun onAccessibilityEvent(event: AccessibilityEvent?) {}
    override fun onInterrupt() {}
    override fun onDestroy() {
        if (active === this) active = null
        super.onDestroy()
    }
}
