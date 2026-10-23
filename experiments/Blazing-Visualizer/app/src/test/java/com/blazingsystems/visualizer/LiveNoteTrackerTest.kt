package com.blazingsystems.visualizer

import com.blazingsystems.visualizer.tuning.LiveNoteTracker
import kotlin.math.*
import org.junit.Assert.*
import org.junit.Test

class LiveNoteTrackerTest {
    private fun audio(vararg pitches: Int, harmonics: Boolean = false): ShortArray = ShortArray(4096) { i ->
        var v = 0.0
        for (p in pitches) {
            val f=440*2.0.pow((p-69)/12.0)
            v += sin(2*PI*f*i/22050)*.17
            if(harmonics) for(h in 2..5) v += sin(2*PI*f*h*i/22050)*.1/h
        }
        (v.coerceIn(-1.0,1.0)*32767).toInt().toShort()
    }
    @Test fun hearsARealTriadTogetherAndSuppressesASingleNotesOvertones() {
        val triad=LiveNoteTracker().update(audio(60,64,67,harmonics=true),200_000).features
        assertEquals(setOf(60,64,67),triad.notes.filter { it.endUs>triad.sourceTimeUs }.map { it.pitch }.toSet())
        val single=LiveNoteTracker().update(audio(45,harmonics=true),200_000)
        assertEquals(listOf(45),single.features.notes.map { it.pitch })
        assertNotNull(single.pitch)
    }
    @Test fun lowE2AndHighC7HaveVisibleNotes() {
        for(p in listOf(40,96)) assertEquals(listOf(p),LiveNoteTracker().update(audio(p),200_000).features.notes.map { it.pitch })
    }
    @Test fun captureTimeAdvancesWhilePlaybackIsPausedAndHeldNotesKeepTheirOnset() {
        val tracker=LiveNoteTracker()
        val first=tracker.update(audio(69),200_000).features
        val second=tracker.update(audio(69),246_000).features
        assertEquals(246_000L,second.sourceTimeUs)
        assertEquals(first.notes.single().id,second.notes.single().id)
        assertEquals(first.notes.single().startUs,second.notes.single().startUs)
        val quiet=tracker.update(ShortArray(4096),300_000).features
        assertTrue(quiet.notes.none { it.startUs<=300_000 && it.endUs>300_000 })
    }
    @Test fun seededBroadbandNoiseDoesNotBecomeAChord() {
        val random=java.util.Random(321)
        val noise=ShortArray(4096) { (random.nextGaussian()*1800).toInt().coerceIn(-32000,32000).toShort() }
        assertTrue(LiveNoteTracker().update(noise,200_000).features.notes.isEmpty())
    }
}
