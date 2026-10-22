package com.blazingsystems.visualizer.playback
import android.content.Context
import android.media.MediaMetadataRetriever
import android.net.Uri
import android.provider.OpenableColumns
import com.blazingsystems.visualizer.project.*
import kotlinx.serialization.Serializable
import kotlinx.serialization.encodeToString
import kotlinx.serialization.decodeFromString
import kotlinx.serialization.json.Json
import java.io.File
import java.io.IOException

class SourceUnavailableException(message:String,cause:Throwable?=null):IOException(message,cause)
@Serializable data class Playlist(val id:String,val name:String,val tracks:List<SourceRef>)
class LibraryRepository(private val context:Context) {
 private val root=File(context.filesDir,"library")
 fun open(uri:Uri):SourceRef {
  try {
   require(uri.scheme in setOf("content","file","android.resource"))
   context.contentResolver.openFileDescriptor(uri,"r")?.use {} ?: throw IOException("File unavailable")
   var title=uri.lastPathSegment?.substringAfterLast('/') ?: "Untitled"
   runCatching {context.contentResolver.query(uri,arrayOf(OpenableColumns.DISPLAY_NAME),null,null,null)?.use {if(it.moveToFirst())title=it.getString(0) ?: title}}
   val metadata=MediaMetadataRetriever()
   return try {metadata.setDataSource(context,uri);SourceRef(uri.toString(),durationUs=(metadata.extractMetadata(MediaMetadataRetriever.METADATA_KEY_DURATION)?.toLongOrNull() ?: 0)*1000,title=metadata.extractMetadata(MediaMetadataRetriever.METADATA_KEY_TITLE)?.takeIf {it.isNotBlank()} ?: title,artist=metadata.extractMetadata(MediaMetadataRetriever.METADATA_KEY_ARTIST) ?: "")}finally{metadata.release()}
  }catch(failure:Exception){throw SourceUnavailableException("Can't read this track. Choose the file again to restore access.",failure)}
 }
 fun loadQueue():List<SourceRef> = File(root,"queue.json").takeIf {it.isFile}?.let {Json.decodeFromString(it.readText())} ?: emptyList()
 fun saveQueue(queue:List<SourceRef>)=atomicWrite(File(root,"queue.json"),Json.encodeToString(queue).toByteArray())
 fun loadPlaylists():List<Playlist> = File(root,"playlists.json").takeIf {it.isFile}?.let {Json.decodeFromString(it.readText())} ?: emptyList()
 fun savePlaylists(playlists:List<Playlist>)=atomicWrite(File(root,"playlists.json"),Json.encodeToString(playlists).toByteArray())
}
