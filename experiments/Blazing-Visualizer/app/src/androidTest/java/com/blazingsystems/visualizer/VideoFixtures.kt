package com.blazingsystems.visualizer

import android.content.Context
import androidx.test.platform.app.InstrumentationRegistry
import java.io.File
import java.util.UUID

internal class VideoFixtures(private val context: Context) {
    /** Fixed source-clock color changes, independent of the device encoder and EGL setup. */
    fun colorVideo(rotation: Int = 0): File {
        val asset = when (rotation) {
            0 -> "color-video.mp4"
            90 -> "color-video-rotation90.mp4"
            else -> throw IllegalArgumentException("Color video fixture supports only 0 or 90 degrees")
        }
        val file = File(context.cacheDir, "background-${UUID.randomUUID()}.mp4")
        try {
            InstrumentationRegistry.getInstrumentation().context.assets.open(asset)
                .use { input -> file.outputStream().use(input::copyTo) }
            return file
        } catch (failure: Throwable) {
            file.delete()
            throw failure
        }
    }
}
