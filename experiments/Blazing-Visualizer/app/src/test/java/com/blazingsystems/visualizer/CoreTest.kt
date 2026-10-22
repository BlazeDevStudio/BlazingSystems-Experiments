package com.blazingsystems.visualizer

import com.blazingsystems.visualizer.analysis.*
import com.blazingsystems.visualizer.audio.*
import com.blazingsystems.visualizer.avee.*
import com.blazingsystems.visualizer.export.*
import com.blazingsystems.visualizer.playback.*
import com.blazingsystems.visualizer.practice.*
import com.blazingsystems.visualizer.project.*
import com.blazingsystems.visualizer.render.*
import java.io.ByteArrayOutputStream
import kotlin.math.*
import org.junit.Assert.*
import org.junit.Test

class CoreTest {
    private val note = NoteEvent("a", 60, 1_000_000, 2_000_000)

    @Test
    fun changedSourceDropsStaleCorrections() {
        val p =
            Project(
                source = SourceRef("content://a", "old"),
                analysisKey = "stale",
                edits = listOf(NoteEdit.Delete("a")),
            )
        val updated = SourceIdentity.bind(p, p.source.copy(contentSha256 = "new"))
        assertTrue(updated.edits.isEmpty())
        assertNull(updated.analysisKey)
        assertEquals(p.scene, updated.scene)
    }

    @Test
    fun identicalContentKeepsCorrections() {
        val p = Project(source = SourceRef("a", "hash"), edits = listOf(NoteEdit.Delete("a")))
        assertEquals(p.edits, SourceIdentity.bind(p, p.source.copy(uri = "b")).edits)
    }

    @Test
    fun changedSourceCannotExportOldNotes() {
        assertThrows(IllegalArgumentException::class.java) {
            SourceIdentity.requireExportMatch("old", "new")
        }
        assertThrows(IllegalArgumentException::class.java) {
            SourceIdentity.requireExportMatch(null, "new")
        }
        SourceIdentity.requireExportMatch("same", "same")
    }

    @Test
    fun noteEditsLeaveRawImmutable() {
        val raw = listOf(note)
        assertEquals(
            64,
            applyNoteEdits(raw, listOf(NoteEdit.Replace(note.copy(pitch = 64))))[0].pitch,
        )
        assertEquals(60, raw[0].pitch)
        assertTrue(applyNoteEdits(raw, listOf(NoteEdit.Delete("a"))).isEmpty())
    }

    @Test
    fun activeNotesUseHalfOpenSourceClock() {
        val s = Scene(layers = listOf(Layer(type = ElementType.NOTE_WHEEL)))
        val f = FeatureFrame(0, notes = listOf(note))
        assertTrue(SceneEvaluator.evaluate(s, f, 999_999).activeNotes.isEmpty())
        assertEquals(1, SceneEvaluator.evaluate(s, f, 1_000_000).activeNotes.size)
        assertTrue(SceneEvaluator.evaluate(s, f, 2_000_000).activeNotes.isEmpty())
    }

    @Test
    fun seekReplayIsDeterministic() {
        val s = Scene(layers = listOf(Layer(type = ElementType.PARTICLES)))
        val f = FeatureFrame(0, .3f, notes = listOf(note))
        val a = SceneEvaluator.evaluate(s, f, 1_100_000)
        SceneEvaluator.evaluate(s, f, 4_000_000)
        assertEquals(a, SceneEvaluator.evaluate(s, f, 1_100_000))
    }

    @Test
    fun visibilityAndBindingAreEvaluated() {
        val layer =
            Layer(
                type = ElementType.SHAPE,
                bindings = listOf(Binding("scale", BindingSource.RMS, 2f)),
            )
        val scene = Scene(layers = listOf(layer, layer.copy(id = "hidden", visible = false)))
        val e = SceneEvaluator.evaluate(scene, FeatureFrame(0, .25f), 0)
        assertEquals(1, e.layers.size)
        assertEquals(1.5f, e.layers[0].scale, .0001f)
    }

    @Test
    fun namesRetainConcertPitch() {
        assertEquals("A4", NoteNames.name(69))
        assertEquals("D4", NoteNames.name(60, displayTranspose = 2))
        assertEquals("D♭4", NoteNames.name(61, true))
    }

    @Test
    fun loopRewindsAtEnd() {
        val r = LoopRange(1_000_000, 2_000_000)
        assertEquals(1_000_000, r.rewindIfOutside(2_000_000))
        assertEquals(1_500_000, r.rewindIfOutside(1_500_000))
    }

    @Test
    fun midiIsRealFormatZero() {
        val out = ByteArrayOutputStream()
        NoteExport.writeMidi(listOf(note), out)
        val b = out.toByteArray()
        assertEquals("MThd", String(b, 0, 4))
        assertEquals("MTrk", String(b, 14, 4))
        assertTrue(
            b.toList().windowed(3).any { it == listOf(0x90.toByte(), 60.toByte(), 127.toByte()) },
        )
    }

