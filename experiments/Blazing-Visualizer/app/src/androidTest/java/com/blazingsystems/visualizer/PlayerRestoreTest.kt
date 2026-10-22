package com.blazingsystems.visualizer

import android.net.Uri
import android.os.SystemClock
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import com.blazingsystems.visualizer.playback.PlayerController
import com.blazingsystems.visualizer.project.SourceRef
import java.io.File
import org.junit.*
import org.junit.Assert.*
import org.junit.runner.RunWith

/** No Activity/ViewModel owns this session, so restored Practice state has one owner. */
@RunWith(AndroidJUnit4::class)
class PlayerRestoreTest {
    private val instrument = InstrumentationRegistry.getInstrumentation()
    private val context = instrument.targetContext
    private fun waitUntil(timeout: Long, condition: () -> Boolean) {
        val end = SystemClock.uptimeMillis() + timeout
        while (!condition() && SystemClock.uptimeMillis() < end) SystemClock.sleep(20)
        assertTrue("Timed out waiting for MediaSession", condition())
    }
    private fun clearSession() {
        lateinit var controller: PlayerController
        instrument.runOnMainSync { controller = PlayerController(context) }
        waitUntil(15_000) { controller.state.value.connected }
        instrument.runOnMainSync { controller.clearQueue(); controller.close() }
    }
    @Test
    fun coldQueueRestorationKeepsPendingLoopAndReorderingKeepsPosition() {
        val inst = InstrumentationRegistry.getInstrumentation()
        val tracks = (0..3).map { index ->
            val f = File(context.filesDir, "queue-$index.wav")
            inst.context.assets.open("synthetic.wav").use { input -> f.outputStream().use(input::copyTo) }
            SourceRef(Uri.fromFile(f).toString(), title = "Track $index")
        }
        clearSession()
        lateinit var controller: PlayerController
        instrument.runOnMainSync {
            controller = PlayerController(context)
            controller.restoreQueue(tracks.take(3), 1)
            controller.setPracticeSpeed(.75f)
            controller.setLoop(300_000, 700_000)
        }
        try {
            waitUntil(15_000) {
                controller.state.value.connected && controller.state.value.sourceUri == tracks[1].uri &&
                    controller.state.value.durationUs > 0
            }
            assertFalse(controller.state.value.isPlaying)
            assertEquals(.75f, controller.state.value.speed, .001f)
            assertTrue(controller.state.value.sourceTimeUs in 280_000..350_000)
            instrument.runOnMainSync {
                controller.seekTo(500_000)
                controller.moveQueueItem(1, 2)
                controller.insertQueueItem(tracks[3], 1)
            }
            waitUntil(5_000) { controller.queue.value.map { it.uri } ==
                listOf(tracks[0], tracks[3], tracks[2], tracks[1]).map { it.uri } }
            assertEquals(tracks[1].uri, controller.state.value.sourceUri)
            assertTrue(controller.state.value.sourceTimeUs in 450_000..550_000)
        } finally { instrument.runOnMainSync { controller.clearQueue(); controller.close() } }
    }
    @Test fun reconnectNeverSeeksLiveTrackBUsingSavedTrackALoop() {
        clearSession()
        val file = File(context.filesDir, "live-session.wav")
        instrument.context.assets.open("synthetic.wav").use { input -> file.outputStream().use(input::copyTo) }
        val live = SourceRef(Uri.fromFile(file).toString(), title = "Live B")
        lateinit var first: PlayerController
        var reconnected: PlayerController? = null
        instrument.runOnMainSync { first = PlayerController(context); first.setQueue(listOf(live)) }
        try {
            waitUntil(15_000) { first.state.value.isPlaying }
            instrument.runOnMainSync { first.pause(); first.seekTo(1_200_000); first.setPracticeSpeed(1.1f) }
            waitUntil(5_000) { first.state.value.sourceTimeUs in 1_150_000..1_250_000 }
            instrument.runOnMainSync {
                reconnected = PlayerController(context)
                reconnected!!.restoreQueue(listOf(SourceRef("content://stale/a")))
                reconnected!!.setPracticeSpeed(.5f)
                reconnected!!.setLoop(300_000, 700_000)
            }
            waitUntil(15_000) { reconnected!!.state.value.connected }
            assertEquals(live.uri, reconnected!!.state.value.sourceUri)
            assertTrue(reconnected!!.state.value.sourceTimeUs in 1_150_000..1_250_000)
            assertEquals(1.1f, reconnected!!.state.value.speed, .001f)
        } finally {
            instrument.runOnMainSync {
                reconnected?.close()
                first.clearQueue(); first.close()
            }
        }
    }
}
