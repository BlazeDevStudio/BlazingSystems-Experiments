package com.example.lan_messenger

import android.content.Context
import android.graphics.Color
import android.graphics.PixelFormat
import android.graphics.Typeface
import android.os.Build
import android.provider.Settings
import android.view.Gravity
import android.view.MotionEvent
import android.view.View
import android.view.WindowManager
import android.widget.Button
import android.widget.LinearLayout
import android.widget.TextView

/**
 * User-consented TYPE_APPLICATION_OVERLAY for calls while the activity is not
 * visible. Does not create or steal a task, and cannot bypass OS overlay policy.
 * The ongoing notification remains the reliable fallback without permission.
 */
class AndroidCallOverlay(
    private val context: Context,
    private val action: (String, String) -> Unit
) {
    private val windows = context.getSystemService(Context.WINDOW_SERVICE) as WindowManager
    private var root: View? = null
    private var params: WindowManager.LayoutParams? = null
    private var activeCallId: String? = null

    fun permitted(): Boolean = Build.VERSION.SDK_INT >= 26 &&
        Settings.canDrawOverlays(context)

    fun dismiss() {
        val window = root ?: return
        root = null
        params = null
        activeCallId = null
        try { windows.removeView(window) } catch (_: Exception) { }
    }

    fun show(caller: String, callId: String, video: Boolean,
             incoming: Boolean, muted: Boolean): Boolean {
        if (!permitted() || callId.isBlank() || caller.isBlank()) return false
        dismiss()
        val id = callId
        val density = context.resources.displayMetrics.density
        fun px(value: Int) = (value * density + 0.5f).toInt()
        val layout = LinearLayout(context).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(px(14), px(12), px(14), px(12))
            setBackgroundColor(Color.rgb(22, 43, 75))
            elevation = px(12).toFloat()
        }
        val heading = TextView(context).apply {
            text = caller.take(60)
            textSize = 16f
            setTextColor(Color.WHITE)
            setTypeface(null, Typeface.BOLD)
            setPadding(0, 0, 0, px(4))
        }
        val caption = TextView(context).apply {
            text = if (incoming) {
                if (video) "Incoming video call" else "Incoming voice call"
            } else if (video) "Video call connected — open video" else "Voice call connected"
            textSize = 12f
            setTextColor(Color.rgb(185, 214, 236))
        }
        layout.addView(heading)
        layout.addView(caption)
        val buttons = LinearLayout(context).apply {
            orientation = LinearLayout.HORIZONTAL
            setPadding(0, px(12), 0, 0)
        }
        fun addButton(label: String, result: String, tint: Int) {
            val button = Button(context).apply {
                text = label
                isAllCaps = false
                textSize = 12f
                setTextColor(Color.WHITE)
                setBackgroundColor(tint)
                setOnClickListener {
                    action(result, id)
                    // Dismiss only for finished incoming choice or call end;
                    // keep the ongoing bar after muting.
                    if (incoming || result == "end" || result == "open") dismiss()
                }
            }
            val lp = LinearLayout.LayoutParams(0, px(42), 1f)
            lp.marginEnd = px(6)
            buttons.addView(button, lp)
        }
        if (incoming) {
            addButton("Decline", "decline", Color.rgb(165, 37, 65))
            addButton("Answer", "answer", Color.rgb(17, 132, 91))
        } else {
            addButton(if (muted) "Unmute" else "Mute", "mute", Color.rgb(66, 91, 126))
            addButton("End", "end", Color.rgb(165, 37, 65))
            addButton(if (video) "Open video" else "Thread", "open", Color.rgb(37, 104, 184))
        }
        layout.addView(buttons)
        val display = context.resources.displayMetrics
        val p = WindowManager.LayoutParams(
            px(330), WindowManager.LayoutParams.WRAP_CONTENT,
            WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY,
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or
                WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL or
                WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN,
            PixelFormat.TRANSLUCENT
        ).apply {
            gravity = Gravity.TOP or Gravity.START
            x = (display.widthPixels - px(346)).coerceAtLeast(0)
            y = (display.heightPixels - px(245)).coerceAtLeast(0)
        }
        var x0 = 0
        var y0 = 0
        var touchX = 0f
        var touchY = 0f
        heading.setOnTouchListener { _: View, event: MotionEvent ->
            when (event.actionMasked) {
                MotionEvent.ACTION_DOWN -> {
                    x0 = p.x; y0 = p.y
                    touchX = event.rawX; touchY = event.rawY
                    true
                }
                MotionEvent.ACTION_MOVE -> {
                    p.x = (x0 + (event.rawX - touchX).toInt()).coerceAtLeast(0)
                    p.y = (y0 + (event.rawY - touchY).toInt()).coerceAtLeast(0)
                    try { windows.updateViewLayout(layout, p) } catch (_: Exception) { }
                    true
                }
                else -> true
            }
        }
        return try {
            windows.addView(layout, p)
            root = layout
            params = p
            activeCallId = id
            true
        } catch (_: Exception) {
            root = null; params = null; activeCallId = null
            false
        }
    }

    fun isFor(id: String?): Boolean = id != null && activeCallId == id
}
