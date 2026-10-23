package com.blazingsystems.visualizer

import android.graphics.Bitmap
import android.graphics.Canvas
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
@Config(sdk=[33])
@GraphicsMode(GraphicsMode.Mode.NATIVE)
class MotionRenderingTest {
    private val notes=listOf(60,64,67,71).map { NoteEvent("n-$it",it,0,4_000_000) }
    private fun render(scene: Scene,time: Long): IntArray {
        val root=Files.createTempDirectory("motion-frame").toFile()
        val bitmap=Bitmap.createBitmap(240,240,Bitmap.Config.ARGB_8888)
        try {
            ScenePainter(root).use { it.draw(Canvas(bitmap),SceneEvaluator.evaluate(scene,FeatureFrame(time,notes=notes),time),240,240) }
            return IntArray(240*240).also { bitmap.getPixels(it,0,240,0,0,240,240) }
        } finally { bitmap.recycle();root.deleteRecursively() }
    }
    @Test fun newPresetsHaveDifferentMotionAndRemainSeekDeterministic() {
        val images=MotionScenes.all().map { scene ->
            val a=render(scene,1_000_000)
            render(scene,2_000_000)
            assertArrayEquals(a,render(scene,1_000_000))
            a.contentHashCode()
        }
        assertEquals(5,images.distinct().size)
        assertTrue(MotionScenes.all().all { !it.showEquations })
    }
    @Test fun zeroEffectsFreezesEveryNewModeAndTrailIsNotAnOutline() {
        for(scene in MotionScenes.all()) {
            val still=scene.copy(layers=scene.layers.filter { it.type==ElementType.MATH_CURVE },
                animationIntensity=0f,pianoIntensity=0f)
            assertArrayEquals(render(still,500_000),render(still,2_000_000))
        }
        val scene=MotionScenes.all().first()
        val layers=scene.layers.map { if(it.type==ElementType.MATH_CURVE)
            it.copy(properties=JsonObject(it.properties+("motion" to JsonPrimitive("OUTLINE")))) else it }
        assertFalse(render(scene,1_000_000).contentEquals(render(scene.copy(layers=layers),1_000_000)))
    }
}
