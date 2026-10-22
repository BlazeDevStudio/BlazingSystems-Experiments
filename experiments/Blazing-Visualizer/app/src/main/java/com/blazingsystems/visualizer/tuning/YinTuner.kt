package com.blazingsystems.visualizer.tuning

import java.util.ArrayDeque
import kotlin.math.*

/** YIN (de Cheveigné and Kawahara, JASA 111(4), 2002), for one sounding note. */
data class PitchReading(
    val frequencyHz: Double,
    val midi: Int,
    val cents: Double,
    val confidence: Double,
)

object YinTuner {
    private const val MIN_HZ = 65.0
    private const val MAX_HZ = 1100.0

    fun fromHz(frequency: Double, a4Hz: Double, confidence: Double): PitchReading {
        require(frequency.isFinite() && frequency in MIN_HZ..MAX_HZ)
        require(a4Hz in 400.0..480.0 && confidence.isFinite() && confidence in 0.0..1.0)
        val fractional = 69 + 12 * log2(frequency / a4Hz)
        val midi = fractional.roundToInt()
        return PitchReading(frequency, midi, 100 * (fractional - midi), confidence)
    }

    fun estimate(samples: ShortArray, rate: Int, a4Hz: Double = 440.0): PitchReading? {
        require(samples.size >= 1024 && rate > 0 && a4Hz in 400.0..480.0)
        val mean = samples.sumOf { it.toDouble() } / samples.size / 32768
        val s = DoubleArray(samples.size) { samples[it] / 32768.0 - mean }
        if (sqrt(s.sumOf { it * it } / s.size) < 0.012) return null
        val minTau = (rate / MAX_HZ).toInt().coerceAtLeast(2)
        val maxTau = (rate / MIN_HZ).toInt().coerceAtMost(samples.size / 2)
        if (maxTau <= minTau) return null
        val window = (samples.size - maxTau).coerceAtMost(2048)
        val difference = DoubleArray(maxTau + 1)
        for (tau in 1..maxTau) {
            var total = 0.0
            for (i in 0 until window) {
                val d = s[i] - s[i + tau]
                total += d * d
            }
            difference[tau] = total
        }
        val normalized = DoubleArray(maxTau + 1) { 1.0 }
        var cumulative = 0.0
        for (tau in 1..maxTau) {
            cumulative += difference[tau]
            if (cumulative > 0) normalized[tau] = difference[tau] * tau / cumulative
        }
        var candidate = -1
        var tau = minTau
        while (tau <= maxTau) {
            if (normalized[tau] < 0.13) {
                while (tau + 1 <= maxTau && normalized[tau + 1] < normalized[tau]) tau++
                candidate = tau
                break
            }
            tau++
        }
        if (candidate < 0) return null
        // A dominant second harmonic can create an early minimum with a measurable residual.
        // Only prefer its doubled period when that residual almost disappears. A pure sine's
        // first minimum is already near zero, so it must not be shifted down an octave.
        if (candidate * 2 + 2 <= maxTau && normalized[candidate] > .02) {
            val longer = (candidate * 2 - 2..candidate * 2 + 2).minBy { normalized[it] }
            if (normalized[longer] < normalized[candidate] * .25) candidate = longer
        }
        val confidence = (1 - normalized[candidate]).coerceIn(0.0, 1.0)
        if (confidence < 0.85) return null
        val refined = if (candidate in 2 until maxTau) {
            val left = normalized[candidate - 1]
            val mid = normalized[candidate]
            val right = normalized[candidate + 1]
            val denominator = 2 * (left - 2 * mid + right)
            candidate + if (abs(denominator) < 1e-10) 0.0
                else ((left - right) / denominator).coerceIn(-.5, .5)
        } else candidate.toDouble()
        val frequency = rate / refined
        if (frequency !in MIN_HZ..MAX_HZ || !frequency.isFinite()) return null
        return fromHz(frequency, a4Hz, confidence)
    }
}

/** Median smoothing follows a changed note immediately instead of retaining the old string. */
internal class PitchSmoother {
    private val history = ArrayDeque<Double>()

    fun update(reading: PitchReading?, a4Hz: Double): PitchReading? {
        if (reading == null) {
            history.clear()
            return null
        }
        val previous = history.peekLast()
        if (previous != null && abs(1200 * log2(reading.frequencyHz / previous)) > 80) {
            history.clear()
        }
        history.addLast(reading.frequencyHz)
        if (history.size > 5) history.removeFirst()
        val median = history.toList().sorted()[history.size / 2]
        return YinTuner.fromHz(median, a4Hz, reading.confidence)
    }
}
