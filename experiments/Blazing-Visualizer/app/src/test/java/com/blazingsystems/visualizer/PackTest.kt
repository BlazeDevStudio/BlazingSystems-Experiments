package com.blazingsystems.visualizer

import android.graphics.Bitmap
import com.blazingsystems.visualizer.packs.*
import com.blazingsystems.visualizer.project.*
import java.io.*
import java.nio.file.Files
import java.util.zip.*
import kotlinx.serialization.json.*
import org.junit.*
import org.junit.Assert.*
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class)
@Config(sdk = [28])
class PackTest {
    private lateinit var root: File

    @Before
    fun setup() {
        root = Files.createTempDirectory("packs").toFile()
    }

    @After
    fun cleanup() {
        root.deleteRecursively()
    }

    private fun wideImage(): File =
        File(root, "disguised.bin").also { f ->
            Bitmap.createBitmap(4097, 1, Bitmap.Config.ARGB_8888).let { b ->
                f.outputStream().use { b.compress(Bitmap.CompressFormat.PNG, 100, it) }
                b.recycle()
            }
        }

    @Test
    fun imageLimitUsesContentDespiteExtension() {
        assertThrows(IllegalArgumentException::class.java) {
            AssetChecks.validateImage(wideImage())
        }
    }

    @Test
    fun aveeLocalImageUsesSameLimit() {
        wideImage()
        val json =
            """{"compositions":[{"elements":[{"objType":"Image","customImage":{"v":"local:disguised.bin"}}]}]}"""
        assertThrows(IllegalArgumentException::class.java) { AveePresetAdapter.read(json, root) }
    }

    @Test
    fun nativeImageCannotBypassLimit() {
        val image = wideImage()
        val scene =
            Scene(
                layers =
                    listOf(
                        Layer(
                            type = ElementType.IMAGE,
                            properties = buildJsonObject { put("asset", image.name) },
                        ),
                    ),
            )
        val bytes = ByteArrayOutputStream()
        NativePackCodec()
            .write(VisualizerPack(scene = scene), AssetResolver { image.inputStream() }, bytes)
        assertThrows(IllegalArgumentException::class.java) {
            NativePackCodec().read(bytes.toByteArray().inputStream(), File(root, "installed"))
        }
    }

    @Test
    fun nativeSceneRoundTrip() {
        val scene =
            Scene(name = "Round trip", layers = listOf(Layer(type = ElementType.NOTE_WHEEL)))
        val out = ByteArrayOutputStream()
        NativePackCodec()
            .write(VisualizerPack(scene = scene), AssetResolver { error("No assets") }, out)
        val imported = NativePackCodec().read(out.toByteArray().inputStream(), root)
        assertEquals(scene, imported.scene)
    }

    @Test
    fun traversalIsRejectedWithoutEscaping() {
        val out = ByteArrayOutputStream()
        ZipOutputStream(out).use {
            it.putNextEntry(ZipEntry("../escape"))
            it.write(42)
            it.closeEntry()
        }
        assertThrows(IllegalArgumentException::class.java) {
            NativePackCodec().read(out.toByteArray().inputStream(), root)
        }
        assertFalse(File(root.parentFile, "escape").exists())
    }

    @Test
    fun deepJsonIsRejected() {
        assertThrows(IllegalArgumentException::class.java) {
            boundedJson("[".repeat(65) + "0" + "]".repeat(65))
        }
    }

    @Test
    fun zippedJsonVizIsDiscoverableWithoutCallingItFullFidelity() {
        val archive = File(root, "compatible.viz")
        ZipOutputStream(archive.outputStream()).use { zip ->
            zip.putNextEntry(ZipEntry("templates/single.viz"))
            zip.write("""{"compositions":[{"elements":[{"objType":"Waveform"}]}]}""".toByteArray())
            zip.closeEntry()
        }
        val content = AveePresetAdapter.loadPresetText(archive, File(root, "extract"))
        val imported = AveePresetAdapter.read(content, root)
        assertEquals(ElementType.WAVEFORM, imported.scene.layers.single().type)
        assertTrue(imported.report.requiresPartialAcceptance)
    }

