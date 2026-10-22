package com.blazingsystems.visualizer.project

import com.blazingsystems.visualizer.analysis.applyNoteEdits

data class NoteEditTarget(val projectId: String, val sourceHash: String?) {
    companion object {
        fun of(project: Project) = NoteEditTarget(project.id, project.source.contentSha256)
    }
}

object NoteEditing {
    fun apply(project: Project, target: NoteEditTarget, edit: NoteEdit): Project {
        require(
            project.id == target.projectId && project.source.contentSha256 == target.sourceHash,
        ) {
            "The track changed. Open its note again before correcting it."
        }
        applyNoteEdits(emptyList(), listOf(edit))
        return project.copy(edits = project.edits + edit)
    }
}
