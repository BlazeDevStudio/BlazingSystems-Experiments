package com.blazingsystems.visualizer.project
import kotlinx.serialization.encodeToString
import kotlinx.serialization.decodeFromString
import kotlinx.serialization.json.Json
import java.io.File
import java.io.FileOutputStream
import java.nio.file.Files
import java.nio.file.StandardCopyOption

fun atomicWrite(file:File,bytes:ByteArray) {
 file.parentFile!!.mkdirs()
 val temporary=File(file.parentFile,file.name+".tmp")
 FileOutputStream(temporary).use {it.write(bytes);it.fd.sync()}
 Files.move(temporary.toPath(),file.toPath(),StandardCopyOption.REPLACE_EXISTING,StandardCopyOption.ATOMIC_MOVE)
}
class ProjectStore(private val root:File) {
 private val json=Json {encodeDefaults=true;ignoreUnknownKeys=true}
 private fun file(id:String):File {require(id.matches(Regex("[A-Za-z0-9_-]{1,80}")));return File(root,"$id.json")}
 @Synchronized fun save(project:Project)=atomicWrite(file(project.id),json.encodeToString(project).toByteArray())
 @Synchronized fun load(id:String):Project?=file(id).takeIf {it.isFile}?.let {json.decodeFromString<Project>(it.readText())}
 @Synchronized fun list():List<Project> = root.listFiles()?.filter {it.extension=="json"}?.sortedByDescending {it.lastModified()}?.mapNotNull {runCatching {json.decodeFromString<Project>(it.readText())}.getOrNull()} ?: emptyList()
}
