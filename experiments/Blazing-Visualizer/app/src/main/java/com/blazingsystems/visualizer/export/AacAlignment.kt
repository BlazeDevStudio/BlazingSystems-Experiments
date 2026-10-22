package com.blazingsystems.visualizer.export

import kotlin.math.*

/** A known prefix lets us measure the device's AAC priming instead of guessing its delay. */
object AacAlignment {
    const val PREFIX_FRAMES = 8192
    const val MARKER_START = 2048
    const val MARKER_SIZE = 4096

    fun prefix(sampleRate: Int): FloatArray =
        FloatArray(PREFIX_FRAMES) { i ->
            val n = i - MARKER_START
            if (n !in 0 until MARKER_SIZE) 0f
            else {
                val t = n.toDouble() / sampleRate
                val duration = MARKER_SIZE.toDouble() / sampleRate
                val high = min(6000.0, sampleRate * .35)
                (.25 *
                        sin(2 * PI * (200 * t + (high - 200) * t * t / (2 * duration))) *
                        (.5 - .5 * cos(2 * PI * n / (MARKER_SIZE - 1))))
                    .toFloat()
            }
        }

    fun measureDelay(decoded: FloatArray, sampleRate: Int): Int {
        val known = prefix(sampleRate)
        fun score(delay: Int): Double {
            val start = MARKER_START + delay
            if (start < 0 || start + MARKER_SIZE > decoded.size) return -1.0
            var xy = 0.0
            var xx = 0.0
            var yy = 0.0
            for (i in 0 until MARKER_SIZE step 8) {
                val x = known[MARKER_START + i].toDouble()
                val y = decoded[start + i].toDouble()
                xy += x * y
                xx += x * x
                yy += y * y
            }
            return xy / sqrt(xx * yy).coerceAtLeast(1e-12)
        }
        var best = -1.0
        var delay = 0
        for (d in -2048..8192 step 8) {
            val s = score(d)
            if (s > best) {
                best = s
                delay = d
            }
        }
        val coarse = delay
        for (d in coarse - 8..coarse + 8) {
            val s = score(d)
            if (s > best) {
                best = s
                delay = d
            }
        }
        val blocks = (delay / 1024.0).roundToInt() * 1024
        require(best > .75 && abs(blocks - delay) <= 64) {
            "This AAC encoder could not be aligned accurately. Choose another device or encoder."
        }
        return blocks
    }

    fun sourcePts(encodedPts: Long, shiftUs: Long, durationUs: Long): Long? {
        val t = encodedPts - shiftUs
        return t.takeIf { it >= 0 && it < durationUs }
    }
}
