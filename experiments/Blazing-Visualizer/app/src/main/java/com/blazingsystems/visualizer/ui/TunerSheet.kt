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
    var a4 by rememberSaveable { mutableFloatStateOf(440f) }
    var stringIndex by rememberSaveable { mutableIntStateOf(0) }
    val guitar = listOf(
        "E2" to 82.4069, "A2" to 110.0, "D3" to 146.8324,
        "G3" to 195.9977, "B3" to 246.9417, "E4" to 329.6276,
    )
    val (stringName, standardHz) = guitar[stringIndex]
    val targetHz = standardHz * a4 / 440.0
    val centsFromTarget = reading?.let { 1200 * log2(it.frequencyHz / targetHz) }
    Column(Modifier.verticalScroll(rememberScrollState()).padding(20.dp)) {
        Text("Microphone tuner", fontSize = 25.sp, fontWeight = FontWeight.Bold)
        Text("Tune one string at a time. Music playback pauses to avoid feedback.")
        Text(
            reading?.let {
                "${NoteNames.name(it.midi)} · %.1f Hz · %+.1f cents"
                    .format(it.frequencyHz, it.cents)
            } ?: "Listening · play a clear note",
            fontSize = 20.sp, modifier = Modifier.padding(vertical = 16.dp),
        )
        Text(reading?.let { "Pitch confidence: %.0f%%".format(it.confidence * 100) }
            ?: "Silence or noisy input is ignored")
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
                    abs(it) <= 5 -> "In tune (±5 cents)"
                    it < 0 -> "Flat: tighten string (%.0f cents)".format(-it)
                    else -> "Sharp: loosen string (%.0f cents)".format(it)
                }
            } ?: "Pluck $stringName and let it ring",
            fontWeight = FontWeight.Bold,
        )
        Text("A4 calibration: ${a4.toInt()} Hz")
        Slider(
            value = a4, onValueChange = { a4 = it },
            valueRange = 430f..450f,
            onValueChangeFinished = { model.startTuner(a4.toDouble()) },
        )
        Text(
            "YIN uses one detected fundamental at a time; overlapping notes, harmonics " +
                "and background noise can cause octave errors. Recorded songs still use Basic Pitch.",
            fontSize = 12.sp,
        )
        OutlinedButton(onClick = model::stopTuner) { Text("Stop microphone") }
    }
}
