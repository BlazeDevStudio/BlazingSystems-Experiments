package com.blazesystems.threadharbor

import android.app.DownloadManager
import android.content.Context
import android.net.Uri
import android.provider.DocumentsContract
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ensureActive
import kotlinx.coroutines.withContext
import kotlin.coroutines.coroutineContext

/**
 * Copy a successfully downloaded system file to a user-selected SAF document.
 * This does NOT re-download an HTTP URL, transfer browser cookies, or implement resume.
 * Both source and output remain under Android's ContentResolver permission checks.
 *
 * On copy failure, best-effort removal of the newly created document prevents
 * presenting a truncated file as successful. Process death may still leave a partial
 * document, so this is not a transactional download engine.
 */
suspend fun exportCompletedDownload(
    context: Context,
    manager: DownloadManager,
    downloadId: Long,
    destination: Uri
): Result<Long> = withContext(Dispatchers.IO) {
    var bytes = 0L
    try {
        if (destination.scheme != "content") {
            error("Save destination must be a selected Android document")
        }
        val source = manager.getUriForDownloadedFile(downloadId)
            ?: error("Download is unavailable or not complete")
        val resolver = context.contentResolver
        val input = resolver.openInputStream(source) ?: error("Cannot read the completed download")
        try {
            input.use { stream ->
                val output = resolver.openOutputStream(destination, "wt")
                    ?: error("Cannot write selected destination")
                val cancellationContext = coroutineContext
                output.use { sink ->
                    bytes = copyStreams(stream, sink) { cancellationContext.ensureActive() }
                }
            }
            Result.success(bytes)
        } catch (problem: Exception) {
            try { DocumentsContract.deleteDocument(resolver, destination) } catch (_: Exception) {}
            throw problem
        }
    } catch (problem: Exception) {
        Result.failure(problem)
    }
}
