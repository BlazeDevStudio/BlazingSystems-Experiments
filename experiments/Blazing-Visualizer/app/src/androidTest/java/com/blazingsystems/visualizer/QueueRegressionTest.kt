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
