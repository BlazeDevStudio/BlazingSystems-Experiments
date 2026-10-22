package com.blazingsystems.visualizer.ui

import androidx.compose.foundation.*
import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.*
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.*
import com.blazingsystems.visualizer.playback.PlaybackState
import com.blazingsystems.visualizer.practice.NoteNames
import com.blazingsystems.visualizer.project.*
import java.util.UUID

private data class NoteDraft(val note: NoteEvent, val target: NoteEditTarget, val isNew: Boolean)

@Composable
fun PracticeSheet(
    s: StudioState,
    p: PlaybackState,
    model: StudioModel,
    onMidi: () -> Unit,
    onCsv: () -> Unit,
) {
    val practice = s.project?.practice ?: PracticeSettings()
    val flats = practice.preferFlats
    val transpose = practice.instrumentSemitones
    val register = practice.register
    val a = practice.loopStartUs
    val b = practice.loopEndUs
    val looping = practice.loopEnabled
    var editing by
        remember(s.project?.id, s.project?.source?.contentSha256) {
            mutableStateOf<NoteDraft?>(null)
        }
    Column(Modifier.verticalScroll(rememberScrollState()).padding(20.dp)) {
        Text("Practice", fontSize = 25.sp, fontWeight = FontWeight.Bold)
        Text(
            "Estimated notes • listen, follow, and correct",
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        val active = s.notes.filter { it.startUs <= p.sourceTimeUs && p.sourceTimeUs < it.endUs }
        Text(
            active
                .joinToString("  ") { NoteNames.name(it.pitch, flats, transpose) }
                .ifEmpty { "—" },
            fontSize = 30.sp,
            fontWeight = FontWeight.Bold,
            color = MaterialTheme.colorScheme.primary,
            modifier = Modifier.padding(vertical = 16.dp),
        )
        Text("Playback speed · pitch stays the same", fontSize = 12.sp)
        Row(Modifier.horizontalScroll(rememberScrollState())) {
            listOf(.5f, .75f, 1f, 1.25f, 1.5f).forEach { speed ->
                FilterChip(
                    p.speed == speed,
                    { model.updatePractice { it.copy(speed = speed) } },
                    label = { Text("${speed}×") },
                    modifier = Modifier.padding(end = 8.dp),
                )
            }
        }
        Row(verticalAlignment = Alignment.CenterVertically) {
            OutlinedButton(
                onClick = {
                    model.updatePractice {
                        it.copy(loopStartUs = p.sourceTimeUs, loopEndUs = null, loopEnabled = false)
                    }
                },
                enabled = s.project != null,
            ) {
                Text("A ${a?.let(::time) ?: "—"}")
            }
            Spacer(Modifier.width(8.dp))
            OutlinedButton(
                onClick = {
                    if (a != null && p.sourceTimeUs > a!!) {
                        model.updatePractice {
                            it.copy(loopEndUs = p.sourceTimeUs, loopEnabled = true)
                        }
                    }
                },
                enabled = a != null && p.sourceTimeUs > (a ?: Long.MAX_VALUE),
            ) {
                Text("B ${b?.let(::time) ?: "—"}")
            }
            Spacer(Modifier.width(8.dp))
            FilterChip(
                looping,
                {
                    model.updatePractice { it.copy(loopEnabled = !looping) }
                },
                enabled = b != null,
                label = { Text("Loop") },
            )
        }
        Row(Modifier.horizontalScroll(rememberScrollState())) {
            listOf(0 to "Concert", 2 to "B♭ instrument", 9 to "E♭ instrument").forEach {
                (shift, label) ->
                FilterChip(
                    transpose == shift,
                    { model.updatePractice { it.copy(instrumentSemitones = shift) } },
                    label = { Text(label) },
                    modifier = Modifier.padding(end = 8.dp),
                )
            }
        }
        Row(verticalAlignment = Alignment.CenterVertically) {
            Switch(flats, { value -> model.updatePractice { it.copy(preferFlats = value) } })
            Text("Prefer flats", Modifier.padding(start = 8.dp))
            Spacer(Modifier.weight(1f))
            TextButton(
                onClick = {
                    model.setScene(com.blazingsystems.visualizer.render.BuiltinScenes.noteWheel())
                },
            ) {
                Text("Note wheel")
            }
        }
        Row(Modifier.horizontalScroll(rememberScrollState())) {
            listOf("All", "Bass", "Middle", "High").forEachIndexed { i, label ->
                FilterChip(
                    register == i,
                    { model.updatePractice { it.copy(register = i) } },
                    label = { Text(label) },
                    modifier = Modifier.padding(end = 8.dp),
                )
            }
        }
        Text(
            "Sounding MIDI pitch is retained in exports. Dense mixes can need corrections.",
            fontSize = 11.sp,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        Row {
            TextButton(
                onClick = {
                    s.project?.let {
                        editing =
                            NoteDraft(
                                NoteEvent(
                                    UUID.randomUUID().toString(),
                                    60,
                                    p.sourceTimeUs,
                                    p.sourceTimeUs + 500_000,
                                ),
                                NoteEditTarget.of(it),
                                true,
                            )
                    }
                },
                enabled = s.project != null && s.progress == null,
            ) {
                Text("Add note")
            }
            TextButton(
                onClick = model::undoNote,
                enabled = s.project?.edits?.isNotEmpty() == true,
            ) {
                Text("Undo correction")
            }
        }
        val visible =
            s.notes
                .filter {
                    it.endUs > p.sourceTimeUs - 500_000 &&
                        when (register) {
                            1 -> it.pitch < 48
                            2 -> it.pitch in 48..71
                            3 -> it.pitch >= 72
                            else -> true
                        }
                }
                .take(28)
        visible.forEach { n ->
            ListItem(
                headlineContent = {
                    Text(
                        NoteNames.name(n.pitch, flats, transpose),
                        color =
                            if (n in active) MaterialTheme.colorScheme.primary
                            else MaterialTheme.colorScheme.onSurface,
                        fontWeight = FontWeight.Bold,
                    )
                },
                supportingContent = {
                    Text(
                        "%.2f–%.2f s  ·  %s"
                            .format(
                                n.startUs / 1e6,
                                n.endUs / 1e6,
                                if (n.provenance == NoteProvenance.CORRECTED) "corrected"
                                else "estimated",
                            ),
                    )
                },
                modifier = Modifier.clickable { model.player.seekTo(n.startUs) },
                trailingContent = {
                    IconButton(
                        onClick = {
                            s.project?.let { editing = NoteDraft(n, NoteEditTarget.of(it), false) }
                        },
                    ) {
                        Icon(Icons.Rounded.Edit, "Correct ${NoteNames.name(n.pitch)}")
                    }
                },
            )
        }
        if (s.notes.isEmpty())
            Text(
                s.status,
                Modifier.padding(vertical = 20.dp),
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        Row {
            OutlinedButton(onClick = onMidi, enabled = s.notes.isNotEmpty()) { Text("Export MIDI") }
            Spacer(Modifier.width(8.dp))
            OutlinedButton(onClick = onCsv, enabled = s.notes.isNotEmpty()) { Text("Export CSV") }
        }
    }
    editing?.let { draft ->
        NoteCorrectionDialog(
            draft.note,
            draft.isNew,
            s.project?.source?.durationUs ?: Long.MAX_VALUE,
            onClose = { editing = null },
            onSave = { event ->
                model.editNote(
                    if (draft.isNew) NoteEdit.Insert(event) else NoteEdit.Replace(event),
                    draft.target,
                )
                editing = null
            },
            onDelete = {
                model.editNote(NoteEdit.Delete(draft.note.id), draft.target)
                editing = null
            },
        )
    }
}

@Composable
private fun NoteCorrectionDialog(
    note: NoteEvent,
    isNew: Boolean,
    durationUs: Long,
    onClose: () -> Unit,
    onSave: (NoteEvent) -> Unit,
    onDelete: () -> Unit,
) {
    var pitch by remember(note.id) { mutableStateOf(note.pitch.toString()) }
    var start by
        remember(note.id) { mutableStateOf("%.3f".format(java.util.Locale.US, note.startUs / 1e6)) }
    var end by
        remember(note.id) { mutableStateOf("%.3f".format(java.util.Locale.US, note.endUs / 1e6)) }
    val parsedPitch = pitch.toIntOrNull()
    val startUs = start.toDoubleOrNull()?.takeIf { it.isFinite() }?.let { (it * 1e6).toLong() }
    val endUs = end.toDoubleOrNull()?.takeIf { it.isFinite() }?.let { (it * 1e6).toLong() }
    val valid =
        parsedPitch != null &&
            parsedPitch in 0..127 &&
            startUs != null &&
            endUs != null &&
            startUs >= 0 &&
            endUs > startUs &&
            endUs <= durationUs
    AlertDialog(
        onDismissRequest = onClose,
        title = { Text(if (isNew) "Add note" else "Correct note") },
        text = {
            Column {
                OutlinedTextField(
                    pitch,
                    { pitch = it },
                    label = { Text("Sounding MIDI pitch (0–127)") },
                )
                OutlinedTextField(start, { start = it }, label = { Text("Start in seconds") })
                OutlinedTextField(end, { end = it }, label = { Text("End in seconds") })
                if (!isNew)
                    TextButton(onClick = onDelete) {
                        Text("Delete note", color = MaterialTheme.colorScheme.error)
                    }
            }
        },
        confirmButton = {
            TextButton(
                onClick = {
                    if (valid)
                        onSave(
                            note.copy(pitch = parsedPitch!!, startUs = startUs!!, endUs = endUs!!),
                        )
                },
                enabled = valid,
            ) {
                Text("Save")
            }
        },
        dismissButton = { TextButton(onClick = onClose) { Text("Cancel") } },
    )
}
