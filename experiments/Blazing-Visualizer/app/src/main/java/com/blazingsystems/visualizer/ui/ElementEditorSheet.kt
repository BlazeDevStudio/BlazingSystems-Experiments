package com.blazingsystems.visualizer.ui

import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.*
import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.*
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.*
import com.blazingsystems.visualizer.project.*
import com.blazingsystems.visualizer.practice.NoteNames
import com.blazingsystems.visualizer.render.MathVisualMode
import com.blazingsystems.visualizer.render.CurveMotion
import kotlin.math.pow
import kotlinx.serialization.json.*

@Composable
fun ElementEditorSheet(scene: Scene, model: StudioModel, onArrange: (Boolean) -> Unit = {}) {
    var selected by rememberSaveable { mutableStateOf<String?>(null) }
    var add by remember { mutableStateOf(false) }
    var imageLayer by remember { mutableStateOf<Layer?>(null) }
    val picker =
        rememberLauncherForActivityResult(ActivityResultContracts.OpenDocument()) { uri ->
            if (uri != null) imageLayer?.let { model.attachImage(it, uri) }
        }
    Column(Modifier.verticalScroll(rememberScrollState()).padding(20.dp)) {
        Text("Composition", fontSize = 25.sp, fontWeight = FontWeight.Bold)
        OutlinedTextField(
            scene.name,
            { model.editScene(scene.copy(name = it.take(200))) },
            label = { Text("Visualizer name") },
            modifier = Modifier.fillMaxWidth(),
        )
        Spacer(Modifier.height(10.dp))
        Row {
            OutlinedButton(onClick = { onArrange(false) }, modifier = Modifier.weight(1f)) { Text("Arrange preview") }
            Spacer(Modifier.width(8.dp))
            OutlinedButton(onClick = { onArrange(true) }, modifier = Modifier.weight(1f)) { Text("Arrange export") }
        }
        Row(verticalAlignment = Alignment.CenterVertically) {
            Checkbox(scene.showEquations, { model.editScene(scene.copy(showEquations = it)) })
            Text("Include math equations in graph visuals")
        }
        ColorField("Background color", scene.backgroundColor) {
            model.editScene(scene.copy(backgroundColor = it))
        }
        PropertySlider("Global animation intensity", scene.animationIntensity, 0f..2f) {
            model.editScene(scene.copy(animationIntensity = it))
        }
        PropertySlider("Independent piano effects", scene.pianoIntensity, 0f..2f) {
            model.editScene(scene.copy(pianoIntensity = it))
        }
        var paletteInput by remember(scene.id) {
            mutableStateOf(scene.paletteColor ?: "#FF9C83FF")
        }
        Row(verticalAlignment = Alignment.CenterVertically) {
            Switch(
                scene.paletteColor != null,
                { enabled ->
                    model.editScene(scene.copy(paletteColor = if (enabled)
                        paletteInput.takeIf { validColor(it) } ?: "#FF9C83FF" else null))
                },
            )
            Text("Global palette (layer colors can override)", Modifier.padding(start = 10.dp))
        }
        if (scene.paletteColor != null) OutlinedTextField(
            paletteInput,
            { text ->
                paletteInput = text
                if (text.matches(Regex("#[0-9a-fA-F]{6}([0-9a-fA-F]{2})?")))
                    model.editScene(scene.copy(paletteColor = text))
            },
            label = { Text("Global palette #RRGGBB") },
            singleLine = true,
        )
        scene.layers.forEachIndexed { i, layer ->
            Card(Modifier.fillMaxWidth().padding(vertical = 4.dp)) {
                Column(Modifier.padding(12.dp)) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Checkbox(layer.visible, { model.setLayer(layer.copy(visible = it)) })
                        TextButton(
                            onClick = { selected = if (selected == layer.id) null else layer.id },
                            modifier = Modifier.weight(1f),
                        ) {
                            Text(layer.name)
                        }
                        IconButton(onClick = { model.moveLayer(layer.id, -1) }, enabled = i > 0) {
                            Icon(Icons.Rounded.ArrowUpward, "Move layer up")
                        }
                        IconButton(onClick = { model.removeLayer(layer.id) }) {
                            Icon(Icons.Rounded.DeleteOutline, "Delete layer")
                        }
                    }
                    if (selected == layer.id) {
                        fun prop(key: String, value: String) =
                            model.setLayer(
                                layer.copy(
                                    properties =
                                        JsonObject(
                                            layer.properties + (key to JsonPrimitive(value)),
                                        ),
                                ),
                            )
                        OutlinedTextField(
                            layer.name,
                            { model.setLayer(layer.copy(name = it.take(200))) },
                            label = { Text("Layer name") },
                            modifier = Modifier.fillMaxWidth(),
                        )
                        if (layer.type == ElementType.TEXT)
                            OutlinedTextField(
                                layer.properties["text"]?.jsonPrimitive?.content ?: "BLAZING",
                                { prop("text", it.take(500)) },
                                label = { Text("Text") },
                                modifier = Modifier.fillMaxWidth(),
                            )
                        if (layer.type == ElementType.NOTE_WHEEL)
                            OutlinedTextField(
                                layer.properties["emptyText"]?.jsonPrimitive?.content
                                    ?: "FOLLOW THE NOTES",
                                { prop("emptyText", it.take(120)) },
                                label = { Text("Note wheel · text when no notes are detected") },
                                modifier = Modifier.fillMaxWidth(),
                            )
                        if (layer.type == ElementType.IMAGE)
                            OutlinedButton(
                                onClick = {
                                    imageLayer = layer
                                    picker.launch(arrayOf("image/*"))
                                },
                            ) {
                                Text("Choose image")
                            }
                        var color by
                            remember(layer.id) {
                                mutableStateOf(
                                    layer.properties["color"]?.jsonPrimitive?.content
                                        ?: "#FF9C83FF",
                                )
                            }
                        OutlinedTextField(
                            color,
                            {
                                color = it
                                if (it.matches(Regex("#[0-9a-fA-F]{6}([0-9a-fA-F]{2})?")))
                                    prop("color", it)
                            },
                            label = { Text("Color #RRGGBB or #AARRGGBB") },
                            singleLine = true,
                            modifier = Modifier.fillMaxWidth(),
                        )
                        if (layer.type == ElementType.NOTE_WHEEL ||
                            layer.type == ElementType.PIANO_ROLL ||
                            layer.type == ElementType.MATH_CURVE ||
                            layer.type == ElementType.SPECTRUM || layer.bindings.isNotEmpty()) {
                            Text("Detected note band (pitch, not volume)")
                            Row(Modifier.horizontalScroll(rememberScrollState())) {
                                NoteBand.entries.forEach { band ->
                                    FilterChip(
                                        selected = layer.noteRouting.band == band,
                                        onClick = {
                                            model.setLayer(layer.copy(
                                                noteRouting = NoteRouting(band),
                                            ))
                                        },
                                        label = { Text(band.name.lowercase()) },
                                        modifier = Modifier.padding(end = 6.dp),
                                    )
                                }
                            }
                            val bounds = layer.noteRouting.bounds()
                            fun pitchLabel(pitch: Int): String {
                                val hz = 440.0 * 2.0.pow((pitch - 69) / 12.0)
                                return "${NoteNames.name(pitch)} (${hz.toInt()} Hz)"
                            }
                            PropertySlider(
                                "Low MIDI ${bounds.first}: ${pitchLabel(bounds.first)}",
                                bounds.first.toFloat(), 0f..127f,
                            ) {
                                model.setLayer(layer.copy(noteRouting = layer.noteRouting.copy(
                                    lowMidi = it.toInt().coerceAtMost(bounds.last),
                                )))
                            }
                            PropertySlider(
                                "High MIDI ${bounds.last}: ${pitchLabel(bounds.last)}",
                                bounds.last.toFloat(), 0f..127f,
                            ) {
                                model.setLayer(layer.copy(noteRouting = layer.noteRouting.copy(
                                    highMidi = it.toInt().coerceAtLeast(bounds.first),
                                )))
                            }
                        }
                        if (layer.type == ElementType.MATH_CURVE) {
                            Text("Graph view shows up to 12 simultaneous pitches; Practice keeps the full detection.",
                                style = MaterialTheme.typography.bodySmall)
                            Row(Modifier.horizontalScroll(rememberScrollState())) {
                            MathVisualMode.entries.forEach { mode ->
                                FilterChip(
                                    (layer.properties["mode"]?.jsonPrimitive?.content ?: "LISSAJOUS") == mode.name,
                                    { prop("mode", mode.name) }, label = { Text(mode.name.lowercase()) },
                                    modifier = Modifier.padding(end = 6.dp),
                                )
                            }
                            }
                            Row(Modifier.horizontalScroll(rememberScrollState())) {
                                CurveMotion.entries.forEach { motion ->
                                    FilterChip((layer.properties["motion"]?.jsonPrimitive?.content ?: "OUTLINE")==motion.name,
                                        { prop("motion",motion.name) },label={ Text(motion.name.lowercase()) },modifier=Modifier.padding(end=6.dp))
                                }
                            }
                            PropertySlider("Motion speed",layer.properties["speed"]?.jsonPrimitive?.floatOrNull ?: 1f,0f..4f) { prop("speed",it.toString()) }
                            PropertySlider("Trail / reveal seconds",layer.properties["trailSeconds"]?.jsonPrimitive?.floatOrNull ?: 1.5f,.2f..8f) { prop("trailSeconds",it.toString()) }
                            PropertySlider("Spatial camera motion",layer.properties["cameraAmount"]?.jsonPrimitive?.floatOrNull ?: 1f,0f..2f) { prop("cameraAmount",it.toString()) }
                            if(layer.properties["mode"]?.jsonPrimitive?.content=="RHYTHM")
                                OutlinedTextField(layer.properties["rhythmDivisions"]?.jsonPrimitive?.content ?: "2,3,4,5,6,7",
                                    { prop("rhythmDivisions",it.take(64)) },label={ Text("Visual subdivisions · e.g. 4,5,6") })
                        }
                        if (layer.type == ElementType.PIANO_ROLL) {
                            val baseColor = layer.properties["color"]?.jsonPrimitive?.content ?: scene.paletteColor ?: "#FF9C83FF"
                            listOf("whiteKeyColor" to "#FFDBDCE8", "blackKeyColor" to "#FF171723",
                                "activeKeyColor" to baseColor, "glowColor" to baseColor,
                                "sparkColor" to "#FFFFFFFF").forEach { (key, fallback) ->
                                ColorField(key.removeSuffix("Color").replace(Regex("([A-Z])"), " $1") + " color",
                                    layer.properties[key]?.jsonPrimitive?.content ?: fallback) { prop(key, it) }
                            }
                        }
                        val t = layer.transform
                        PropertySlider("Position X", t.x, -.5f..1.5f) {
                            model.setLayer(layer.copy(transform = t.copy(x = it)))
                        }
                        PropertySlider("Position Y", t.y, -.5f..1.5f) {
                            model.setLayer(layer.copy(transform = t.copy(y = it)))
                        }
                        PropertySlider("Width", t.width, .05f..2f) {
                            model.setLayer(layer.copy(transform = t.copy(width = it)))
                        }
                        PropertySlider("Height", t.height, .05f..2f) {
                            model.setLayer(layer.copy(transform = t.copy(height = it)))
                        }
                        PropertySlider("Rotation", t.rotation, -180f..180f) {
                            model.setLayer(layer.copy(transform = t.copy(rotation = it)))
                        }
                        if (layer.type == ElementType.SPECTRUM)
                            Row {
                                listOf("circle", "bars").forEach { path ->
                                    FilterChip(
                                        layer.properties["path"]?.jsonPrimitive?.content == path,
                                        { prop("path", path) },
                                        label = { Text(path) },
                                        modifier = Modifier.padding(end = 8.dp),
                                    )
                                }
                            }
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Switch(
                                layer.bindings.isNotEmpty(),
                                {
                                    model.setLayer(
                                        layer.copy(
                                            bindings =
                                                if (it)
                                                    listOf(Binding("scale", BindingSource.RMS, 1f))
                                                else emptyList(),
                                        ),
                                    )
                                },
                            )
                            Text("Pulse scale with music", Modifier.padding(start = 10.dp))
                        }
                        layer.bindings.firstOrNull()?.let { binding ->
                            Row(Modifier.horizontalScroll(rememberScrollState())) {
                                BindingSource.entries.forEach { source ->
                                    FilterChip(
                                        binding.source == source,
                                        {
                                            model.setLayer(
                                                layer.copy(
                                                    bindings =
                                                        listOf(binding.copy(source = source)),
                                                ),
                                            )
                                        },
                                        label = { Text(source.name.lowercase().replace('_', ' ')) },
                                        modifier = Modifier.padding(end = 8.dp),
                                    )
                                }
                            }
                            PropertySlider("Response", binding.amount, 0f..4f) {
                                model.setLayer(
                                    layer.copy(bindings = listOf(binding.copy(amount = it))),
                                )
                            }
                        }
                    }
                }
            }
        }
        Button(onClick = { add = true }, modifier = Modifier.fillMaxWidth().padding(top = 12.dp)) {
            Icon(Icons.Rounded.Add, null)
            Text("Add element")
        }
        Text(
            "Layers draw from top to bottom. Note layers use the track's detected notes.",
            fontSize = 12.sp,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            modifier = Modifier.padding(top = 12.dp),
        )
    }
    if (add)
        AlertDialog(
            onDismissRequest = { add = false },
            title = { Text("Add element") },
            text = {
                Column(Modifier.verticalScroll(rememberScrollState())) {
                    ElementType.entries.forEach { type ->
                        TextButton(
                            onClick = {
                                model.addLayer(type)
                                add = false
                            },
                        ) {
                            Text(type.name.lowercase().replace('_', ' '))
                        }
                    }
                }
            },
            confirmButton = { TextButton(onClick = { add = false }) { Text("Close") } },
        )
}

private fun validColor(text: String) = text.matches(Regex("#[0-9a-fA-F]{6}([0-9a-fA-F]{2})?"))

@Composable
private fun ColorField(label: String, value: String, onChange: (String) -> Unit) {
    var input by remember(label, value) { mutableStateOf(value) }
    OutlinedTextField(input, { input = it; if (validColor(it)) onChange(it) },
        label = { Text("$label · #RRGGBB or #AARRGGBB") }, singleLine = true,
        modifier = Modifier.fillMaxWidth())
}

@Composable
private fun PropertySlider(
    label: String,
    value: Float,
    range: ClosedFloatingPointRange<Float>,
    onChange: (Float) -> Unit,
) {
    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
        Text(label, fontSize = 12.sp)
        Text(
            "%.2f".format(value),
            fontSize = 12.sp,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
    }
    Slider(value.coerceIn(range), onChange, valueRange = range)
}
