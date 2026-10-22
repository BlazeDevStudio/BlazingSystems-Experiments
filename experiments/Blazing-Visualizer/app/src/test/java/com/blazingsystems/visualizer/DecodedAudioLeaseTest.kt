package com.blazingsystems.visualizer

import android.content.Context
import android.content.ContextWrapper
import android.net.Uri
import com.blazingsystems.visualizer.audio.*
import com.blazingsystems.visualizer.export.ExportRequest
import com.blazingsystems.visualizer.export.VideoExporter
import com.blazingsystems.visualizer.project.Project
import com.blazingsystems.visualizer.project.SourceRef
import java.io.File
import java.nio.file.Files
import java.security.MessageDigest
import java.util.concurrent.LinkedBlockingQueue
import java.util.concurrent.TimeUnit
import kotlin.coroutines.CoroutineContext
import kotlinx.coroutines.*
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import org.junit.*
import org.junit.Assert.*
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.RuntimeEnvironment
import org.robolectric.annotation.Config
import org.robolectric.shadows.ShadowStatFs

@RunWith(RobolectricTestRunner::class)
@Config(sdk = [28])
class DecodedAudioLeaseTest {
    private lateinit var directory: File
    private lateinit var context: Context
    private lateinit var source: SourceRef
    private lateinit var decoded: DecodedAudio

    @Before
    fun setup() {
        directory = Files.createTempDirectory("decoded-audio-leases").toFile()
        context = object : ContextWrapper(RuntimeEnvironment.getApplication()) {
            override fun getCacheDir() = directory
        }
        val original = File(directory, "source.audio").apply { writeText("cached source") }
        val hash = MessageDigest.getInstance("SHA-256").digest(original.readBytes())
            .joinToString("") { "%02x".format(it) }
        source = SourceRef(Uri.fromFile(original).toString())
        val folder = File(directory, "audio-v1/$hash").apply { mkdirs() }
        decoded = DecodedAudio(hash, 22050, 1, 1, folder.path)
        decoded.pcmFile.writeBytes(byteArrayOf(1, 2))
        decoded.monoFile.writeBytes(byteArrayOf(0, 0, 0, 0))
        File(folder, "audio.json").writeText(Json.encodeToString(decoded))
    }

    @After
    fun cleanup() {
        directory.deleteRecursively()
    }

    @Test
    fun previewAndExportBothKeepPcmUntilTheirLastLeaseCloses() {
        val preview = AudioRepository(context).retain(decoded.hash)
        val export = AudioRepository(context).retain(decoded.hash)
        val cleaner = AudioRepository(context)
        try {
            cleaner.discardDecoded(decoded.hash)
            cleaner.compactDecodedCache(emptySet(), limitBytes = 0)
            assertTrue(decoded.pcmFile.isFile)
            preview.close()
            preview.close()
            cleaner.compactDecodedCache(emptySet(), limitBytes = 0)
            assertTrue("An export still needs the original PCM", decoded.pcmFile.isFile)
        } finally {
            preview.close()
            export.close()
        }
        cleaner.compactDecodedCache(emptySet(), limitBytes = 0)
        assertFalse(File(decoded.rootPath).exists())
    }

    @Test
    fun acquiredExportCanReopenOriginalPcmAfterBackgroundCleanup() = runBlocking {
        AudioRepository(context).acquireDecoded(source).use { lease ->
            assertEquals(decoded, lease.audio)
            assertEquals(4, lease.audio.monoFile.readBytes().size)
            AudioRepository(context).discardDecoded(decoded.hash)
            AudioRepository(context).compactDecodedCache(emptySet(), limitBytes = 0)
            assertArrayEquals(byteArrayOf(1, 2), lease.audio.pcmFile.readBytes())
        }
        AudioRepository(context).discardDecoded(decoded.hash)
        assertFalse(File(decoded.rootPath).exists())
    }

