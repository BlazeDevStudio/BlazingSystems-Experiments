package com.blazingsystems.visualizer.playback

import android.Manifest
import android.content.ContentUris
import android.content.Context
import android.content.pm.PackageManager
import android.os.Build
import android.provider.MediaStore
import android.media.MediaMetadataRetriever
import android.media.MediaExtractor
import android.media.MediaFormat
import android.net.Uri
import android.provider.OpenableColumns
import com.blazingsystems.visualizer.project.*
import java.io.File
import java.io.IOException
import kotlinx.serialization.Serializable
import kotlinx.serialization.decodeFromString
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json

class SourceUnavailableException(message: String, cause: Throwable? = null) :
    IOException(message, cause)

@Serializable data class Playlist(val id: String, val name: String, val tracks: List<SourceRef>)

class LibraryRepository(private val context: Context) {
    private val root = File(context.filesDir, "library")

    fun open(uri: Uri): SourceRef {
        try {
            require(uri.scheme in setOf("content", "file", "android.resource"))
            context.contentResolver.openFileDescriptor(uri, "r")?.use {}
                ?: throw IOException("File unavailable")
            var title = uri.lastPathSegment?.substringAfterLast('/') ?: "Untitled"
            runCatching {
                context.contentResolver
                    .query(uri, arrayOf(OpenableColumns.DISPLAY_NAME), null, null, null)
                    ?.use { if (it.moveToFirst()) title = it.getString(0) ?: title }
            }
            val metadata = MediaMetadataRetriever()
            return try {
                metadata.setDataSource(context, uri)
                // Inspect tracks rather than extensions: a video may be silent, and
                // document providers often supply application/octet-stream.
                val extractor = MediaExtractor()
                val mimes = try {
                    extractor.setDataSource(context, uri, null)
                    (0 until extractor.trackCount).mapNotNull {
                        extractor.getTrackFormat(it).getString(MediaFormat.KEY_MIME)
                    }
                } finally { extractor.release() }
                val hasVideo = mimes.any { it.startsWith("video/") }
                val hasAudio = mimes.any { it.startsWith("audio/") }
                require(hasAudio || hasVideo) { "No supported audio or video track" }
                SourceRef(
                    uri.toString(),
                    durationUs =
                        (metadata
                            .extractMetadata(MediaMetadataRetriever.METADATA_KEY_DURATION)
                            ?.toLongOrNull() ?: 0) * 1000,
                    title =
                        metadata
                            .extractMetadata(MediaMetadataRetriever.METADATA_KEY_TITLE)
                            ?.takeIf { it.isNotBlank() } ?: title,
                    artist =
                        metadata.extractMetadata(MediaMetadataRetriever.METADATA_KEY_ARTIST) ?: "",
                    mimeType = metadata.extractMetadata(MediaMetadataRetriever.METADATA_KEY_MIMETYPE)
                        ?: context.contentResolver.getType(uri),
                    hasVideo = hasVideo,
                    hasAudio = hasAudio,
                )
            } finally {
                metadata.release()
            }
        } catch (failure: Exception) {
            throw SourceUnavailableException(
                "Can't read this media file. Choose it again to restore access or use a supported format.",
                failure,
            )
        }
    }

    /** MediaStore is read only after the matching runtime permission is granted. */
    fun discoverAudio(): List<SourceRef> {
        val permission = if (Build.VERSION.SDK_INT >= 33) Manifest.permission.READ_MEDIA_AUDIO
            else Manifest.permission.READ_EXTERNAL_STORAGE
        if (context.checkSelfPermission(permission) != PackageManager.PERMISSION_GRANTED)
            return emptyList()
        val columns = arrayOf(
            MediaStore.Audio.Media._ID,
            MediaStore.Audio.Media.TITLE,
            MediaStore.Audio.Media.ARTIST,
            MediaStore.Audio.Media.DURATION,
        )
        val tracks = mutableListOf<SourceRef>()
        context.contentResolver.query(
            MediaStore.Audio.Media.EXTERNAL_CONTENT_URI,
            columns, null, null, MediaStore.Audio.Media.TITLE + " COLLATE NOCASE ASC",
        )?.use { rows ->
            val id = rows.getColumnIndexOrThrow(MediaStore.Audio.Media._ID)
            val title = rows.getColumnIndexOrThrow(MediaStore.Audio.Media.TITLE)
            val artist = rows.getColumnIndexOrThrow(MediaStore.Audio.Media.ARTIST)
            val duration = rows.getColumnIndexOrThrow(MediaStore.Audio.Media.DURATION)
            while (rows.moveToNext()) {
                val millis = rows.getLong(duration)
                if (millis <= 0) continue
                val uri = ContentUris.withAppendedId(
                    MediaStore.Audio.Media.EXTERNAL_CONTENT_URI, rows.getLong(id),
                )
                tracks += SourceRef(
                    uri = uri.toString(),
                    title = rows.getString(title)?.takeIf { it.isNotBlank() } ?: "Audio track",
                    artist = rows.getString(artist).orEmpty().takeUnless { it == "<unknown>" } ?: "",
                    durationUs = millis * 1000,
                )
            }
        }
        return tracks
    }

    fun loadLibrary(): List<SourceRef> =
        File(root, "library.json").takeIf { it.isFile }
            ?.let { Json.decodeFromString(it.readText()) } ?: emptyList()

    @Synchronized
    fun saveLibrary(tracks: List<SourceRef>) =
        atomicWrite(File(root, "library.json"), Json.encodeToString(tracks).toByteArray())

    fun loadQueue(): List<SourceRef> =
        File(root, "queue.json").takeIf { it.isFile }?.let { Json.decodeFromString(it.readText()) }
            ?: emptyList()

    @Synchronized
    fun saveQueue(queue: List<SourceRef>) =
        atomicWrite(File(root, "queue.json"), Json.encodeToString(queue).toByteArray())

    fun loadPlaylists(): List<Playlist> =
        File(root, "playlists.json")
            .takeIf { it.isFile }
            ?.let { Json.decodeFromString(it.readText()) } ?: emptyList()

    @Synchronized
    fun savePlaylists(playlists: List<Playlist>) =
        atomicWrite(File(root, "playlists.json"), Json.encodeToString(playlists).toByteArray())
}
