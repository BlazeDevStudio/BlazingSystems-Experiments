package com.blazingsystems.visualizer.playback

import androidx.media3.exoplayer.video.MediaCodecVideoRenderer

@androidx.annotation.OptIn(androidx.media3.common.util.UnstableApi::class)
internal class StartupSafeVideoRenderer(builder: MediaCodecVideoRenderer.Builder) :
    MediaCodecVideoRenderer(builder) {

    override fun onPositionReset(positionUs: Long, joining: Boolean) {
        val codecBeforeFirstOutput = if (getCodecOutputMediaFormat() == null) getCodec() else null
        super.onPositionReset(positionUs, joining)
        if (codecBeforeFirstOutput != null && getCodec() === codecBeforeFirstOutput) {
            // MediaCodec may lose codec-specific data when flushed before its first output format.
            // Keep the normal position/sink reset, then recreate with fresh CSD on the next render.
            // https://developer.android.com/reference/android/media/MediaCodec#codec-specific-data
            releaseCodec()
        }
    }
}
