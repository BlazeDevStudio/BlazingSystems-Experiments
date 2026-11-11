package com.blazesystems.threadharbor

import android.content.Context
import android.net.Uri
import androidx.documentfile.provider.DocumentFile
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ensureActive
import kotlinx.coroutines.withContext
import kotlin.coroutines.coroutineContext

/**
 * All SAF provider calls and document streaming belong off the Compose UI thread.
 * Uses the user's explicit source selection and explicit authorized tree.
 * A partially written destination is deleted on most failures; process death is
 * not transactional and must still be handled at a higher level.
 */
suspend fun importIntoAuthorizedFolder(
    context: Context,
    source: Uri,
    directory: DocumentFile
): Result<String> = withContext(Dispatchers.IO) {
    var target: DocumentFile? = null
    try {
        require(directory.isDirectory && directory.canWrite()) {
            "Selected folder is not writable"
        }
        val resolver = context.contentResolver
        val filename = DocumentFile.fromSingleUri(context, source)?.name
            ?.take(180)?.ifBlank { "imported-file" } ?: "imported-file"
        val type = resolver.getType(source) ?: "application/octet-stream"
        val created = directory.createFile(type, filename)
            ?: error("Document provider rejected new file")
        target = created
        resolver.openInputStream(source)?.use { input ->
            resolver.openOutputStream(created.uri, "wt")?.use { output ->
                val cancellationContext = coroutineContext
                copyStreams(input, output) { cancellationContext.ensureActive() }
            } ?: error("Cannot write imported file")
        } ?: error("Cannot read picked document")
        Result.success(filename)
    } catch (failure: CancellationException) {
        try { target?.delete() } catch (_: Exception) {}
        throw failure
    } catch (failure: Exception) {
        try { target?.delete() } catch (_: Exception) {}
        Result.failure(failure)
    }
}
