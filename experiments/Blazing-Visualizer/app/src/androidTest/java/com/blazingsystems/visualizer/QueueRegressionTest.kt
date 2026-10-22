package com.blazingsystems.visualizer

import android.app.Application
import android.net.Uri
import androidx.lifecycle.*
import androidx.test.platform.app.InstrumentationRegistry
import com.blazingsystems.visualizer.ui.StudioModel
import java.io.File
import org.junit.*
import org.junit.Assert.*

class QueueRegressionTest {
    /** Real Media3 end-of-song transitions must not need a user to tap Next. */
    @Test
    fun naturalTrackEndAdvancesAndRepeatAllWrapsToFirstTrack() {
        val instrumentation = InstrumentationRegistry.getInstrumentation()
        val context = instrumentation.targetContext
        val tracks = listOf("repeat-first", "repeat-second").map { filename ->
            val output = File(context.filesDir, "$filename.wav")
            instrumentation.context.assets.open("synthetic.wav").use { input ->
                output.outputStream().use(input::copyTo)
            }
            com.blazingsystems.visualizer.project.SourceRef(
                uri = Uri.fromFile(output).toString(), title = filename,
            )
        }
        lateinit var player: com.blazingsystems.visualizer.playback.PlayerController
        fun awaitPlayback(label: String, condition: () -> Boolean) {
            val stop = System.currentTimeMillis() + 20_000
            while (System.currentTimeMillis() < stop && !condition()) Thread.sleep(50)
            assertTrue("$label: playback state = ${player.state.value}", condition())
        }
        try {
            instrumentation.runOnMainSync {
                player = com.blazingsystems.visualizer.playback.PlayerController(context)
                player.setQueue(tracks, 0)
            }
            awaitPlayback("first track becomes playable") {
                player.state.value.sourceUri == tracks[0].uri &&
                    player.state.value.durationUs > 500_000 &&
                    player.state.value.connected
            }
            instrumentation.runOnMainSync {
                // Settings can persist across tests, force the publicly supported mode.
                repeat(3) {
                    if (player.state.value.repeatMode !=
                        androidx.media3.common.Player.REPEAT_MODE_ALL) player.cycleRepeatMode()
                }
                assertEquals(androidx.media3.common.Player.REPEAT_MODE_ALL,
                    player.state.value.repeatMode)
                player.seekTo(player.state.value.durationUs - 120_000)
            }
            awaitPlayback("first track naturally advances without tapping Next") {
                player.state.value.sourceUri == tracks[1].uri &&
                    player.state.value.isPlaying
            }
            awaitPlayback("second track has a known duration") {
                player.state.value.durationUs > 500_000
            }
            instrumentation.runOnMainSync {
                player.seekTo(player.state.value.durationUs - 120_000)
            }
            awaitPlayback("repeat all wraps to first after the last track") {
                player.state.value.sourceUri == tracks[0].uri &&
                    player.state.value.isPlaying
            }
        } finally {
            instrumentation.runOnMainSync { player.close() }
        }
    }

    @Test
    fun removingQueuedTrackUpdatesMedia3Playlist() {
        val inst = InstrumentationRegistry.getInstrumentation()
        val context = inst.targetContext
        val uris =
            listOf("queue-a", "queue-b", "queue-c").map { name ->
                val f = File(context.filesDir, "$name.wav")
                inst.context.assets.open("synthetic.wav").use { input ->
                    f.outputStream().use(input::copyTo)
                }
                Uri.fromFile(f)
            }
        lateinit var model: StudioModel
        val store = ViewModelStore()
        val owner =
            object : ViewModelStoreOwner {
                override val viewModelStore = store
            }
        fun waitUntil(timeout: Long, predicate: () -> Boolean) {
            val deadline = System.currentTimeMillis() + timeout
            while (!predicate() && System.currentTimeMillis() < deadline) Thread.sleep(50)
            assertTrue("Playback condition timed out: ${model.playback.value}", predicate())
        }
        try {
            inst.runOnMainSync {
                model =
                    ViewModelProvider(
                        owner,
                        ViewModelProvider.AndroidViewModelFactory.getInstance(
                            context.applicationContext as Application,
                        ),
                    )[StudioModel::class.java]
                model.importTracks(uris)
            }
            waitUntil(30_000) {
                model.playback.value.sourceUri == uris[0].toString() &&
                    model.playback.value.durationUs > 0
            }
            inst.runOnMainSync {
                model.player.pause()
                model.removeQueue(uris[1].toString())
                model.player.next()
            }
            waitUntil(10_000) { model.playback.value.sourceUri == uris[2].toString() }
            assertEquals(uris[2].toString(), model.playback.value.sourceUri)
            waitUntil(30_000) { model.state.value.project?.source?.uri == uris[2].toString() }
        } finally {
            inst.runOnMainSync { store.clear() }
        }
    }
}
