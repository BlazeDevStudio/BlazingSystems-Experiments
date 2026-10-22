package com.blazingsystems.visualizer

import com.blazingsystems.visualizer.analysis.*
import com.blazingsystems.visualizer.audio.*
import com.blazingsystems.visualizer.export.*
import com.blazingsystems.visualizer.packs.*
import com.blazingsystems.visualizer.project.*
import java.io.ByteArrayOutputStream
import java.io.File
import java.nio.file.Files
import java.util.zip.*
import kotlin.math.*
import org.junit.*
import org.junit.Assert.*

class StorageTest {
    private lateinit var root: File

    @Before
    fun setup() {
        root = Files.createTempDirectory("studio-storage").toFile()
    }

    @After
    fun cleanup() {
        root.deleteRecursively()
    }

    @Test
    fun projectRestoresSceneAndSeparateEdits() {
        val store = ProjectStore(root)
        val note = NoteEvent("n", 61, 100, 200)
        val p =
            Project(
                source = SourceRef("content://track", "sha", 500),
                scene =
                    Scene(name = "Edited", layers = listOf(Layer(type = ElementType.NOTE_WHEEL))),
                edits = listOf(NoteEdit.Insert(note)),
            )
        store.save(p)
        assertEquals(p, store.load(p.id))
        assertEquals(
            note.pitch,
            applyNoteEdits(emptyList(), store.load(p.id)!!.edits).first().pitch,
        )
    }

    @Test
    fun practiceSettingsPersistPerTrackAndReadLegacyProjects() {
        val store = ProjectStore(root)
        val configured = PracticeSettings(
            speed = .75f, preferFlats = true, instrumentSemitones = 2,
            register = 1, loopStartUs = 500_000, loopEndUs = 1_500_000,
            loopEnabled = true,
        )
        val first = Project(source = SourceRef("content://first"), practice = configured)
        val second = Project(source = SourceRef("content://second"))
        store.save(first)
        store.save(second)
        assertEquals(configured, store.load(first.id)!!.practice)
        assertEquals(PracticeSettings(), store.load(second.id)!!.practice)
        assertTrue(configured.isValid())
        assertFalse(configured.copy(loopStartUs = 2_000_000).isValid())
        val legacy = """{"source":{"uri":"content://legacy"}}"""
        val loaded = kotlinx.serialization.json.Json { ignoreUnknownKeys = true }
            .decodeFromString<Project>(legacy)
        assertEquals(PracticeSettings(), loaded.practice)
    }

    @Test
    fun intermediateNoteBandsAreDistinctAndPackSettingsRoundTrip() {
        val bands = NoteBand.entries.filter { it != NoteBand.ALL }
        val notes = (0..127).toList()
        val routed = bands.flatMap { band -> notes.filter { NoteRouting(band).allows(it) } }
        assertEquals(notes, routed.sorted())
        assertTrue(NoteRouting(NoteBand.LO2).allows(47))
        assertFalse(NoteRouting(NoteBand.LO2).allows(69))
        val range = NoteRouting(NoteBand.MID, lowMidi = 60, highMidi = 64)
        assertTrue(range.allows(62))
        assertFalse(range.allows(65))
        assertFalse(range.copy(lowMidi = 100).isValid())
        val p = Project(
            source = SourceRef("content://notes"),
            scene = Scene(
                animationIntensity = 0f, pianoIntensity = .3f,
                paletteColor = "#3366AA",
                layers = listOf(Layer(type = ElementType.PIANO_ROLL, noteRouting = range)),
            ),
        )
        ProjectStore(root).save(p)
        assertEquals(p, ProjectStore(root).load(p.id))
    }

    @Test
    fun abandonedTemporaryAndCorruptProjectDoNotHideGoodOne() {
        val store = ProjectStore(root)
        val p = Project(source = SourceRef("a"))
        store.save(p)
        File(root, "interrupted.json.tmp").writeText("broken")
        File(root, "corrupt.json").writeText("{")
        assertEquals(listOf(p), store.list())
    }

    @Test
    fun projectIdCannotEscapeRoot() {
        assertThrows(IllegalArgumentException::class.java) { ProjectStore(root).load("../private") }
    }

    @Test
    fun jobRecoveryMarksOnlyIncompleteWorkInterrupted() {
        val store = ExportJobStore(root)
        val request =
            ExportRequest(
                Project(source = SourceRef("a", "hash", 1_000_000)),
                0,
                1_000_000,
                "content://out",
            )
        store.save(ExportJob("pending", request, ExportStatus.RUNNING, .7f))
        store.save(ExportJob("done", request, ExportStatus.COMPLETED, 1f))
        val recovered = store.recover().associateBy { it.id }
        assertEquals(ExportStatus.INTERRUPTED, recovered["pending"]!!.status)
        assertEquals(ExportStatus.COMPLETED, recovered["done"]!!.status)
        assertEquals(ExportStatus.INTERRUPTED, store.recover().first { it.id == "pending" }.status)
    }

    @Test
    fun snapshotDoesNotFollowLaterSceneOrNoteEdits() {
        val p = Project(source = SourceRef("a", "hash"), scene = Scene(name = "First"))
        val export = ExportRequest(p, 0, 1_000_000, "out")
        val later =
            p.copy(scene = p.scene.copy(name = "Later"), edits = listOf(NoteEdit.Delete("old")))
        assertEquals("First", export.project.scene.name)
        assertTrue(export.project.edits.isEmpty())
        assertEquals("Later", later.scene.name)
    }

    @Test
    fun unknownPackSchemaIsRejectedBeforeInstalling() {
        val bytes = ByteArrayOutputStream()
        ZipOutputStream(bytes).use {
            it.putNextEntry(ZipEntry("manifest.json"))
            it.write("{\"schemaVersion\":2}".toByteArray())
            it.closeEntry()
        }
        assertThrows(IllegalArgumentException::class.java) {
            NativePackCodec().read(bytes.toByteArray().inputStream(), root)
        }
        assertTrue(root.listFiles()!!.isEmpty())
    }

    @Test
    fun streamingStereoDownmixAndTailKeepOriginalTime() {
        val input =
            FloatArray(48000 * 2) { i ->
                if (i % 2 == 0) sin(2 * PI * 330 * (i / 2) / 48000).toFloat()
                else -sin(2 * PI * 330 * (i / 2) / 48000).toFloat()
            }
        val a = PcmResampler(48000, 2)
        val all = a.feed(input) + a.feed(FloatArray(0), true)
        val b = PcmResampler(48000, 2)
        val chunks =
            input
                .toList()
                .chunked(2000)
                .flatMap { b.feed(it.toFloatArray()).toList() }
                .toFloatArray() + b.feed(FloatArray(0), true)
        assertEquals(22050, all.size)
        assertArrayEquals(all, chunks, .000001f)
        assertTrue(all.all { abs(it) < .000001f })
    }

    @Test
    fun frameDecoderDoesNotInventNotesInSilence() {
        val zero = Array(100) { FloatArray(88) }
        assertTrue(
            NotePostprocessor.decode(ModelOutputs(zero, zero, emptyArray()), 1_000_000).isEmpty(),
        )
    }

    @Test
    fun shortAudioIsSafelyEmpty() {
        assertTrue(
            NotePostprocessor.decode(
                    ModelOutputs(
                        Array(2) { FloatArray(88) },
                        Array(2) { FloatArray(88) },
                        emptyArray(),
                    ),
                    1000,
                )
                .isEmpty(),
        )
    }
}
