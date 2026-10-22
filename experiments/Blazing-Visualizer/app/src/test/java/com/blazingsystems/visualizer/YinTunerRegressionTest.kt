package com.blazingsystems.visualizer

import com.blazingsystems.visualizer.tuning.PitchSmoother
import com.blazingsystems.visualizer.tuning.YinTuner
import java.util.Random
import kotlin.math.*
import org.junit.Assert.*
import org.junit.Test

class YinTunerRegressionTest {
    private val rate = 22050
    private val strings = listOf(82.4069, 110.0, 146.8324, 195.9977, 246.9417, 329.6276)

    private fun tone(frequency: Double, harmonic: Double = 0.0, phase: Double = .37): ShortArray =
        ShortArray(4096) { i ->
            val angle = 2 * PI * frequency * i / rate + phase
            ((sin(angle) + harmonic * sin(2 * angle)) * 24_000 / (1 + harmonic))
                .toInt().toShort()
        }

    @Test
    fun dominantSecondHarmonicRetainsLowGuitarFundamental() {
        for (frequency in strings.take(2)) for (harmonic in listOf(4.0, 8.0)) {
            for (detune in listOf(-20, 0, 20)) {
                val expected = frequency * 2.0.pow(detune / 1200.0)
                val reading = YinTuner.estimate(tone(expected, harmonic), rate)
                assertNotNull("No reading for $expected Hz with harmonic $harmonic", reading)
                assertTrue(
                    "Octave error: expected $expected Hz, received ${reading!!.frequencyHz}",
                    abs(1200 * log2(reading.frequencyHz / expected)) < 3,
                )
            }
        }
    }

    @Test
    fun pureSinesNeverSelectASubharmonic() {
        for (frequency in strings + listOf(65.5, 440.0, 880.0, 1080.0)) {
            for (phase in listOf(0.0, .7)) {
                val reading = YinTuner.estimate(tone(frequency, phase = phase), rate)
                assertNotNull("No reading for pure $frequency Hz", reading)
                assertTrue(
                    "Pure tone $frequency Hz became ${reading!!.frequencyHz}",
                    abs(1200 * log2(reading.frequencyHz / frequency)) < 4,
                )
            }
        }
    }

    @Test
    fun sixStringsRemainAccurateWithSmallDetuning() {
        for (frequency in strings) for (cents in listOf(-40, -15, 0, 17, 40)) {
            val expected = frequency * 2.0.pow(cents / 1200.0)
            val reading = YinTuner.estimate(tone(expected), rate)
            assertNotNull(reading)
            assertTrue(abs(1200 * log2(reading!!.frequencyHz / expected)) < 3)
        }
    }

    @Test
    fun silenceAndSeededBroadbandNoiseDoNotBecomeNotes() {
        assertNull(YinTuner.estimate(ShortArray(4096), rate))
        val random = Random(1701)
        repeat(8) {
            val noise = ShortArray(4096) { (random.nextInt(24_001) - 12_000).toShort() }
            assertNull(YinTuner.estimate(noise, rate))
        }
    }

    @Test
    fun pitchMappingIsMonotonicAndValidatesItsSupportedRange() {
        var previous = Double.NEGATIVE_INFINITY
        for (hz in 65..1100) {
            val pitch = YinTuner.fromHz(hz.toDouble(), 440.0, 1.0)
            val semitones = pitch.midi + pitch.cents / 100
            assertTrue(semitones > previous)
            assertEquals(hz.toDouble(), 440 * 2.0.pow((semitones - 69) / 12), 1e-8)
            previous = semitones
        }
        for (invalid in listOf(Double.NaN, Double.POSITIVE_INFINITY, -1.0, 0.0, 64.0, 1101.0)) {
            assertThrows(IllegalArgumentException::class.java) { YinTuner.fromHz(invalid, 440.0, 1.0) }
        }
        assertThrows(IllegalArgumentException::class.java) { YinTuner.fromHz(110.0, 0.0, 1.0) }
        assertThrows(IllegalArgumentException::class.java) { YinTuner.fromHz(110.0, 440.0, Double.NaN) }
        assertThrows(IllegalArgumentException::class.java) { YinTuner.estimate(tone(110.0), 0) }
    }

    @Test
    fun detectedFrequenciesRiseThroughTheSupportedRange() {
        var previous = 0.0
        for (hz in 70..1080 step 10) {
            val reading = YinTuner.estimate(tone(hz.toDouble()), rate)
            assertNotNull("No reading for $hz Hz", reading)
            assertTrue("Pitch did not rise at $hz Hz", reading!!.frequencyHz > previous)
            previous = reading.frequencyHz
        }
    }

    @Test
    fun smoothingResetsOnANewNoteAndOnSilence() {
        val smoother = PitchSmoother()
        for (hz in listOf(109.9, 110.0, 110.1, 110.05, 109.95)) {
            smoother.update(YinTuner.fromHz(hz, 440.0, 1.0), 440.0)
        }
        val newNote = smoother.update(YinTuner.fromHz(146.8324, 440.0, 1.0), 440.0)
        assertEquals(146.8324, newNote!!.frequencyHz, 1e-9)
        assertNull(smoother.update(null, 440.0))
        val afterSilence = smoother.update(YinTuner.fromHz(110.0, 440.0, 1.0), 440.0)
        assertEquals(110.0, afterSilence!!.frequencyHz, 1e-9)
    }
}
