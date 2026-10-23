package com.blazingsystems.visualizer

import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Color
import com.blazingsystems.visualizer.project.*
import com.blazingsystems.visualizer.render.*
import java.nio.file.Files
import kotlinx.serialization.json.*
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config
import org.robolectric.annotation.GraphicsMode

@RunWith(RobolectricTestRunner::class)
@Config(sdk = [33])
@GraphicsMode(GraphicsMode.Mode.NATIVE)
class VideoBackgroundRenderingTest {
    private val foreground = Layer(
        type = ElementType.SHAPE,
        transform = Transform(width = .25f, height = .25f),
        properties = buildJsonObject { put("shape", "rect"); put("color", "#FFFF0000") },
    )

    private fun evaluated(scene: Scene) = SceneEvaluator.evaluate(scene, FeatureFrame(0), 0)

    @Test fun nativeForegroundRemainsAboveTheVideoFrame() {
        val assets = Files.createTempDirectory("video-native").toFile()
        val video = Bitmap.createBitmap(120, 120, Bitmap.Config.ARGB_8888)
        val output = Bitmap.createBitmap(120, 120, Bitmap.Config.ARGB_8888)
        try {
            video.eraseColor(Color.GREEN)
            ScenePainter(assets).use {
                it.draw(Canvas(output), evaluated(Scene(layers = listOf(foreground))), 120, 120,
                    videoFrame = video)
            }
            assertEquals(Color.GREEN, output.getPixel(5, 5))
            assertEquals(Color.RED, output.getPixel(60, 60))
        } finally { output.recycle(); video.recycle(); assets.deleteRecursively() }
    }

    @Test fun importedCompositionDoesNotClearTheVideoFrame() {
        val assets = Files.createTempDirectory("video-imported").toFile()
        val video = Bitmap.createBitmap(120, 120, Bitmap.Config.ARGB_8888)
        val output = Bitmap.createBitmap(120, 120, Bitmap.Config.ARGB_8888)
        val reference = Layer(type = ElementType.IMAGE,
            transform = Transform(width = .25f, height = .25f),
            avee = buildJsonObject { put("objType", "Image"); put("customImage", "composition:1") })
        val child = Layer(type = ElementType.IMAGE, composition = 1,
            avee = buildJsonObject {
                put("objType", "Image"); put("customImage", "internalres:white"); put("color", "#FFFF0000")
            })
        val scene = Scene(layers = listOf(reference, child), originalAvee = buildJsonObject {},
            aveeCompositionCount = 2, aveeRenderAspect = 1f)
        try {
            video.eraseColor(Color.GREEN)
            ScenePainter(assets).use {
                it.draw(Canvas(output), evaluated(scene), 120, 120, videoFrame = video)
            }
            assertEquals(Color.GREEN, output.getPixel(5, 5))
            assertEquals(Color.RED, output.getPixel(60, 60))
        } finally { output.recycle(); video.recycle(); assets.deleteRecursively() }
    }

    @Test fun transparentPreviewClearsPreviousPixelsAndAudioRestoresOpaqueBackground() {
        val assets = Files.createTempDirectory("video-transition").toFile()
        val output = Bitmap.createBitmap(120, 120, Bitmap.Config.ARGB_8888)
        try {
            ScenePainter(assets).use { painter ->
                output.eraseColor(Color.GREEN)
                painter.draw(Canvas(output), evaluated(Scene(layers = listOf(foreground))), 120, 120,
                    transparentBackground = true)
                assertEquals(Color.TRANSPARENT, output.getPixel(5, 5))
                assertEquals(Color.RED, output.getPixel(60, 60))
                // Reusing the bitmap must not leave the old foreground in a new source's frame.
                painter.draw(Canvas(output), evaluated(Scene()), 120, 120, transparentBackground = true)
                assertEquals(Color.TRANSPARENT, output.getPixel(60, 60))
                painter.draw(Canvas(output), evaluated(Scene(backgroundColor = "#FF123456")), 120, 120)
                assertEquals(Color.rgb(18, 52, 86), output.getPixel(5, 5))
                assertEquals(Color.rgb(18, 52, 86), output.getPixel(60, 60))
            }
        } finally { output.recycle(); assets.deleteRecursively() }
    }

    @Test fun portraitVideoIsContainedWithoutStretchingInALandscapeFrame() {
        val assets = Files.createTempDirectory("video-aspect").toFile()
        val video = Bitmap.createBitmap(20, 40, Bitmap.Config.ARGB_8888)
        val output = Bitmap.createBitmap(120, 60, Bitmap.Config.ARGB_8888)
        try {
            video.eraseColor(Color.GREEN)
            ScenePainter(assets).use {
                it.draw(Canvas(output), evaluated(Scene()), 120, 60, videoFrame = video)
            }
            assertEquals(Color.BLACK, output.getPixel(10, 30))
            assertEquals(Color.GREEN, output.getPixel(46, 30))
            assertEquals(Color.GREEN, output.getPixel(73, 30))
            assertEquals(Color.BLACK, output.getPixel(100, 30))
        } finally { output.recycle(); video.recycle(); assets.deleteRecursively() }
    }

    @Test fun importedAudioFallbackRemainsOpaqueAndLiveVideoPreviewCanClearIt() {
        val assets = Files.createTempDirectory("video-imported-alpha").toFile()
        val output = Bitmap.createBitmap(120, 120, Bitmap.Config.ARGB_8888)
        val scene = evaluated(Scene(backgroundColor = "invalid", originalAvee = buildJsonObject {},
            aveeCompositionCount = 1))
        try {
            ScenePainter(assets).use { painter ->
                output.eraseColor(Color.GREEN)
                painter.draw(Canvas(output), scene, 120, 120)
                assertEquals(Color.BLACK, output.getPixel(5, 5))
                painter.draw(Canvas(output), scene, 120, 120, transparentBackground = true)
                assertEquals(Color.TRANSPARENT, output.getPixel(5, 5))
            }
        } finally { output.recycle(); assets.deleteRecursively() }
    }
}
