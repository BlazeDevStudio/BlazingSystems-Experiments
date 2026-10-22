package com.blazingsystems.visualizer.export
import com.blazingsystems.visualizer.project.*
import kotlinx.serialization.Serializable
import kotlinx.serialization.encodeToString
import kotlinx.serialization.decodeFromString
import kotlinx.serialization.json.Json
import java.io.File
@Serializable data class ExportRequest(val project:Project,val clipStartUs:Long,val clipEndUs:Long,val outputUri:String,val settings:ExportSettings=project.export)
class ExportTimeline(val startUs:Long,val endUs:Long,val fps:Int) {
 init{require(startUs>=0 && endUs>startUs && fps==30)}
 val durationUs=endUs-startUs
 val frameCount: Int get()=((durationUs*fps+999999)/1000000).toInt()
 fun presentationTimeUs(frame:Int):Long {require(frame in 0 until frameCount);return frame*1_000_000L/fps}
 fun sourceTimeUs(frame:Int)=startUs+presentationTimeUs(frame)
}
fun validateExportSettings(s:ExportSettings){require(s.width in 128..1920 && s.height in 128..1920 && s.width%2==0 && s.height%2==0 && s.fps==30 && s.videoBitrate in 500_000..30_000_000 && s.audioBitrate in 64_000..320_000){"Choose an even video size from 128 to 1920 pixels at 30 fps"}}
@Serializable enum class ExportStatus { QUEUED,RUNNING,COMPLETED,CANCELLED,FAILED,INTERRUPTED }
@Serializable data class ExportJob(val id:String,val request:ExportRequest,val status:ExportStatus=ExportStatus.QUEUED,val progress:Float=0f,val message:String?=null)
class ExportJobStore(private val root:File) {
 @Synchronized fun save(job:ExportJob){require(job.id.matches(Regex("[a-zA-Z0-9-]+")));atomicWrite(File(root,"${job.id}.json"),Json.encodeToString(job).toByteArray())}
 @Synchronized fun recover():List<ExportJob> = root.listFiles()?.filter{it.extension=="json"}?.mapNotNull{f->runCatching{Json.decodeFromString<ExportJob>(f.readText())}.getOrNull()}?.map{if(it.status in setOf(ExportStatus.QUEUED,ExportStatus.RUNNING))it.copy(status=ExportStatus.INTERRUPTED,message="Export was interrupted. Start it again.").also(::save) else it} ?: emptyList()
}
