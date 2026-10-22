package com.blazingsystems.visualizer.project

import java.util.UUID
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.JsonObject

@Serializable
data class SourceRef(
    val uri: String,
    val contentSha256: String? = null,
    val durationUs: Long = 0,
    val title: String = "Untitled",
    val artist: String = "",
)

@Serializable
enum class NoteProvenance {
    ESTIMATED,
    CORRECTED,
}

@Serializable
data class NoteEvent(
    val id: String,
    val pitch: Int,
    val startUs: Long,
    val endUs: Long,
    val amplitude: Float = 1f,
    val activation: Float = 1f,
    val provenance: NoteProvenance = NoteProvenance.ESTIMATED,
    val bendCents: List<Float> = emptyList(),
)

@Serializable
sealed class NoteEdit {
    @Serializable data class Insert(val event: NoteEvent) : NoteEdit()

    @Serializable data class Replace(val event: NoteEvent) : NoteEdit()

    @Serializable data class Delete(val id: String) : NoteEdit()
}

@Serializable
enum class ElementType {
    IMAGE,
    TEXT,
    SHAPE,
    SPECTRUM,
    WAVEFORM,
    PARTICLES,
    BLUR,
    NOTE_WHEEL,
    PIANO_ROLL,
}

@Serializable
data class Transform(
    val x: Float = .5f,
    val y: Float = .5f,
    val width: Float = 1f,
    val height: Float = 1f,
    val rotation: Float = 0f,
)

@Serializable
enum class BindingSource {
    RMS,
    NOTE_ENERGY,
    SPECTRUM_BAND,
}

@Serializable
data class Binding(
    val property: String,
    val source: BindingSource,
    val amount: Float = 1f,
    val band: Int = 0,
)

/** The intermediate "2" bands are adjacent pitch regions, never loudness levels. */
@Serializable
enum class NoteBand { ALL, LO, LO2, MID, MID2, HI, HI2 }

@Serializable
data class NoteRouting(
    val band: NoteBand = NoteBand.ALL,
    val lowMidi: Int? = null,
    val highMidi: Int? = null,
) {
    fun bounds(): IntRange {
        val defaults = when (band) {
            NoteBand.ALL -> 0..127
            NoteBand.LO -> 0..40
            NoteBand.LO2 -> 41..52
            NoteBand.MID -> 53..64
            NoteBand.MID2 -> 65..76
            NoteBand.HI -> 77..88
            NoteBand.HI2 -> 89..127
        }
        return (lowMidi ?: defaults.first)..(highMidi ?: defaults.last)
    }

    fun allows(pitch: Int) = pitch in bounds()

    fun isValid(): Boolean {
        val range = bounds()
        return range.first in 0..127 && range.last in 0..127 &&
            range.first <= range.last
    }
}

@Serializable
data class Layer(
    val id: String = UUID.randomUUID().toString(),
    val type: ElementType,
    val name: String = type.name,
    val visible: Boolean = true,
    val transform: Transform = Transform(),
    val properties: JsonObject = JsonObject(emptyMap()),
    val bindings: List<Binding> = emptyList(),
    val noteRouting: NoteRouting = NoteRouting(),
)

@Serializable
data class Scene(
    val id: String = UUID.randomUUID().toString(),
    val name: String = "My visualizer",
    val layers: List<Layer> = emptyList(),
    val seed: Long = 1,
    val animationIntensity: Float = 1f,
    val pianoIntensity: Float = 1f,
    val paletteColor: String? = null,
)

data class FeatureFrame(
    val sourceTimeUs: Long,
    val rms: Float = 0f,
    val spectrum: List<Float> = emptyList(),
    val waveform: List<Float> = emptyList(),
    val notes: List<NoteEvent> = emptyList(),
    val chord: String? = null,
)

@Serializable
data class ExportSettings(
    val width: Int = 1280,
    val height: Int = 720,
    val fps: Int = 30,
    val videoBitrate: Int = 8_000_000,
    val audioBitrate: Int = 192_000,
)

@Serializable
data class PracticeSettings(
    val speed: Float = 1f,
    val preferFlats: Boolean = false,
    val instrumentSemitones: Int = 0,
    val register: Int = 0,
    val loopStartUs: Long? = null,
    val loopEndUs: Long? = null,
    val loopEnabled: Boolean = false,
) {
    fun isValid(): Boolean =
        speed.isFinite() && speed in .5f..1.5f &&
            instrumentSemitones in -12..12 && register in 0..3 &&
            (loopStartUs == null || loopStartUs >= 0) &&
            (loopEndUs == null || (loopStartUs != null && loopEndUs > loopStartUs)) &&
            (!loopEnabled || loopEndUs != null)
}

@Serializable
data class Project(
    val id: String = UUID.randomUUID().toString(),
    val source: SourceRef,
    val scene: Scene = Scene(),
    val analysisKey: String? = null,
    val edits: List<NoteEdit> = emptyList(),
    val export: ExportSettings = ExportSettings(),
    val practice: PracticeSettings = PracticeSettings(),
)

object SourceIdentity {
    fun bind(project: Project, source: SourceRef): Project {
        val changed =
            project.source.contentSha256 != null &&
                source.contentSha256 != null &&
                project.source.contentSha256 != source.contentSha256
        return project.copy(
            source = source,
            analysisKey = if (changed) null else project.analysisKey,
            edits = if (changed) emptyList() else project.edits,
        )
    }

    fun requireExportMatch(expected: String?, actual: String) {
        require(expected != null) {
            "The track is still preparing. Open it and wait before exporting."
        }
        require(expected == actual) {
            "This audio file changed. Open it again to reanalyze before exporting."
        }
    }
}
