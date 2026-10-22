package com.blazingsystems.visualizer.audio
import kotlin.math.*
/** Bounded, streaming windowed-sinc low-pass resampling with an absolute sample clock. */
class PcmResampler(val sampleRate:Int,val channels:Int,val targetRate:Int=22050) {
 private var buffer=FloatArray(0);private var base=0L;private var received=0L;private var produced=0L;private var ended=false
 init {require(sampleRate>0 && channels in 1..8 && targetRate>0)}
 fun feed(interleaved:FloatArray,end:Boolean=false):FloatArray {
  check(!ended);require(interleaved.size%channels==0)
  val mono=FloatArray(interleaved.size/channels){frame->var sum=0f;repeat(channels){sum+=interleaved[frame*channels+it]};sum/channels}
  buffer+=mono;received+=mono.size;val step=sampleRate.toDouble()/targetRate
  val maxCount=if(end)ceil(received/step).toLong() else max(0L,ceil((received-32)/step).toLong())
  val output=FloatArray((maxCount-produced).coerceAtLeast(0).toInt());val cutoff=min(1.0,targetRate.toDouble()/sampleRate)*.94
  output.indices.forEach {index->val position=produced*step
   if(sampleRate==targetRate)output[index]=buffer[(produced-base).toInt()] else {
    val center=floor(position).toLong();var sum=0.0;var weightSum=0.0
    for(tap in -31..32){val distance=position-(center+tap);val x=distance*cutoff;val sinc=if(abs(x)<1e-10)1.0 else sin(PI*x)/(PI*x);val window=if(abs(distance)<=32).5+.5*cos(PI*distance/32) else 0.0;val weight=cutoff*sinc*window;val relative=center+tap-base;if(relative>=0 && relative<buffer.size)sum+=buffer[relative.toInt()]*weight;weightSum+=weight}
    output[index]=(sum/weightSum).toFloat()
   };produced++
  }
  val keep=max(base,floor(produced*step).toLong()-32).coerceAtMost(received);buffer=buffer.copyOfRange((keep-base).toInt(),buffer.size);base=keep;ended=end;return output
 }
}