    @Test
    fun csvEscapesAndKeepsMicroseconds() {
        val out = ByteArrayOutputStream()
        NoteExport.writeCsv(listOf(note.copy(id = "a,\"b")), out)
        val text = out.toString("UTF-8")
        assertTrue(text.contains("\"a,\"\"b\""))
        assertTrue(text.contains(",1000000,2000000,"))
    }

    @Test
    fun modelFrameClockIncludesWindowCorrection() {
        assertEquals(1_986_590, NotePostprocessor.frameTimeUs(172))
    }

    @Test
    fun cacheIdentityIncludesAllAnalysisParameters() {
        val a = AnalysisKeys.key("s", "m", AnalysisParameters())
        assertNotEquals(a, AnalysisKeys.key("s", "m", AnalysisParameters(frameThreshold = .4f)))
        assertNotEquals(a, AnalysisKeys.key("s2", "m", AnalysisParameters()))
    }

    @Test
    fun majorChordRequiresActiveTriad() {
        val notes = listOf(60, 64, 67).map { note.copy(id = "$it", pitch = it) }
        assertEquals("C", ChordEstimator.estimate(notes, 1_200_000))
        assertNull(ChordEstimator.estimate(notes, 2_000_000))
    }

    @Test
    fun chordDictionaryNamesExtendedAndSuspendedHarmony() {
        fun notes(vararg pitches: Int) = pitches.mapIndexed { i, pitch ->
            NoteEvent("h$i", pitch, 0, 1_000_000)
        }
        assertEquals("Am", ChordEstimator.estimate(notes(57, 60, 64), 10))
        assertEquals("Cmaj7", ChordEstimator.estimate(notes(48, 52, 55, 59), 10))
        assertEquals("Dsus4", ChordEstimator.estimate(notes(50, 55, 57), 10))
        assertEquals("C9", ChordEstimator.estimate(notes(48, 50, 52, 55, 58), 10))
    }

    @Test
    fun unmatchedNotesAreAllShownAndEmptyTextIsCustomizable() {
        val simultaneous = listOf(60, 61, 69).mapIndexed { i, pitch ->
            NoteEvent("note-$i", pitch, 0, 1_000_000)
        }
        assertNull(ChordEstimator.estimate(simultaneous, 1))
        assertEquals("C · C♯ · A", ChordEstimator.displayLabel(simultaneous, 1))
        assertEquals("PLAY A CHORD", ChordEstimator.displayLabel(simultaneous, 2_000_000, "PLAY A CHORD"))
    }

    @Test
    fun liveMicrophoneFramesDriveMainVisualizerWithoutMutatingTrackNotes() {
        val fileNotes = listOf(note)
        val original = FeatureFrame(42, rms = .2f, notes = fileNotes)
        val mic = com.blazingsystems.visualizer.tuning.PitchReading(440.0, 69, 0.0, .95)
        val wave = com.blazingsystems.visualizer.avee.SpectrumFrame(
            .7f, listOf(.1f, .9f), listOf(0f, .3f),
        )
        val live = com.blazingsystems.visualizer.ui.micVisualFeatures(original, mic, wave)
        assertEquals(69, live.notes.single().pitch)
        assertEquals(.7f, live.rms, .0001f)
        assertEquals(listOf(.1f, .9f), live.spectrum)
        assertEquals(fileNotes, original.notes)
        val silence = com.blazingsystems.visualizer.ui.micVisualFeatures(original, null, wave)
        assertTrue(silence.notes.isEmpty())
    }

    @Test
    fun spectrumTracksKnownTone() {
        val pcm = FloatArray(2048) { sin(2 * PI * 441 * it / 22050).toFloat() }
        val result = AveeSpectrumAnalyzer().analyze(pcm, 22050)
        val peak = result.spectrum.indices.maxBy { result.spectrum[it] }
        assertTrue(abs(peak - 441 * 2048 / 22050) <= 1)
    }

    @Test
    fun exportUsesRationalSourceClock() {
        val t = ExportTimeline(1_000_000, 2_000_001, 30)
        assertEquals(31, t.frameCount)
        assertEquals(1_033_333, t.sourceTimeUs(1))
        assertEquals(33_333, t.presentationTimeUs(1))
        assertTrue(t.sourceTimeUs(30) < 2_000_001)
    }

    @Test
    fun exportRejectsEmptyAndInvalidSettings() {
        assertThrows(IllegalArgumentException::class.java) { ExportTimeline(1, 1, 30) }
        assertThrows(IllegalArgumentException::class.java) {
            validateExportSettings(ExportSettings(width = 127))
        }
    }

    @Test
    fun resamplerPreservesToneAndDuration() {
        val input = FloatArray(48000) { sin(2 * PI * 440 * it / 48000).toFloat() }
        val r = PcmResampler(48000, 1)
        val out = r.feed(input) + r.feed(FloatArray(0), true)
        assertTrue(abs(out.size - 22050) <= 1)
        val crossings = out.indices.drop(1).count { out[it - 1] < 0 && out[it] >= 0 }
        assertTrue(abs(crossings - 440) <= 1)
    }
}
