package com.blazingsystems.visualizer

import androidx.media3.common.C
import androidx.media3.common.Format
import androidx.media3.common.MimeTypes
import androidx.media3.exoplayer.audio.AudioSink
import com.blazingsystems.visualizer.audio.*
import com.blazingsystems.visualizer.playback.PreviewAudioSink
import java.lang.reflect.Proxy
import java.nio.ByteBuffer
import java.nio.ByteOrder
import kotlin.math.PI
import kotlin.math.sin
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.*
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

@OptIn(ExperimentalCoroutinesApi::class)
@androidx.annotation.OptIn(androidx.media3.common.util.UnstableApi::class)
@RunWith(RobolectricTestRunner::class)
@Config(sdk = [33])
class PlaybackPcmPreviewTest {
    @Test fun supportedPcmFormatsKeepSignedAmplitudeAndRejectNonFiniteFloats() {
        assertArrayEquals(floatArrayOf(-1f, 0f, 32767f / 32768), decodePlaybackPcm(
            byteArrayOf(0, -128, 0, 0, -1, 127), C.ENCODING_PCM_16BIT), .00001f)
        assertArrayEquals(floatArrayOf(-1f, 0f, 8388607f / 8388608), decodePlaybackPcm(
            byteArrayOf(0, 0, -128, 0, 0, 0, -1, -1, 127), C.ENCODING_PCM_24BIT), .00001f)
        assertArrayEquals(floatArrayOf(-1f, 0f, 1f), decodePlaybackPcm(
            byteArrayOf(0, 0, 0, -128, 0, 0, 0, 0, -1, -1, -1, 127), C.ENCODING_PCM_32BIT), .00001f)
        val floats = ByteBuffer.allocate(16).order(ByteOrder.LITTLE_ENDIAN)
            .putFloat(-.5f).putFloat(Float.NaN).putFloat(Float.POSITIVE_INFINITY).putFloat(2f).array()
        assertArrayEquals(floatArrayOf(-.5f, 0f, 0f, 1f), decodePlaybackPcm(floats, C.ENCODING_PCM_FLOAT), 0f)
    }

    @Test fun sinkTapsOnlyConsumedBytesAndOffsetsRepeatedPartialWrites() {
        val captured = mutableListOf<Pair<Long, ByteArray>>()
        var invalidations = 0
        val delegate = Proxy.newProxyInstance(AudioSink::class.java.classLoader, arrayOf(AudioSink::class.java)) { _, method, args ->
            if (method.name == "handleBuffer") {
                val buffer = args!![0] as ByteBuffer
                buffer.position((buffer.position() + 3).coerceAtMost(buffer.limit()))
                !buffer.hasRemaining()
            } else null
        } as AudioSink
        val sink = PreviewAudioSink(delegate, { _, bytes, time -> captured += time to bytes }, { invalidations++ })
        sink.configure(Format.Builder().setSampleMimeType(MimeTypes.AUDIO_RAW)
            .setSampleRate(1000).setChannelCount(2).setPcmEncoding(C.ENCODING_PCM_16BIT).build(), 0, null)
        val buffer = ByteBuffer.wrap(byteArrayOf(99, 98, 1, 2, 3, 4, 5, 6, 7, 8))
        buffer.position(2)
        sink.setOutputStreamOffsetUs(750_000)
        assertFalse(sink.handleBuffer(buffer, 2_000_000, 1))
        assertEquals(5, buffer.position())
        assertTrue("Do not emit half an interleaved PCM sample", captured.isEmpty())
        assertFalse(sink.handleBuffer(buffer, 2_000_000, 1))
        assertTrue(sink.handleBuffer(buffer, 2_000_000, 1))
        assertEquals(listOf(1_250_000L, 1_251_000L), captured.map { it.first })
        assertArrayEquals(byteArrayOf(1, 2, 3, 4), captured[0].second)
        assertArrayEquals(byteArrayOf(5, 6, 7, 8), captured[1].second)
        sink.flush()
        assertTrue("Flush invalidates queued preview PCM", invalidations > 0)
    }

    @Test fun sourceChangeAndSeekDiscardQueuedPcmFromThePreviousGeneration() = runTest {
        val hub = PlaybackPcmPreviewHub(backgroundScope) { testScheduler.currentTime }
        val format = PlaybackPcmFormat(22050, 1, C.ENCODING_PCM_16BIT)
        val tone = ByteBuffer.allocate(8192).order(ByteOrder.LITTLE_ENDIAN).apply {
            repeat(4096) { putShort((sin(2 * PI * 440 * it / 22050) * 12000).toInt().toShort()) }
        }.array()
        hub.setSource("old")
        hub.offer(format, tone, 0)
        hub.setSource("new")
        runCurrent()
        assertEquals("new", hub.state.value.uri)
        assertEquals(0L, hub.state.value.receivedChunks)
        assertTrue(hub.state.value.frames.frames.isEmpty())
        // More than 4096 input samples account for the resampler's bounded lookahead.
        hub.offer(format, tone, 0)
        hub.offer(format, tone, 185_759)
        runCurrent()
        val current = hub.state.value
        assertEquals(2L, current.receivedChunks)
        assertTrue(current.frames.frames.any { it.notes.any { note -> note.pitch == 69 } })
        assertEquals(current.generation, current.frames.positionVersion)
        hub.offer(format, tone, 371_519)
        hub.invalidate()
        runCurrent()
        assertTrue(hub.state.value.generation > current.generation)
        assertEquals(0L, hub.state.value.receivedChunks)
        assertTrue(hub.state.value.frames.frames.isEmpty())
    }
}
