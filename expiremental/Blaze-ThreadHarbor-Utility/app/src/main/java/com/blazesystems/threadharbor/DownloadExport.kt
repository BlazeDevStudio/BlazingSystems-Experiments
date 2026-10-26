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
                output.use { sink ->
                    val buffer = ByteArray(64 * 1024)
                    while (true) {
                        coroutineContext.ensureActive()
                        val count = stream.read(buffer)
                        if (count < 0) break
                        if (count > 0) {
                            sink.write(buffer, 0, count)
                            bytes += count
                        }
                    }
                    sink.flush()
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
