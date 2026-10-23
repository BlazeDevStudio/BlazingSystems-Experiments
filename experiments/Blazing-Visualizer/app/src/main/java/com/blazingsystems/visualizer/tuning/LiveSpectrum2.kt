package com.blazingsystems.visualizer.tuning

import com.blazingsystems.visualizer.avee.Spectrum2Analyzer
import kotlinx.serialization.json.JsonObject

/** Microphone adapter for the imported provider's visual amplitudes. */
class LiveSpectrum2 {
    private var bank: Spectrum2Analyzer? = null

    fun update(samples: ShortArray, timeUs: Long, settings: JsonObject): Pair<List<Float>, Float> {
        if (bank?.settings != settings) bank = Spectrum2Analyzer(settings)
        val analyzer = bank!!
        val pcm = FloatArray(analyzer.inputCount) { i ->
            samples.getOrElse(samples.size - analyzer.inputCount + i) { 0 } / 32768f
        }
        val bars = analyzer.analyze(pcm)
        return bars to analyzer.beat(bars)
    }
}
