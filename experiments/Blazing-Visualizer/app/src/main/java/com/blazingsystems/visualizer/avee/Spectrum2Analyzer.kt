package com.blazingsystems.visualizer.avee

import kotlin.math.*
import kotlinx.serialization.json.*

/** Original Goertzel correlation bank for the observed Spectrum2 data contract.
 * Magnitudes are visualizer amplitudes; this class does not claim to identify notes.
 */
class Spectrum2Analyzer(val settings: JsonObject,private val rate: Int=22050) {
    private fun number(key: String,default: Double)=(settings[key] as? JsonPrimitive)?.doubleOrNull?.takeIf(Double::isFinite) ?: default
    val inputCount=(rate*number("audioDurationMs",60.0).coerceIn(20.0,300.0)/1000).toInt()
    val count=number("sampleOutCount",80.0).toInt().coerceIn(1,512)
    val response=number("smooth",1.0).coerceIn(.1,1.0)
    private val low=number("lowerHz",20.0).coerceIn(.1,rate/2.0-1)
    private val high=number("higherHz",11025.0).coerceIn(low+1,rate/2.0)
    private val linear=number("hzLinearFactor",.5).coerceIn(0.0,1.0)
    private val gap=number("starAndEndGap",0.0).toInt().coerceIn(0,30)
    private val repeats=number("repeatSamples",1.0).toInt().coerceIn(1,6)
    private val mirror=number("mirrorSamples",0.0)!=0.0
    private val shift=number("freqShift",0.0).coerceIn(0.0,1.0)
    val frequencies=List(count) { index ->
        if(index<gap || index>=count-gap) 0.0 else {
            val usable=(count-2*gap).coerceAtLeast(1)
            var fraction=(((index-gap).toDouble()/usable+shift)*repeats)%1.0
            if(mirror) fraction=1-abs(2*fraction-1)
            val logFraction=(fraction*usable/(usable-1).coerceAtLeast(1)).coerceIn(0.0,1.0)
            (low*(high/low).pow(logFraction)*(1-linear)+(low+(high-low)*fraction)*linear).coerceAtMost(rate/2.0)
        }
    }
    private val coefficient=frequencies.map { 2*cos(2*PI*it/rate) }
    private val window=DoubleArray(inputCount) { .5-.5*cos(2*PI*it/(inputCount-1)) }
    private val radius=number("filterRadius",0.0).coerceIn(0.0,20.0)
    private val kernel=if(radius==0.0) doubleArrayOf(1.0) else {
        val half=ceil(2.57*radius).toInt()
        val gaussian=DoubleArray(half*2+1) { exp(-.5*((it-half)/radius).pow(2)) }
        val sum=gaussian.sum();val strength=number("filterStrength",1.0).coerceIn(.1,2.0)
        val detail=DoubleArray(gaussian.size) { (if(it==half) 1.0 else 0.0)-strength*gaussian[it]/sum }
        val norm=detail.sumOf { abs(it) }.coerceAtLeast(1e-9)
        detail.map { it/norm }.toDoubleArray()
    }
    fun analyze(pcm: FloatArray): List<Float> {
        if(count<4) return List(count) { 0f }
        val samples=DoubleArray(inputCount) { (pcm.getOrElse(it){0f}.takeIf(Float::isFinite) ?: 0f)*window[it] }
        val raw=DoubleArray(count) { i ->
            if(frequencies[i]<1) 0.0 else {
                var previous=0.0;var older=0.0;val c=coefficient[i]
                for(sample in samples) { val next=sample+c*previous-older;older=previous;previous=next }
                sqrt(max(0.0,previous*previous+older*older-c*previous*older))*4/inputCount
            }
        }
        val gain=number("outputMultiplier",1.0).coerceIn(.1,3.0)
        return List(count) { i ->
            var v=0.0
            for(k in kernel.indices) v+=kernel[k]*raw[(i+k-kernel.size/2).coerceIn(0,count-1)]
            (v.coerceAtLeast(0.0)*gain).toFloat()
        }
    }
    fun beat(bars: List<Float>): Float {
        if(bars.isEmpty()) return 0f
        val first=(number("beatRangeBarFirst",0.0).coerceIn(0.0,1.0)*(bars.size-1)).toInt()
        val last=(number("beatRangeBarLast",.25).coerceIn(0.0,1.0)*(bars.size-1)).toInt().coerceAtLeast(first)
        val low=number("beatRangeValueLower",0.0);val high=number("beatRangeValueHigher",20.0).coerceAtLeast(low+.001)
        return ((bars.subList(first,last+1).average()*100-low)/(high-low)).toFloat().coerceIn(0f,1f)
    }
}
