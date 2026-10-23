package com.blazingsystems.visualizer

import android.content.Context
import android.media.MediaCodec
import android.media.MediaCodecInfo
import android.media.MediaExtractor
import android.media.MediaFormat
import android.media.MediaMuxer
import java.io.File
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.util.UUID
import kotlin.math.PI
import kotlin.math.sin

/** Real short AAC segments at 300ms and after a 300ms gap, inside a 1.2s video. */
internal class TimedAudioVideoFixture(private val context: Context) {
    data class Result(val file: File, val gapStartUs: Long, val gapEndUs: Long)
    private data class Packet(val bytes: ByteArray, val timeUs: Long, val flags: Int)
    private data class Audio(val format: MediaFormat, val packets: List<Packet>)

    fun create(): Result {
        val audio = encodeTone()
        check(audio.packets.size >= 6)
        val video = VideoFixtures(context).colorVideo()
        val file = File(context.cacheDir, "audio-timeline-${UUID.randomUUID()}.mp4")
        val extractor = MediaExtractor()
        val muxer = MediaMuxer(file.path, MediaMuxer.OutputFormat.MUXER_OUTPUT_MPEG_4)
        var started = false
        val split = audio.packets.size / 2
        val origin = audio.packets.first().timeUs
        val gapStart = 300_000 + audio.packets[split].timeUs - origin
        try {
            extractor.setDataSource(video.path)
            val videoTrack = muxer.addTrack(extractor.getTrackFormat(0))
            val audioTrack = muxer.addTrack(audio.format)
            muxer.start(); started = true
            extractor.selectTrack(0)
            val buffer = ByteBuffer.allocateDirect(1_048_576)
            val info = MediaCodec.BufferInfo()
            while (true) {
                buffer.clear()
                val size = extractor.readSampleData(buffer, 0)
                if (size < 0) break
                info.set(0, size, extractor.sampleTime, extractor.sampleFlags)
                muxer.writeSampleData(videoTrack, buffer, info)
                extractor.advance()
            }
            audio.packets.forEachIndexed { index, packet ->
                val timeUs = 300_000 + packet.timeUs - origin + if (index >= split) 300_000 else 0
                info.set(0, packet.bytes.size, timeUs, packet.flags)
                muxer.writeSampleData(audioTrack, ByteBuffer.wrap(packet.bytes), info)
            }
            return Result(file, gapStart, gapStart + 300_000)
        } catch (failure: Throwable) {
            file.delete(); throw failure
        } finally {
            extractor.release()
            try { if (started) muxer.stop() } finally { muxer.release(); video.delete() }
        }
    }

    private fun encodeTone(): Audio {
        val rate = 22050
        val frameCount = 6 * 1024
        val codec = MediaCodec.createEncoderByType(MediaFormat.MIMETYPE_AUDIO_AAC)
        val packets = mutableListOf<Packet>()
        var format: MediaFormat? = null
        var configured = false
        try {
            codec.configure(MediaFormat.createAudioFormat(MediaFormat.MIMETYPE_AUDIO_AAC, rate, 1).apply {
                setInteger(MediaFormat.KEY_AAC_PROFILE, MediaCodecInfo.CodecProfileLevel.AACObjectLC)
                setInteger(MediaFormat.KEY_BIT_RATE, 64000)
            }, null, null, MediaCodec.CONFIGURE_FLAG_ENCODE)
            configured = true
            codec.start()
            var sent = 0
            var inputEnded = false
            val info = MediaCodec.BufferInfo()
            val deadline = System.nanoTime() + 30_000_000_000L
            while (true) {
                check(System.nanoTime() < deadline) { "Fixture AAC encoder stalled" }
                if (!inputEnded) {
                    val index = codec.dequeueInputBuffer(10_000)
                    if (index >= 0) {
                        val buffer = codec.getInputBuffer(index)!!.order(ByteOrder.LITTLE_ENDIAN)
                        buffer.clear()
                        val count = minOf(1024, frameCount - sent, buffer.remaining() / 2)
                        repeat(count) { frame ->
                            buffer.putShort((sin(2 * PI * 440 * (sent + frame) / rate) * 14000).toInt().toShort())
                        }
                        codec.queueInputBuffer(index, 0, count * 2, sent * 1_000_000L / rate,
                            if (count == 0) MediaCodec.BUFFER_FLAG_END_OF_STREAM else 0)
                        sent += count
                        inputEnded = count == 0
                    }
                }
                when (val index = codec.dequeueOutputBuffer(info, 10_000)) {
                    MediaCodec.INFO_OUTPUT_FORMAT_CHANGED -> format = codec.outputFormat
                    else -> if (index >= 0) {
                        try {
                            if (info.size > 0 && info.flags and MediaCodec.BUFFER_FLAG_CODEC_CONFIG == 0) {
                                val buffer = codec.getOutputBuffer(index)!!.duplicate()
                                buffer.position(info.offset); buffer.limit(info.offset + info.size)
                                val bytes = ByteArray(info.size).also { buffer.get(it) }
                                packets += Packet(bytes, info.presentationTimeUs,
                                    info.flags and MediaCodec.BUFFER_FLAG_END_OF_STREAM.inv())
                            }
                            if (info.flags and MediaCodec.BUFFER_FLAG_END_OF_STREAM != 0)
                                return Audio(requireNotNull(format), packets)
                        } finally { codec.releaseOutputBuffer(index, false) }
                    }
                }
            }
        } finally {
            if (configured) runCatching { codec.stop() }
            codec.release()
        }
    }
}
