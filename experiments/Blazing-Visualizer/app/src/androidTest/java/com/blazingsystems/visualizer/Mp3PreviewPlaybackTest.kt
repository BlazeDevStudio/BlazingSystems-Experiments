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
import com.blazingsystems.visualizer.render.BuiltinScenes
import com.blazingsystems.visualizer.render.SceneView
import com.blazingsystems.visualizer.ui.StudioModel
import java.io.File
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.withTimeout
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
        val uri = Uri.fromFile(file).toString()
        val samples = mutableListOf<Pair<Long, Set<Int>>>()
        val started = SystemClock.elapsedRealtime()
        try {
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
            rule.onNodeWithText("Visualizer", useUnmergedTree = true).performClick()
            rule.waitUntil(15_000) { model().playback.value.sourceUri == uri && model().playback.value.isPlaying }
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
                    "player=${model().playback.value} status=${model().state.value.status}", section.size >= 8)
                return section.count { it.second.intersect(expected).size >= 2 }.toDouble() / section.size
            }
            val first = coverage(1_500_000, 4_500_000, setOf(69, 73, 76))
            val second = coverage(6_000_000, 8_000_000, setOf(72, 76, 79))
            assertTrue("First chord lost visible notes: $first; state=${model().state.value.status}", first >= .8)
            assertTrue("Second chord lost visible notes: $second; state=${model().state.value.status}", second >= .8)
            assertFalse("Full neural analysis must still be gated", model().state.value.analysisReady)
            assertTrue("Temporary notes must not become saved detailed notes", model().state.value.notes.isEmpty())
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
                """{"fixture":"generated-44100hz-stereo-mp3","neuralAnalysisGated":true,"firstChordCoverage":$first,"secondChordCoverage":$second,"coloredCanvasPixels":$coloredPixels,"elapsedMs":${SystemClock.elapsedRealtime()-started},"seekVersion":${model().playback.value.positionVersion}}"""
            )
        } finally {
            rule.runOnUiThread { model().player.clearQueue() }
            neuralLock.unlock()
            file.delete()
        }
    }
}
