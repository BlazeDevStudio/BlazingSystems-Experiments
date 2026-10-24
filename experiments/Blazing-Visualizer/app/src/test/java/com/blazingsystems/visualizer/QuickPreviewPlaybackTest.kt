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
                while (offset * 1_000_000 / 22050 <= duration) {
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
}
