package com.blazingsystems.visualizer.tuning

import com.NAudio.FastFourierTransform
import com.blazingsystems.visualizer.avee.AveeSpectrumAnalyzer
import com.blazingsystems.visualizer.project.*
import kotlin.math.*

data class LiveNoteFrame(val features: FeatureFrame, val pitch: PitchReading?)

/** Six conservative simultaneous estimates; precise YIN remains monophonic.
 * Octave doublings and dense low chords can be ambiguous in microphone audio.
 */
class LiveNoteTracker(private val rate: Int = 22050, private val a4: Double = 440.0) {
    private data class Peak(val hz: Double,val amplitude: Float) {
        fun midi(a4: Double)=(69+12*log2(hz/a4)).roundToInt().coerceIn(0,127)
    }
    private data class Held(val event: NoteEvent,val seen: Long)
    private val analyzer=AveeSpectrumAnalyzer()
    private val smoother=PitchSmoother()
    private val active=mutableMapOf<Int,Held>()
    private val recent=mutableListOf<NoteEvent>()
    private val hann=FloatArray(4096) { (.5-.5*cos(2*PI*it/4095)).toFloat() }
    private var last=-1L
    private var serial=0L
    init { require(rate in 8000..48000 && a4 in 400.0..480.0) }

    fun update(samples: ShortArray,sourceTimeUs: Long): LiveNoteFrame {
        require(samples.size==4096 && sourceTimeUs>=0)
        if(sourceTimeUs<last) { active.clear();recent.clear();smoother.update(null,a4) }
        last=sourceTimeUs
        val expired=active.filterValues { sourceTimeUs-it.seen>=120_000 }.keys.toList()
        expired.forEach { pitch -> active.remove(pitch)?.event?.let(recent::add) }
        val pcm=FloatArray(4096) { samples[it]/32768f }
        val spectrum=analyzer.analyze(pcm.copyOfRange(2048,4096),rate)
        val candidates=if(spectrum.rms<.012f) emptyList() else peaks(pcm)
        if(spectrum.rms<.012f) {
            active.values.forEach { recent+=it.event.copy(endUs=sourceTimeUs) };active.clear()
        }
        val precise=if(candidates.size==1) YinTuner.estimate(samples,rate,a4)?.takeIf {
            abs(1200*log2(it.frequencyHz/candidates.single().hz))<70
        } else null
        val pitch=smoother.update(precise,a4)
        for(candidate in candidates) {
            val midi=pitch?.midi ?: candidate.midi(a4)
            val previous=active[midi]
            active[midi]=Held(NoteEvent(previous?.event?.id ?: "live-${++serial}-$midi",midi,
                previous?.event?.startUs ?: sourceTimeUs,sourceTimeUs+120_000,
                candidate.amplitude.coerceIn(0f,1f),pitch?.confidence?.toFloat() ?: .9f),sourceTimeUs)
        }
        recent.removeAll { sourceTimeUs-it.endUs>350_000 }
        if(recent.size>96) recent.subList(0,recent.size-96).clear()
        val notes=(recent+active.values.map { it.event }).sortedBy { it.pitch }
        return LiveNoteFrame(FeatureFrame(sourceTimeUs,spectrum.rms,spectrum.spectrum,spectrum.waveform,notes),pitch)
    }

    private fun peaks(pcm: FloatArray): List<Peak> {
        val mean=pcm.sumOf { it.toDouble() }/pcm.size
        val fft=Array(4096) { FastFourierTransform.Complex(((pcm[it]-mean)*hann[it]).toFloat(),0f) }
        FastFourierTransform.FFT(true,fft)
        val magnitudes=FloatArray(2048) { hypot(fft[it].re(),fft[it].im())*4 }
        val floor=magnitudes.drop(2).sorted()[1023]
        val first=max(2,(32*4096.0/rate).toInt())
        val last=min(2046,ceil(4200*4096.0/rate).toInt())
        val highest=(first..last).maxOf { magnitudes[it] }
        val threshold=maxOf(.004f,highest*.045f,floor*8)
        val peaks=(first..last).mapNotNull { i ->
            val level=magnitudes[i]
            if(level<threshold || level<=magnitudes[i-1] || level<magnitudes[i+1]) return@mapNotNull null
            val left=ln(max(1e-12,magnitudes[i-1].toDouble()))
            val middle=ln(max(1e-12,level.toDouble()))
            val right=ln(max(1e-12,magnitudes[i+1].toDouble()))
            val denominator=left-2*middle+right
            val offset=if(abs(denominator)<1e-12) 0.0 else (.5*(left-right)/denominator).coerceIn(-.5,.5)
            val hz=(i+offset)*rate/4096
            if(hz !in 32.0..4200.0) null else Peak(hz,level)
        }.groupBy { it.midi(a4) }.values.map { it.maxBy { p->p.amplitude } }.sortedBy { it.hz }
        val fundamentals=mutableListOf<Peak>()
        for(peak in peaks) {
            val overtone=fundamentals.any { lower ->
                val h=(peak.hz/lower.hz).roundToInt()
                h in 2..16 && abs(1200*log2(peak.hz/(h*lower.hz)))<35
            }
            if(!overtone) fundamentals+=peak
        }
        return fundamentals.sortedByDescending { it.amplitude }.take(6).sortedBy { it.hz }
    }
}
