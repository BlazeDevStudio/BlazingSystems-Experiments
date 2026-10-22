package com.blazingsystems.visualizer.audio
import android.content.Context
import android.net.Uri
import com.blazingsystems.visualizer.project.*
import com.blazingsystems.visualizer.avee.AveeSpectrumAnalyzer
import kotlinx.coroutines.*
import kotlinx.serialization.Serializable
import kotlinx.serialization.encodeToString
import kotlinx.serialization.decodeFromString
import kotlinx.serialization.json.Json
import java.io.*
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.security.MessageDigest

@Serializable data class DecodedAudio(val hash:String,val sampleRate:Int,val channels:Int,val frames:Long,val rootPath:String) {
 val pcmFile get()=File(rootPath,"original.pcm");val monoFile get()=File(rootPath,"mono.f32");val durationUs get()=frames*1_000_000/sampleRate
}
class AudioRepository(private val context:Context) {
 private val root=File(context.cacheDir,"audio-v1").apply {mkdirs()}
 suspend fun get(source:SourceRef,progress:(Float)->Unit={}):DecodedAudio=withContext(Dispatchers.IO){
  val hash=MessageDigest.getInstance("SHA-256")
  context.contentResolver.openInputStream(Uri.parse(source.uri))!!.use {input->val bytes=ByteArray(65536);while(true){ensureActive();val count=input.read(bytes);if(count<0)break;hash.update(bytes,0,count)}}
  val digest=hash.digest().joinToString(""){"%02x".format(it)};val folder=File(root,digest);val metadata=File(folder,"audio.json")
  if(metadata.isFile){val audio=Json.decodeFromString<DecodedAudio>(metadata.readText()).copy(rootPath=folder.path);if(audio.pcmFile.isFile && audio.monoFile.isFile)return@withContext audio;folder.deleteRecursively()}
  val staging=File(root,"$digest.pending");staging.deleteRecursively();staging.mkdirs()
  try {var resampler:PcmResampler?=null;var rate=0;var channels=0;var frames=0L
   DataOutputStream(BufferedOutputStream(FileOutputStream(File(staging,"mono.f32")))).use {mono->BufferedOutputStream(FileOutputStream(File(staging,"original.pcm"))).use {pcm->
    PcmDecoder(context).decode(Uri.parse(source.uri)).collect {chunk->ensureActive();if(resampler==null){rate=chunk.sampleRate;channels=chunk.channels;resampler=PcmResampler(rate,channels)};require(rate==chunk.sampleRate && channels==chunk.channels){"Audio format changed mid-track"}
     val bytes=ByteBuffer.allocate(chunk.samples.size*2).order(ByteOrder.LITTLE_ENDIAN);chunk.samples.forEach {bytes.putShort((it.coerceIn(-1f,1f)*32767).toInt().toShort())};pcm.write(bytes.array())
     resampler!!.feed(chunk.samples).forEach {mono.writeInt(Integer.reverseBytes(java.lang.Float.floatToRawIntBits(it)))};frames+=chunk.samples.size/channels;progress((frames*1_000_000f/rate/source.durationUs.coerceAtLeast(1)).coerceIn(0f,1f))
    };resampler?.feed(FloatArray(0),true)?.forEach {mono.writeInt(Integer.reverseBytes(java.lang.Float.floatToRawIntBits(it)))}
   }}
   require(frames>0){"The track is empty"};val decoded=DecodedAudio(digest,rate,channels,frames,folder.path);File(staging,"audio.json").writeText(Json.encodeToString(decoded));check(staging.renameTo(folder)){"Could not finalize decoded audio"};decoded
  }catch(failure:Throwable){staging.deleteRecursively();throw failure}
 }
}
class AudioFeatures(private val audio:DecodedAudio):AutoCloseable {
 private val file=RandomAccessFile(audio.monoFile,"r");private val analyzer=AveeSpectrumAnalyzer()
 @Synchronized fun at(timeUs:Long,notes:List<NoteEvent> = emptyList()):FeatureFrame {
  val start=(timeUs.coerceAtLeast(0)*22050/1_000_000).coerceAtMost(file.length()/4);file.seek(start*4);val bytes=ByteArray(2048*4);val count=file.read(bytes);val buffer=ByteBuffer.wrap(bytes).order(ByteOrder.LITTLE_ENDIAN);val pcm=FloatArray(2048){if(it*4+4<=count)buffer.float else 0f};val f=analyzer.analyze(pcm,22050);return FeatureFrame(timeUs,f.rms,f.spectrum,f.waveform,notes)
 }
 @Synchronized override fun close()=file.close()
}
