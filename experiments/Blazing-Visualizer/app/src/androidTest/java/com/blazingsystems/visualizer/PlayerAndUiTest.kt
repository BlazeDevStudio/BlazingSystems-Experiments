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
    @get:Rule val rule = createAndroidComposeRule<MainActivity>()

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
        rule.waitUntil(60_000) { model().state.value.notes.isNotEmpty() }
        rule.runOnUiThread {
            model().player.pause()
            model().setScene(BuiltinScenes.noteWheel())
            val n = model().state.value.notes.first()
            model().editNote(NoteEdit.Replace(n.copy(pitch = 62)))
        }
        rule.onNodeWithText("Practice").performClick()
        rule.onNodeWithText("Playback speed · pitch stays the same").assertIsDisplayed()
        rule.onNodeWithText("0.5×").performClick()
        rule.onNodeWithText("Export MIDI").performScrollTo().assertIsEnabled()
        rule.activityRule.scenario.recreate()
        rule.waitUntil(10_000) { model().state.value.project?.edits?.isNotEmpty() == true }
        assertEquals(62, model().state.value.notes.first().pitch)
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
