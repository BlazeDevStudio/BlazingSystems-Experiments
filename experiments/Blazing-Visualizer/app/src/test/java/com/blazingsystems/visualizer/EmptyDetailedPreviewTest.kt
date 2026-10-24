package com.blazingsystems.visualizer

import com.blazingsystems.visualizer.project.*
import com.blazingsystems.visualizer.ui.StudioState
import org.junit.Assert.*
import org.junit.Test

class EmptyDetailedPreviewTest {
    @Test fun anEmptyUneditedAnalysisLeavesLiveEstimatesAvailable() {
        assertFalse(StudioState(analysisReady = true, analysisNoteCount = 0).prefersDetailedNotes())
        assertTrue(StudioState(analysisReady = true, analysisNoteCount = 3).prefersDetailedNotes())
    }

    @Test fun explicitCorrectionsRemainAuthoritativeEvenWhenAllNotesAreRemoved() {
        val project = Project(source = SourceRef("test"), edits = listOf(NoteEdit.Delete("note")))
        assertTrue(StudioState(project = project, analysisReady = true, analysisNoteCount = 0)
            .prefersDetailedNotes())
    }
}
