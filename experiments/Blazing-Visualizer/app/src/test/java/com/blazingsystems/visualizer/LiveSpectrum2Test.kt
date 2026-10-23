package com.blazingsystems.visualizer

import com.blazingsystems.visualizer.avee.Spectrum2Analyzer
import com.blazingsystems.visualizer.tuning.LiveSpectrum2
import kotlin.math.*
import kotlinx.serialization.json.*
import org.junit.Assert.*
import org.junit.Test

class LiveSpectrum2Test {
    private fun settings(smooth: Float=1f)=buildJsonObject {
        put("sampleOutCount",41);put("lowerHz",110);put("higherHz",1760)
        put("hzLinearFactor",0);put("audioDurationMs",300);put("smooth",smooth)
    }
    private fun window(end: Int)=ShortArray(4096) { i ->
        (.4*sin(2*PI*440*(end-4096+i)/22050)*32767).toInt().toShort()
    }
    @Test fun longWindowUsesEarlierCaptureSamplesRatherThanPermanentZeroPadding() {
        val profile=settings();val live=LiveSpectrum2();var output=emptyList<Float>()
        for(end in 4096..14336 step 1024) output=live.update(window(end),end*1_000_000L/22050,profile).first
        val bank=Spectrum2Analyzer(profile)
        val expected=bank.analyze(FloatArray(bank.inputCount) { i ->
            (.4*sin(2*PI*440*(14336-bank.inputCount+i)/22050)).toFloat()
        })
        val index=bank.frequencies.indices.minBy { abs(bank.frequencies[it]-440) }
        assertEquals(expected[index],output[index],.015f)
    }
    @Test fun responseControlsAttackAndReleaseAtTheCaptureClock() {
        fun frames(smooth: Float): Pair<Float,Float> {
            val profile=settings(smooth);val live=LiveSpectrum2()
            live.update(ShortArray(4096),185_759,profile)
            val attack=live.update(window(5120),232_199,profile).first.max()
            var release=emptyList<Float>()
            for(i in 1..10) release=live.update(ShortArray(4096),232_199+i*46_440L,profile).first
            return attack to release.max()
        }
        val fast=frames(1f);val slow=frames(.1f)
        assertTrue("slow attack=${slow.first}, fast=${fast.first}",fast.first>slow.first*3)
        assertTrue("slow release=${slow.second}, fast=${fast.second}",slow.second>fast.second+.001f)
    }
}
