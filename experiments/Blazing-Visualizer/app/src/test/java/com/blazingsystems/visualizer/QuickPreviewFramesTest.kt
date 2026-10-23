package com.blazingsystems.visualizer

import com.blazingsystems.visualizer.audio.QuickPreviewFrames
import com.blazingsystems.visualizer.project.FeatureFrame
import org.junit.Assert.*
import org.junit.Test

class QuickPreviewFramesTest {
    @Test fun rejectsAnOldSourcesLateDecodeAndNeverUsesAFutureOrStaleFrame() {
        val frames = QuickPreviewFrames("new")
            .withFrame("new", FeatureFrame(200_000, rms = .5f))
            .withFrame("old", FeatureFrame(250_000, rms = 1f))
        assertNull(frames.at("old", 200_000))
        assertNull(frames.at("new", 199_999))
        assertEquals(.5f, frames.at("new", 250_000)!!.rms, .001f)
        assertNull(frames.at("new", 400_000))
    }

    @Test fun overlappingDecodeWindowsRemainSortedDeduplicatedAndBounded() {
        var frames = QuickPreviewFrames("track")
        for (i in 0..120) frames = frames.withFrame("track", FeatureFrame(i * 40_000L))
        frames = frames.withFrame("track", FeatureFrame(4_000_000, rms = .75f))
        assertEquals(96, frames.frames.size)
        assertEquals(96, frames.frames.map { it.sourceTimeUs }.distinct().size)
        assertEquals(frames.frames.sortedBy { it.sourceTimeUs }, frames.frames)
        assertEquals(.75f, frames.at("track", 4_010_000)!!.rms, .001f)
        assertNull(frames.at("track", 0))
    }
}
