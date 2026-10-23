package com.blazingsystems.visualizer

import android.media.MediaFormat
import android.net.Uri
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import androidx.media3.exoplayer.MediaExtractorCompat
import com.blazingsystems.visualizer.audio.AudioRepository
import com.blazingsystems.visualizer.audio.DecodedAudio
import com.blazingsystems.visualizer.playback.LibraryRepository
import java.io.RandomAccessFile
import java.nio.ByteBuffer
import java.nio.ByteOrder
import kotlin.math.sqrt
import kotlinx.coroutines.runBlocking
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
@androidx.annotation.OptIn(androidx.media3.common.util.UnstableApi::class)
class AudioTimelineNativeTest {
    private val context = InstrumentationRegistry.getInstrumentation().targetContext

    /** Read the real export PCM at a source-clock position; missing frames are silence. */
    private fun rms(audio: DecodedAudio, timeUs: Long): Double {
        val bytes = ByteArray(audio.sampleRate / 20 * audio.channels * 2)
        RandomAccessFile(audio.pcmFile, "r").use { file ->
            file.seek(timeUs * audio.sampleRate / 1_000_000 * audio.channels * 2)
            var offset = 0
            while (offset < bytes.size) {
                val count = file.read(bytes, offset, bytes.size - offset)
                if (count < 0) break
                offset += count
            }
        }
        val pcm = ByteBuffer.wrap(bytes).order(ByteOrder.LITTLE_ENDIAN)
        var power = 0.0
        repeat(bytes.size / 2) { val sample = pcm.short / 32768.0; power += sample * sample }
        return sqrt(power / (bytes.size / 2))
    }

    private fun monoRms(audio: DecodedAudio, timeUs: Long): Double {
        val bytes = ByteArray(22050 / 20 * 4)
        RandomAccessFile(audio.monoFile, "r").use { file ->
            file.seek(timeUs * 22050 / 1_000_000 * 4)
            var offset = 0
            while (offset < bytes.size) {
                val count = file.read(bytes, offset, bytes.size - offset)
                if (count < 0) break
                offset += count
            }
        }
        val pcm = ByteBuffer.wrap(bytes).order(ByteOrder.LITTLE_ENDIAN)
        var power = 0.0
        repeat(bytes.size / 4) { val sample = pcm.float.toDouble(); power += sample * sample }
        return sqrt(power / (bytes.size / 4))
    }

    private fun withDecodedVideo(check: (TimedAudioVideoFixture.Result, DecodedAudio) -> Unit) = runBlocking {
        val fixture = TimedAudioVideoFixture(context).create()
        val repository = AudioRepository(context)
        var hash: String? = null
        try {
            // Verify the fixture's offset/gap survived the real MP4 muxer before testing PCM.
            val extractor = MediaExtractorCompat(context)
            try {
                extractor.setDataSource(fixture.file.path)
                val track = (0 until extractor.trackCount).single {
                    extractor.getTrackFormat(it).getString(MediaFormat.KEY_MIME)?.startsWith("audio/") == true
                }
                extractor.selectTrack(track)
                assertEquals("Fixture lost its delayed audio start", 300_000L, extractor.sampleTime)
                var previous = extractor.sampleTime
                var largestGap = 0L
                while (extractor.advance()) {
                    largestGap = maxOf(largestGap, extractor.sampleTime - previous)
                    previous = extractor.sampleTime
                }
                assertTrue("Fixture lost its interior timestamp gap", largestGap >= 300_000)
                assertTrue("Audio must end before the video", previous < 1_100_000)
            } finally { extractor.release() }
            val source = LibraryRepository(context).open(Uri.fromFile(fixture.file))
            assertTrue(source.hasVideo && source.hasAudio)
            assertTrue("Fixture video must outlast its short audio", source.durationUs >= 1_150_000)
            repository.acquireDecoded(source).use { lease ->
                hash = lease.audio.hash
                check(fixture, lease.audio)
            }
        } finally {
            hash?.let(repository::discardDecoded)
            fixture.file.delete()
        }
    }

    @Test fun delayedAudioLeavesLeadingSilenceInExportPcm() = withDecodedVideo { _, audio ->
        assertTrue("The real audio must remain available", audio.hasAudio)
        assertTrue("Audio was moved from 300ms to the start of the video", rms(audio, 100_000) < .001)
        assertTrue("Analysis PCM lost the initial delay", monoRms(audio, 100_000) < .001)
    }

    @Test fun audioAfterATimestampGapKeepsItsSourcePosition() = withDecodedVideo { fixture, audio ->
        assertTrue("Interior timestamp gaps must be silence", rms(audio, fixture.gapStartUs + 50_000) < .001)
        assertTrue("The second audio segment was moved earlier or dropped", rms(audio, fixture.gapEndUs + 50_000) > .05)
        assertTrue("Analysis PCM collapsed the timestamp gap", monoRms(audio, fixture.gapStartUs + 50_000) < .001)
        assertTrue("Analysis PCM lost the second segment", monoRms(audio, fixture.gapEndUs + 50_000) > .05)
    }

    @Test fun decodedPcmIncludesTheSilentTailOfTheVideo() = withDecodedVideo { fixture, audio ->
        val source = LibraryRepository(context).open(Uri.fromFile(fixture.file))
        assertEquals("Video duration was truncated to the audio sample count",
            source.durationUs.toDouble(), audio.durationUs.toDouble(), 1_000_000.0 / audio.sampleRate)
        assertTrue("The video tail must not repeat the final sound", rms(audio, 1_100_000) < .001)
        assertTrue("Analysis PCM must include the video tail", audio.monoFile.length() / 4 >= 22050 * 1.19)
        assertTrue("Analysis PCM must keep the tail silent", monoRms(audio, 1_100_000) < .001)
    }
}