    @Test
    fun modernShapedVectorsAndBooleanVisibilityDoNotCrashImporter() {
        val json = """{"elements":[{"objType":"Image","_name":"foreground",
          "position":{"v":[0.3,0.7]},"scale":{"v":{"x":0.5,"y":0.2}},
          "rotation":{"v":45},"visible":{"v":false}}]}"""
        val result = AveePresetAdapter.read(json, root)
        val layer = result.scene.layers.single()
        assertFalse(layer.visible)
        assertEquals(.3f, layer.transform.x, .0001f)
        assertEquals(.7f, layer.transform.y, .0001f)
        assertEquals(.5f, layer.transform.width, .0001f)
        assertEquals(.2f, layer.transform.height, .0001f)
        assertEquals(45f, layer.transform.rotation, .0001f)
    }

    @Test
    fun archiveWithTwoPresetsRequiresExplicitChoice() {
        val archive = File(root, "ambiguous.viz")
        ZipOutputStream(archive.outputStream()).use { zip ->
            for (name in listOf("one.viz", "two.viz")) {
                zip.putNextEntry(ZipEntry(name))
                zip.write("""{"compositions":[]}""".toByteArray())
                zip.closeEntry()
            }
        }
        assertThrows(IllegalArgumentException::class.java) {
            AveePresetAdapter.loadPresetText(archive, File(root, "ambiguous"))
        }
    }

    @Test
    fun modernAveeAudioProviderAndBlurRoundTripWithoutSourceBranding() {
        val json = """{"compositions":[{"elements":[
          {"objType":"AudioProvider","sampleProvider":{"v":"Spectrum2"},
           "sampleOutCount":{"v":128},"lowerHz":{"v":30},
           "higherHz":{"v":9000},"outputMultiplier":{"v":1.8}},
          {"objType":"Bars","position":{"v":"0.5 0.4"},
           "scale":{"v":"0.8 0.3"},"ShapePath":{"v":"Circle"},
           "rotation":{"v":20},"visible":{"v":1}},
          {"objType":"BlurEffect","visible":{"v":1},"color":{"v":-1}},
          {"objType":"AppLogo","visible":{"v":1}}
        ]}]}"""
        val imported = AveePresetAdapter.read(json, root)
        assertEquals(2, imported.scene.layers.size)
        assertEquals(ElementType.SPECTRUM, imported.scene.layers[0].type)
        assertEquals(20f, imported.scene.layers[0].transform.rotation, .001f)
        assertEquals(ElementType.BLUR, imported.scene.layers[1].type)
        assertEquals("128", imported.scene.aveeAudio["sampleOutCount"]?.jsonPrimitive?.content)
        assertFalse(imported.scene.layers.any { it.name == "AppLogo" })
        val out = ByteArrayOutputStream()
        NativePackCodec().write(VisualizerPack(scene = imported.scene),
            AssetResolver { error("No assets") }, out)
        val restored = NativePackCodec().read(out.toByteArray().inputStream(),
            File(root, "native-avee")).scene
        assertEquals(imported.scene, restored)
    }

    @Test
    fun modernSpectrumWaveformAndBlurAliasesPreserveColorsAndVisibility() {
        val json = """{"compositions":[{"elements":[
            {"objType":"Spectrum2","position":[0.25,0.75],"scale":{"v":"0.6 0.2"},"visible":true,"color":"#FF44CC88"},
            {"objType":"Waveform","visible":false},
            {"objType":"BlurEffect","visible":1},
            {"objType":"MotionBlurEffect","visible":0}
        ]}]}"""
        val imported = AveePresetAdapter.read(json, root)
        assertEquals(4, imported.scene.layers.size)
        assertEquals(ElementType.SPECTRUM, imported.scene.layers[0].type)
        assertEquals(.25f, imported.scene.layers[0].transform.x, .0001f)
        assertEquals(.75f, imported.scene.layers[0].transform.y, .0001f)
        assertEquals(.6f, imported.scene.layers[0].transform.width, .0001f)
        assertEquals("#FF44CC88", imported.scene.layers[0].properties["color"]!!.jsonPrimitive.content)
        assertEquals(ElementType.WAVEFORM, imported.scene.layers[1].type)
        assertFalse(imported.scene.layers[1].visible)
        assertEquals(ElementType.BLUR, imported.scene.layers[2].type)
        assertFalse(imported.scene.layers[3].visible)
        assertTrue(imported.report.requiresPartialAcceptance)
    }

    @Test
    fun partialAveeSupportIsExplicit() {
        val result =
            AveePresetAdapter.read(
                """{"compositions":[{"elements":[{"objType":"UnknownShader"}]}]}""",
                root,
            )
        assertTrue(result.report.requiresPartialAcceptance)
        assertTrue(result.report.unsupported.any { it.contains("UnknownShader") })
    }
}
