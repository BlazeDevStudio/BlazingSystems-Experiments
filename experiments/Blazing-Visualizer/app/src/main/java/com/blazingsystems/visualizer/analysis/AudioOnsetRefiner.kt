package com.blazingsystems.visualizer.analysis

import com.blazingsystems.visualizer.project.NoteEvent
import kotlin.math.*

object AudioOnsetRefiner {
    fun refine(
        notes: List<NoteEvent>,
        sampleRate: Int,
        read: (Long, Int) -> FloatArray,
    ): List<NoteEvent> = notes.map { note ->
        val start = (note.startUs - 120_000).coerceAtLeast(0)
        if (notes.any { it.id != note.id && it.startUs < start && it.endUs > start })
            return@map note
        val pcm = read(start * sampleRate / 1_000_000, (170_000L * sampleRate / 1_000_000).toInt())
        val window = (sampleRate * .02).toInt().coerceAtLeast(1)
        val hop = (sampleRate * .005).toInt().coerceAtLeast(1)
        val envelope =
            (0..(pcm.size - window).coerceAtLeast(0) step hop).map { offset ->
                sqrt(
                    (offset until min(offset + window, pcm.size)).sumOf {
                        (pcm[it] * pcm[it]).toDouble()
                    } / window,
                )
            }
        if (envelope.size < 5) return@map note
        val peak = envelope.maxOrNull() ?: 0.0
        val floor = envelope.take(4).maxOrNull() ?: 0.0
        if (peak < .0001 || floor > peak * .06) return@map note
        val threshold = max(peak * .12, floor * 4)
        val crossing =
            envelope.indices.firstOrNull {
                it >= 2 && envelope[it] >= threshold && envelope[it - 1] < threshold
            } ?: return@map note
        val onset = start + (crossing.toLong() * hop + window / 2) * 1_000_000 / sampleRate
        if (abs(onset - note.startUs) <= 100_000 && onset < note.endUs) note.copy(startUs = onset)
        else note
    }
}
