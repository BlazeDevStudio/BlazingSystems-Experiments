package com.blazingsystems.visualizer.audio

import android.content.Context
import android.media.*
import android.net.Uri
import java.nio.ByteOrder
import kotlin.math.ceil
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*

data class PcmChunk(
    val samples: FloatArray,
    val sampleRate: Int,
    val channels: Int,
    val sourceTimeUs: Long,
    val synthesizedSilence: Boolean = false,
)

class PcmDecoder(private val context: Context) {
    fun decode(uri: Uri, startUs: Long = 0, durationUs: Long? = null): Flow<PcmChunk> = flow {
        require(startUs >= 0 && (durationUs == null || durationUs > 0))
        val endUs = durationUs?.let { startUs + it.coerceAtMost(Long.MAX_VALUE - startUs) }
        val extractor = MediaExtractor()
        var decoder: MediaCodec? = null
        try {
            extractor.setDataSource(context, uri, null)
            val track =
                (0 until extractor.trackCount).firstOrNull {
                    extractor
                        .getTrackFormat(it)
                        .getString(MediaFormat.KEY_MIME)
                        ?.startsWith("audio/") == true
                }
            if (track == null) {
                val videos = (0 until extractor.trackCount).map(extractor::getTrackFormat).filter {
                    it.getString(MediaFormat.KEY_MIME)?.startsWith("video/") == true
                }
                require(videos.isNotEmpty()) { "No decodable audio or video track" }
                val length = videos.mapNotNull {
                    if (it.containsKey(MediaFormat.KEY_DURATION)) it.getLong(MediaFormat.KEY_DURATION) else null
                }.maxOrNull() ?: 0
                require(length > 0) { "The silent video has no usable duration" }
                val stop = minOf(length, endUs ?: length)
                var frame = startUs * 22050 / 1_000_000
                val lastFrame = stop * 22050 / 1_000_000
                while (frame < lastFrame) {
                    currentCoroutineContext().ensureActive()
                    val count = minOf(2048L, lastFrame - frame).toInt()
                    emit(PcmChunk(FloatArray(count), 22050, 1, frame * 1_000_000 / 22050,
                        synthesizedSilence = true))
                    frame += count
                }
                return@flow
            }
            extractor.selectTrack(track)
            if (startUs > 0) extractor.seekTo(startUs, MediaExtractor.SEEK_TO_PREVIOUS_SYNC)
            val format = extractor.getTrackFormat(track)
            val codec = MediaCodec.createDecoderByType(format.getString(MediaFormat.KEY_MIME)!!)
            decoder = codec
            codec.configure(format, null, null, 0)
            codec.start()
            var rate = format.getInteger(MediaFormat.KEY_SAMPLE_RATE)
            var channels = format.getInteger(MediaFormat.KEY_CHANNEL_COUNT)
            var encoding = AudioFormat.ENCODING_PCM_16BIT
            var inputEnded = false
            var outputEnded = false
            val info = MediaCodec.BufferInfo()
            while (!outputEnded) {
                currentCoroutineContext().ensureActive()
                if (!inputEnded) {
                    val index = codec.dequeueInputBuffer(10_000)
                    if (index >= 0) {
                        val buffer = codec.getInputBuffer(index)!!
                        val size = extractor.readSampleData(buffer, 0)
                        if (size < 0 || endUs != null && extractor.sampleTime >= endUs) {
                            codec.queueInputBuffer(
                                index,
                                0,
                                0,
                                0,
                                MediaCodec.BUFFER_FLAG_END_OF_STREAM,
                            )
                            inputEnded = true
                        } else {
                            codec.queueInputBuffer(
                                index,
                                0,
                                size,
                                extractor.sampleTime.coerceAtLeast(0),
                                0,
                            )
                            extractor.advance()
                        }
                    }
                }
                when (val index = codec.dequeueOutputBuffer(info, 10_000)) {
                    MediaCodec.INFO_OUTPUT_FORMAT_CHANGED -> {
                        val out = codec.outputFormat
                        rate = out.getInteger(MediaFormat.KEY_SAMPLE_RATE)
                        channels = out.getInteger(MediaFormat.KEY_CHANNEL_COUNT)
                        encoding =
                            if (out.containsKey(MediaFormat.KEY_PCM_ENCODING))
                                out.getInteger(MediaFormat.KEY_PCM_ENCODING)
                            else AudioFormat.ENCODING_PCM_16BIT
                    }
                    else ->
                        if (index >= 0) {
                            try {
                                if (info.size > 0) {
                                    val buffer =
                                        codec
                                            .getOutputBuffer(index)!!
                                            .duplicate()
                                            .order(ByteOrder.LITTLE_ENDIAN)
                                    buffer.position(info.offset)
                                    buffer.limit(info.offset + info.size)
                                    val samples =
                                        when (encoding) {
                                            AudioFormat.ENCODING_PCM_FLOAT ->
                                                FloatArray(info.size / 4) {
                                                    buffer.float.coerceIn(-1f, 1f)
                                                }
                                            AudioFormat.ENCODING_PCM_16BIT ->
                                                FloatArray(info.size / 2) { buffer.short / 32768f }
                                            else -> error("Unsupported decoded PCM format")
                                        }
                                    val count = samples.size / channels
                                    val first = ceil((startUs - info.presentationTimeUs) * rate / 1_000_000.0)
                                        .toInt().coerceIn(0, count)
                                    val last = endUs?.let {
                                        ceil((it - info.presentationTimeUs) * rate / 1_000_000.0)
                                            .toInt().coerceIn(0, count)
                                    } ?: count
                                    if (last > first) emit(PcmChunk(
                                        samples.copyOfRange(first * channels, last * channels), rate, channels,
                                        (info.presentationTimeUs + first * 1_000_000L / rate).coerceAtLeast(0),
                                    ))
                                    if (endUs != null && info.presentationTimeUs + count * 1_000_000L / rate >= endUs)
                                        outputEnded = true
                                }
                                outputEnded = outputEnded ||
                                    info.flags and MediaCodec.BUFFER_FLAG_END_OF_STREAM != 0
                            } finally {
                                codec.releaseOutputBuffer(index, false)
                            }
                        }
                }
            }
        } finally {
            decoder?.let {
                runCatching { it.stop() }
                it.release()
            }
            extractor.release()
        }
    }
}
