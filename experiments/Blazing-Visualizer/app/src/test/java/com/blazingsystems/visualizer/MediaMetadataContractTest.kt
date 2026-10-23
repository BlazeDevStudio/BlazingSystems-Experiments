package com.blazingsystems.visualizer

import android.view.TextureView
import androidx.test.core.app.ApplicationProvider
import com.blazingsystems.visualizer.project.SourceRef
import com.blazingsystems.visualizer.render.SceneView
import kotlinx.serialization.decodeFromString
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.*
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class)
@Config(sdk = [33])
class MediaMetadataContractTest {
    private val json = Json { ignoreUnknownKeys = true; encodeDefaults = true }

    @Test fun silentVideoMetadataSurvivesLibraryAndProjectSerialization() {
        val source = json.decodeFromString<SourceRef>("""{
            "uri":"content://media/video/7", "title":"Silent clip",
            "mimeType":"video/mp4", "hasVideo":true, "hasAudio":false
        }""")
        val saved = json.parseToJsonElement(json.encodeToString(source)).jsonObject
        assertEquals("video/mp4", saved["mimeType"]?.jsonPrimitive?.content)
        assertEquals(true, saved["hasVideo"]?.jsonPrimitive?.boolean)
        assertEquals(false, saved["hasAudio"]?.jsonPrimitive?.boolean)
    }

    @Test fun legacyAudioProjectsStillLoadWithoutAMigration() {
        val source = json.decodeFromString<SourceRef>("""{"uri":"content://media/audio/1","title":"Old track"}""")
        assertEquals("Old track", source.title)
        val saved = json.parseToJsonElement(json.encodeToString(source)).jsonObject
        assertEquals(false, saved["hasVideo"]?.jsonPrimitive?.boolean)
        assertEquals(true, saved["hasAudio"]?.jsonPrimitive?.boolean)
    }

    @Test fun previewSurfaceParticipatesInNormalViewLayering() {
        assertTrue("Video must remain behind the visualizer in normal Android view order",
            (SceneView(ApplicationProvider.getApplicationContext()) as Any) is TextureView)
    }
}
