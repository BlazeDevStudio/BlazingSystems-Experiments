package com.blazingsystems.visualizer.render

data class PreviewCanvasStatus(
    val surface: Long = 0,
    val available: Boolean = false,
    val presentedFrames: Long = 0,
    val sourceTimeUs: Long? = null,
    val activeNotes: Int = 0,
    val error: String? = null,
)

/** Measurements only; the check report never contains pixels, filenames or audio. */
object PreviewCanvasHealth {
    @Volatile var status = PreviewCanvasStatus()
        private set
    private var serial = 0L

    @Synchronized fun available(): Long {
        val id = ++serial
        status = PreviewCanvasStatus(surface = id, available = true)
        return id
    }

    @Synchronized fun presented(surface: Long, scene: EvaluatedScene) {
        if (status.surface == surface) status = status.copy(
            presentedFrames = status.presentedFrames + 1,
            sourceTimeUs = scene.sourceTimeUs,
            activeNotes = scene.activeNotes.size,
            error = null,
        )
    }

    @Synchronized fun destroyed(surface: Long) {
        if (status.surface == surface) status = status.copy(available = false)
    }

    @Synchronized fun failed(surface: Long, error: String) {
        if (status.surface == surface) status = status.copy(error = error)
    }
}
