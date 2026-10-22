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
import org.robolectric.annotation.GraphicsMode

@RunWith(RobolectricTestRunner::class)
@GraphicsMode(GraphicsMode.Mode.NATIVE)
class IterationRenderingTest {
    private fun render(scene: Scene, notes: List<NoteEvent> = emptyList()): Bitmap {
        val bitmap = Bitmap.createBitmap(420, 240, Bitmap.Config.ARGB_8888)
        val root = Files.createTempDirectory("piano-pixels").toFile()
        try {
            ScenePainter(root).use { it.draw(Canvas(bitmap), SceneEvaluator.evaluate(scene, FeatureFrame(100_000, notes = notes), 100_000), 420, 240) }
        } finally { root.deleteRecursively() }
        return bitmap
    }

    @Test fun explicitLayerColorWinsOverGlobalPalette() {
        val layer = Layer(type = ElementType.SHAPE, properties = buildJsonObject { put("color", "#FFFF0000") })
        val bitmap = render(Scene(layers = listOf(layer), paletteColor = "#FF00FF00"))
        assertEquals(Color.RED, bitmap.getPixel(210, 120))
        bitmap.recycle()
    }

    @Test fun zeroIntensityStopsDecorativeScaleMotion() {
        val layer = Layer(type = ElementType.SHAPE, bindings = listOf(Binding("scale", BindingSource.RMS)))
        val evaluated = SceneEvaluator.evaluate(Scene(layers = listOf(layer), animationIntensity = 0f), FeatureFrame(0, rms = 1f), 0)
        assertEquals(1f, evaluated.layers.single().scale, 0f)
    }

    @Test fun aC4ImpactNeverLightsAnUnpressedD4Key() {
        val layer = Layer(type = ElementType.PIANO_ROLL)
        val base = Scene(layers = listOf(layer))
        val note = NoteEvent("C4", 60, 0, 500_000)
        val quiet = render(base.copy(pianoIntensity = 0f), listOf(note))
        val glowing = render(base, listOf(note))
        // 21 white keys from C3 through B5: D4 is the ninth white key.
        val d4Center = 170
        for (y in 161..205) assertEquals("Unpressed D4 changed at y=$y", quiet.getPixel(d4Center, y), glowing.getPixel(d4Center, y))
        quiet.recycle(); glowing.recycle()
    }
}
