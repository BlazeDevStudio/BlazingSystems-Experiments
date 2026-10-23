package com.blazingsystems.visualizer.render

import android.content.Context
import android.graphics.Bitmap
import android.media.MediaMetadataRetriever
import android.net.Uri
import android.os.Build
import kotlin.math.min
import kotlin.math.roundToInt
import kotlin.math.sqrt

/** Source-time export frames, with no retained bitmap cache. The caller recycles each frame. */
class VideoFrameSource(context: Context, uri: Uri) : AutoCloseable {
    private val retriever = MediaMetadataRetriever()
    private var closed = false
    private val durationUs: Long

    init {
        try {
            retriever.setDataSource(context, uri)
            val width = retriever.extractMetadata(MediaMetadataRetriever.METADATA_KEY_VIDEO_WIDTH)?.toIntOrNull() ?: 0
            val height = retriever.extractMetadata(MediaMetadataRetriever.METADATA_KEY_VIDEO_HEIGHT)?.toIntOrNull() ?: 0
            // Retrievers may decode a full frame internally, including on the scaled-frame API.
            // Refuse unbounded source allocations before asking Android to decode a bitmap.
            require(width in 1..4096 && height in 1..4096 && width.toLong() * height <= 4096L * 2160) {
                "Video backgrounds support source frames up to 4096 pixels and 8.8 megapixels"
            }
            durationUs = (retriever.extractMetadata(MediaMetadataRetriever.METADATA_KEY_DURATION)
                ?.toLongOrNull() ?: 0).coerceIn(0, Long.MAX_VALUE / 1000) * 1000
        } catch (failure: Throwable) {
            runCatching { retriever.release() }
            throw failure
        }
    }

    @Synchronized
    fun frameAt(sourceTimeUs: Long, targetWidth: Int, targetHeight: Int): Bitmap {
        check(!closed) { "Video frame source is closed" }
        require(sourceTimeUs >= 0 && targetWidth in 1..8192 && targetHeight in 1..8192)
        val factor = min(1.0, min(1920.0 / maxOf(targetWidth, targetHeight),
            sqrt(2_073_600.0 / (targetWidth.toDouble() * targetHeight))))
        val width = (targetWidth * factor).roundToInt().coerceAtLeast(1)
        val height = (targetHeight * factor).roundToInt().coerceAtLeast(1)
        val time = if (durationUs > 0) sourceTimeUs.coerceAtMost(durationUs - 1) else sourceTimeUs
        // Android's retriever applies the container rotation; rotating again would invert portrait clips.
        val frame = (if (Build.VERSION.SDK_INT >= 27)
            retriever.getScaledFrameAtTime(time, MediaMetadataRetriever.OPTION_CLOSEST, width, height)
        else retriever.getFrameAtTime(time, MediaMetadataRetriever.OPTION_CLOSEST))
            ?: error("Could not decode the video background at ${time / 1000} ms")
        val scale = min(1f, min(width.toFloat() / frame.width, height.toFloat() / frame.height))
        if (scale >= 1f) return frame
        try {
            return Bitmap.createScaledBitmap(frame, (frame.width * scale).roundToInt().coerceAtLeast(1),
                (frame.height * scale).roundToInt().coerceAtLeast(1), true)
        } finally { frame.recycle() }
    }

    @Synchronized
    override fun close() {
        if (closed) return
        closed = true
        retriever.release()
    }
}
