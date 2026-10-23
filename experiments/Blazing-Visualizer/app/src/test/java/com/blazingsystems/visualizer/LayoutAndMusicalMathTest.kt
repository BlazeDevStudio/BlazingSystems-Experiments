package com.blazingsystems.visualizer

import com.blazingsystems.visualizer.project.*
import com.blazingsystems.visualizer.render.*
import kotlin.math.*
import kotlinx.serialization.decodeFromString
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import org.junit.Assert.*
import org.junit.Test

class LayoutAndMusicalMathTest {
    @Test fun equalTemperamentUsesMidi69AndDoesNotSnapAFifthToJustTuning() {
        assertEquals(440.0, MusicalMath.frequency(69), 1e-9)
        assertEquals(27.5, MusicalMath.frequency(21), 1e-9)
        assertEquals(1.4983070768766815, MusicalMath.ratio(67, 60), 1e-12)
        assertNotEquals(1.5, MusicalMath.ratio(67, 60), 1e-6)
    }

    @Test fun unisonCircleUsesQuadratureAndAllChordVoicesContribute() {
        for (i in 0..80) {
            val theta = i * PI / 40
            val p = MusicalMath.point(MathVisualMode.LISSAJOUS, listOf(1.0), listOf(1.0), theta)
            assertEquals(1.0, p.x * p.x + p.y * p.y, 1e-9)
        }
        val four = MusicalMath.point(MathVisualMode.ORBITS, listOf(1.0, 1.25, 1.5, 1.875), List(4) { 1.0 }, .71)
        val three = MusicalMath.point(MathVisualMode.ORBITS, listOf(1.0, 1.25, 1.875), List(3) { 1.0 }, .71)
        assertTrue(abs(four.x - three.x) + abs(four.y - three.y) > .01)
    }

    @Test fun fitKeepsPhysicalScaleAndStaysInsideEveryExportShape() {
        val scene = Scene(designAspect = 1f, layers = listOf(Layer(type = ElementType.PIANO_ROLL, transform = Transform(width = .8f, height = .7f))))
        for (aspect in listOf(16f/9, 9f/16, 1f)) {
            val t = SceneLayouts.fit(scene, aspect).layers.single().transform
            assertTrue(t.x - t.width/2 >= 0f && t.x + t.width/2 <= 1f)
            assertTrue(t.y - t.height/2 >= 0f && t.y + t.height/2 <= 1f)
            assertEquals(.8f/.7f, t.width * aspect/t.height, .00001f)
        }
    }

    @Test fun coverFillsPortraitInsteadOfLeavingEmptyBottomSpace() {
        val layer = Layer(type = ElementType.SHAPE,
            transform = Transform(width = .8f, height = 1f))
        val scene = Scene(designAspect = 1f, layers = listOf(layer))
        val project = Project(source = SourceRef("content://test"), scene = scene,exportFrameMode=ExportFrameMode.COVER)
        val settings = ExportSettings(720, 1280)
        val cover = SceneLayouts.forExport(project, settings)
        val fit = SceneLayouts.forExport(project.copy(exportFrameMode = ExportFrameMode.CONTAIN), settings)
        assertEquals(1f, cover.layers.single().transform.height, .00001f)
        assertTrue(fit.layers.single().transform.height < .6f)
        assertTrue(cover.layers.single().transform.width > fit.layers.single().transform.width)
        val stretch = SceneLayouts.forExport(project.copy(exportFrameMode = ExportFrameMode.STRETCH), settings)
        assertEquals(settings.width.toFloat() / settings.height, stretch.designAspect, .00001f)
        assertEquals(ExportFrameMode.COVER,
            Json.decodeFromString<Project>(Json.encodeToString(project)).exportFrameMode)
    }

    @Test fun separateExportArrangementRoundTripsWithoutMovingPreview() {
        val layer = Layer(id = "piano", type = ElementType.PIANO_ROLL)
        val moved = Transform(x = .25f, y = .3f, width = .4f, height = .3f)
        val p = Project(source = SourceRef("content://song"), scene = Scene(layers = listOf(layer)), exportLayout = ExportLayoutMode.SEPARATE, exportTransforms = mapOf(layer.id to moved))
        val restored = Json.decodeFromString<Project>(Json.encodeToString(p))
        assertEquals(layer.transform, restored.scene.layers.single().transform)
        assertEquals(moved, SceneLayouts.forExport(restored, ExportSettings(720, 720)).layers.single().transform)
        assertFalse(restored.scene.showEquations)
    }

    @Test fun rotatedHitTestAndResizeHaveBoundedCoordinates() {
        val layer = Layer(type = ElementType.SHAPE, transform = Transform(width = .2f, height = .2f, rotation = 45f))
        val scene = Scene(layers = listOf(layer))
        assertEquals(layer.id, SceneLayouts.hitTest(scene, .5f, .5f, 1f))
        assertNull(SceneLayouts.hitTest(scene, .9f, .9f, 1f))
        val t = SceneLayouts.resize(layer.transform, -10f, 100f)
        assertTrue(t.width >= .05f && t.height <= 2f)
    }
}
