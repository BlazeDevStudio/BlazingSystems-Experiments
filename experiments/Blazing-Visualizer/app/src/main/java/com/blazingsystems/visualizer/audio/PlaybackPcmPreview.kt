package com.blazingsystems.visualizer.audio

import android.os.SystemClock
import androidx.media3.common.C
import com.blazingsystems.visualizer.project.FeatureFrame
import com.blazingsystems.visualizer.tuning.LiveNoteTracker
import com.blazingsystems.visualizer.tuning.LiveSpectrum2
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.util.concurrent.atomic.AtomicLong
import kotlin.math.abs
import kotlin.math.sqrt
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.channels.Channel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.jsonPrimitive

data class PlaybackPreviewState(
    val uri: String? = null,
    val generation: Long = 0,
    val frames: QuickPreviewFrames = QuickPreviewFrames(),
    val receivedChunks: Long = 0,
    val featureFrames: Long = 0,
    val sampleRate: Int = 0,
    val channels: Int = 0,
    val lastSourceTimeUs: Long? = null,
    val lastReceivedMs: Long? = null,
    val rms: Float = 0f,
    val error: String? = null,
)

/** A bounded observer of PCM accepted by the player's audio sink; it never decodes a second stream. */
object PlaybackPcmPreview {
    private val hub = PlaybackPcmPreviewHub(CoroutineScope(SupervisorJob() + Dispatchers.Default)) {
        SystemClock.elapsedRealtime()
    }
    val state: StateFlow<PlaybackPreviewState> = hub.state
    fun setProfile(profile: JsonObject) = hub.setProfile(profile)
    fun setSource(uri: String?) = hub.setSource(uri)
    fun invalidate() = hub.invalidate()
    internal fun offer(format: PlaybackPcmFormat, bytes: ByteArray, sourceTimeUs: Long) =
        hub.offer(format, bytes, sourceTimeUs)
}

internal data class PlaybackPcmFormat(val sampleRate: Int, val channels: Int, val encoding: Int) {
    val sampleBytes: Int get() = when (encoding) {
        C.ENCODING_PCM_8BIT -> 1
        C.ENCODING_PCM_16BIT -> 2
        C.ENCODING_PCM_24BIT -> 3
        C.ENCODING_PCM_32BIT, C.ENCODING_PCM_FLOAT -> 4
        else -> 0
    }
    val frameBytes: Int get() = sampleBytes * channels
    val supported: Boolean get() = sampleRate > 0 && channels in 1..8 && sampleBytes != 0
}

/** Media3 raw PCM uses little endian samples. Invalid floating samples must not poison the FFT. */
internal fun decodePlaybackPcm(bytes: ByteArray, encoding: Int): FloatArray {
    val buffer = ByteBuffer.wrap(bytes).order(ByteOrder.LITTLE_ENDIAN)
    val size = when (encoding) {
        C.ENCODING_PCM_8BIT -> 1
        C.ENCODING_PCM_16BIT -> 2
        C.ENCODING_PCM_24BIT -> 3
        C.ENCODING_PCM_32BIT, C.ENCODING_PCM_FLOAT -> 4
        else -> error("Unsupported playback PCM encoding: $encoding")
    }
    require(bytes.size % size == 0)
    return FloatArray(bytes.size / size) {
        when (encoding) {
            C.ENCODING_PCM_8BIT -> ((buffer.get().toInt() and 255) - 128) / 128f
            C.ENCODING_PCM_16BIT -> buffer.short / 32768f
            C.ENCODING_PCM_24BIT -> {
                val value = (buffer.get().toInt() and 255) or
                    ((buffer.get().toInt() and 255) shl 8) or (buffer.get().toInt() shl 16)
                value / 8388608f
            }
            C.ENCODING_PCM_32BIT -> (buffer.int / 2147483648.0).toFloat()
            else -> buffer.float.let { value -> if (value.isFinite()) value.coerceIn(-1f, 1f) else 0f }
        }
    }
}

internal class PlaybackPcmPreviewHub(scope: CoroutineScope, private val clockMs: () -> Long) {
    private data class Packet(val generation: Long, val serial: Long, val format: PlaybackPcmFormat,
        val bytes: ByteArray, val sourceTimeUs: Long, val receivedMs: Long)
    private val mutable = MutableStateFlow(PlaybackPreviewState())
    val state: StateFlow<PlaybackPreviewState> = mutable
    private val guard = Any()
    private val serial = AtomicLong()
    private val packets = Channel<Packet>(16)
    @Volatile private var profile = JsonObject(emptyMap())

