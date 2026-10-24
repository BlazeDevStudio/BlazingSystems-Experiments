package com.blazingsystems.visualizer.audio

import kotlin.math.*

/** Bounded, streaming windowed-sinc low-pass resampling with an absolute sample clock. */
class PcmResampler(val sampleRate: Int, val channels: Int, val targetRate: Int = 22050) {
    private data class Kernel(val weights: DoubleArray, val weightSum: Double)

    private var buffer = FloatArray(0)
    private var base = 0L
    private var received = 0L
    private var produced = 0L
    private var ended = false
    private val kernels = object : LinkedHashMap<Int, Kernel>(16, .75f, true) {
        override fun removeEldestEntry(eldest: MutableMap.MutableEntry<Int, Kernel>?): Boolean = size > 512
    }

    init {
        require(sampleRate > 0 && channels in 1..8 && targetRate > 0)
    }

    fun feed(interleaved: FloatArray, end: Boolean = false): FloatArray {
        check(!ended)
        require(interleaved.size % channels == 0)
        val mono =
            FloatArray(interleaved.size / channels) { frame ->
                var sum = 0f
                repeat(channels) { sum += interleaved[frame * channels + it] }
                sum / channels
            }
        buffer += mono
        received += mono.size
        val step = sampleRate.toDouble() / targetRate
        val maxCount =
            if (end) ceil(received / step).toLong()
            else max(0L, ceil((received - 32) / step).toLong())
        val output = FloatArray((maxCount - produced).coerceAtLeast(0).toInt())
        val cutoff = min(1.0, targetRate.toDouble() / sampleRate) * .94
        output.indices.forEach { index ->
            if (sampleRate == targetRate) output[index] = buffer[(produced - base).toInt()]
            else {
                val numerator = produced * sampleRate
                val center = numerator / targetRate
                val phase = (numerator % targetRate).toInt()
                // Integer clocks give 44.1 kHz one phase and 48 kHz 147 phases at 22.05 kHz.
                val kernel = kernels.getOrPut(phase) {
                    val fraction = phase.toDouble() / targetRate
                    var weightSum = 0.0
                    val weights = DoubleArray(64) { tapIndex ->
                        val distance = fraction - (tapIndex - 31)
                        val x = distance * cutoff
                        val sinc = if (abs(x) < 1e-10) 1.0 else sin(PI * x) / (PI * x)
                        val window = if (abs(distance) <= 32) .5 + .5 * cos(PI * distance / 32) else 0.0
                        (cutoff * sinc * window).also { weightSum += it }
                    }
                    Kernel(weights, weightSum)
                }
                var sum = 0.0
                for (tapIndex in kernel.weights.indices) {
                    val relative = center + tapIndex - 31 - base
                    if (relative >= 0 && relative < buffer.size)
                        sum += buffer[relative.toInt()] * kernel.weights[tapIndex]
                }
                output[index] = (sum / kernel.weightSum).toFloat()
            }
            produced++
        }
        val keep = max(base, produced * sampleRate / targetRate - 32).coerceAtMost(received)
        buffer = buffer.copyOfRange((keep - base).toInt(), buffer.size)
        base = keep
        ended = end
        return output
    }
}
