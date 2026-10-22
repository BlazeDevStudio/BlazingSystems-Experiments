package com.blazingsystems.visualizer.audio
import android.content.Context
import android.media.*
import android.net.Uri
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*
import java.nio.ByteOrder

data class PcmChunk(val samples:FloatArray,val sampleRate:Int,val channels:Int,val sourceTimeUs:Long)
class PcmDecoder(private val context:Context) {
 fun decode(uri:Uri):Flow<PcmChunk> = flow {
  val extractor=MediaExtractor();var decoder:MediaCodec?=null
  try {
   extractor.setDataSource(context,uri,null)
   val track=(0 until extractor.trackCount).firstOrNull {extractor.getTrackFormat(it).getString(MediaFormat.KEY_MIME)?.startsWith("audio/")==true} ?: error("No decodable audio track")
   extractor.selectTrack(track);val format=extractor.getTrackFormat(track);val codec=MediaCodec.createDecoderByType(format.getString(MediaFormat.KEY_MIME)!!);decoder=codec;codec.configure(format,null,null,0);codec.start()
   var rate=format.getInteger(MediaFormat.KEY_SAMPLE_RATE);var channels=format.getInteger(MediaFormat.KEY_CHANNEL_COUNT);var encoding=AudioFormat.ENCODING_PCM_16BIT;var inputEnded=false;var outputEnded=false;val info=MediaCodec.BufferInfo()
   while(!outputEnded){currentCoroutineContext().ensureActive()
    if(!inputEnded){val index=codec.dequeueInputBuffer(10_000);if(index>=0){val buffer=codec.getInputBuffer(index)!!;val size=extractor.readSampleData(buffer,0);if(size<0){codec.queueInputBuffer(index,0,0,0,MediaCodec.BUFFER_FLAG_END_OF_STREAM);inputEnded=true}else{codec.queueInputBuffer(index,0,size,extractor.sampleTime.coerceAtLeast(0),0);extractor.advance()}}}
    when(val index=codec.dequeueOutputBuffer(info,10_000)){
     MediaCodec.INFO_OUTPUT_FORMAT_CHANGED->{val out=codec.outputFormat;rate=out.getInteger(MediaFormat.KEY_SAMPLE_RATE);channels=out.getInteger(MediaFormat.KEY_CHANNEL_COUNT);encoding=if(out.containsKey(MediaFormat.KEY_PCM_ENCODING))out.getInteger(MediaFormat.KEY_PCM_ENCODING) else AudioFormat.ENCODING_PCM_16BIT}
     else->if(index>=0){try{if(info.size>0){val buffer=codec.getOutputBuffer(index)!!.duplicate().order(ByteOrder.LITTLE_ENDIAN);buffer.position(info.offset);buffer.limit(info.offset+info.size);val samples=when(encoding){AudioFormat.ENCODING_PCM_FLOAT->FloatArray(info.size/4){buffer.float.coerceIn(-1f,1f)};AudioFormat.ENCODING_PCM_16BIT->FloatArray(info.size/2){buffer.short/32768f};else->error("Unsupported decoded PCM format")};emit(PcmChunk(samples,rate,channels,info.presentationTimeUs))};outputEnded=info.flags and MediaCodec.BUFFER_FLAG_END_OF_STREAM!=0}finally{codec.releaseOutputBuffer(index,false)}}
    }
   }
  }finally{decoder?.let {runCatching {it.stop()};it.release()};extractor.release()}
 }
}
