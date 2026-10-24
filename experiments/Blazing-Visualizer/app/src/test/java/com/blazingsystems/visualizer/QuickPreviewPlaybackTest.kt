package com.blazingsystems.visualizer

import com.blazingsystems.visualizer.audio.*
import com.blazingsystems.visualizer.project.*
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.test.*
import org.junit.Assert.*
import org.junit.Test

@OptIn(ExperimentalCoroutinesApi::class)
class QuickPreviewPlaybackTest {
    @Test fun decoderStartupDoesNotStarveNotesAtEveryPlaybackSecond() = runTest {
        val positions = MutableStateFlow<QuickPreviewPosition?>(QuickPreviewPosition("track", 0))
        var cache = QuickPreviewFrames()
        var starts = 0
        backgroundScope.launch(UnconfinedTestDispatcher(testScheduler)) {
            quickPreviewPlayback(positions, { _, start, duration, _ -> flow {
                starts++
                // Slower startup, then faster-than-real-time estimation (hop is 46.44 ms).
                delay(250)
                var offset = 4096L
                while (offset * 1_000_000 / 22050 <= (duration ?: 20_000_000)) {
                    delay(40)
                    val time = start + offset * 1_000_000 / 22050
                    emit(FeatureFrame(time, notes = listOf(NoteEvent("held", 69, time, time + 120_000))))
                    offset += 1024
                }
            } }, { _, error -> throw error }).collect { cache = it }
        }
        var visible = 0
        var observed = 0
        repeat(200) { tick ->
            advanceTimeBy(40)
            val time = (tick + 1) * 40_000L
            positions.value = QuickPreviewPosition("track", time)
            runCurrent()
            if (time >= 2_000_000) {
                observed++
                val frame = cache.at("track", time)
                if (frame?.notes?.any { it.startUs <= time && time < it.endUs } == true) visible++
            }
        }
        assertTrue("Produced notes must remain visible after startup: $visible/$observed ticks, $starts decoder starts",
            visible >= observed * .85)
    }

    @Test fun seekingWithinTheSameSecondCancelsOldFramesAndStartsAtTheNewPlayhead() = runTest {
        val positions = MutableStateFlow<QuickPreviewPosition?>(QuickPreviewPosition("track", 0))
        val starts = mutableListOf<Long>()
        var cache = QuickPreviewFrames()
        backgroundScope.launch(UnconfinedTestDispatcher(testScheduler)) {
            quickPreviewPlayback(positions, { _, start, _, _ -> flow {
                starts += start
                delay(100)
                emit(FeatureFrame(start + 200_000, rms = .5f))
                delay(10_000)
            } }, { _, error -> throw error }).collect { cache = it }
        }
        advanceTimeBy(300)
        positions.value = QuickPreviewPosition("track", 300_000)
        runCurrent()
        assertNotNull(cache.at("track", 300_000))
        positions.value = QuickPreviewPosition("track", 800_000, discontinuity = 1)
        runCurrent()
        assertEquals(listOf(0L, 800_000L), starts)
        assertTrue("Seek must clear frames from before the discontinuity", cache.frames.isEmpty())
        advanceTimeBy(120)
        runCurrent()
        assertEquals(1_000_000L, cache.frames.single().sourceTimeUs)
        assertNull("Never show a future note early", cache.at("track", 800_000, 1))
        assertNull("Frames from another seek version cannot be displayed", cache.at("track", 1_000_000, 0))
        assertNotNull(cache.at("track", 1_000_000, 1))
    }

    @Test fun pausedPlaybackBoundsDecodeLookaheadAndTrackSwitchDropsTheOldCache() = runTest {
        val positions = MutableStateFlow<QuickPreviewPosition?>(QuickPreviewPosition("a", 0))
        var produced = 0
        var cancelled = false
        var cache = QuickPreviewFrames()
        backgroundScope.launch(UnconfinedTestDispatcher(testScheduler)) {
            quickPreviewPlayback(positions, { uri, start, _, _ -> flow {
                try {
                    var time = start + 200_000
                    while (true) {
                        produced++
                        emit(FeatureFrame(time, rms = if (uri == "a") .4f else .8f))
                        time += 40_000
                    }
                } finally { if (uri == "a") cancelled = true }
            } }, { _, error -> throw error }).collect { cache = it }
        }
        advanceTimeBy(5_000)
        runCurrent()
        assertTrue("A paused playhead must not decode the whole track: $produced frames", produced <= 23)
        assertTrue(cache.frames.all { it.sourceTimeUs <= 1_000_000 })
        positions.value = QuickPreviewPosition("b", 0)
        runCurrent()
        assertTrue(cancelled)
        assertNull(cache.at("a", 200_000))
        assertEquals(.8f, cache.at("b", 200_000)!!.rms, .001f)
    }

    @Test fun endOfFileStopsInsteadOfReopeningAnEmptyDecoder() = runTest {
        val positions = MutableStateFlow<QuickPreviewPosition?>(QuickPreviewPosition("track", 0))
        var starts = 0
        backgroundScope.launch(UnconfinedTestDispatcher(testScheduler)) {
            quickPreviewPlayback(positions, { _, _, _, _ -> flow<FeatureFrame> { starts++ } },
                { _, error -> throw error }).collect()
        }
        advanceTimeBy(5_000)
        runCurrent()
        assertEquals(1, starts)
    }
}
