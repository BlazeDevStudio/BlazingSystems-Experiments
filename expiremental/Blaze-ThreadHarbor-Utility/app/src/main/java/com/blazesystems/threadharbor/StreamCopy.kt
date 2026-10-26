package com.blazesystems.threadharbor

import java.io.InputStream
import java.io.OutputStream

/**
 * Transfer already-authorized byte streams without buffering entire files in RAM.
 * The checkpoint callback lets callers enforce coroutine cancellation between reads.
 */
internal fun copyStreams(
    input: InputStream,
    output: OutputStream,
    checkpoint: () -> Unit = {}
): Long {
    val buffer = ByteArray(64 * 1024)
    var bytesCopied = 0L
    while (true) {
        checkpoint()
        val bytesRead = input.read(buffer)
        if (bytesRead < 0) break
        if (bytesRead == 0) continue
        output.write(buffer, 0, bytesRead)
        bytesCopied += bytesRead
    }
    output.flush()
    return bytesCopied
}
