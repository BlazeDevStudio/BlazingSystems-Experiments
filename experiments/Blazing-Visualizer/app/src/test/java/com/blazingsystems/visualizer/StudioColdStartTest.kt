package com.blazingsystems.visualizer

import androidx.lifecycle.ViewModelStore
import com.blazingsystems.visualizer.playback.*
import com.blazingsystems.visualizer.project.*
import com.blazingsystems.visualizer.render.*
import com.blazingsystems.visualizer.ui.StudioModel
import java.io.File
import kotlinx.coroutines.*
import kotlinx.coroutines.test.*
import org.junit.*
import org.junit.Assert.*
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.RuntimeEnvironment
import org.robolectric.annotation.Config

@OptIn(ExperimentalCoroutinesApi::class)
@RunWith(RobolectricTestRunner::class)
@Config(sdk = [33])
class StudioColdStartTest {
    private val main = TestCoroutineScheduler()
    private val disk = TestCoroutineScheduler()
    private val owner = ViewModelStore()
    private val app: android.app.Application get() = RuntimeEnvironment.getApplication()
    private val repository get() = LibraryRepository(app)
    private val store get() = ProjectStore(File(app.filesDir, "projects"))
    private val a = SourceRef("content://test/missing-a", title = "A")
    private val b = SourceRef("content://test/missing-b", title = "B")
    private val preset = BuiltinScenes.noteWheel().copy(id = "saved-look")

    @Before fun setup() {
        Dispatchers.setMain(StandardTestDispatcher(main))
        repository.saveLibrary(listOf(a,b))
        repository.saveQueue(listOf(a,b))
        repository.savePlaylists(listOf(Playlist("saved-list", "Saved list", listOf(a,b))))
        PresetStore(File(app.filesDir,"presets.json")).save(listOf(preset))
    }
    @After fun cleanup() {
        owner.clear()
        main.runCurrent()
        disk.runCurrent()
        Dispatchers.resetMain()
    }
    private fun model() = StudioModel(app, StandardTestDispatcher(disk)).also { owner.put("studio", it) }
    private fun pumpUntil(condition: () -> Boolean) {
        val end = System.nanoTime() + 5_000_000_000L
        while (!condition() && System.nanoTime() < end) {
            main.runCurrent()
            Thread.sleep(5)
        }
        assertTrue("Initialization/selection did not finish", condition())
    }

    @Test fun viewportMeasurementBeforeLoadingCannotEraseSavedCollections() {
        val model = model()
        // Main initialization is deliberately paused; simulate the first layout callback.
        model.setPreviewAspect(.6f)
        disk.runCurrent()
        assertEquals(listOf(a,b), repository.loadLibrary())
        assertEquals(listOf(a,b), repository.loadQueue())
        assertEquals("saved-list", repository.loadPlaylists().single().id)
        assertEquals(listOf(preset), PresetStore(File(app.filesDir,"presets.json")).load())
        pumpUntil { model.state.value.library.isNotEmpty() }
        assertEquals(.6f, model.state.value.displayScene().designAspect, .0001f)
    }

    @Test fun choosingPresetAfterMeasurementKeepsTheRealPreviewAspect() {
        val model = model()
        pumpUntil { model.state.value.library.isNotEmpty() }
        model.setPreviewAspect(.6f)
        model.setScene(BuiltinScenes.noteWheel())
        assertEquals(.6f, model.state.value.displayScene().designAspect, .0001f)
    }

    @Test fun resizingThePhoneCanvasDoesNotCancelArrangementOrShrinkSavedGeometry() {
        val model = model()
        pumpUntil { model.state.value.ready }
        val original = BuiltinScenes.noteWheel()
        model.setScene(original)
        model.beginLayoutEdit(false, .6f)
        model.setPreviewAspect(.48f) // bottom controls hide when arrangement opens
        assertTrue("Viewport resize must not close the arrangement tools", model.state.value.layoutEditing)
        model.finishLayoutEdit()
        model.beginLayoutEdit(false, .6f)
        model.finishLayoutEdit()
        assertEquals("Opening/closing tools must not bake repeated contain transforms", original, model.state.value.scene)
    }

    @Test fun pendingChangesForAStillSaveWhenBIsSelectedBeforeDiskCatchesUp() {
        val projectA = Project(id = "project-a", source = a, scene = preset)
        val projectB = Project(id = "project-b", source = b, scene = preset)
        store.save(projectA); store.save(projectB); store.save(projectA)
        val model = model()
        pumpUntil { model.state.value.library.isNotEmpty() }
        model.select(a, false)
        pumpUntil { model.state.value.project?.source?.uri == a.uri && model.state.value.progress == null }
        model.updatePractice { it.copy(speed = .5f, preferFlats = true, register = 2) }
        model.select(b, false)
        pumpUntil { model.state.value.project?.source?.uri == b.uri && model.state.value.progress == null }
        model.updatePractice { it.copy(speed = .75f) }
        // The writer has been paused throughout both edits and the track change.
        disk.runCurrent()
        assertEquals(.5f, store.load(projectA.id)!!.practice.speed, .0001f)
        assertTrue(store.load(projectA.id)!!.practice.preferFlats)
        assertEquals(2, store.load(projectA.id)!!.practice.register)
        assertEquals(.75f, store.load(projectB.id)!!.practice.speed, .0001f)
    }
}
