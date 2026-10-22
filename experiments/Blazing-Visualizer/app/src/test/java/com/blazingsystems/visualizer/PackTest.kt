package com.blazingsystems.visualizer
import android.graphics.Bitmap
import com.blazingsystems.visualizer.packs.*
import com.blazingsystems.visualizer.project.*
import kotlinx.serialization.json.*
import org.junit.*
import org.junit.Assert.*
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config
import java.io.*
import java.nio.file.Files
import java.util.zip.*
@RunWith(RobolectricTestRunner::class) @Config(sdk=[28])
class PackTest {
 private lateinit var root:File
 @Before fun setup(){root=Files.createTempDirectory("packs").toFile()}
 @After fun cleanup(){root.deleteRecursively()}
 private fun wideImage():File=File(root,"disguised.bin").also {f->Bitmap.createBitmap(4097,1,Bitmap.Config.ARGB_8888).let{b->f.outputStream().use{b.compress(Bitmap.CompressFormat.PNG,100,it)};b.recycle()}}
 @Test fun imageLimitUsesContentDespiteExtension(){assertThrows(IllegalArgumentException::class.java){AssetChecks.validateImage(wideImage())}}
 @Test fun aveeLocalImageUsesSameLimit(){wideImage();val json="""{"compositions":[{"elements":[{"objType":"Image","customImage":{"v":"local:disguised.bin"}}]}]}""";assertThrows(IllegalArgumentException::class.java){AveePresetAdapter.read(json,root)}}
 @Test fun nativeImageCannotBypassLimit(){val image=wideImage();val scene=Scene(layers=listOf(Layer(type=ElementType.IMAGE,properties=buildJsonObject{put("asset",image.name)})));val bytes=ByteArrayOutputStream();NativePackCodec().write(VisualizerPack(scene=scene),AssetResolver{image.inputStream()},bytes);assertThrows(IllegalArgumentException::class.java){NativePackCodec().read(bytes.toByteArray().inputStream(),File(root,"installed"))}}
 @Test fun nativeSceneRoundTrip(){val scene=Scene(name="Round trip",layers=listOf(Layer(type=ElementType.NOTE_WHEEL)));val out=ByteArrayOutputStream();NativePackCodec().write(VisualizerPack(scene=scene),AssetResolver{error("No assets")},out);val imported=NativePackCodec().read(out.toByteArray().inputStream(),root);assertEquals(scene,imported.scene)}
 @Test fun traversalIsRejectedWithoutEscaping(){val out=ByteArrayOutputStream();ZipOutputStream(out).use{it.putNextEntry(ZipEntry("../escape"));it.write(42);it.closeEntry()};assertThrows(IllegalArgumentException::class.java){NativePackCodec().read(out.toByteArray().inputStream(),root)};assertFalse(File(root.parentFile,"escape").exists())}
 @Test fun deepJsonIsRejected(){assertThrows(IllegalArgumentException::class.java){boundedJson("[".repeat(65)+"0"+"]".repeat(65))}}
 @Test fun partialAveeSupportIsExplicit(){val result=AveePresetAdapter.read("""{"compositions":[{"elements":[{"objType":"UnknownShader"}]}]}""",root);assertTrue(result.report.requiresPartialAcceptance);assertTrue(result.report.unsupported.any{it.contains("UnknownShader")})}
}
