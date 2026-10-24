package com.blazingsystems.visualizer

import com.blazingsystems.visualizer.audio.PcmResampler
import com.blazingsystems.visualizer.tuning.LiveNoteTracker
import java.io.File
import java.nio.ByteBuffer
import java.nio.ByteOrder

/** Local-only CLI: inspect private decoded PCM with the actual production DSP classes.
 * Input: interleaved little-endian float32 PCM, rate, channels, maximum seconds.
 * Output contains measurements only. No files or audio are uploaded by this tool.
 */
object LocalPcmProbe {
    @JvmStatic fun main(args: Array<String>) {
        require(args.size == 4) { "PCM file, sample rate, channels, max seconds required" }
        val rate = args[1].toInt()
        val channels = args[2].toInt()
        val limit = rate.toLong() * args[3].toInt()
        val resampler = PcmResampler(rate, channels)
        val tracker = LiveNoteTracker()
        var sourceFrames = 0L
        var offset = 0L
        var pending = FloatArray(0)
        var frames = 0
        var nonempty = 0
        var resampleNs = 0L
        var trackerNs = 0L
        var maxRms = 0f
        val nearFive = mutableSetOf<Int>()
        val began = System.nanoTime()
        fun accept(mono: FloatArray) {
            pending += mono
            while (pending.size >= 4096) {
                val samples = ShortArray(4096) { (pending[it].coerceIn(-1f, 1f) * 32767).toInt().toShort() }
                val time = (offset + 4096) * 1_000_000 / 22050
                val start = System.nanoTime()
                val features = tracker.update(samples, time).features
                trackerNs += System.nanoTime() - start
                frames++
                if (features.notes.any { it.startUs <= time && time < it.endUs }) nonempty++
                maxRms = maxOf(maxRms, features.rms)
                if (time in 4_750_000..5_250_000) nearFive += features.notes.map { it.pitch }
                pending = pending.copyOfRange(1024, pending.size)
                offset += 1024
            }
        }
        File(args[0]).inputStream().use { input ->
            while (sourceFrames < limit) {
                val bytes = input.readNBytes(minOf(1152L, limit - sourceFrames).toInt() * channels * 4)
                if (bytes.isEmpty()) break
                val buffer = ByteBuffer.wrap(bytes).order(ByteOrder.LITTLE_ENDIAN)
                val pcm = FloatArray(bytes.size / 4) { buffer.float }
                val start = System.nanoTime()
                val mono = resampler.feed(pcm)
                resampleNs += System.nanoTime() - start
                sourceFrames += pcm.size / channels
                accept(mono)
            }
        }
        accept(resampler.feed(FloatArray(0), end = true))
        println("""{"rate":$rate,"channels":$channels,"sourceSeconds":${sourceFrames.toDouble()/rate},"featureFrames":$frames,"framesWithActiveNotes":$nonempty,"maxRms":$maxRms,"pitchesNearFiveSeconds":${nearFive.sorted()},"resampleMs":${resampleNs/1_000_000},"trackerMs":${trackerNs/1_000_000},"elapsedMs":${(System.nanoTime()-began)/1_000_000}}""")
    }
}
