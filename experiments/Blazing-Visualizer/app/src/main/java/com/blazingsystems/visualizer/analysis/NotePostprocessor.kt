package com.blazingsystems.visualizer.analysis

// Copyright 2022 Spotify AB. Adapted from Basic Pitch note_creation.py, Apache-2.0.
import com.blazingsystems.visualizer.project.*
import java.security.MessageDigest
import kotlin.math.*
import kotlinx.serialization.Serializable
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json

@Serializable
data class AnalysisParameters(
    val onsetThreshold: Float = .5f,
    val frameThreshold: Float = .3f,
    val minNoteFrames: Int = 11,
    val inferOnsets: Boolean = true,
    val melodia: Boolean = true,
    val refineIsolatedOnsets: Boolean = true,
    val includePitchBends: Boolean = false,
)

data class ModelOutputs(
    val note: Array<FloatArray>,
    val onset: Array<FloatArray>,
    val contour: Array<FloatArray>,
)

fun sha256(bytes: ByteArray) =
    MessageDigest.getInstance("SHA-256").digest(bytes).joinToString("") { "%02x".format(it) }

object AnalysisKeys {
    fun key(sourceHash: String, modelHash: String, parameters: AnalysisParameters) =
        sha256(
            "basic-pitch-cache-v2:$sourceHash:$modelHash:${Json.encodeToString(parameters)}"
                .toByteArray(),
        )
}

object NotePostprocessor {
    fun frameTimeUs(frame: Int): Long {
        val offset = (256.0 / 22050) * (172 - 43844.0 / 256) + .0018
        return ((frame * 256.0 / 22050 - offset * floor(frame / 172.0)) * 1_000_000).roundToLong()
    }

    fun decode(
        output: ModelOutputs,
        durationUs: Long,
        parameters: AnalysisParameters = AnalysisParameters(),
    ): List<NoteEvent> {
        val frames = output.note
        val n = frames.size
        if (n < 3) return emptyList()
        require(
            output.onset.size == n &&
                frames.all { it.size == 88 } &&
                output.onset.all { it.size == 88 },
        )
        val onsets = Array(n) { output.onset[it].copyOf() }
        if (parameters.inferOnsets) {
            val diff = Array(n) { FloatArray(88) }
            var maxDiff = 0f
            var maxOnset = 0f
            for (t in 0 until n) for (p in 0..87) {
                maxOnset = max(maxOnset, onsets[t][p])
                if (t >= 2) {
                    diff[t][p] =
                        max(
                            0f,
                            min(frames[t][p] - frames[t - 1][p], frames[t][p] - frames[t - 2][p]),
                        )
                    maxDiff = max(maxDiff, diff[t][p])
                }
            }
            if (maxDiff > 0)
                for (t in 0 until n) for (p in 0..87) onsets[t][p] =
                    max(onsets[t][p], diff[t][p] * maxOnset / maxDiff)
        }
        val remaining = Array(n) { frames[it].copyOf() }
        data class Span(val start: Int, val end: Int, val pitch: Int)
        val spans = mutableListOf<Span>()
        fun clear(t: Int, p: Int) {
            for (adjacent in max(0, p - 1)..min(87, p + 1)) remaining[t][adjacent] = 0f
        }
        for (t in n - 2 downTo 1) for (p in 87 downTo 0) {
            if (
                onsets[t][p] < parameters.onsetThreshold ||
                    onsets[t][p] <= onsets[t - 1][p] ||
                    onsets[t][p] <= onsets[t + 1][p]
            )
                continue
            var end = t + 1
            var below = 0
            while (end < n - 1 && below < 11) {
                if (remaining[end][p] < parameters.frameThreshold) below++ else below = 0
                end++
            }
            end -= below
            if (end - t <= parameters.minNoteFrames) continue
            for (i in t until end) clear(i, p)
            spans += Span(t, end, p)
        }
        if (parameters.melodia) {
            val candidates = ArrayList<Int>()
            for (t in 0 until n) for (p in 0..87) if (remaining[t][p] > parameters.frameThreshold)
                candidates += t * 88 + p
            candidates.sortWith(
                compareByDescending<Int> { remaining[it / 88][it % 88] }.thenBy { it },
            )
            for (index in candidates) {
                val middle = index / 88
                val pitch = index % 88
                if (remaining[middle][pitch] <= parameters.frameThreshold) continue
                remaining[middle][pitch] = 0f
                var i = middle + 1
                var below = 0
                while (i < n - 1 && below < 11) {
                    if (remaining[i][pitch] < parameters.frameThreshold) below++ else below = 0
                    clear(i, pitch)
                    i++
                }
                val end = i - 1 - below
                i = middle - 1
                below = 0
                while (i > 0 && below < 11) {
                    if (remaining[i][pitch] < parameters.frameThreshold) below++ else below = 0
                    clear(i, pitch)
                    i--
                }
                val start = i + 1 + below
                if (end - start > parameters.minNoteFrames) spans += Span(start, end, pitch)
            }
        }
        return spans
            .mapNotNull { span ->
                val start = frameTimeUs(span.start).coerceIn(0, durationUs)
                val end = frameTimeUs(span.end).coerceIn(0, durationUs)
                if (end <= start) return@mapNotNull null
                val amplitude =
                    (span.start until span.end)
                        .sumOf { frames[it][span.pitch].toDouble() }
                        .div(span.end - span.start)
                        .toFloat()
                val bends =
                    if (parameters.includePitchBends && output.contour.size == n)
                        (span.start until span.end).map { t ->
                            val center = span.pitch * 3
                            val bin =
                                (max(0, center - 25)..min(263, center + 25)).maxBy {
                                    output.contour[t][it] * exp(-.5 * ((it - center) / 5.0).pow(2))
                                }
                            (bin - center) * 100f / 3
                        }
                    else emptyList()
                NoteEvent(
                    "bp-${span.pitch+21}-${span.start}-${span.end}",
                    span.pitch + 21,
                    start,
                    end,
                    amplitude,
                    onsets[span.start][span.pitch],
                    bendCents = bends,
                )
            }
            .sortedWith(compareBy<NoteEvent> { it.startUs }.thenBy { it.pitch })
    }
}

