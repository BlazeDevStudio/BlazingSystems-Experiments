package com.blazingsystems.visualizer

import android.content.Context
import androidx.test.platform.app.InstrumentationRegistry
import java.io.File
import java.util.UUID

/** Identical MP4 bytes on API26/API36; older platform muxers alter the first audio timestamp. */
internal class TimedAudioVideoFixture(private val context: Context) {
    data class Result(val file: File, val gapStartUs: Long, val gapEndUs: Long)

    fun create(): Result {
        val file = File(context.cacheDir, "audio-timeline-${UUID.randomUUID()}.mp4")
        try {
            InstrumentationRegistry.getInstrumentation().context.assets.open("timed-audio-video.mp4")
                .use { input -> file.outputStream().use(input::copyTo) }
            return Result(file, GAP_START_US, GAP_END_US)
        } catch (failure: Throwable) {
            file.delete()
            throw failure
        }
    }

    companion object {
        // Synthetic green H264 video and 440Hz mono AAC, encoded/remuxed once with FFmpeg7.1.
        // Independently verified MP4 boxes: movie timescale1000/duration1200; audio timescale22050;
        // elst[(300,-1),(626,0)]; stts[(2,1024),(1,7639),(4,1024)]. No downloaded media.
        // 6224 bytes; SHA2564008faec8bd308183297363e538852aa263daf36d2e291514592855cb6f1ba67.
        const val FIRST_AUDIO_PTS_US = 300_000L
        const val GAP_START_US = 439_319L
        const val GAP_END_US = 739_319L
        const val AUDIO_END_US = 925_079L
        const val VIDEO_DURATION_US = 1_200_000L
    }
}
