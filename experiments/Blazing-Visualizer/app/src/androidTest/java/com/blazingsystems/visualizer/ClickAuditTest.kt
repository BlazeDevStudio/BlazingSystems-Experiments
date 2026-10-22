package com.blazingsystems.visualizer

import android.net.Uri
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.lifecycle.ViewModelProvider
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import com.blazingsystems.visualizer.ui.StudioModel
import java.io.File
import java.util.UUID
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

/**
 * An interaction-by-interaction audit. Every action goes through the real
 * Compose screen, except the SAF picker: its fixture URI is handed to the
 * same model entry point as OpenMultipleDocuments.
 */
@RunWith(AndroidJUnit4::class)
class ClickAuditTest {
    @get:Rule(order = 0) val audioPermission = AudioPermissionRule()
    @get:Rule(order = 1) val rule = createAndroidComposeRule<MainActivity>()
    private fun model() = ViewModelProvider(rule.activity)[StudioModel::class.java]

    private fun ready() = rule.waitUntil(15_000) { model().state.value.ready }

    @Test
    fun navigationPresetPickerEditorAndCanvasArrangement() {
        ready()
        rule.onNodeWithText("Library", useUnmergedTree = true).performClick()
        rule.onNodeWithText("Your library").assertIsDisplayed()
        rule.onNodeWithContentDescription("Refresh library").assertIsEnabled()
        rule.onNodeWithContentDescription("Import music").assertIsEnabled()
        rule.onNodeWithText("Queue", useUnmergedTree = true).performClick()
        rule.onNodeWithText("Up next").assertIsDisplayed()
        rule.onNodeWithText("Visualizer", useUnmergedTree = true).performClick()
        rule.onNodeWithContentDescription("Choose visualizer").performClick()
        rule.onNodeWithText("Visualizers").assertIsDisplayed()
        rule.onAllNodes(hasText("Harmonic compass") and hasClickAction()).onFirst().performClick()
        // Tapping a preset must expose the visualizer, not leave a sheet over it.
        rule.onNodeWithText("Visualizers").assertDoesNotExist()
        rule.onNodeWithContentDescription("Edit visualizer").performClick()
        rule.onNodeWithText("Composition").assertIsDisplayed()
        rule.onNodeWithText("Arrange preview").performScrollTo().performClick()
        rule.waitUntil(10_000) { model().state.value.layoutEditing }
        rule.onNodeWithText("Arrange preview").assertExists()
        rule.onNodeWithTag("visualizer-canvas").assertExists()
        rule.onNodeWithTag("visualizer-canvas").performTouchInput {
            click(Offset(3f, 3f))
        }
        rule.onNodeWithText("Reset layer").assertIsNotEnabled()
        rule.onNodeWithTag("visualizer-canvas").performTouchInput { click(center) }
        rule.onNodeWithText("Reset layer").assertIsEnabled()
        rule.onNodeWithText("Done").performClick()
        rule.waitUntil(10_000) { !model().state.value.layoutEditing }
        rule.onNodeWithContentDescription("Edit visualizer").assertIsDisplayed()
    }

    @Test
    fun partialImportSearchQueueSortAndPlaylistButtons() {
        ready()
        val instrumentation = InstrumentationRegistry.getInstrumentation()
        val valid = File(rule.activity.filesDir, "click-audit-${UUID.randomUUID()}.wav")
        instrumentation.context.assets.open("synthetic.wav").use { input ->
            valid.outputStream().use(input::copyTo)
        }
        val source = Uri.fromFile(valid)
        val bad = Uri.fromFile(File(rule.activity.filesDir, "missing-${UUID.randomUUID()}.wav"))
        rule.runOnUiThread { model().importTracks(listOf(source, bad)) }
        rule.waitUntil(20_000) { model().state.value.library.any { it.uri == source.toString() } }
        rule.onNodeWithText("Library", useUnmergedTree = true).performClick()
        rule.onNodeWithText("Your library").assertIsDisplayed()
        rule.onNodeWithTag("track-search").performTextInput("no-song-matches-this-search")
        rule.onNodeWithText("No tracks match", substring = true).assertExists()
        rule.onNodeWithTag("track-search").performTextClearance()
        rule.onNodeWithText("Queue", useUnmergedTree = true).performClick()
        rule.onNodeWithContentDescription("Sort queue").performClick()
        rule.onNodeWithText("Title A–Z").performClick()
        rule.onNodeWithText("Save queue as playlist").performClick()
        rule.onNodeWithText("Save", useUnmergedTree = true).performClick()
        rule.waitUntil(10_000) { model().state.value.playlists.any { it.name == "My playlist" } }
        rule.onNodeWithText("Library", useUnmergedTree = true).performClick()
        rule.onNodeWithText("Playlists").assertExists()
        assertTrue(model().state.value.queue.any { it.uri == source.toString() })
        rule.onNodeWithContentDescription("Delete playlist").performClick()
        rule.onNodeWithText("Delete playlist?").assertIsDisplayed()
        rule.onNodeWithText("Cancel").performClick()
        assertTrue(model().state.value.playlists.any { it.name == "My playlist" })
    }

    private fun openFixture(): Uri {
        ready()
        val f = File(rule.activity.filesDir, "click-audit-${UUID.randomUUID()}.wav")
        InstrumentationRegistry.getInstrumentation().context.assets.open("synthetic.wav").use {
            input -> f.outputStream().use(input::copyTo)
        }
        val uri = Uri.fromFile(f)
        rule.runOnUiThread { model().importTracks(listOf(uri)) }
        rule.waitUntil(20_000) {
            model().state.value.project?.source?.uri == uri.toString()
        }
        return uri
    }

    @Test
    fun practiceSpeedTransposeAndNoteWheelAreClickDriven() {
        openFixture()
        rule.onNodeWithText("Visualizer", useUnmergedTree = true).performClick()
        rule.onNodeWithText("Practice").performClick()
        rule.onNodeWithText("Playback speed · pitch stays the same").assertIsDisplayed()
        rule.onNodeWithText("0.75×").performClick()
        rule.waitUntil(10_000) { model().state.value.project?.practice?.speed == .75f }
        rule.onNodeWithText("B♭ instrument").performScrollTo().performClick()
        assertEquals(2, model().state.value.project!!.practice.instrumentSemitones)
        rule.onNodeWithText("Note wheel").performScrollTo().performClick()
        assertEquals("Harmonic compass", model().state.value.scene.name)
    }

    @Test
    fun exportOrientationAndSeparateCanvasLayoutAreClickDriven() {
        openFixture()
        rule.onNodeWithText("Visualizer", useUnmergedTree = true).performClick()
        rule.onNodeWithContentDescription("Export video").performClick()
        rule.onNodeWithText("Composition preview at selected output shape").assertExists()
        rule.onNodeWithText("Portrait 9:16").performScrollTo().performClick()
        rule.onNodeWithText("Output: 720 × 1280 pixels").assertExists()
        rule.onNodeWithText("Separate arrangement").performScrollTo().performClick()
        rule.waitUntil(10_000) {
            model().state.value.project?.exportLayout ==
                com.blazingsystems.visualizer.project.ExportLayoutMode.SEPARATE
        }
        rule.onNodeWithText("Arrange export on canvas").performScrollTo().performClick()
        rule.waitUntil(10_000) {
            model().state.value.layoutEditing && model().state.value.editingExportLayout
        }
        rule.onNodeWithText("Arrange export").assertExists()
        rule.onNodeWithText("Done").performClick()
        assertFalse(model().state.value.layoutEditing)
        assertEquals(1280, model().state.value.project!!.export.height)
    }
}
