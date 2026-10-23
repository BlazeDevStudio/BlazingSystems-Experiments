package com.blazingsystems.visualizer.tuning

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.media.AudioFormat
import android.media.AudioManager
import android.media.AudioRecord
import android.media.MediaRecorder
import kotlinx.coroutines.*

/** Releases recording hardware on background, sheet dismissal and job cancellation. */
class MicrophoneCapture(private val context: Context) : AutoCloseable {
    @Volatile private var active: AudioRecord? = null

    suspend fun run(
        a4Hz: Double,
        onPitch: suspend (PitchReading?) -> Unit,
        onSamples: suspend (FloatArray) -> Unit = {},
    ) {
        val smoother=PitchSmoother()
        runFrames { samples, _ ->
            onSamples(FloatArray(2048) { samples[it+2048]/32768f })
            onPitch(smoother.update(YinTuner.estimate(samples,22050,a4Hz),a4Hz))
        }
    }

    suspend fun runFrames(onFrame: suspend (ShortArray,Long) -> Unit) =
        withContext(Dispatchers.IO) {
            val rate = 22050
            val minimum = AudioRecord.getMinBufferSize(
                rate, AudioFormat.CHANNEL_IN_MONO, AudioFormat.ENCODING_PCM_16BIT,
            )
            require(minimum > 0) { "Microphone sample format is not supported" }
            check(context.checkSelfPermission(Manifest.permission.RECORD_AUDIO) ==
                PackageManager.PERMISSION_GRANTED) {
                "Microphone permission was revoked; grant access and try again."
            }
            val manager = context.getSystemService(Context.AUDIO_SERVICE) as? AudioManager
            val source = if (manager?.getProperty(
                    AudioManager.PROPERTY_SUPPORT_AUDIO_SOURCE_UNPROCESSED,
                ) == "true") MediaRecorder.AudioSource.UNPROCESSED
                else MediaRecorder.AudioSource.VOICE_RECOGNITION
            val recorder = AudioRecord(
                source, rate,
                AudioFormat.CHANNEL_IN_MONO, AudioFormat.ENCODING_PCM_16BIT,
                (minimum * 2).coerceAtLeast(8192),
            )
            if (recorder.state != AudioRecord.STATE_INITIALIZED) {
                recorder.release()
                error("Microphone not available")
            }
            active = recorder
            val samples = ShortArray(4096)
            var received = 0
            var totalSamples=0L
            try {
                currentCoroutineContext().ensureActive()
                recorder.startRecording()
                check(recorder.recordingState == AudioRecord.RECORDSTATE_RECORDING) {
                    "Microphone could not start recording"
                }
                while (currentCoroutineContext().isActive) {
                    val count = recorder.read(
                        samples, received, samples.size - received, AudioRecord.READ_BLOCKING,
                    )
                    currentCoroutineContext().ensureActive()
                    check(count >= 0) { "Microphone read failed (AudioRecord error $count)" }
                    if (count == 0) continue
                    received += count
                    totalSamples += count
                    if (received == samples.size) {
                        currentCoroutineContext().ensureActive()
                        onFrame(samples.copyOf(),totalSamples*1_000_000/rate)
                        System.arraycopy(samples,1024,samples,0,3072)
                        received = 3072
                    }
                }
            } finally { close() }
        }

    override fun close() {
        val recorder = active
        active = null
        recorder?.let {
            runCatching { it.stop() }
            runCatching { it.release() }
        }
    }
}
