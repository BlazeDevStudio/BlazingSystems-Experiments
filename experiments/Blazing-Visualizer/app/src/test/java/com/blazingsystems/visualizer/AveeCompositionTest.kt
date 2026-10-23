package com.blazingsystems.visualizer

import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Color
import com.blazingsystems.visualizer.packs.*
import com.blazingsystems.visualizer.project.*
import com.blazingsystems.visualizer.render.*
import java.io.ByteArrayOutputStream
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
class AveeCompositionTest {
    private fun raw(source: String,color: String="#FFFFFFFF")=buildJsonObject {
        put("objType","Image");put("customImage",buildJsonObject { put("v",source) });put("color",color)
    }
    private fun render(scene: Scene,w: Int=120,h: Int=120,features: FeatureFrame=FeatureFrame(0)): Bitmap {
        val root=Files.createTempDirectory("composition").toFile()
        return Bitmap.createBitmap(w,h,Bitmap.Config.ARGB_8888).also { b ->
            try { ScenePainter(root).use { it.draw(Canvas(b),SceneEvaluator.evaluate(scene,features,0),w,h) } }
            finally { root.deleteRecursively() }
        }
    }
    @Test fun onlyReferencedChildPassesReachTheOutput() {
        val layers=listOf(
            Layer(type=ElementType.IMAGE,avee=raw("composition:1"),transform=Transform(width=.5f,height=.5f)),
            Layer(type=ElementType.IMAGE,composition=1,avee=raw("internalres:white","#FFFF0000")),
            Layer(type=ElementType.IMAGE,composition=2,avee=raw("internalres:white","#FF00FF00")),
        )
        val scene=Scene(layers=layers,originalAvee=buildJsonObject {},aveeCompositionCount=3)
        val image=render(scene)
        assertEquals(Color.RED,image.getPixel(60,60))
        assertEquals(Color.rgb(8,9,17),image.getPixel(5,5))
        image.recycle()
    }
    @Test fun importedCircleIsFittedOnceAcrossAllCompositionPasses() {
        val child=Layer(type=ElementType.IMAGE,composition=1,avee=JsonObject(raw("internalres:white")+("Shape" to JsonPrimitive("Circle"))))
        val scene=Scene(layers=listOf(Layer(type=ElementType.IMAGE,avee=raw("composition:1")),child),originalAvee=buildJsonObject {},aveeCompositionCount=2)
        val image=render(SceneLayouts.fit(scene,.5f),120,240)
        assertEquals(Color.WHITE,image.getPixel(60,65))
        assertEquals(Color.WHITE,image.getPixel(5,120))
        assertNotEquals(Color.WHITE,image.getPixel(60,15))
        image.recycle()
    }
    @Test fun cyclicReferenceCannotHideItsOrdinarySiblingAndMetadataRoundTrips() {
        val text="""{"customFutureField":{"keep":true},"compositions":[{"elements":[
            {"objType":"Image","customImage":{"v":"composition:1"}}]},
            {"elements":[{"objType":"Image","customImage":{"v":"composition:1"}},
              {"objType":"Image","customImage":{"v":"internalres:white"},"color":-65536}]}]}"""
        val root=Files.createTempDirectory("composition-roundtrip").toFile()
        try {
            val imported=AveePresetAdapter.read(text,root)
            assertEquals(2,imported.scene.aveeCompositionCount)
            val image=render(imported.scene);assertEquals(Color.RED,image.getPixel(60,60));image.recycle()
            val bytes=ByteArrayOutputStream()
            NativePackCodec().write(VisualizerPack(scene=imported.scene),AssetResolver { error("no files") },bytes)
            val restored=NativePackCodec().read(bytes.toByteArray().inputStream(),root.resolve("pack"))
            assertEquals(imported.scene,restored.scene)
            assertNotNull(restored.scene.originalAvee?.get("customFutureField"))
        } finally { root.deleteRecursively() }
    }
    @Test fun bothSegmentsRetainTheirOwnColorAndSignedHeight() {
        val root=Files.createTempDirectory("dual-segment").toFile()
        try {
            val imported=AveePresetAdapter.read("""{"compositions":[{"elements":[{
                "objType":"Bars","position":{"v":"0.5 0.5"},"scale":{"v":"0.8 0.8"},
                "heightScale":{"v":1},"ShapePath":{"v":"HorizontalLine"},
                "Segment1":{"v":"Bars","colorFrom":{"v":-65536},"colorTo":{"v":-65536},"barHeightMultiplier":{"v":1}},
                "Segment2":{"v":"Bars","colorFrom":{"v":-16776961},"colorTo":{"v":-16776961},"barHeightMultiplier":{"v":-1}}
            }]}]}""",root)
            assertEquals(2,imported.scene.layers.size)
            val image=render(imported.scene,features=FeatureFrame(0,aveeSpectrum=List(32){.7f}))
            assertEquals(Color.RED,image.getPixel(60,40))
            assertEquals(Color.BLUE,image.getPixel(60,80))
            image.recycle()
        } finally { root.deleteRecursively() }
    }
    @Test fun explicitImageReplacementOverridesInternalAndCompositionSources() {
        val root=Files.createTempDirectory("image-override").toFile()
        try {
            val replacement=Bitmap.createBitmap(8,8,Bitmap.Config.ARGB_8888)
            replacement.eraseColor(Color.GREEN)
            root.resolve("replacement.png").outputStream().use { replacement.compress(Bitmap.CompressFormat.PNG,100,it) }
            replacement.recycle()
            for(source in listOf("internalres:white","composition:1")) {
                val imageLayer=Layer(type=ElementType.IMAGE,avee=raw(source),
                    properties=buildJsonObject { put("asset","replacement.png") })
                val child=Layer(type=ElementType.IMAGE,composition=1,avee=raw("internalres:white","#FFFF0000"))
                val scene=Scene(layers=listOf(imageLayer,child),originalAvee=buildJsonObject {},aveeCompositionCount=2)
                val image=Bitmap.createBitmap(120,120,Bitmap.Config.ARGB_8888)
                ScenePainter(root).use { it.draw(Canvas(image),SceneEvaluator.evaluate(scene,FeatureFrame(0),0),120,120) }
                assertEquals(source,Color.GREEN,image.getPixel(60,60));image.recycle()
            }
        } finally { root.deleteRecursively() }
    }
}
