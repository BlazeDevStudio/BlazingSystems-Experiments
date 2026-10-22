package com.blazingsystems.visualizer

import android.media.*
import android.net.Uri
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import com.blazingsystems.visualizer.analysis.*
import com.blazingsystems.visualizer.audio.*
import com.blazingsystems.visualizer.export.*
import com.blazingsystems.visualizer.packs.*
import com.blazingsystems.visualizer.practice.*
import com.blazingsystems.visualizer.project.*
import com.blazingsystems.visualizer.render.*
import java.io.*
import java.nio.*
import kotlin.math.*
import kotlinx.coroutines.*
import org.json.*
import org.junit.*
import org.junit.Assert.*
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class NativeAcceptanceTest {
    private val instrument = InstrumentationRegistry.getInstrumentation()
    private val context = instrument.targetContext

    private fun floats(name: String): FloatArray {
        val bytes = instrument.context.assets.open(name).use { it.readBytes() }
        val b = ByteBuffer.wrap(bytes).order(ByteOrder.LITTLE_ENDIAN)
        return FloatArray(bytes.size / 4) { b.float }
    }

    private fun array(name: String, bins: Int): Array<FloatArray> {
        val values = floats(name)
        return Array(values.size / bins) { t -> FloatArray(bins) { p -> values[t * bins + p] } }
    }

    private fun fixture(name: String): SourceRef {
        val file = File(context.filesDir, "$name.wav")
        instrument.context.assets.open("$name.wav").use { input ->
            file.outputStream().use(input::copyTo)
        }
        return SourceRef(Uri.fromFile(file).toString(), title = name)
    }

    private fun evidence(name: String, value: JSONObject) {
        atomicWrite(
            File(context.filesDir, "acceptance/$name.json"),
            value.toString(2).toByteArray(),
        )
    }

    @Test
    fun modelMatchesIndependentPythonOutput() {
        ModelRunner(context).use { runner ->
            assertEquals(ModelRunner.MODEL_SHA256, runner.modelHash)
            val out = runner.run(floats("synthetic.window.f32"))
            val errors = JSONObject()
            for ((key, predicted, bins) in
                listOf(
                    Triple("note", out.note, 88),
                    Triple("onset", out.onset, 88),
                    Triple("contour", out.contour, 264),
                )) {
                val expected = array("first-window.$key.f32", bins)
                var error = 0f
                for (t in predicted.indices) for (p in 0 until bins) error =
                    max(error, abs(predicted[t][p] - expected[t][p]))
                errors.put(key, error.toDouble())
            }
            evidence("model-parity", errors)
            for (key in errors.keys()) assertTrue(
                "$key max error ${errors.getDouble(key)}",
                errors.getDouble(key) < .001,
            )
        }
    }

    @Test
    fun postprocessorMatchesSpotifyReference() {
        val output =
            ModelOutputs(
                array("full.note.f32", 88),
                array("full.onset.f32", 88),
                array("full.contour.f32", 264),
            )
        val actual = NotePostprocessor.decode(output, 4_000_000)
        val expected =
            JSONArray(
                instrument.context.assets
                    .open("synthetic.reference.json")
                    .bufferedReader()
                    .readText(),
            )
        assertEquals(expected.length(), actual.size)
        actual.forEachIndexed { i, n ->
            val e = expected.getJSONObject(i)
            assertEquals(e.getInt("pitch"), n.pitch)
            assertTrue(abs(e.getLong("startUs") - n.startUs) <= 2)
            assertTrue(abs(e.getLong("endUs") - n.endUs) <= 2)
        }
    }

    @Test
    fun rawSyntheticAndRecordedFluteMeetOnsetTarget() = runBlocking {
        for (name in listOf("synthetic", "flute")) {
            val source = fixture(name)
            val decoded = AudioRepository(context).get(source)
            val result = AnalysisRepository(context).getOrAnalyze(decoded)
            val expected =
                JSONObject(
                        instrument.context.assets
                            .open("$name.expected.json")
                            .bufferedReader()
                            .readText(),
                    )
                    .getJSONArray("events")
            val available = result.rawNotes.toMutableList()
            var matched = 0
            val deltas = JSONArray()
            for (i in 0 until expected.length()) {
                val e = expected.getJSONObject(i)
                val candidate =
                    available
                        .filter { it.pitch == e.getInt("pitch") }
                        .minByOrNull { abs(it.startUs - e.getLong("startUs")) }
                if (candidate != null && abs(candidate.startUs - e.getLong("startUs")) <= 50_000) {
                    matched++
                    deltas.put(candidate.startUs - e.getLong("startUs"))
                    available.remove(candidate)
                }
            }
            val f1 = 2.0 * matched / (expected.length() + result.rawNotes.size)
            val report =
                JSONObject()
                    .put("fixture", name)
                    .put("matches", matched)
                    .put("expected", expected.length())
                    .put("predicted", result.rawNotes.size)
                    .put("onsetToleranceUs", 50000)
                    .put("rawF1", f1)
                    .put("deltasUs", deltas)
                    .put(
                        "notes",
                        JSONArray(
                            result.rawNotes.map {
                                JSONObject()
                                    .put("pitch", it.pitch)
                                    .put("startUs", it.startUs)
                                    .put("endUs", it.endUs)
                            },
                        ),
                    )
            evidence("$name-accuracy", report)
            assertTrue("$name raw onset F1=$f1: $report", f1 >= .8)
        }
    }

    @Test
    fun rendererReplaysSamePixelsAfterSeek() {
        for ((width, height) in listOf(320 to 180, 180 to 320, 240 to 240)) {
            val notes = listOf(60, 64, 67).map { NoteEvent("$it", it, 100_000, 2_000_000) }
            val frame =
                FeatureFrame(
                    1_000_000,
                    .2f,
                    List(1024) { .15f },
                    List(256) { sin(it * .1).toFloat() },
                    notes,
                )
            val scene = SceneEvaluator.evaluate(BuiltinScenes.noteWheel(), frame, 1_000_000)
            fun draw(value: EvaluatedScene): ByteArray =
                GlTarget.pbuffer(width, height).use { target ->
                    GlSceneRenderer(File(context.filesDir, "assets")).use {
                        it.render(value, target)
                        target.readPixels()
                    }
                }
            val first = draw(scene)
            draw(SceneEvaluator.evaluate(scene.scene, frame, 2_500_000))
            val replay = draw(scene)
            assertArrayEquals(first, replay)
            assertTrue(first.toSet().size > 8)
        }
        evidence(
            "renderer-parity",
            JSONObject().put("aspectRatios", 3).put("sameTimestampReplay", true),
        )
    }

    @Test
    fun noteEditsAndPackRoundTripRemainExportable() = runBlocking {
        val decoded = AudioRepository(context).get(fixture("synthetic"))
        val raw = AnalysisRepository(context).getOrAnalyze(decoded).rawNotes
        val edited = applyNoteEdits(raw, listOf(NoteEdit.Replace(raw.first().copy(pitch = 62))))
        assertEquals(62, edited.first().pitch)
        assertNotEquals(62, raw.first().pitch)
        val midi = ByteArrayOutputStream()
        NoteExport.writeMidi(edited, midi)
        assertEquals("MThd", String(midi.toByteArray(), 0, 4))
        val scene = BuiltinScenes.noteWheel()
        val pack = ByteArrayOutputStream()
        NativePackCodec()
            .write(VisualizerPack(scene = scene), AssetResolver { error("no assets") }, pack)
        val imported =
            NativePackCodec()
                .read(pack.toByteArray().inputStream(), File(context.cacheDir, "test-pack"))
        assertEquals(scene, imported.scene)
    }

    @Test
    fun mp4ExportHasAudioVideoForAllRequiredPresets() = runBlocking {
        val decoded = AudioRepository(context).get(fixture("synthetic"))
        val source =
            SourceRef(
                Uri.fromFile(File(context.filesDir, "synthetic.wav")).toString(),
                decoded.hash,
                decoded.durationUs,
                "Acceptance",
            )
        val reports = JSONArray()
        for ((width, height) in
            listOf(
                1280 to 720,
                720 to 1280,
                720 to 720,
                1920 to 1080,
                1080 to 1920,
                1080 to 1080,
            )) {
            val file =
                File(context.filesDir, "acceptance/export-${width}x$height.mp4").apply {
                    parentFile!!.mkdirs()
                }
            val project = Project(source = source, scene = BuiltinScenes.noteWheel())
            VideoExporter(context)
                .export(
                    ExportRequest(
                        project,
                        300_000,
                        400_000,
                        Uri.fromFile(file).toString(),
                        ExportSettings(width, height),
                    ),
                )
            val report = inspect(file, 100_000, width, height)
            reports.put(report)
            file.delete()
        }
        val full = File(context.filesDir, "acceptance/export-full.mp4")
        VideoExporter(context)
            .export(
                ExportRequest(
                    Project(source = source, scene = BuiltinScenes.noteWheel()),
                    0,
                    4_000_000,
                    Uri.fromFile(full).toString(),
                    ExportSettings(320, 180),
                ),
            )
        reports.put(inspect(full, 4_000_000, 320, 180))
        val originalBytes = decoded.monoFile.readBytes()
        val originalBuffer = ByteBuffer.wrap(originalBytes).order(ByteOrder.LITTLE_ENDIAN)
        val original = FloatArray(originalBytes.size / 4) { originalBuffer.float }
        val converted = ArrayList<Float>()
        var resampler: PcmResampler? = null
        PcmDecoder(context).decode(Uri.fromFile(full)).collect { chunk ->
            if (resampler == null) resampler = PcmResampler(chunk.sampleRate, chunk.channels)
            resampler!!.feed(chunk.samples).forEach { converted.add(it) }
        }
        resampler?.feed(FloatArray(0), true)?.forEach { converted.add(it) }
        var best = -1.0
        var bestLag = 0
        for (lag in -2200..2200 step 8) {
            var xy = 0.0
            var xx = 0.0
            var yy = 0.0
            for (i in 2304 until min(original.size, converted.size) - 2304 step 32) {
                val x = original[i].toDouble()
                val y = converted[i + lag].toDouble()
                xy += x * y
                xx += x * x
                yy += y * y
            }
            val score = xy / sqrt(xx * yy).coerceAtLeast(1e-12)
            if (score > best) {
                best = score
                bestLag = lag
            }
        }
        val lagUs = bestLag * 1_000_000L / 22050
        evidence(
            "audio-alignment",
            JSONObject()
                .put("bestLagUs", lagUs)
                .put("normalizedCorrelation", best)
                .put("toleranceUs", 50000),
        )
        assertTrue("AAC/source correlation=$best, lag=$lagUs us", best > .8 && abs(lagUs) <= 50_000)

        evidence("export-matrix", JSONObject().put("results", reports))
    }

    private fun inspect(file: File, duration: Long, width: Int, height: Int): JSONObject {
        assertTrue(file.length() > 0)
        val e = MediaExtractor()
        try {
            e.setDataSource(file.path)
            assertEquals(2, e.trackCount)
            val tracks = JSONArray()
            for (i in 0 until e.trackCount) {
                val f = e.getTrackFormat(i)
                val mime = f.getString(MediaFormat.KEY_MIME)!!
                val actual = f.getLong(MediaFormat.KEY_DURATION)
                assertTrue("$mime duration $actual vs $duration", abs(actual - duration) <= 50_000)
                if (mime.startsWith("video")) {
                    assertEquals(width, f.getInteger(MediaFormat.KEY_WIDTH))
                    assertEquals(height, f.getInteger(MediaFormat.KEY_HEIGHT))
                }
                e.selectTrack(i)
                var previous = -1L
                var first = -1L
                var count = 0
                while (e.sampleTrackIndex >= 0) {
                    val time = e.sampleTime
                    if (first < 0) first = time
                    assertTrue(time >= previous)
                    previous = time
                    count++
                    e.advance()
                }
                e.unselectTrack(i)
                assertTrue(count > 0)
                assertTrue(first in 0..50_000)
                tracks.put(
                    JSONObject()
                        .put("mime", mime)
                        .put("durationUs", actual)
                        .put("firstPtsUs", first)
                        .put("lastPtsUs", previous)
                        .put("samples", count),
                )
            }
            return JSONObject().put("width", width).put("height", height).put("tracks", tracks)
        } finally {
            e.release()
        }
    }

    @Test
    fun cancellationNeverCompletesDestination() = runBlocking {
        val decoded = AudioRepository(context).get(fixture("synthetic"))
        val file = File(context.filesDir, "cancel-test.mp4")
        file.delete()
        val source =
            SourceRef(
                Uri.fromFile(File(context.filesDir, "synthetic.wav")).toString(),
                decoded.hash,
                decoded.durationUs,
            )
        val worker = launch {
            VideoExporter(context).export(
                ExportRequest(
                    Project(source = source),
                    0,
                    4_000_000,
                    Uri.fromFile(file).toString(),
                    ExportSettings(320, 180),
                ),
            ) {
                if (it > .1f) cancel()
            }
        }
        worker.join()
        assertTrue(worker.isCancelled)
        assertFalse(file.exists())
    }
}
