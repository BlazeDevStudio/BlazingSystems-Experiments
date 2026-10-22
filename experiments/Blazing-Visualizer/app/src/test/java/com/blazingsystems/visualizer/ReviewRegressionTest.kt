package com.blazingsystems.visualizer

import com.blazingsystems.visualizer.export.*
import com.blazingsystems.visualizer.playback.*
import com.blazingsystems.visualizer.project.*
import java.io.File
import java.nio.file.Files
import java.util.concurrent.*
import org.junit.*
import org.junit.Assert.*

class ReviewRegressionTest {
    private lateinit var root: File

    @Before
    fun setup() {
        root = Files.createTempDirectory("review-regressions").toFile()
    }

    @After
    fun cleanup() {
        root.deleteRecursively()
    }

    @Test
    fun nextTrackIsSelectedWhilePreviousAnalysisIsRunning() {
        val a = SourceRef("a")
        val b = SourceRef("b")
        val c = TrackCoordinator()
        c.begin("a")
        assertNull(c.selectionFor("a", listOf(a, b)))
        assertEquals(b, c.selectionFor("b", listOf(a, b)))
        c.begin("b")
        c.finish("a")
        assertEquals("b", c.loadingUri)
    }

    @Test
    fun correctionCannotCrossProjectBoundary() {
        val a = Project(source = SourceRef("a", "sha"))
        val b = Project(source = SourceRef("b", "other"))
        val edit = NoteEdit.Insert(NoteEvent("a-note", 60, 0, 100))
        assertThrows(IllegalArgumentException::class.java) {
            NoteEditing.apply(b, NoteEditTarget.of(a), edit)
        }
        assertTrue(b.edits.isEmpty())
    }

    @Test
    fun correctionCannotCrossChangedContent() {
        val a = Project(source = SourceRef("a", "old"))
        val changed = a.copy(source = a.source.copy(contentSha256 = "new"))
        assertThrows(IllegalArgumentException::class.java) {
            NoteEditing.apply(changed, NoteEditTarget.of(a), NoteEdit.Delete("same-model-id"))
        }
    }

    @Test
    fun presetCollectionSurvivesSwitchAndColdReload() {
        val file = File(root, "presets.json")
        val a = Scene(name = "My imported scene")
        val b = Scene(name = "My duplicate")
        val store = PresetStore(file)
        store.save(PresetStore.upsert(PresetStore.upsert(emptyList(), a), b))
        assertEquals(setOf(a, b), PresetStore(file).load().toSet())
    }

    @Test
    fun updatingPresetKeepsOtherSavedPresets() {
        val a = Scene(name = "A")
        val b = Scene(name = "B")
        val updated = PresetStore.upsert(listOf(a, b), a.copy(name = "A edited"))
        assertEquals(2, updated.size)
        assertTrue(b in updated)
        assertEquals("A edited", updated.first { it.id == a.id }.name)
    }

    @Test
    fun failedContainerFinalizationCannotReachPublish() {
        var released = false
        var published = false
        assertThrows(java.io.IOException::class.java) {
            ExportFinalization.close(
                null,
                { throw java.io.IOException("No room for MP4 metadata") },
                { released = true },
            )
            published = true
        }
        assertTrue(released)
        assertFalse(published)
    }

    @Test
    fun cleanupRetainsCancellationAsPrimaryFailure() {
        val cancelled = CancellationException("cancel")
        ExportFinalization.close(
            cancelled,
            { throw IllegalStateException("partial container") },
            {},
        )
        assertEquals(1, cancelled.suppressed.size)
    }

    @Test
    fun atomicWritesDoNotShareATemporaryFile() {
        val pool = Executors.newFixedThreadPool(12)
        val target = File(root, "queue.json")
        val start = CountDownLatch(1)
        try {
            val jobs =
                (0 until 60).map { i ->
                    pool.submit {
                        start.await()
                        repeat(4) { atomicWrite(target, "{\"version\":$i}".toByteArray()) }
                    }
                }
            start.countDown()
            jobs.forEach { it.get(20, TimeUnit.SECONDS) }
            assertTrue(target.readText().matches(Regex("\\{\"version\":\\d+}")))
        } finally {
            pool.shutdownNow()
        }
    }
}
