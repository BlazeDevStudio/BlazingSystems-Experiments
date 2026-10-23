package com.blazingsystems.visualizer

import com.blazingsystems.visualizer.avee.Spectrum2Analyzer
import kotlin.math.*
import kotlinx.serialization.json.*
import org.junit.Assert.*
import org.junit.Test

class Spectrum2Test {
    private fun settings(linear: Int=0)=buildJsonObject {
        put("sampleOutCount",121);put("lowerHz",110);put("higherHz",1760)
        put("hzLinearFactor",linear);put("audioDurationMs",100);put("filterRadius",0)
    }
    @Test fun arbitraryFrequencyCorrelationFinds440HzAndSilenceStaysSilent() {
        val bank=Spectrum2Analyzer(settings())
        val bars=bank.analyze(FloatArray(bank.inputCount) { (.4*sin(2*PI*440*it/22050)).toFloat() })
        val peak=bars.indices.maxBy { bars[it] }
        assertEquals(440.0,bank.frequencies[peak],.01)
        assertTrue(bars[peak]>.35f)
        assertTrue(bars[peak]>bars[peak-8]*4)
        assertTrue(bank.analyze(FloatArray(bank.inputCount)).all { it==0f })
    }
    @Test fun logAndLinearLayoutsUseTheirDifferentEndDenominators() {
        assertEquals(1760.0,Spectrum2Analyzer(settings()).frequencies.last(),.001)
        assertEquals(110+1650*120.0/121,Spectrum2Analyzer(settings(1)).frequencies.last(),.001)
    }
}
