package com.blazingsystems.visualizer

import android.content.ContextWrapper
import com.blazingsystems.visualizer.analysis.*
import java.io.File
import java.nio.file.Files
import kotlinx.coroutines.runBlocking
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import org.junit.Assert.assertNull
import org.junit.Test
import org.junit.runner.RunWith
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry

@RunWith(AndroidJUnit4::class)
class TimelineAnalysisCacheTest {
    @Test fun notesFromConcatenatedPcmAreNotReusedForSourceTimeAudio() = runBlocking {
        val directory = Files.createTempDirectory("timeline-analysis-cache").toFile()
        val context = object : ContextWrapper(InstrumentationRegistry.getInstrumentation().targetContext) {
            override fun getFilesDir() = directory
        }
        try {
            val parameters = AnalysisParameters()
            val hash = "old-video-content"
            val modelHash = ModelRunner.MODEL_SHA256
            val legacyKey = sha256(
                "basic-pitch-cache-v2:$hash:$modelHash:${Json.encodeToString(parameters)}".toByteArray(),
            )
            val legacy = AnalysisResult(legacyKey, hash, modelHash, parameters, 300_000, emptyList())
            File(directory, "analysis-v2/$legacyKey.json").apply {
                parentFile!!.mkdirs()
                writeText(Json.encodeToString(legacy))
            }
            assertNull("Old zero-based notes must be reanalyzed on the corrected timeline",
                AnalysisRepository(context).cached(hash, parameters))
        } finally { directory.deleteRecursively() }
    }
}
