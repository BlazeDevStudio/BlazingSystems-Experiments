package com.blazingsystems.visualizer

import com.blazingsystems.visualizer.audio.PcmResampler
import kotlin.math.*
import org.junit.Assert.*
import org.junit.Test

class PcmResamplerKernelTest {
    @Test fun cachedPhasesPreserveLegacyFilterAcrossStereoChunksAndTail() {
        // 48 kHz visits all 147 fractional phases; 44,101 Hz exceeds the bounded cache.
        for (rate in listOf(22050, 44100, 48000, 44101)) {
            val frames = 9001
            val input = FloatArray(frames * 2) { i ->
                val t = (i / 2).toDouble() / rate
                (.37 * sin(2 * PI * 330 * t + (i % 2) * .7) +
                    .21 * sin(2 * PI * 4100 * t) +
                    .13 * cos(2 * PI * 16000 * t + (i % 2))).toFloat()
            }
            val expected = legacy(input, rate, 2)
            val all = PcmResampler(rate, 2).let { it.feed(input) + it.feed(FloatArray(0), true) }
            val streaming = PcmResampler(rate, 2)
            val pieces = mutableListOf<FloatArray>()
            val chunkFrames = intArrayOf(1, 7, 1152, 2, 31, 13, 2048, 5)
            var first = 0
            var chunk = 0
            while (first < frames) {
                val last = minOf(frames, first + chunkFrames[chunk++ % chunkFrames.size])
                pieces += streaming.feed(input.copyOfRange(first * 2, last * 2))
                first = last
            }
            pieces += streaming.feed(FloatArray(0), true)
            val chunked = FloatArray(pieces.sumOf { it.size })
            var next = 0
            pieces.forEach { it.copyInto(chunked, next); next += it.size }
            assertEquals("output clock at $rate Hz", ceil(frames * 22050.0 / rate).toInt(), all.size)
            assertArrayEquals("legacy filter at $rate Hz", expected, all, .000001f)
            assertArrayEquals("chunk boundaries at $rate Hz", all, chunked, .000001f)
        }
    }

    @Test fun downsamplingStillRejectsFrequenciesThatWouldAliasIntoNotes() {
        for (rate in listOf(44100, 48000)) {
            fun convertedRms(hz: Int): Double {
                val input = FloatArray(rate / 4) { (.8 * sin(2 * PI * hz * it / rate)).toFloat() }
                val converter = PcmResampler(rate, 1)
                val output = converter.feed(input) + converter.feed(FloatArray(0), true)
                return sqrt(output.drop(64).dropLast(64).sumOf { it.toDouble() * it } / (output.size - 128))
            }
            assertTrue("audible band retained at $rate Hz", convertedRms(1000) > .55)
            assertTrue("16 kHz rejected at $rate Hz", convertedRms(16000) < .002)
        }
    }

    /** Independent one-shot form of the original 64-tap filter, without any phase cache. */
    private fun legacy(input: FloatArray, rate: Int, channels: Int): FloatArray {
        val mono = FloatArray(input.size / channels) { frame ->
            var sum = 0f
            repeat(channels) { sum += input[frame * channels + it] }
            sum / channels
        }
        val step = rate.toDouble() / 22050
        val cutoff = min(1.0, 22050.0 / rate) * .94
        return FloatArray(ceil(mono.size / step).toInt()) { produced ->
            if (rate == 22050) mono[produced]
            else {
                val position = produced * step
                val center = floor(position).toInt()
                var sum = 0.0
                var weightSum = 0.0
                for (tap in -31..32) {
                    val distance = position - (center + tap)
                    val x = distance * cutoff
                    val sinc = if (abs(x) < 1e-10) 1.0 else sin(PI * x) / (PI * x)
                    val window = if (abs(distance) <= 32) .5 + .5 * cos(PI * distance / 32) else 0.0
                    val weight = cutoff * sinc * window
                    if (center + tap in mono.indices) sum += mono[center + tap] * weight
                    weightSum += weight
                }
                (sum / weightSum).toFloat()
            }
        }
    }
}
