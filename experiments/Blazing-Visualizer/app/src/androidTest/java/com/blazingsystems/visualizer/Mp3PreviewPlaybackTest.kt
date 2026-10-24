package com.blazingsystems.visualizer

import android.graphics.Bitmap
import android.graphics.Color
import android.net.Uri
import android.os.SystemClock
import android.view.View
import android.view.ViewGroup
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.lifecycle.ViewModelProvider
import androidx.media3.common.Player
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import com.blazingsystems.visualizer.project.ElementType
import com.blazingsystems.visualizer.audio.PlaybackPcmPreview
import com.blazingsystems.visualizer.analysis.AnalysisResult
import com.blazingsystems.visualizer.analysis.AnalysisKeys
import com.blazingsystems.visualizer.analysis.ModelRunner
import com.blazingsystems.visualizer.analysis.AnalysisParameters
import com.blazingsystems.visualizer.render.PreviewCanvasHealth
import com.blazingsystems.visualizer.render.BuiltinScenes
import com.blazingsystems.visualizer.render.SceneView
import com.blazingsystems.visualizer.ui.StudioModel
import java.io.File
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.withTimeout
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import java.security.MessageDigest
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class Mp3PreviewPlaybackTest {
    @get:Rule(order = 0) val audioPermission = AudioPermissionRule()
    @get:Rule(order = 1) val rule = createAndroidComposeRule<MainActivity>()
    private fun model() = ViewModelProvider(rule.activity)[StudioModel::class.java]
    private fun descendants(view: View): List<View> = buildList {
        add(view)
        if (view is ViewGroup) repeat(view.childCount) { addAll(descendants(view.getChildAt(it))) }
    }

    @Test fun stereoMp3KeepsNotesAndActualCanvasAliveBeforeDetailedAnalysisAndAfterSeeking() {
        val inst = InstrumentationRegistry.getInstrumentation()
        val file = File(rule.activity.cacheDir, "quick-stereo-chords.mp3")
        inst.context.assets.open("audio/quick-stereo-chords.mp3").use { input ->
            file.outputStream().use(input::copyTo)
        }
        rule.waitUntil(15_000) { model().state.value.ready }
        lateinit var neuralLock: Mutex
        rule.runOnUiThread {
            neuralLock = StudioModel::class.java.getDeclaredField("analysisLock").let {
                it.isAccessible = true; it.get(model()) as Mutex
            }
        }
        runBlocking { withTimeout(30_000) { neuralLock.lock() } }
        var ownsLock = true
        val hash = MessageDigest.getInstance("SHA-256").digest(file.readBytes()).joinToString("") { "%02x".format(it) }
        val parameters = AnalysisParameters()
        val key = AnalysisKeys.key(hash, ModelRunner.MODEL_SHA256, parameters)
        val emptyAnalysis = File(rule.activity.filesDir, "analysis-v2/$key.json")
        emptyAnalysis.parentFile!!.mkdirs()
        // A valid empty detailed result must not suppress live estimates from audible PCM.
        emptyAnalysis.writeText(Json.encodeToString(AnalysisResult(key, hash, ModelRunner.MODEL_SHA256,
            parameters, 16_000_000, emptyList())))
        val uri = Uri.fromFile(file).toString()
        val samples = mutableListOf<Pair<Long, Set<Int>>>()
        val started = SystemClock.elapsedRealtime()
        try {
            // Navigate before starting the clock, so Compose idling cannot miss a chord.
            rule.onNodeWithText("Visualizer", useUnmergedTree = true).performClick()
            rule.runOnUiThread {
                model().setScene(BuiltinScenes.noteWheel().let { scene ->
                    scene.copy(backgroundColor = "#FF000000", paletteColor = "#FFFF20FF", layers = scene.layers.filter {
                        it.type == ElementType.NOTE_WHEEL || it.type == ElementType.PIANO_ROLL
                    })
                })
                model().player.setRepeatMode(Player.REPEAT_MODE_OFF)
                model().player.setShuffle(false)
                model().importTracks(listOf(Uri.fromFile(file)))
            }
            rule.waitUntil(15_000) { model().playback.value.sourceUri == uri && model().playback.value.isPlaying }
            val firstPlayerUs = model().playback.value.sourceTimeUs
            val deadline = SystemClock.elapsedRealtime() + 18_000
            while (model().playback.value.sourceTimeUs < 8_000_000 && SystemClock.elapsedRealtime() < deadline) {
                val scene = model().rendered.value
                samples += scene.sourceTimeUs to scene.activeNotes.map { it.pitch }.toSet()
                SystemClock.sleep(80)
            }
            assertTrue("Playback did not advance: ${model().playback.value}", model().playback.value.sourceTimeUs >= 8_000_000)
            fun coverage(start: Long, end: Long, expected: Set<Int>): Double {
                val section = samples.filter { it.first in start..end }
                assertTrue("Insufficient source-time samples in $start..$end: ${section.size}; total=${samples.size} " +
                    "renderRange=${samples.minOfOrNull { it.first }}..${samples.maxOfOrNull { it.first }} " +
                    "firstPlayerUs=$firstPlayerUs player=${model().playback.value} status=${model().state.value.status}", section.size >= 8)
                return section.count { it.second.intersect(expected).size >= 2 }.toDouble() / section.size
            }
            val first = coverage(1_500_000, 4_500_000, setOf(69, 73, 76))
            val second = coverage(6_000_000, 8_000_000, setOf(72, 76, 79))
            assertTrue("First chord lost visible notes: $first; state=${model().state.value.status}", first >= .8)
            assertTrue("Second chord lost visible notes: $second; state=${model().state.value.status}", second >= .8)
            assertFalse("Full neural analysis must still be gated", model().state.value.analysisReady)
            assertTrue("Temporary notes must not become saved detailed notes", model().state.value.notes.isEmpty())
            val pcm = PlaybackPcmPreview.state.value
            assertEquals("The audible session must supply the visualizer", uri, pcm.uri)
            assertTrue("No PCM reached the visualizer: ${model().visualizerReport()}", pcm.receivedChunks > 0)
            assertTrue("Playback PCM produced no features: ${model().visualizerReport()}", pcm.featureFrames > 0)
            rule.waitUntil(5_000) { model().visualizerReport().contains("Input: Playback audio;") }
            neuralLock.unlock()
            ownsLock = false
            rule.waitUntil(10_000) { model().state.value.analysisReady }
            assertEquals(0, model().state.value.analysisNoteCount)
            assertTrue("Live estimates must remain separate from the empty detailed cache", model().state.value.notes.isEmpty())
            rule.waitUntil(5_000) { model().rendered.value.activeNotes.isNotEmpty() }
            val oldVersion = model().playback.value.positionVersion
            rule.runOnUiThread { model().player.seekTo(2_000_000) }
            rule.waitUntil(8_000) {
                model().playback.value.positionVersion > oldVersion &&
                    model().rendered.value.sourceTimeUs in 2_000_000..4_500_000 &&
                    model().rendered.value.activeNotes.count { it.pitch in setOf(69, 73, 76) } >= 2
            }
            rule.runOnUiThread { model().player.pause() }
            var coloredPixels = 0
            val evidence = File(rule.activity.filesDir, "acceptance/mp3-note-preview.png")
            evidence.parentFile!!.mkdirs()
            rule.waitUntil(8_000) {
                rule.runOnUiThread {
                    descendants(rule.activity.window.decorView).filterIsInstance<SceneView>()
                        .singleOrNull()?.bitmap?.let { bitmap ->
                            try {
                                coloredPixels = 0
                                for (y in 0 until bitmap.height step 3) for (x in 0 until bitmap.width step 3) {
                                    val c = bitmap.getPixel(x, y)
                                    if (Color.red(c) > 160 && Color.blue(c) > 160 && Color.green(c) < 100) coloredPixels++
                                }
                                if (coloredPixels > 40) evidence.outputStream().use {
                                    bitmap.compress(Bitmap.CompressFormat.PNG, 100, it)
                                }
                            } finally { bitmap.recycle() }
                        }
                }
                coloredPixels > 40
            }
            File(evidence.parentFile, "mp3-note-preview.json").writeText(
                """{"fixture":"generated-44100hz-stereo-mp3","neuralAnalysisGatedDuringCoverage":true,"emptyDetailedResultKeptLiveNotes":true,"playbackPcmChunks":${pcm.receivedChunks},"playbackFeatureFrames":${pcm.featureFrames},"firstSamplePlayerUs":$firstPlayerUs,"firstChordCoverage":$first,"secondChordCoverage":$second,"coloredCanvasPixels":$coloredPixels,"elapsedMs":${SystemClock.elapsedRealtime()-started},"seekVersion":${model().playback.value.positionVersion}}"""
            )
            assertTrue(PreviewCanvasHealth.status.presentedFrames > 0)
            rule.onNodeWithContentDescription("Playback options").performClick()
            rule.onNodeWithText("Check visualizer").performClick()
            rule.waitUntil(18_000) { model().visualizerCheck.value.completed }
            rule.onNodeWithText("Copy report").performClick()
            val clipboard = rule.activity.getSystemService(android.content.Context.CLIPBOARD_SERVICE) as android.content.ClipboardManager
            val report = clipboard.primaryClip!!.getItemAt(0).text.toString()
            assertTrue(report.contains("Playback PCM:"))
            assertFalse("Report must omit the file address", report.contains(uri))
            assertFalse("Report must omit the file name", report.contains(file.name))
        } finally {
            rule.runOnUiThread { model().player.clearQueue() }
            if (ownsLock) neuralLock.unlock()
            file.delete()
            emptyAnalysis.delete()
        }
    }
}
