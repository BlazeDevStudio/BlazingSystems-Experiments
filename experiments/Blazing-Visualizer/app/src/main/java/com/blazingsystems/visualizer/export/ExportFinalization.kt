package com.blazingsystems.visualizer.export

/** Container finalization must succeed before a file is published. */
object ExportFinalization {
    fun close(primaryFailure: Throwable?, stop: () -> Unit, release: () -> Unit) {
        try {
            try {
                stop()
            } catch (failure: Throwable) {
                if (primaryFailure == null) throw failure else primaryFailure.addSuppressed(failure)
            }
        } finally {
            release()
        }
    }
}