    init {
        scope.launch {
            var worker: Worker? = null
            var previousSerial = -1L
            for (packet in packets) {
                val before = mutable.value
                if (before.uri == null || packet.generation != before.generation) continue
                try {
                    val current = worker
                    if (current == null || current.generation != packet.generation || current.format != packet.format ||
                        previousSerial + 1 != packet.serial ||
                        current.expectedUs?.let { abs(packet.sourceTimeUs - it) > 20_000 } == true) {
                        worker = Worker(packet.generation, packet.format, packet.sourceTimeUs, profile)
                    }
                    previousSerial = packet.serial
                    val samples = decodePlaybackPcm(packet.bytes, packet.format.encoding)
                    require(samples.size % packet.format.channels == 0)
                    val features = worker!!.accept(samples)
                    worker!!.expectedUs = packet.sourceTimeUs + samples.size / packet.format.channels *
                        1_000_000L / packet.format.sampleRate
                    synchronized(guard) {
                        val latest = mutable.value
                        // A seek/source/format reset can happen while resampling or estimating notes.
                        if (latest.generation == packet.generation) {
                            var cache = latest.frames
                            for (frame in features) cache = cache.withFrame(latest.uri!!, frame)
                            mutable.value = latest.copy(frames = cache, receivedChunks = latest.receivedChunks + 1,
                                featureFrames = latest.featureFrames + features.size,
                                sampleRate = packet.format.sampleRate, channels = packet.format.channels,
                                lastSourceTimeUs = worker!!.expectedUs, lastReceivedMs = packet.receivedMs,
                                rms = features.lastOrNull()?.rms ?: sqrt(samples.sumOf { (it * it).toDouble() } /
                                    samples.size.coerceAtLeast(1)).toFloat(), error = null)
                        }
                    }
                } catch (failure: Exception) {
                    worker = null
                    synchronized(guard) {
                        if (mutable.value.generation == packet.generation)
                            mutable.value = mutable.value.copy(error = failure.message ?: "Playback PCM preview failed")
                    }
                }
            }
        }
    }

    fun setSource(uri: String?) = synchronized(guard) {
        if (uri != mutable.value.uri) reset(uri)
    }
    fun setProfile(value: JsonObject) = synchronized(guard) {
        if (profile != value) { profile = value; reset(mutable.value.uri) }
    }
    fun invalidate() = synchronized(guard) { reset(mutable.value.uri) }
    private fun reset(uri: String?) {
        val generation = mutable.value.generation + 1
        mutable.value = PlaybackPreviewState(uri, generation, QuickPreviewFrames(uri, positionVersion = generation))
    }

    /** No suspension, blocking send, or DSP on the audio-renderer thread. A dropped packet resets DSP. */
    fun offer(format: PlaybackPcmFormat, bytes: ByteArray, sourceTimeUs: Long) {
        val snapshot = mutable.value
        if (snapshot.uri == null || !format.supported || bytes.isEmpty()) return
        packets.trySend(Packet(snapshot.generation, serial.incrementAndGet(), format, bytes, sourceTimeUs, clockMs()))
    }

    private class Worker(val generation: Long, val format: PlaybackPcmFormat, val originUs: Long,
        val profile: JsonObject) {
        val resampler = PcmResampler(format.sampleRate, format.channels)
        val tracker = LiveNoteTracker()
        val spectrum = LiveSpectrum2()
        var pending = FloatArray(0)
        var offset = 0L
        var expectedUs: Long? = null
        fun accept(samples: FloatArray): List<FeatureFrame> {
            pending += resampler.feed(samples)
            val frames = ArrayList<FeatureFrame>()
            while (pending.size >= 4096) {
                val window = ShortArray(4096) { (pending[it].coerceIn(-1f, 1f) * 32767).toInt().toShort() }
                val timeUs = originUs + (offset + 4096) * 1_000_000 / 22050
                if (timeUs >= 0) {
                    var frame = tracker.update(window, timeUs).features
                    if (profile["sampleProvider"]?.jsonPrimitive?.content == "Spectrum2") {
                        val (bars, beat) = spectrum.update(window, timeUs, profile)
                        frame = frame.copy(aveeSpectrum = bars, beat = beat)
                    }
                    frames += frame
                }
                pending = pending.copyOfRange(1024, pending.size)
                offset += 1024
            }
            return frames
        }
    }
}
