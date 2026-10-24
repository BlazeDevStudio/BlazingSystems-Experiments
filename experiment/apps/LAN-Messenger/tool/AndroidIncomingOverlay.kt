package com.example.lan_messenger

import android.content.Context
import android.graphics.Color
import android.graphics.PixelFormat
import android.graphics.drawable.GradientDrawable
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
 * User-authorized overlay for an incoming call while the Flutter Activity is
 * hidden. It never requests keyboard focus and never simulates UI interactions.
 * CallStyle notifications remain the fallback when overlay access is disabled.
 */
class AndroidIncomingOverlay(private val context: Context) {
    private val manager = context.getSystemService(Context.WINDOW_SERVICE) as WindowManager
    private var view: View? = null

    private fun dp(n: Int) = (n * context.resources.displayMetrics.density + .5f).toInt()

    fun permitted() = Build.VERSION.SDK_INT >= 26 && Settings.canDrawOverlays(context)

    fun dismiss() {
        val old = view ?: return
        view = null
        try { manager.removeView(old) } catch (_: Exception) {}
    }

    fun show(name: String, video: Boolean, onAnswer: () -> Unit,
             onDecline: () -> Unit): Boolean {
        if (!permitted()) return false
        dismiss()
        return try {
            val panel = LinearLayout(context).apply {
                orientation = LinearLayout.VERTICAL
                setPadding(dp(14), dp(11), dp(14), dp(12))
                background = GradientDrawable().apply {
                    setColor(Color.rgb(20, 44, 78))
                    cornerRadius = dp(17).toFloat()
                    setStroke(dp(1), Color.rgb(68, 111, 157))
                }
            }
            val title = TextView(context).apply {
                text = name.take(80)
                textSize = 17f
                setTextColor(Color.WHITE)
                isSingleLine = true
            }
            val subtitle = TextView(context).apply {
                text = if (video) "Incoming video • Drag to move"
                    else "Incoming voice • Drag to move"
                textSize = 12f
                setTextColor(Color.LTGRAY)
            }
            val buttons = LinearLayout(context).apply {
                orientation = LinearLayout.HORIZONTAL
                gravity = Gravity.CENTER
            }
            val decline = Button(context).apply {
                text = "Decline"
                setOnClickListener { dismiss(); onDecline() }
            }
            val answer = Button(context).apply {
                text = "Answer"
                setOnClickListener { dismiss(); onAnswer() }
            }
            buttons.addView(decline, LinearLayout.LayoutParams(0, dp(48), 1f))
            buttons.addView(answer, LinearLayout.LayoutParams(0, dp(48), 1f))
            panel.addView(title)
            panel.addView(subtitle)
            panel.addView(buttons)
            val params = WindowManager.LayoutParams(
                dp(320), WindowManager.LayoutParams.WRAP_CONTENT,
                WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY,
                WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or
                    WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL,
                PixelFormat.TRANSLUCENT
            ).apply {
                gravity = Gravity.TOP or Gravity.END
                x = dp(12)
                y = dp(56)
            }
            var x = 0f
            var y = 0f
            var startRight = 0
            var startTop = 0
            val drag = View.OnTouchListener { _, event ->
                when (event.actionMasked) {
                    MotionEvent.ACTION_DOWN -> {
                        x = event.rawX
                        y = event.rawY
                        startRight = params.x
                        startTop = params.y
                        true
                    }
                    MotionEvent.ACTION_MOVE -> {
                        params.x = (startRight - (event.rawX - x)).toInt()
                        params.y = (startTop + (event.rawY - y)).toInt()
                        try { manager.updateViewLayout(panel, params) } catch (_: Exception) {}
                        true
                    }
                    else -> false
                }
            }
            title.setOnTouchListener(drag)
            subtitle.setOnTouchListener(drag)
            manager.addView(panel, params)
            view = panel
            true
        } catch (_: Exception) {
            dismiss()
            false
        }
    }
}
