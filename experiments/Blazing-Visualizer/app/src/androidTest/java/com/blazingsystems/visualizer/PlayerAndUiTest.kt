package com.blazingsystems.visualizer

import android.net.Uri
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.lifecycle.ViewModelProvider
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import com.blazingsystems.visualizer.playback.PlayerController
import com.blazingsystems.visualizer.project.*
import com.blazingsystems.visualizer.render.BuiltinScenes
import com.blazingsystems.visualizer.ui.StudioModel
import java.io.File
import org.junit.*
import org.junit.Assert.*
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class PlayerAndUiTest {
    @get:Rule(order = 0) val audioPermission = AudioPermissionRule()
    @get:Rule(order = 1) val rule = createAndroidComposeRule<MainActivity>()

    private fun model() = ViewModelProvider(rule.activity)[StudioModel::class.java]

    @Test
    fun familiarWorkflowOpensPresetsAndLayerEditor() {
        rule.onNodeWithText("Library", useUnmergedTree = true).performClick()
        rule.onNodeWithText("Your library").assertIsDisplayed()
        rule.onNodeWithText("Visualizer", useUnmergedTree = true).performClick()
        rule.onNodeWithContentDescription("Choose visualizer").performClick()
        rule.onAllNodes(hasText("Harmonic compass") and hasClickAction()).onFirst().performClick()
        rule.activityRule.scenario.recreate()
        rule.onNodeWithContentDescription("Edit visualizer").performClick()
        rule.onNodeWithText("Composition").assertIsDisplayed()
        rule.onNodeWithText("Add element").performScrollTo().performClick()
        rule.onNodeWithText("waveform").performClick()
        rule.onNodeWithText("WAVEFORM").performScrollTo().assertExists()
    }

    @Test
    fun noteGuideUsesSelectedTrackAndKeepsCorrectionsAfterRecreation() {
        val inst = InstrumentationRegistry.getInstrumentation()
        val f = File(rule.activity.filesDir, "ui-synthetic.wav")
        inst.context.assets.open("synthetic.wav").use { input ->
            f.outputStream().use(input::copyTo)
        }
        rule.runOnUiThread { model().importTracks(listOf(Uri.fromFile(f))) }
        val expectedUri = Uri.fromFile(f).toString()
        rule.waitUntil(30_000) { model().playback.value.sourceUri == expectedUri }
        rule.runOnUiThread { model().player.pause() }
        rule.waitUntil(60_000) {
            model().state.value.project?.source?.uri == expectedUri &&
                model().state.value.progress == null &&
                model().state.value.notes.isNotEmpty()
        }
        rule.runOnUiThread {
            model().setScene(BuiltinScenes.noteWheel())
            val n = model().state.value.notes.first()
            model().editNote(NoteEdit.Replace(n.copy(pitch = 62)))
        }
        rule.onNodeWithText("Practice").performClick()
        rule.onNodeWithText("Playback speed · pitch stays the same").assertIsDisplayed()
        rule.onNodeWithText("0.5×").performClick()
        rule.onNodeWithText("Export MIDI").performScrollTo().assertIsEnabled()
        rule.activityRule.scenario.recreate()
        rule.waitUntil(10_000) {
            model().state.value.project?.source?.uri == expectedUri &&
                model().state.value.project?.edits?.isNotEmpty() == true
        }
        assertEquals(62, model().state.value.notes.first().pitch)
        assertEquals(.5f, model().state.value.project!!.practice.speed, .001f)
        rule.runOnUiThread {
            model().editScene(model().state.value.scene.copy(showEquations = true))
            model().setExportSettings(ExportSettings(720, 1280))
            model().beginLayoutEdit(true, 1f)
            val id = model().state.value.scene.layers.last().id
            model().setLayoutTransform(id, Transform(x = .25f, y = .3f, width = .4f, height = .2f))
            model().finishLayoutEdit()
        }
        rule.activityRule.scenario.recreate()
        assertTrue(model().state.value.scene.showEquations)
        assertEquals(ExportLayoutMode.SEPARATE, model().state.value.project!!.exportLayout)
        assertEquals(1280, model().state.value.project!!.export.height)
        assertEquals(.25f, model().state.value.project!!.exportTransforms.values.last().x, .0001f)
    }

    @Test
    fun playbackSeeksAndLoopsUsingSourceTime() {
        val inst = InstrumentationRegistry.getInstrumentation()
        val f = File(rule.activity.filesDir, "playback.wav")
        inst.context.assets.open("synthetic.wav").use { input ->
            f.outputStream().use(input::copyTo)
        }
        lateinit var player: PlayerController
        rule.runOnUiThread {
            player = PlayerController(rule.activity)
            player.open(Uri.fromFile(f))
        }
        try {
            rule.waitUntil(30_000) { player.state.value.isPlaying }
            rule.runOnUiThread {
                player.pause()
                player.seekTo(1_000_000)
                player.setPracticeSpeed(.5f)
            }
            rule.waitUntil(5_000) {
                kotlin.math.abs(player.state.value.sourceTimeUs - 1_000_000) <= 50_000
            }
            assertEquals(.5f, player.state.value.speed, .001f)
            rule.runOnUiThread {
                player.setLoop(300_000, 700_000)
                player.play()
            }
            Thread.sleep(1300)
            assertTrue(player.state.value.sourceTimeUs in 300_000..750_000)
        } finally {
            rule.runOnUiThread { player.close() }
        }
    }

}
