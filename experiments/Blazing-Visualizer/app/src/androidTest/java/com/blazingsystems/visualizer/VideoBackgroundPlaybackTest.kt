package com.blazingsystems.visualizer

import android.graphics.Color
import android.graphics.Bitmap
import android.net.Uri
import android.view.TextureView
import android.view.View
import android.view.ViewGroup
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.captureToImage
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.graphics.asAndroidBitmap
import androidx.compose.ui.graphics.toPixelMap
import androidx.lifecycle.ViewModelProvider
import androidx.media3.common.Player
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import com.blazingsystems.visualizer.project.*
import com.blazingsystems.visualizer.render.SceneView
import com.blazingsystems.visualizer.ui.StudioModel
import java.io.File
import java.util.UUID
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.put
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class VideoBackgroundPlaybackTest {
    @get:Rule(order = 0) val audioPermission = AudioPermissionRule()
    @get:Rule(order = 1) val rule = createAndroidComposeRule<MainActivity>()

    private fun model() = ViewModelProvider(rule.activity)[StudioModel::class.java]

    private fun descendants(view: View): List<View> = buildList {
        add(view)
        if (view is ViewGroup) for (index in 0 until view.childCount)
            addAll(descendants(view.getChildAt(index)))
    }

    private fun videoColor(): Int? {
        var color: Int? = null
        rule.runOnUiThread {
            val video = descendants(rule.activity.window.decorView)
                .filterIsInstance<TextureView>().firstOrNull { it !is SceneView && it.isAvailable }
            video?.bitmap?.let { frame ->
                try { color = frame.getPixel(frame.width / 2, frame.height / 2) }
                finally { frame.recycle() }
            }
        }
        return color
    }

    @Test fun pausedVideoSeeksWithTheSessionAndAudioRestoresAnOpaqueVisualizer() {
        val inst = InstrumentationRegistry.getInstrumentation()
        val video = VideoFixtures(rule.activity).colorVideo()
        val audio = File(rule.activity.cacheDir, "background-audio-${UUID.randomUUID()}.wav")
        inst.context.assets.open("synthetic.wav").use { input -> audio.outputStream().use(input::copyTo) }
        val videoUri = Uri.fromFile(video).toString()
        val audioUri = Uri.fromFile(audio).toString()
        try {
            rule.runOnUiThread { model().importTracks(listOf(Uri.fromFile(video), Uri.fromFile(audio))) }
            rule.waitUntil(30_000) {
                model().playback.value.sourceUri == videoUri &&
                    model().state.value.project?.source?.hasVideo == true &&
                    model().state.value.analysisReady &&
                    model().playback.value.durationUs > 1_000_000
            }
            val player = model().player
            rule.runOnUiThread {
                player.pause()
                player.setRepeatMode(Player.REPEAT_MODE_OFF)
                player.setShuffle(false)
                player.setPracticeSpeed(.5f)
                player.seekTo(100_000)
                model().setScene(Scene(backgroundColor = "#FF123456", layers = listOf(Layer(type = ElementType.SHAPE,
                    transform = Transform(width = .25f, height = .25f),
                    properties = buildJsonObject { put("shape", "rect"); put("color", "#FFFF0000") }))))
            }
            rule.waitUntil(20_000) { videoColor()?.let { Color.red(it) > 170 && Color.green(it) < 80 } == true }
            rule.runOnUiThread { player.seekTo(800_000) }
            rule.waitUntil(20_000) { videoColor()?.let { Color.green(it) > 170 && Color.red(it) < 80 } == true }
            assertSame(player, model().player)
            assertEquals(.5f, player.state.value.speed, .001f)
            assertFalse(player.state.value.isPlaying)
            assertTrue("Paused video and session clocks differ: ${player.state.value}",
                player.state.value.sourceTimeUs in 740_000L..860_000L)
            rule.waitUntil(10_000) {
                var ready = false
                rule.runOnUiThread {
                    descendants(rule.activity.window.decorView).filterIsInstance<SceneView>()
                        .singleOrNull()?.bitmap?.let { frame ->
                            try {
                                val pixel = frame.getPixel(frame.width / 2, frame.height / 2)
                                ready = Color.red(pixel) > 170 && Color.green(pixel) < 80
                            } finally { frame.recycle() }
                        }
                }
                ready
            }
            rule.runOnUiThread {
                val visualizer = descendants(rule.activity.window.decorView).filterIsInstance<SceneView>().single()
                assertFalse(visualizer.isOpaque)
                val frame = requireNotNull(visualizer.bitmap)
                try { assertEquals(0, Color.alpha(frame.getPixel(5, 5))) }
                finally { frame.recycle() }
            }
            assertTrue(rule.activity.window.decorView.isHardwareAccelerated)
            val composed = rule.onNodeWithTag("visualizer-scene").captureToImage()
            val pixels = composed.toPixelMap()
            var green = 0
            var red = 0
            for (y in 0 until pixels.height step 4) for (x in 0 until pixels.width step 4) {
                val pixel = pixels[x, y]
                if (pixel.green > .65f && pixel.red < .3f && pixel.blue < .3f) green++
                if (pixel.red > .65f && pixel.green < .3f && pixel.blue < .3f) red++
            }
            assertTrue("Hardware composition hid the video background", green > 50)
            assertTrue("Hardware composition hid the foreground", red > 10)
            val evidence = File(rule.activity.filesDir, "acceptance/video-background-preview.png")
            evidence.parentFile!!.mkdirs()
            evidence.outputStream().use { composed.asAndroidBitmap().compress(Bitmap.CompressFormat.PNG, 100, it) }
            rule.runOnUiThread { player.next() }
            rule.waitUntil(30_000) {
                player.state.value.sourceUri == audioUri &&
                    model().state.value.project?.source?.uri == audioUri
            }
            rule.waitUntil(10_000) {
                var opaque = false
                rule.runOnUiThread {
                    val visualizer = descendants(rule.activity.window.decorView).filterIsInstance<SceneView>()
                        .singleOrNull()
                    if (visualizer?.isOpaque == true) visualizer.bitmap?.let { frame ->
                        try { opaque = frame.getPixel(5, 5) == Color.rgb(18, 52, 86) }
                        finally { frame.recycle() }
                    }
                }
                opaque
            }
            assertSame(player, model().player)
            assertFalse(model().state.value.project!!.source.hasVideo)
        } finally {
            rule.runOnUiThread { model().player.pause(); model().player.clearQueue() }
            video.delete(); audio.delete()
        }
    }
}
