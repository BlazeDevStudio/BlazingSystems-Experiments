package com.blazingsystems.visualizer.avee
// Copyright 2019 Avee Player. Adapted circle/windowed-spectrum algorithms, Apache-2.0.
// See THIRD_PARTY_NOTICES.md and the retained original Java source headers.
import com.NAudio.FastFourierTransform
import com.aveeopen.comp.Visualizer.Dsp.DspWindows
import kotlin.math.*
data class Vec2(val x:Float,val y:Float)
object AveeCirclePath {fun points(count:Int,radius:Float):List<Vec2>{require(count>0 && radius.isFinite() && radius>=0);return List(count){val a=2*PI*it/count;Vec2((sin(a)*radius).toFloat(),(-cos(a)*radius).toFloat())}}}
data class SpectrumFrame(val rms:Float,val spectrum:List<Float>,val waveform:List<Float>)
class AveeSpectrumAnalyzer {
 fun analyze(pcm:FloatArray,sampleRate:Int):SpectrumFrame {
  require(sampleRate>0);val n=2048;val samples=FloatArray(n){pcm.getOrElse(it){0f}.takeIf(Float::isFinite) ?: 0f}
  val data=Array(n){FastFourierTransform.Complex(samples[it]*DspWindows.hannWindow(it,n),0f)};FastFourierTransform.FFT(true,data)
  return SpectrumFrame(sqrt(samples.sumOf {(it*it).toDouble()}/n).toFloat(),List(n/2){hypot(data[it].re(),data[it].im())*4},List(256){samples[it*n/256]})
 }
}
