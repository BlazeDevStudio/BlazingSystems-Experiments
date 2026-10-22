package com.blazingsystems.visualizer.ui

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.gestures.detectDragGestures
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.*
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.drawscope.rotate
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.unit.dp
import com.blazingsystems.visualizer.project.*
import com.blazingsystems.visualizer.render.SceneLayouts
import kotlin.math.*

/** Long press enters arrangement; a selected layer has a drag handle for resizing. */
@Composable
fun LayoutOverlay(scene: Scene, editing: Boolean, export: Boolean, model: StudioModel,
    onBegin: (Float) -> Unit) {
    var selected by remember { mutableStateOf<String?>(null) }
    val latest by rememberUpdatedState(scene)
    LaunchedEffect(editing) {
        if (editing && scene.layers.none { it.id == selected }) selected = scene.layers.lastOrNull {
            it.visible && it.type !in setOf(ElementType.BLUR, ElementType.PARTICLES)
        }?.id
    }
    Box(Modifier.fillMaxSize()) {
        Canvas(Modifier.fillMaxSize().testTag("visualizer-canvas").pointerInput(editing, export) {
            if (!editing) detectTapGestures(onLongPress = { point ->
                selected = SceneLayouts.hitTest(latest, point.x / size.width,
                    point.y / size.height, size.width.toFloat() / size.height)
                onBegin(size.width.toFloat() / size.height)
            }) else {
                var resizing = false
                detectDragGestures(
                    onDragStart = { point ->
                        val t = latest.layers.firstOrNull { it.id == selected }?.transform
                        val handle = t?.let {
                            val angle = Math.toRadians(it.rotation.toDouble())
                            val dx = it.width * size.width / 2
                            val dy = it.height * size.height / 2
                            Offset(it.x * size.width + (cos(angle)*dx - sin(angle)*dy).toFloat(),
                                it.y * size.height + (sin(angle)*dx + cos(angle)*dy).toFloat())
                        }
                        resizing = handle != null && (point - handle).getDistance() <= 36.dp.toPx()
                        if (!resizing) selected = SceneLayouts.hitTest(latest,
                            point.x / size.width, point.y / size.height,
                            size.width.toFloat() / size.height)
                    },
                    onDrag = { change, delta ->
                        change.consume()
                        latest.layers.firstOrNull { it.id == selected }?.let { layer ->
                            val t = layer.transform
                            val angle = Math.toRadians(t.rotation.toDouble())
                            val next = if (resizing) SceneLayouts.resize(t,
                                (2 * (cos(angle)*delta.x + sin(angle)*delta.y) / size.width).toFloat(),
                                (2 * (-sin(angle)*delta.x + cos(angle)*delta.y) / size.height).toFloat())
                            else SceneLayouts.move(t, delta.x / size.width, delta.y / size.height)
                            model.setLayoutTransform(layer.id, next)
                        }
                    },
                )
            }
        }.pointerInput(editing) {
            if (editing) detectTapGestures(onTap = { point ->
                selected = SceneLayouts.hitTest(latest, point.x / size.width,
                    point.y / size.height, size.width.toFloat() / size.height)
            })
        }) {
            if (editing) latest.layers.firstOrNull { it.id == selected }?.transform?.let { t ->
                val center = Offset(t.x * size.width, t.y * size.height)
                val width = t.width * size.width
                val height = t.height * size.height
                rotate(t.rotation, center) {
                    drawRect(Color(0xFFC5B4FF), center - Offset(width/2, height/2),
                        Size(width, height), style = Stroke(2.dp.toPx()))
                    drawCircle(Color.White, 9.dp.toPx(), center + Offset(width/2, height/2))
                }
            }
        }
        if (editing) Column(Modifier.align(Alignment.BottomCenter).fillMaxWidth()
            .background(MaterialTheme.colorScheme.surface.copy(alpha = .94f)).padding(10.dp)) {
            Text(if (export) "Arrange export" else "Arrange preview")
            Text("Drag a layer to move it. Drag its white corner to resize.", style = MaterialTheme.typography.bodySmall)
            Row(Modifier.horizontalScroll(rememberScrollState())) {
                scene.layers.filter { it.visible }.forEach { layer ->
                    FilterChip(selected == layer.id, { selected = layer.id },
                        label = { Text(layer.name) }, modifier = Modifier.padding(end = 6.dp))
                }
            }
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                TextButton(onClick = { selected?.let(model::resetLayoutTransform) },
                    enabled = selected != null) { Text("Reset layer") }
                Button(onClick = model::finishLayoutEdit) { Text("Done") }
            }
        }
    }
}
