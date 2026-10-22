package com.blazingsystems.visualizer.audio

import java.io.File
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock

/** Keeps both PCM files available until their preview or export finishes using them. */
class DecodedAudioLease internal constructor(
    val audio: DecodedAudio,
    private val retention: AutoCloseable,
) : AutoCloseable {
    override fun close() = retention.close()
}

/** Repository instances and the export service share ownership of the same disk cache. */
internal class DecodedAudioLeases(root: File) {
    private val root = root.canonicalFile

    fun retain(hash: String): AutoCloseable {
        val folder = folder(hash)
        val key = folder.path
        synchronized(monitor) { references[key] = (references[key] ?: 0) + 1 }
        return object : AutoCloseable {
            private var closed = false

            override fun close() {
                synchronized(monitor) {
                    if (!closed) {
                        closed = true
                        val remaining = references.getValue(key) - 1
                        if (remaining == 0) references.remove(key)
                        else references[key] = remaining
                    }
                }
            }
        }
    }

    fun discard(hash: String): Boolean {
        val folder = folder(hash)
        return synchronized(monitor) {
            if ((references[folder.path] ?: 0) > 0) false
            else folder.deleteRecursively()
        }
    }

    /** Cleanup of a cancelled decoder finishes before the next owner touches .pending. */
    suspend fun <T> decoding(action: suspend () -> T): T = decodeMutex.withLock { action() }

    private fun folder(hash: String): File {
        require(hash.matches(Regex("[0-9a-f]{64}")))
        return File(root, hash)
    }

    private companion object {
        val monitor = Any()
        val references = mutableMapOf<String, Int>()
        val decodeMutex = Mutex()
    }
}
