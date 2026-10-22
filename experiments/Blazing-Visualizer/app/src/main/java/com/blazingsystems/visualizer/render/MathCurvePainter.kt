package com.blazingsystems.visualizer.render

import android.graphics.*
import com.blazingsystems.visualizer.project.*
import kotlin.math.*
import kotlinx.serialization.json.*

/** Original note-derived curves. Does not trace video or retune the music. */
class MathCurvePainter {
    private val paint = Paint(Paint.ANTI_ALIAS_FLAG)
    private fun alpha(color: Int, amount: Int) = Color.argb(amount.coerceIn(0,255), Color.red(color), Color.green(color), Color.blue(color))

    fun draw(c: Canvas, s: EvaluatedScene, layer: Layer, width: Float, height: Float, tint: Int, intensity: Float) {
        val voices = s.activeNotes.groupBy { it.pitch }.values.map { it.maxBy { n -> n.amplitude } }.sortedBy { it.pitch }.take(12)
        if (voices.isEmpty()) return
        val mode = runCatching { MathVisualMode.valueOf(layer.properties["mode"]?.jsonPrimitive?.content?.uppercase() ?: "LISSAJOUS") }.getOrDefault(MathVisualMode.LISSAJOUS)
        val ratios = voices.map { MusicalMath.ratio(it.pitch, voices.first().pitch) }
        val weights = voices.map { it.amplitude.toDouble().coerceIn(.02,1.0) }
        // At least eight samples per cycle of the highest displayed voice.
        val span = 2*PI*min(4.0,64.0/ratios.max())
        val offset = s.sourceTimeUs/1e6*.38*intensity
        val w = width*.43f; val h = height*(if (s.scene.showEquations) .32f else .43f)
        val hsv = FloatArray(3); Color.colorToHSV(tint,hsv)
        val count = if (mode == MathVisualMode.LISSAJOUS) max(1,voices.size-1) else 1
        for (voice in 0 until count) {
            val pair = if (voices.size <= 1) listOf(1.0) else listOf(1.0,ratios[voice+1])
            val path = Path(); var head = CurvePoint(0.0,0.0)
            for (i in 0..512) {
                val theta = span*i/512+offset
                val point = when (mode) {
                    MathVisualMode.LISSAJOUS -> MusicalMath.point(mode,pair,List(pair.size){1.0},theta)
                    MathVisualMode.ORBITS -> MusicalMath.point(mode,ratios,weights,theta)
                    MathVisualMode.WAVES -> MusicalMath.point(mode,ratios,weights,theta).copy(x = -1+2.0*i/512)
                }
                val x = (point.x*w).toFloat(); val y = (-point.y*h).toFloat()
                if (i == 0) path.moveTo(x,y) else path.lineTo(x,y)
                head = point
            }
            val color = if (voice == 0) tint else Color.HSVToColor(floatArrayOf((hsv[0]+voice*39)%360,hsv[1].coerceAtLeast(.4f),hsv[2]))
            paint.style = Paint.Style.STROKE; paint.strokeCap = Paint.Cap.ROUND; paint.shader = null
            if (intensity > 0f) {
                paint.color = alpha(color,(35*intensity).toInt()); paint.strokeWidth = max(3f,width/80)*intensity
                c.drawPath(path,paint)
            }
            paint.color = alpha(color,220); paint.strokeWidth = max(1.2f,width/250); c.drawPath(path,paint)
            if (intensity > 0f) {
                val x = (head.x*w).toFloat(); val y = (-head.y*h).toFloat(); val radius = max(4f,width*.035f)*intensity
                paint.style = Paint.Style.FILL
                paint.shader = RadialGradient(x,y,radius,intArrayOf(alpha(color,190),Color.TRANSPARENT),null,Shader.TileMode.CLAMP)
                c.drawCircle(x,y,radius,paint); paint.shader = null
                paint.color = Color.WHITE; c.drawCircle(x,y,max(1.5f,width*.005f),paint)
            }
        }
        if (mode == MathVisualMode.ORBITS) {
            paint.style = Paint.Style.STROKE; paint.strokeWidth = max(1f,width/550)
            for (i in voices.indices) {
                val radius = min(w,h)*(.35f+.6f*(i+1)/voices.size)
                paint.color = alpha(tint,30); c.drawCircle(0f,0f,radius,paint)
                if (intensity > 0f) {
                    val angle = offset*ratios[i]
                    paint.style = Paint.Style.FILL; paint.color = alpha(tint,230)
                    c.drawCircle((cos(angle)*radius).toFloat(),(sin(angle)*radius).toFloat(),width*.008f,paint)
                    paint.style = Paint.Style.STROKE
                }
            }
        }
        if (s.scene.showEquations) {
            paint.shader = null; paint.style = Paint.Style.FILL; paint.color = alpha(tint,230)
            paint.typeface = Typeface.MONOSPACE; paint.textAlign = Paint.Align.CENTER; paint.textSize = (width/42).coerceAtLeast(6f)
            val formula = when (mode) {
                MathVisualMode.LISSAJOUS -> "x = cos(θ), yⱼ = sin(rⱼθ)"
                MathVisualMode.ORBITS -> "z(θ) = Σ aⱼ exp(i rⱼθ) / Σ aⱼ"
                MathVisualMode.WAVES -> "y(θ) = Σ aⱼ sin(rⱼθ) / Σ aⱼ"
            }
            c.drawText(formula,0f,height*.36f,paint)
            c.drawText("f(m) = 440 × 2^((m−69)/12); θ is visual phase",0f,height*.42f,paint)
            paint.textSize *= .8f
            val label = if (ratios.size > 6) "r (first 6/${ratios.size}): " else "r: "
            c.drawText(label+ratios.take(6).joinToString(" : "){"%.3f".format(java.util.Locale.US,it)},0f,height*.47f,paint)
        }
    }
}
