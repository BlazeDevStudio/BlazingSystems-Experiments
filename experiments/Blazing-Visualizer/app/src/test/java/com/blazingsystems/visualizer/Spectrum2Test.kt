package com.blazingsystems.visualizer

import com.blazingsystems.visualizer.avee.Spectrum2Analyzer
import com.blazingsystems.visualizer.audio.AudioFeatures
import com.blazingsystems.visualizer.audio.DecodedAudio
import java.io.DataOutputStream
import java.nio.file.Files
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
    @Test fun recordedResponseIsIndependentOfSeekAndSettingsOrder() {
        val root=Files.createTempDirectory("spectrum-response").toFile()
        try {
            DataOutputStream(root.resolve("mono.f32").outputStream()).use { out ->
                repeat(22050) { i ->
                    val v=if(i<11025) (.35*sin(2*PI*440*i/22050)).toFloat() else 0f
                    out.writeInt(Integer.reverseBytes(v.toRawBits()))
                }
            }
            val profile=JsonObject(settings()+("sampleProvider" to JsonPrimitive("Spectrum2")))
            AudioFeatures(DecodedAudio("test",22050,1,22050,root.path)).use { audio ->
                val first=audio.at(350_000,profile=profile).aveeSpectrum
                assertTrue(first.max()>.2f)
                audio.at(900_000,profile=profile)
                assertEquals(first,audio.at(350_000,profile=profile).aveeSpectrum)
                audio.at(350_000,profile=JsonObject(profile+("hzLinearFactor" to JsonPrimitive(1))))
                assertEquals(first,audio.at(350_000,profile=profile).aveeSpectrum)
            }
        } finally { root.deleteRecursively() }
    }
}
