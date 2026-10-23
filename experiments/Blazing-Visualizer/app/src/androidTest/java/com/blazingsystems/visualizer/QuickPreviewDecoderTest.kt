package com.blazingsystems.visualizer

import android.net.Uri
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import com.blazingsystems.visualizer.audio.PcmDecoder
import com.blazingsystems.visualizer.audio.QuickNotePreview
import java.io.File
import java.nio.ByteBuffer
import java.nio.ByteOrder
import kotlin.math.PI
import kotlin.math.sin
import kotlinx.coroutines.flow.toList
import kotlinx.coroutines.runBlocking
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class QuickPreviewDecoderTest {
    @Test fun seekingUsesOnlyTheRequestedSourceWindowAndHearsTheNewPitch() = runBlocking {
        val context = InstrumentationRegistry.getInstrumentation().targetContext
        val file = File(context.cacheDir, "quick-seek-two-tones.wav")
        val rate = 22050
        val count = rate * 3
        val bytes = ByteBuffer.allocate(44 + count * 2).order(ByteOrder.LITTLE_ENDIAN)
        bytes.put("RIFF".toByteArray()).putInt(36 + count * 2).put("WAVEfmt ".toByteArray())
            .putInt(16).putShort(1).putShort(1).putInt(rate).putInt(rate * 2).putShort(2)
            .putShort(16).put("data".toByteArray()).putInt(count * 2)
        repeat(count) { i ->
            val frequency = if (i < rate) 440 else 660
            bytes.putShort((sin(2 * PI * frequency * i / rate) * 14000).toInt().toShort())
        }
        file.writeBytes(bytes.array())
        try {
            val uri = Uri.fromFile(file)
            val pcm = PcmDecoder(context).decode(uri, 1_100_000, 400_000).toList()
            assertTrue(pcm.isNotEmpty())
            assertTrue(pcm.all { it.sourceTimeUs >= 1_100_000 })
            assertTrue(pcm.all { it.sourceTimeUs + it.samples.size * 1_000_000L / rate <= 1_500_050 })
            assertTrue(pcm.sumOf { it.samples.size } in 8800..8830)
            val frames = QuickNotePreview(context).frames(uri.toString(), 1_100_000, 400_000).toList()
            assertTrue(frames.isNotEmpty())
            assertTrue(frames.all { it.sourceTimeUs in 1_100_000..1_500_050 })
            assertTrue(frames.any { frame -> frame.notes.any { it.pitch == 76 } })
            assertTrue(frames.none { frame -> frame.notes.any { it.pitch == 69 } })
        } finally { file.delete() }
    }
}