    @Test
    fun cancelledOwnerReleasesItsDecodedFiles() = runBlocking {
        val acquired = CompletableDeferred<Unit>()
        val owner = launch(Dispatchers.Default) {
            AudioRepository(context).acquireDecoded(source).use {
                acquired.complete(Unit)
                awaitCancellation()
            }
        }
        try {
            withTimeout(5_000) { acquired.await() }
            AudioRepository(context).discardDecoded(decoded.hash)
            assertTrue(decoded.pcmFile.isFile)
        } finally {
            owner.cancelAndJoin()
        }
        AudioRepository(context).discardDecoded(decoded.hash)
        assertFalse(File(decoded.rootPath).exists())
    }

    @Test
    fun cancellationWhileReturningFromIoDoesNotLeakAnAcquiredLease() = runBlocking {
        val dispatcher = QueuedDispatcher()
        val owner = launch(dispatcher) {
            AudioRepository(context).acquireDecoded(source).use { awaitCancellation() }
        }
        dispatcher.next().run()
        val returningFromIo = dispatcher.next()
        owner.cancel()
        returningFromIo.run()
        withTimeout(5_000) { owner.join() }
        AudioRepository(context).discardDecoded(decoded.hash)
        assertFalse("Prompt cancellation must close the unreturned lease", decoded.pcmFile.exists())
    }

    @Test
    fun rejectedExportReleasesItsLease() = runBlocking {
        ShadowStatFs.registerStats(directory.path, 100_000, 100_000, 100_000)
        val request = ExportRequest(
            Project(source = source.copy(contentSha256 = "changed")), 0, 1, "content://unused",
        )
        try {
            VideoExporter(context).export(request)
            fail("Expected the changed audio to be rejected")
        } catch (caught: IllegalArgumentException) {
            assertTrue(caught.message.orEmpty().contains("audio file changed"))
        }
        AudioRepository(context).discardDecoded(decoded.hash)
        assertFalse(File(decoded.rootPath).exists())
    }

    @Test
    fun failedCacheLookupReleasesItsLease() = runBlocking {
        File(decoded.rootPath, "audio.json").writeText("{")
        try {
            AudioRepository(context).acquireDecoded(source).close()
            fail("Expected invalid metadata to fail")
        } catch (_: kotlinx.serialization.SerializationException) {
            // A failed acquisition has no caller that could release its temporary retention.
        }
        AudioRepository(context).discardDecoded(decoded.hash)
        assertFalse(File(decoded.rootPath).exists())
    }

    @Test
    fun anotherDecoderWaitsForCancelledStagingCleanupAcrossInstances() = runBlocking {
        val first = DecodedAudioLeases(File(directory, "audio-v1"))
        val second = DecodedAudioLeases(File(directory, "audio-v1/../audio-v1"))
        val staging = File(directory, "audio-v1/${decoded.hash}.pending")
        val started = CompletableDeferred<Unit>()
        val following = CompletableDeferred<Unit>()
        val cancelledDecoder = launch(Dispatchers.Default) {
            first.decoding {
                staging.mkdirs()
                File(staging, "original.pcm").writeText("partial")
                started.complete(Unit)
                try {
                    awaitCancellation()
                } finally {
                    staging.deleteRecursively()
                }
            }
        }
        withTimeout(5_000) { started.await() }
        val followingDecoder = launch(start = CoroutineStart.UNDISPATCHED) {
            second.decoding {
                assertFalse("The cancelled decode must finish cleanup first", staging.exists())
                staging.mkdirs()
                File(staging, "original.pcm").writeText("complete")
                following.complete(Unit)
            }
        }
        try {
            assertFalse("The same cache cannot have two staging owners", following.isCompleted)
        } finally {
            cancelledDecoder.cancelAndJoin()
        }
        withTimeout(5_000) { followingDecoder.join() }
        assertEquals("complete", File(staging, "original.pcm").readText())
    }

    private class QueuedDispatcher : CoroutineDispatcher() {
        private val pending = LinkedBlockingQueue<Runnable>()

        override fun dispatch(context: CoroutineContext, block: Runnable) {
            pending.add(block)
        }

        fun next(): Runnable =
            checkNotNull(pending.poll(5, TimeUnit.SECONDS)) { "Coroutine dispatch timed out" }
    }
}
