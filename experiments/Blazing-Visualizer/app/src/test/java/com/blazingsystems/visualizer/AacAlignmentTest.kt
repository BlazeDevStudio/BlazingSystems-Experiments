package com.blazingsystems.visualizer

import com.blazingsystems.visualizer.export.AacAlignment
import org.junit.Assert.*
import org.junit.Test

class AacAlignmentTest {
    @Test
    fun measuresCodecPrimingWithoutReadingMusic() {
        for (rate in listOf(22050, 44100, 48000)) for (delay in listOf(0, 1024, 2048)) {
            val prefix = AacAlignment.prefix(rate)
            val decoded =
                FloatArray(prefix.size + delay + 4096) { i ->
                    if (i - delay in prefix.indices) prefix[i - delay] * .97f else 0f
                }
            assertEquals("rate $rate", delay, AacAlignment.measureDelay(decoded, rate))
        }
    }

    @Test
    fun missingCalibrationIsRejected() {
        assertThrows(IllegalArgumentException::class.java) {
            AacAlignment.measureDelay(FloatArray(20000), 44100)
        }
    }

    @Test
    fun prefixPacketsAreDroppedAndMusicStartsAtZero() {
        val shift = (8192 + 2048) * 1_000_000L / 22050
        assertNull(AacAlignment.sourcePts(0, shift, 1_000_000))
        assertEquals(0L, AacAlignment.sourcePts(shift, shift, 1_000_000))
        assertNull(AacAlignment.sourcePts(shift + 1_000_000, shift, 1_000_000))
    }
}
