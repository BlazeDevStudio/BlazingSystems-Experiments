package com.blazingsystems.visualizer.render

import kotlin.math.*

enum class MathVisualMode { LISSAJOUS, ORBITS, WAVES }
data class CurvePoint(val x: Double, val y: Double)

/** Equal temperament; visual phase is intentionally slowed, never used to retune audio. */
object MusicalMath {
    fun frequency(midi: Int, a4: Double = 440.0): Double {
        require(midi in 0..127 && a4.isFinite() && a4 > 0)
        return a4 * 2.0.pow((midi - 69) / 12.0)
    }

    fun ratio(midi: Int, referenceMidi: Int) = frequency(midi) / frequency(referenceMidi)

    fun point(mode: MathVisualMode, ratios: List<Double>, weights: List<Double>, theta: Double): CurvePoint {
        require(ratios.isNotEmpty() && ratios.size == weights.size && ratios.size <= 12)
        require(theta.isFinite() && ratios.all { it.isFinite() && it > 0 } && weights.all { it.isFinite() && it >= 0 })
        if (mode == MathVisualMode.LISSAJOUS) {
            return CurvePoint(cos(ratios.first() * theta), sin(ratios.getOrElse(1) { ratios.first() } * theta))
        }
        val total = weights.sum().coerceAtLeast(1e-9)
        var x = 0.0; var y = 0.0
        for (i in ratios.indices) {
            x += weights[i] * cos(ratios[i] * theta)
            y += weights[i] * sin(ratios[i] * theta)
        }
        return CurvePoint(x / total, y / total)
    }
}
