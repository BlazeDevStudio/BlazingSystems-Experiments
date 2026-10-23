package com.blazingsystems.visualizer

import android.content.Context
import android.media.MediaCodec
import android.media.MediaCodecInfo
import android.media.MediaFormat
import android.media.MediaMuxer
import android.opengl.GLES20
import android.view.Surface
import com.blazingsystems.visualizer.render.GlTarget
import java.io.File
import java.util.UUID

internal class VideoFixtures(private val context: Context) {
    /** Independently encoded color changes expose a mistaken zero-based export timestamp. */
    fun colorVideo(rotation: Int = 0): File {
        val file = File(context.cacheDir, "background-${UUID.randomUUID()}.mp4")
        val codec = MediaCodec.createEncoderByType(MediaFormat.MIMETYPE_VIDEO_AVC)
        val muxer = MediaMuxer(file.path, MediaMuxer.OutputFormat.MUXER_OUTPUT_MPEG_4)
        var surface: Surface? = null
        var configured = false
        var started = false
        var track = -1
        try {
            muxer.setOrientationHint(rotation)
            codec.configure(MediaFormat.createVideoFormat(MediaFormat.MIMETYPE_VIDEO_AVC, 320, 180).apply {
                setInteger(MediaFormat.KEY_COLOR_FORMAT, MediaCodecInfo.CodecCapabilities.COLOR_FormatSurface)
                setInteger(MediaFormat.KEY_BIT_RATE, 1_000_000)
                setInteger(MediaFormat.KEY_FRAME_RATE, 30)
                setInteger(MediaFormat.KEY_I_FRAME_INTERVAL, 1)
            }, null, null, MediaCodec.CONFIGURE_FLAG_ENCODE)
            configured = true
            val input = codec.createInputSurface().also { surface = it }
            codec.start()
            val info = MediaCodec.BufferInfo()
            fun drain(end: Boolean) {
                val deadline = System.nanoTime() + 30_000_000_000L
                while (true) {
                    val index = codec.dequeueOutputBuffer(info, if (end) 10_000 else 0)
                    when {
                        index == MediaCodec.INFO_TRY_AGAIN_LATER -> {
                            if (!end) return
                            check(System.nanoTime() < deadline) { "Fixture video encoder stalled" }
                        }
                        index == MediaCodec.INFO_OUTPUT_FORMAT_CHANGED -> {
                            check(!started)
                            track = muxer.addTrack(codec.outputFormat)
                            muxer.start(); started = true
                        }
                        index >= 0 -> {
                            try {
                                if (info.size > 0 && info.flags and MediaCodec.BUFFER_FLAG_CODEC_CONFIG == 0) {
                                    val bytes = codec.getOutputBuffer(index)!!
                                    bytes.position(info.offset); bytes.limit(info.offset + info.size)
                                    muxer.writeSampleData(track, bytes, info)
                                }
                                if (info.flags and MediaCodec.BUFFER_FLAG_END_OF_STREAM != 0) return
                            } finally { codec.releaseOutputBuffer(index, false) }
                        }
                    }
                }
            }
            GlTarget.encoder(input, 320, 180).use { target ->
                for (frame in 0 until 36) {
                    GLES20.glClearColor(if (frame < 18) 1f else 0f, if (frame < 18) 0f else 1f, 0f, 1f)
                    GLES20.glClear(GLES20.GL_COLOR_BUFFER_BIT)
                    target.present(frame * 1_000_000L / 30)
                    drain(false)
                }
            }
            codec.signalEndOfInputStream(); drain(true)
            check(started)
            return file
        } catch (failure: Throwable) {
            file.delete(); throw failure
        } finally {
            if (configured) runCatching { codec.stop() }
            codec.release(); surface?.release()
            try { if (started) muxer.stop() } finally { muxer.release() }
        }
    }

}
