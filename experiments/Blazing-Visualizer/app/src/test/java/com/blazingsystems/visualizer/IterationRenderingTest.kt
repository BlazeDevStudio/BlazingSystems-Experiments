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
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class)
@Config(sdk = [33])
@GraphicsMode(GraphicsMode.Mode.NATIVE)
class IterationRenderingTest {
    private fun render(scene: Scene, notes: List<NoteEvent> = emptyList(), width: Int = 420, height: Int = 240, time: Long = 100_000): Bitmap {
        val bitmap = Bitmap.createBitmap(width, height, Bitmap.Config.ARGB_8888)
        val root = Files.createTempDirectory("piano-pixels").toFile()
        try {
            ScenePainter(root).use { it.draw(Canvas(bitmap), SceneEvaluator.evaluate(scene, FeatureFrame(time, notes = notes), time), width, height) }
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

    @Test fun lowRoutedPianoActuallyDisplaysTheGuitarE2() {
        val scene = Scene(layers = listOf(Layer(type = ElementType.PIANO_ROLL,
            noteRouting = NoteRouting(NoteBand.LO))))
        val idle = render(scene)
        val played = render(scene, listOf(NoteEvent("E2", 40, 0, 500_000)))
        var changed = 0
        for (x in 0 until 420) for (y in 155 until 235)
            if (idle.getPixel(x,y) != played.getPixel(x,y)) changed++
        assertTrue("The selected low note must reach a visible key", changed > 10)
        idle.recycle(); played.recycle()
    }

    @Test fun fittedTextUsesTheSamePhysicalScaleAsItsLayer() {
        val scene = Scene(designAspect = 16f/9, layers = listOf(Layer(type = ElementType.TEXT,
            transform = Transform(width = .5f, height = .5f),
            properties = buildJsonObject { put("text", "X"); put("fontSize", "100"); put("color", "#FF0000") })))
        val landscape = render(scene, width = 640, height = 360)
        val portrait = render(SceneLayouts.fit(scene, 9f/16), width = 360, height = 640)
        fun inkHeight(bitmap: Bitmap): Int {
            val ys = (0 until bitmap.height).filter { y ->
                (0 until bitmap.width).any { x -> Color.red(bitmap.getPixel(x,y)) > 80 }
            }
            return ys.last() - ys.first() + 1
        }
        assertEquals(inkHeight(landscape)*360.0/640, inkHeight(portrait).toDouble(), 2.0)
        landscape.recycle(); portrait.recycle()
    }

    @Test fun graphEquationsAreAbsentUntilEnabledAndZeroEffectsAreStill() {
        val notes = listOf(NoteEvent("A4",69,0,3_000_000))
        val scene = Scene(layers = listOf(Layer(type = ElementType.MATH_CURVE)), animationIntensity = 0f)
        val hidden = render(scene, notes)
        val later = render(scene, notes, time = 2_000_000)
        val shown = render(scene.copy(showEquations = true), notes)
        var textPixels = 0
        for (x in 0 until 420) for (y in 0 until 240) {
            assertEquals(hidden.getPixel(x,y), later.getPixel(x,y))
            if (y >= 229) {
                assertEquals(Color.rgb(8,9,17), hidden.getPixel(x,y))
                if (shown.getPixel(x,y) != hidden.getPixel(x,y)) textPixels++
            }
        }
        assertTrue(textPixels > 5)
        hidden.recycle(); later.recycle(); shown.recycle()
    }
}
