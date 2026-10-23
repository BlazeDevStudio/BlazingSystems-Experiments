package com.blazingsystems.visualizer

import android.graphics.Color
import android.media.MediaExtractor
import android.media.MediaFormat
import android.media.MediaMetadataRetriever
import android.net.Uri
import android.opengl.GLES20
import android.opengl.EGL14
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import com.blazingsystems.visualizer.audio.AudioRepository
import com.blazingsystems.visualizer.export.ExportRequest
import com.blazingsystems.visualizer.export.VideoExporter
import com.blazingsystems.visualizer.project.*
import com.blazingsystems.visualizer.playback.LibraryRepository
import com.blazingsystems.visualizer.render.VideoFrameSource
import com.blazingsystems.visualizer.render.GlTarget
import java.io.File
import java.util.UUID
import kotlinx.coroutines.runBlocking
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.put
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class VideoBackgroundNativeTest {
    private val context = InstrumentationRegistry.getInstrumentation().targetContext

    private fun assertGreen(pixel: Int) {
        assertTrue("Expected green video pixel: ${Integer.toHexString(pixel)}",
            Color.green(pixel) > 170 && Color.red(pixel) < 80 && Color.blue(pixel) < 80)
    }

    @Test fun closingOneEglTargetKeepsTheOtherTargetUsable() {
        GlTarget.pbuffer(32, 32).use { preview ->
            GlTarget.pbuffer(32, 32).use { export ->
                export.makeCurrent()
                GLES20.glClearColor(1f, 0f, 0f, 1f)
                GLES20.glClear(GLES20.GL_COLOR_BUFFER_BIT)
            }
            preview.makeCurrent()
            GLES20.glClearColor(0f, 1f, 0f, 1f)
            GLES20.glClear(GLES20.GL_COLOR_BUFFER_BIT)
            val pixels = preview.readPixels()
            assertEquals(0, pixels[0].toInt() and 255)
            assertEquals(255, pixels[1].toInt() and 255)
            assertEquals(0, pixels[2].toInt() and 255)
            assertEquals(255, pixels[3].toInt() and 255)
        }
    }

    @Test fun closingAnInactiveTargetPreservesTheCurrentTargetAndIsIdempotent() {
        val preview = GlTarget.pbuffer(32, 32)
        try {
            GlTarget.pbuffer(32, 32).use { export ->
                val current = EGL14.eglGetCurrentContext()
                preview.close()
                assertEquals("Closing an inactive target detached the export", current,
                    EGL14.eglGetCurrentContext())
                preview.close()
                assertEquals("Closing twice detached the export", current,
                    EGL14.eglGetCurrentContext())
                GLES20.glClearColor(0f, 1f, 0f, 1f)
                GLES20.glClear(GLES20.GL_COLOR_BUFFER_BIT)
                assertEquals(GLES20.GL_NO_ERROR, GLES20.glGetError())
                val pixels = export.readPixels()
                assertEquals(255, pixels[1].toInt() and 255)
                assertEquals(255, pixels[3].toInt() and 255)
            }
        } finally { preview.close() }
    }

    @Test fun readerUsesSourceTimeAndReturnsRotatedBoundedFrames() {
        val file = VideoFixtures(context).colorVideo(rotation = 90)
        try {
            val metadata = LibraryRepository(context).open(Uri.fromFile(file))
            assertTrue(metadata.hasVideo)
            assertFalse(metadata.hasAudio)
            assertTrue(metadata.mimeType?.startsWith("video/") == true)
            assertTrue(metadata.durationUs > 0)
            val reader = VideoFrameSource(context, Uri.fromFile(file))
            reader.use {
                val before = it.frameAt(100_000, 120, 200)
                try {
                    assertTrue(Color.red(before.getPixel(before.width / 2, before.height / 2)) > 170)
                    assertTrue(before.width <= 120 && before.height <= 200)
                    assertTrue(before.height > before.width)
                    assertEquals(180f / 320, before.width.toFloat() / before.height, .02f)
                } finally { before.recycle() }
                val after = it.frameAt(800_000, 120, 200)
                try { assertGreen(after.getPixel(after.width / 2, after.height / 2)) }
                finally { after.recycle() }
            }
            try { reader.frameAt(0, 120, 200); fail("Closed reader accepted a frame request") }
            catch (_: IllegalStateException) { }
        } finally { file.delete() }
    }

    @Test fun exportedClipShowsSourceTimeVideoBehindForegroundWithOneAudioTrack() = runBlocking {
        val file = VideoFixtures(context).colorVideo()
        val output = File(context.cacheDir, "background-export-${UUID.randomUUID()}.mp4")
        try {
            val candidate = LibraryRepository(context).open(Uri.fromFile(file))
            assertTrue(candidate.hasVideo)
            assertFalse(candidate.hasAudio)
            val source = AudioRepository(context).acquireDecoded(candidate).use {
                candidate.copy(contentSha256 = it.audio.hash, durationUs = it.audio.durationUs)
            }
            val foreground = Layer(type = ElementType.SHAPE,
                transform = Transform(width = .25f, height = .25f),
                properties = buildJsonObject { put("shape", "rect"); put("color", "#FFFF0000") })
            VideoExporter(context).export(ExportRequest(
                Project(source = source, scene = Scene(layers = listOf(foreground))),
                700_000, 1_100_000, Uri.fromFile(output).toString(), ExportSettings(320, 180),
            ))
            val extractor = MediaExtractor()
            try {
                extractor.setDataSource(output.path)
                val mimes = (0 until extractor.trackCount).map {
                    extractor.getTrackFormat(it).getString(MediaFormat.KEY_MIME).orEmpty()
                }
                assertEquals(1, mimes.count { it.startsWith("audio/") })
                assertEquals(1, mimes.count { it.startsWith("video/") })
            } finally { extractor.release() }
            val retriever = MediaMetadataRetriever()
            try {
                retriever.setDataSource(output.path)
                val frame = requireNotNull(retriever.getFrameAtTime(100_000, MediaMetadataRetriever.OPTION_CLOSEST))
                try {
                    assertGreen(frame.getPixel(15, 15))
                    val center = frame.getPixel(frame.width / 2, frame.height / 2)
                    assertTrue("Foreground disappeared behind video", Color.red(center) > 170 && Color.green(center) < 80)
                } finally { frame.recycle() }
            } finally { retriever.release() }
        } finally { file.delete(); output.delete() }
    }
}
