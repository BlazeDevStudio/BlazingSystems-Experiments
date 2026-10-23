package com.blazingsystems.visualizer

import android.app.Application
import android.net.Uri
import android.os.SystemClock
import androidx.lifecycle.ViewModelStore
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import com.blazingsystems.visualizer.ui.StudioModel
import java.io.File
import java.nio.ByteBuffer
import java.nio.ByteOrder
import kotlin.math.PI
import kotlin.math.sin
import kotlinx.coroutines.sync.Mutex
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class PreviewStartupTest {
    private val instrument = InstrumentationRegistry.getInstrumentation()
    private val app = instrument.targetContext.applicationContext as Application
    private fun waitUntil(timeoutMs: Long, condition: () -> Boolean) {
        val end = SystemClock.uptimeMillis() + timeoutMs
        while (!condition() && SystemClock.uptimeMillis() < end) SystemClock.sleep(20)
        assertTrue("Timed out waiting for independent quick note feedback", condition())
    }

    @Test fun notesAppearWhileFullNeuralAnalysisIsStillWaiting() {
        val file = File(app.cacheDir, "quick-preview-a4.wav")
        val frames = 22050 * 8
        val bytes = ByteBuffer.allocate(44 + frames * 2).order(ByteOrder.LITTLE_ENDIAN)
        bytes.put("RIFF".toByteArray()).putInt(36 + frames * 2).put("WAVEfmt ".toByteArray())
            .putInt(16).putShort(1).putShort(1).putInt(22050).putInt(44100).putShort(2)
            .putShort(16).put("data".toByteArray()).putInt(frames * 2)
        repeat(frames) { bytes.putShort((sin(2 * PI * 440 * it / 22050) * 14000).toInt().toShort()) }
        file.writeBytes(bytes.array())
        val store = ViewModelStore()
        lateinit var model: StudioModel
        lateinit var neuralLock: Mutex
        var ownsLock = false
        var modelCreated = false
        try {
            instrument.runOnMainSync {
                model = StudioModel(app)
                modelCreated = true
                store.put("preview-startup", model)
                // Gate only the existing full-file inference. This deliberately leaves
                // playback and any independent quick estimator free to make progress.
                neuralLock = StudioModel::class.java.getDeclaredField("analysisLock").let {
                    it.isAccessible = true; it.get(model) as Mutex
                }
                ownsLock = neuralLock.tryLock()
            }
            assertTrue("Test must own the neural-analysis gate", ownsLock)
            waitUntil(10_000) { model.state.value.ready }
            val start = SystemClock.elapsedRealtime()
            instrument.runOnMainSync { model.importTracks(listOf(Uri.fromFile(file))) }
            waitUntil(15_000) {
                model.playback.value.sourceUri == Uri.fromFile(file).toString() && model.playback.value.isPlaying
            }
            waitUntil(4_000) { model.rendered.value.activeNotes.any { it.pitch == 69 } }
            assertNotNull("Detailed analysis must still be pending", model.state.value.progress)
            assertTrue("Quick estimates must not be saved as final note analysis", model.state.value.notes.isEmpty())
            File(app.filesDir, "acceptance").mkdirs()
            File(app.filesDir, "acceptance/quick-preview.json").writeText(
                "{\"fixture\":\"generated-a4-440hz\",\"neuralAnalysisGated\":true,\"firstVisibleNoteMs\":" +
                    (SystemClock.elapsedRealtime() - start) + "}")
        } finally {
            if (ownsLock) neuralLock.unlock()
            instrument.runOnMainSync {
                if (modelCreated) model.player.clearQueue()
                store.clear()
            }
            file.delete()
        }
    }
}
