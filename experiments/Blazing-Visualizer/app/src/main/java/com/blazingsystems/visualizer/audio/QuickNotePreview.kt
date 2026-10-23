package com.blazingsystems.visualizer.audio

import android.content.Context
import android.net.Uri
import com.blazingsystems.visualizer.project.FeatureFrame
import com.blazingsystems.visualizer.tuning.LiveNoteTracker
import com.blazingsystems.visualizer.tuning.LiveSpectrum2
import kotlin.math.abs
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.ensureActive
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.flow.flowOn
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.jsonPrimitive

/** Temporary source-clock features. Never serialized into projects or the analysis cache. */
data class QuickPreviewFrames(val sourceUri: String? = null, val frames: List<FeatureFrame> = emptyList()) {
    fun withFrame(uri: String, frame: FeatureFrame): QuickPreviewFrames {
        if (uri != sourceUri) return this
        val next = (frames.filterNot { it.sourceTimeUs == frame.sourceTimeUs } + frame)
            .sortedBy { it.sourceTimeUs }.takeLast(96)
        return copy(frames = next)
    }

    fun at(uri: String?, sourceTimeUs: Long): FeatureFrame? {
        if (uri == null || uri != sourceUri) return null
        return frames.lastOrNull { it.sourceTimeUs <= sourceTimeUs }
            ?.takeIf { sourceTimeUs - it.sourceTimeUs <= 150_000 }
    }
}

/** Bounded decode + FFT/YIN feedback, independent of full-file hashing and neural inference. */
class QuickNotePreview(private val context: Context) {
    fun frames(uri: String, startUs: Long, durationUs: Long = 2_000_000,
               profile: JsonObject = JsonObject(emptyMap())): Flow<FeatureFrame> = flow {
        require(startUs >= 0 && durationUs in 1..3_000_000)
        var resampler: PcmResampler? = null
        var tracker = LiveNoteTracker()
        var bank = LiveSpectrum2()
        var pending = FloatArray(0)
        var originUs = 0L
        var offset = 0L
        var expectedUs: Long? = null

        suspend fun accept(mono: FloatArray) {
            pending += mono
            while (pending.size >= 4096) {
                currentCoroutineContext().ensureActive()
                val samples = ShortArray(4096) { (pending[it].coerceIn(-1f, 1f) * 32767).toInt().toShort() }
                val timeUs = originUs + (offset + 4096) * 1_000_000 / 22050
                var features = tracker.update(samples, timeUs).features
                if (profile["sampleProvider"]?.jsonPrimitive?.content == "Spectrum2") {
                    val (bars, beat) = bank.update(samples, timeUs, profile)
                    features = features.copy(aveeSpectrum = bars, beat = beat)
                }
                emit(features)
                pending = pending.copyOfRange(1024, pending.size)
                offset += 1024
            }
        }

        PcmDecoder(context).decode(Uri.parse(uri), startUs, durationUs).collect { chunk ->
            if (chunk.synthesizedSilence) {
                emit(FeatureFrame(chunk.sourceTimeUs))
            } else {
                val previous = resampler
                if (previous == null || previous.sampleRate != chunk.sampleRate || previous.channels != chunk.channels ||
                    expectedUs?.let { abs(chunk.sourceTimeUs - it) > 20_000 } == true) {
                    resampler = PcmResampler(chunk.sampleRate, chunk.channels)
                    originUs = chunk.sourceTimeUs; offset = 0; pending = FloatArray(0)
                    tracker = LiveNoteTracker(); bank = LiveSpectrum2()
                }
                expectedUs = chunk.sourceTimeUs + chunk.samples.size / chunk.channels * 1_000_000L / chunk.sampleRate
                accept(resampler!!.feed(chunk.samples))
            }
        }
        resampler?.let { accept(it.feed(FloatArray(0), end = true)) }
    }.flowOn(Dispatchers.Default)
}
