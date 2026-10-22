package com.blazingsystems.visualizer.ui

import androidx.compose.foundation.*
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.*
import com.blazingsystems.visualizer.practice.NoteNames
import kotlin.math.abs
import kotlin.math.log2

@Composable
fun TunerSheet(model: StudioModel) {
    val reading by model.tuner.collectAsState()
    val running by model.tunerRunning.collectAsState()
    val liveReading = reading.takeIf { running }
    var a4 by rememberSaveable { mutableFloatStateOf(440f) }
    var stringIndex by rememberSaveable { mutableIntStateOf(0) }
    val guitar = listOf(
        "E2" to 82.4069, "A2" to 110.0, "D3" to 146.8324,
        "G3" to 195.9977, "B3" to 246.9417, "E4" to 329.6276,
    )
    val (stringName, standardHz) = guitar[stringIndex]
    val targetHz = standardHz * a4 / 440.0
    val centsFromTarget = liveReading?.let { 1200 * log2(it.frequencyHz / targetHz) }
    Column(Modifier.verticalScroll(rememberScrollState()).padding(20.dp)) {
        Text("Microphone tuner", fontSize = 25.sp, fontWeight = FontWeight.Bold)
        Text("Tune one string at a time. Music playback pauses to avoid feedback.")
        Text(
            liveReading?.let {
                "${NoteNames.name(it.midi)} · %.1f Hz · %+.1f cents"
                    .format(it.frequencyHz, it.cents)
            } ?: if (running) "Listening · play a clear note" else "Microphone stopped",
            fontSize = 20.sp, modifier = Modifier.padding(vertical = 16.dp),
        )
        Text(liveReading?.let { "Pitch confidence: %.0f%%".format(it.confidence * 100) }
            ?: if (running) "Silence or noisy input is ignored" else "Resume the microphone to tune")
        Row(Modifier.horizontalScroll(rememberScrollState())) {
            guitar.forEachIndexed { i, pair ->
                FilterChip(
                    selected = i == stringIndex,
                    onClick = { stringIndex = i },
                    label = { Text(pair.first) },
                    modifier = Modifier.padding(end = 6.dp),
                )
            }
        }
        Text("Guitar target: $stringName · %.1f Hz".format(targetHz))
        Text(
            centsFromTarget?.let {
                when {
                    abs(it) > 150 -> "Check the selected string or octave before adjusting"
                    abs(it) <= 5 -> "In tune (±5 cents)"
                    it < 0 -> "Flat: tighten string (%.0f cents)".format(-it)
                    else -> "Sharp: loosen string (%.0f cents)".format(it)
                }
            } ?: if (running) "Pluck $stringName and let it ring" else "Resume to tune $stringName",
            fontWeight = FontWeight.Bold,
        )
        Text("A4 calibration: ${a4.toInt()} Hz")
        Slider(
            value = a4, onValueChange = { a4 = it },
            valueRange = 430f..450f,
            onValueChangeFinished = { if (running) model.startTuner(a4.toDouble()) },
        )
        Text(
            "YIN uses one detected fundamental at a time; overlapping notes, harmonics " +
                "and background noise can cause octave errors. Recorded songs still use Basic Pitch.",
            fontSize = 12.sp,
        )
        OutlinedButton(
            onClick = { if (running) model.stopTuner() else model.startTuner(a4.toDouble()) },
        ) { Text(if (running) "Stop microphone" else "Resume microphone") }
    }
}
