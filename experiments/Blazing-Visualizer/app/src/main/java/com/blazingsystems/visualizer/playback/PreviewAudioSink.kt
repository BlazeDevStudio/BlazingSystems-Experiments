package com.blazingsystems.visualizer.playback

import androidx.media3.common.Format
import androidx.media3.common.MimeTypes
import androidx.media3.exoplayer.audio.AudioSink
import androidx.media3.exoplayer.audio.ForwardingAudioSink
import com.blazingsystems.visualizer.audio.PlaybackPcmFormat
import com.blazingsystems.visualizer.audio.PlaybackPcmPreview
import java.nio.ByteBuffer

/** Observes accepted input PCM without changing sink position, effects, speed, or session handling. */
@androidx.annotation.OptIn(androidx.media3.common.util.UnstableApi::class)
internal class PreviewAudioSink(
    delegate: AudioSink,
    private val consumed: (PlaybackPcmFormat, ByteArray, Long) -> Unit = PlaybackPcmPreview::offer,
    private val invalidated: () -> Unit = PlaybackPcmPreview::invalidate,
) : ForwardingAudioSink(delegate) {
    private var format: PlaybackPcmFormat? = null
    private var inputBuffer: ByteBuffer? = null
    private var initialPosition = 0
    private var copiedPosition = 0
    private var inputTimeUs = Long.MIN_VALUE
    private var streamOffsetUs = 0L

    override fun configure(inputFormat: Format, specifiedBufferSize: Int, outputChannels: IntArray?) {
        super.configure(inputFormat, specifiedBufferSize, outputChannels)
        format = if (inputFormat.sampleMimeType == MimeTypes.AUDIO_RAW)
            PlaybackPcmFormat(inputFormat.sampleRate, inputFormat.channelCount, inputFormat.pcmEncoding)
                .takeIf { it.supported } else null
        clearInput()
        invalidated()
    }

    override fun setOutputStreamOffsetUs(outputStreamOffsetUs: Long) {
        super.setOutputStreamOffsetUs(outputStreamOffsetUs)
        streamOffsetUs = outputStreamOffsetUs
    }

    override fun handleBuffer(buffer: ByteBuffer, presentationTimeUs: Long, encodedAccessUnitCount: Int): Boolean {
        if (inputBuffer !== buffer || inputTimeUs != presentationTimeUs) {
            inputBuffer = buffer
            initialPosition = buffer.position()
            copiedPosition = initialPosition
            inputTimeUs = presentationTimeUs
        }
        val handled = super.handleBuffer(buffer, presentationTimeUs, encodedAccessUnitCount)
        val end = buffer.position()
        val pcm = format
        val alignedEnd = if (pcm == null) copiedPosition else initialPosition +
            (end - initialPosition) / pcm.frameBytes * pcm.frameBytes
        if (pcm != null && alignedEnd > copiedPosition) {
            // Only bytes accepted by the delegate are copied. Repeated partial writes
            // retain their original buffer timestamp plus the consumed sample offset.
            // Hold a partial interleaved sample until all its bytes have been consumed.
            val bytes = ByteArray(alignedEnd - copiedPosition)
            buffer.duplicate().apply { position(copiedPosition); limit(alignedEnd) }.get(bytes)
            val timeUs = presentationTimeUs - streamOffsetUs +
                (copiedPosition - initialPosition) / pcm.frameBytes * 1_000_000L / pcm.sampleRate
            runCatching { consumed(pcm, bytes, timeUs) }
            copiedPosition = alignedEnd
        }
        if (handled) clearInput()
        return handled
    }

    override fun flush() {
        super.flush()
        clearInput()
        invalidated()
    }

    override fun reset() {
        super.reset()
        clearInput()
        format = null
        invalidated()
    }

    private fun clearInput() { inputBuffer = null; inputTimeUs = Long.MIN_VALUE }
}
