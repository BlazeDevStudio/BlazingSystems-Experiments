package com.blazingsystems.visualizer.tuning

import com.blazingsystems.visualizer.avee.Spectrum2Analyzer
import kotlin.math.roundToInt
import kotlinx.serialization.json.JsonObject

/** Microphone adapter for the imported provider's visual amplitudes. */
class LiveSpectrum2 {
    private var bank: Spectrum2Analyzer? = null
    private val rate = 22050
    private val history = FloatArray(rate * 300 / 1000)
    private var lastTimeUs: Long? = null
    private var response = FloatArray(0)

    fun update(samples: ShortArray, timeUs: Long, settings: JsonObject): Pair<List<Float>, Float> {
        require(samples.size == 4096 && timeUs >= 0)
        if (lastTimeUs?.let { timeUs < it } == true) {
            history.fill(0f); lastTimeUs = null; bank = null
        }
        val previous = lastTimeUs
        val captured = if (previous == null) samples.size
            else ((timeUs - previous) * rate / 1_000_000.0).roundToInt().coerceAtLeast(0)
        if (captured > samples.size) history.fill(0f)
        val incoming = captured.coerceAtMost(samples.size)
        if (incoming > 0) {
            System.arraycopy(history, incoming, history, 0, history.size - incoming)
            for (i in 0 until incoming)
                history[history.size - incoming + i] = samples[samples.size - incoming + i] / 32768f
        }
        if (bank?.settings != settings) {
            bank = Spectrum2Analyzer(settings)
            response = FloatArray(bank!!.count)
        }
        val analyzer = bank!!
        val pcm = history.copyOfRange(history.size - analyzer.inputCount, history.size)
        val target = analyzer.analyze(pcm)
        val elapsed = if (previous == null) 1024.0 / rate else (timeUs - previous) / 1_000_000.0
        val blend = (20 * elapsed * analyzer.response).coerceIn(0.0, 1.0).toFloat()
        for (i in response.indices) response[i] += (target[i] - response[i]) * blend
        lastTimeUs = timeUs
        val bars = response.toList()
        return bars to analyzer.beat(bars)
    }
}