fun validateNote(note: NoteEvent) {
    require(
        note.pitch in 0..127 &&
            note.startUs >= 0 &&
            note.endUs > note.startUs &&
            note.amplitude.isFinite(),
    ) {
        "Invalid note pitch or duration"
    }
}

fun applyNoteEdits(raw: List<NoteEvent>, edits: List<NoteEdit>): List<NoteEvent> {
    val merged = raw.associateBy { it.id }.toMutableMap()
    edits.forEach {
        when (it) {
            is NoteEdit.Delete -> merged.remove(it.id)
            is NoteEdit.Insert -> {
                validateNote(it.event)
                merged[it.event.id] = it.event.copy(provenance = NoteProvenance.CORRECTED)
            }
            is NoteEdit.Replace -> {
                validateNote(it.event)
                merged[it.event.id] = it.event.copy(provenance = NoteProvenance.CORRECTED)
            }
        }
    }
    return merged.values.sortedWith(compareBy<NoteEvent> { it.startUs }.thenBy { it.pitch })
}

object ChordEstimator {
    private val names = arrayOf(
        "C", "C♯", "D", "E♭", "E", "F", "F♯", "G", "A♭", "A", "B♭", "B",
    )

    // Pitch-class templates: octave doublings and inversions remain valid.
    // Equal pitch sets can have more than one harmonic explanation. Prefer
    // the lowest sounding voice as the root, but never invent a chord from
    // incomplete or extra pitch classes.
    private val quality = listOf(
        "" to setOf(0, 4, 7),
        "m" to setOf(0, 3, 7),
        "dim" to setOf(0, 3, 6),
        "aug" to setOf(0, 4, 8),
        "sus2" to setOf(0, 2, 7),
        "sus4" to setOf(0, 5, 7),
        "maj7" to setOf(0, 4, 7, 11),
        "m7" to setOf(0, 3, 7, 10),
        "7" to setOf(0, 4, 7, 10),
        "mMaj7" to setOf(0, 3, 7, 11),
        "dim7" to setOf(0, 3, 6, 9),
        "m7♭5" to setOf(0, 3, 6, 10),
        "6" to setOf(0, 4, 7, 9),
        "m6" to setOf(0, 3, 7, 9),
        "add9" to setOf(0, 2, 4, 7),
        "9" to setOf(0, 2, 4, 7, 10),
        "m9" to setOf(0, 2, 3, 7, 10),
        "maj9" to setOf(0, 2, 4, 7, 11),
    )

    private fun active(notes: List<NoteEvent>, timeUs: Long): List<NoteEvent> =
        notes.filter { timeUs >= it.startUs && timeUs < it.endUs }

    fun estimate(notes: List<NoteEvent>, timeUs: Long): String? {
        val sounding = active(notes, timeUs)
        val pitches = sounding.map { Math.floorMod(it.pitch, 12) }.toSet()
        if (pitches.size < 3) return null
        val bass = sounding.minByOrNull { it.pitch }?.pitch?.let { Math.floorMod(it, 12) }
        for (root in (listOfNotNull(bass) + (0..11)).distinct()) {
            for ((suffix, intervals) in quality) {
                if (pitches == intervals.map { (root + it) % 12 }.toSet()) {
                    return names[root] + suffix
                }
            }
        }
        return null
    }

    /** Show each detected note once when a chord cannot be named. */
    fun displayLabel(
        notes: List<NoteEvent>, timeUs: Long, emptyText: String = "FOLLOW THE NOTES",
    ): String {
        val sounding = active(notes, timeUs)
        if (sounding.isEmpty()) return emptyText.take(120)
        estimate(sounding, timeUs)?.let { return it }
        return sounding.map { Math.floorMod(it.pitch, 12) }.distinct().sorted()
            .joinToString(" · ") { names[it] }
    }
}
