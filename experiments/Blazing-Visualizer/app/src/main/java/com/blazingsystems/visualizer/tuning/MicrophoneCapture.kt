package com.blazingsystems.visualizer.tuning

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.media.AudioFormat
import android.media.AudioRecord
import android.media.MediaRecorder
import java.util.ArrayDeque
import kotlinx.coroutines.*

/** Releases recording hardware on background, sheet dismissal and job cancellation. */
class MicrophoneCapture(private val context: Context) : AutoCloseable {
    @Volatile private var active: AudioRecord? = null

    suspend fun run(a4Hz: Double, onPitch: (PitchReading?) -> Unit) =
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
            val recorder = AudioRecord(
                MediaRecorder.AudioSource.MIC, rate,
                AudioFormat.CHANNEL_IN_MONO, AudioFormat.ENCODING_PCM_16BIT,
                (minimum * 2).coerceAtLeast(8192),
            )
            if (recorder.state != AudioRecord.STATE_INITIALIZED) {
                recorder.release()
                error("Microphone not available")
            }
            active = recorder
            val samples = ShortArray(4096)
            val history = ArrayDeque<Double>()
            var received = 0
            try {
                recorder.startRecording()
                while (currentCoroutineContext().isActive) {
                    val count = recorder.read(
                        samples, received, samples.size - received, AudioRecord.READ_BLOCKING,
                    )
                    if (count < 0) break
                    if (count == 0) continue
                    received += count
                    if (received == samples.size) {
                        val reading = YinTuner.estimate(samples, rate, a4Hz)
                        if (reading == null) {
                            history.clear()
                            onPitch(null)
                        } else {
                            history.addLast(reading.frequencyHz)
                            if (history.size > 5) history.removeFirst()
                            val median = history.toList().sorted()[history.size / 2]
                            onPitch(YinTuner.fromHz(median, a4Hz, reading.confidence))
                        }
                        System.arraycopy(samples, 2048, samples, 0, 2048)
                        received = 2048
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
