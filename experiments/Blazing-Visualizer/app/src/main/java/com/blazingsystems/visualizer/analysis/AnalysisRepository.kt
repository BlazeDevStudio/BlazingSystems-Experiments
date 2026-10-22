package com.blazingsystems.visualizer.analysis
import android.content.Context
import com.blazingsystems.visualizer.audio.*
import com.blazingsystems.visualizer.project.*
import kotlinx.coroutines.*
import kotlinx.serialization.Serializable
import kotlinx.serialization.encodeToString
import kotlinx.serialization.decodeFromString
import kotlinx.serialization.json.Json
import java.io.*
import java.nio.ByteBuffer
import java.nio.ByteOrder
import kotlin.math.*

@Serializable data class AnalysisResult(val key:String,val sourceHash:String,val modelHash:String,val parameters:AnalysisParameters,val durationUs:Long,val rawNotes:List<NoteEvent>)
class BasicPitchAnalyzer(private val context:Context) {
 suspend fun analyze(audio:DecodedAudio,parameters:AnalysisParameters=AnalysisParameters(),progress:(Float)->Unit={}):AnalysisResult=withContext(Dispatchers.Default){
  val budgetSeconds=min(1800L,(Runtime.getRuntime().maxMemory()*.45/(86*2400)).toLong()).coerceAtLeast(60)
  require(audio.durationUs<=budgetSeconds*1_000_000){"This device can analyze about ${budgetSeconds/60} minutes at once. Choose a shorter track."}
  val count=(audio.monoFile.length()/4).toInt();val hop=43844-30*256;val expected=(count.toDouble()/hop*142).toInt()
  val notes=ArrayList<FloatArray>(expected);val onsets=ArrayList<FloatArray>(expected);val contours=ArrayList<FloatArray>()
  RandomAccessFile(audio.monoFile,"r").use {file->ModelRunner(context).use{runner->
   var offset=0
   while(offset<count+3840){ensureActive();val window=FloatArray(43844);val sourceStart=offset-3840;val start=max(0,sourceStart);val end=min(count,sourceStart+43844)
    if(end>start){file.seek(start*4L);val bytes=ByteArray((end-start)*4);file.readFully(bytes);val buffer=ByteBuffer.wrap(bytes).order(ByteOrder.LITTLE_ENDIAN);for(i in start until end)window[i-sourceStart]=buffer.float}
    val output=runner.run(window);for(frame in 15 until 157){if(notes.size>=expected)break;notes+=output.note[frame];onsets+=output.onset[frame];if(parameters.includePitchBends)contours+=output.contour[frame]};offset+=hop;progress((offset.toFloat()/(count+3840)).coerceIn(0f,1f))
   }
   ensureActive();val modelNotes=NotePostprocessor.decode(ModelOutputs(notes.toTypedArray(),onsets.toTypedArray(),contours.toTypedArray()),audio.durationUs,parameters)
   val events=if(parameters.refineIsolatedOnsets)AudioOnsetRefiner.refine(modelNotes,22050){start,size->ensureActive();file.seek(start*4);val available=min(size.toLong(),(file.length()/4-start).coerceAtLeast(0)).toInt();val data=ByteArray(available*4);file.readFully(data);val buffer=ByteBuffer.wrap(data).order(ByteOrder.LITTLE_ENDIAN);FloatArray(size){if(it<available)buffer.float else 0f}} else modelNotes
   AnalysisResult(AnalysisKeys.key(audio.hash,runner.modelHash,parameters),audio.hash,runner.modelHash,parameters,audio.durationUs,events)
  }}
 }
}
class AnalysisRepository(private val context:Context) {
 private val root=File(context.filesDir,"analysis-v2").apply{mkdirs()}
 suspend fun getOrAnalyze(audio:DecodedAudio,parameters:AnalysisParameters=AnalysisParameters(),progress:(Float)->Unit={}):AnalysisResult=withContext(Dispatchers.Default){
  val key=AnalysisKeys.key(audio.hash,ModelRunner.MODEL_SHA256,parameters);val target=File(root,"$key.json")
  if(target.isFile)runCatching{Json.decodeFromString<AnalysisResult>(target.readText())}.getOrNull()?.let{if(it.key==key && it.sourceHash==audio.hash && it.modelHash==ModelRunner.MODEL_SHA256 && it.parameters==parameters)return@withContext it}
  val result=BasicPitchAnalyzer(context).analyze(audio,parameters,progress);ensureActive();atomicWrite(target,Json.encodeToString(result).toByteArray());result
 }
}
