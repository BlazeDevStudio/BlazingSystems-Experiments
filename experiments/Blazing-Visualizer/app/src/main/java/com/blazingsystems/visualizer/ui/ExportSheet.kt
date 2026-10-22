package com.blazingsystems.visualizer.ui

import android.content.Intent
import android.net.Uri
import androidx.compose.foundation.*
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.*
import androidx.compose.ui.viewinterop.AndroidView
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.*
import com.blazingsystems.visualizer.export.*
import com.blazingsystems.visualizer.playback.PlaybackState
import com.blazingsystems.visualizer.project.*
import com.blazingsystems.visualizer.render.*
import java.io.File

@Composable
fun ExportSheet(
    s: StudioState,
    p: PlaybackState,
    jobs: List<ExportJob>,
    model: StudioModel,
    onArrange: () -> Unit = {},
    onSave: (Long, Long, ExportSettings) -> Unit,
) {
    val previous = s.project?.export ?: ExportSettings()
    var size by rememberSaveable(s.project?.id) { mutableIntStateOf(minOf(previous.width, previous.height)) }
    var aspect by rememberSaveable(s.project?.id) { mutableIntStateOf(
        if (previous.width == previous.height) 2 else if (previous.width < previous.height) 1 else 0) }
    var start by rememberSaveable(s.project?.id) { mutableStateOf("0") }
    var end by
        rememberSaveable(s.project?.id, s.project?.source?.durationUs) {
            mutableStateOf(
                "%.3f".format(java.util.Locale.US, (s.project?.source?.durationUs ?: 0) / 1e6),
            )
        }
    val context = LocalContext.current
    val a = start.toDoubleOrNull()?.takeIf { it.isFinite() }?.let { (it * 1e6).toLong() }
    val b = end.toDoubleOrNull()?.takeIf { it.isFinite() }?.let { (it * 1e6).toLong() }
    Column(Modifier.verticalScroll(rememberScrollState()).padding(20.dp)) {
        Text("Export video", fontSize = 25.sp, fontWeight = FontWeight.Bold)
        Text("MP4 · H.264 + AAC · 30 fps", color = MaterialTheme.colorScheme.onSurfaceVariant)
        Spacer(Modifier.height(14.dp))
        Row {
            listOf(720, 1080).forEach { value ->
                FilterChip(
                    size == value,
                    { size = value },
                    label = { Text("${value}p") },
                    modifier = Modifier.padding(end = 8.dp),
                )
            }
        }
        Row(Modifier.horizontalScroll(rememberScrollState())) {
            listOf("Landscape 16:9", "Portrait 9:16", "Square 1:1").forEachIndexed { i, label ->
                FilterChip(
                    aspect == i,
                    { aspect = i },
                    label = { Text(label) },
                    modifier = Modifier.padding(end = 8.dp),
                )
            }
        }
        val longEdge = if (size == 720) 1280 else 1920
        val width =
            when (aspect) {
                0 -> longEdge
                else -> size
            }
        val height =
            when (aspect) {
                1 -> longEdge
                else -> size
            }
        val settings = ExportSettings(width, height,
            videoBitrate = if (size == 1080) 12_000_000 else 8_000_000)
        LaunchedEffect(settings, s.project?.id) { model.setExportSettings(settings) }
        Row(Modifier.horizontalScroll(rememberScrollState())) {
            FilterChip(s.project?.exportLayout != ExportLayoutMode.SEPARATE,
                { model.setExportLayout(ExportLayoutMode.FOLLOW_FIT) }, label = { Text("Follow preview · auto fit") })
            Spacer(Modifier.width(8.dp))
            FilterChip(s.project?.exportLayout == ExportLayoutMode.SEPARATE,
                { model.setExportLayout(ExportLayoutMode.SEPARATE) }, label = { Text("Separate arrangement") })
        }
        if (s.project?.exportLayout == ExportLayoutMode.SEPARATE)
            TextButton(onClick = onArrange) { Text("Arrange export on canvas") }
        Text("Frame filling", fontWeight = FontWeight.SemiBold)
        Row(Modifier.horizontalScroll(rememberScrollState())) {
            listOf(
                ExportFrameMode.COVER to "Fill screen · crop edges",
                ExportFrameMode.CONTAIN to "Fit entire scene",
                ExportFrameMode.STRETCH to "Stretch to frame",
            ).forEach { (mode, label) ->
                FilterChip(
                    selected = (s.project?.exportFrameMode ?: ExportFrameMode.COVER) == mode,
                    onClick = { model.setExportFrameMode(mode) },
                    label = { Text(label) },
                    modifier = Modifier.padding(end = 8.dp),
                )
            }
        }
        Text("Fill avoids empty borders; Fit retains every edge; Stretch can distort circles.",
            fontSize = 11.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
        Text(
            "Output: $width × $height pixels",
            fontSize = 12.sp,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        val frame by model.rendered.collectAsState()
        val outputScene = s.project?.let { SceneLayouts.forExport(it.copy(scene = s.scene), settings) } ?: s.scene
        val outputFrame = SceneEvaluator.evaluate(outputScene, frame.features, frame.sourceTimeUs)
        Text("Composition preview at selected output shape", fontSize = 12.sp)
        Box(
            Modifier.fillMaxWidth().padding(vertical = 8.dp),
            contentAlignment = Alignment.Center,
        ) {
            AndroidView(
                factory = { context ->
                    com.blazingsystems.visualizer.render.SceneView(context).apply {
                        assets = File(context.filesDir, "assets")
                        update(outputFrame)
                    }
                },
                update = { it.update(outputFrame) },
                modifier = Modifier.width(if (aspect == 1) 130.dp else 220.dp)
                    .aspectRatio(width.toFloat() / height),
            )
        }
        Row(Modifier.padding(vertical = 12.dp)) {
            OutlinedTextField(
                start,
                { start = it },
                label = { Text("Start · seconds") },
                singleLine = true,
                modifier = Modifier.weight(1f),
            )
            Spacer(Modifier.width(8.dp))
            OutlinedTextField(
                end,
                { end = it },
                label = { Text("End · seconds") },
                singleLine = true,
                modifier = Modifier.weight(1f),
            )
        }
        Text(
            "Practice speed and display transposition do not change the exported music.",
            fontSize = 12.sp,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        Button(
            onClick = {
                if (a != null && b != null)
                    onSave(
                        a,
                        b,
                        settings,
                    )
            },
            enabled =
                s.project?.source?.contentSha256 != null &&
                    s.progress == null &&
                    a != null &&
                    b != null &&
                    a >= 0 &&
                    b > a &&
                    b <= s.project!!.source.durationUs,
            modifier = Modifier.fillMaxWidth().padding(vertical = 16.dp),
        ) {
            Text("Save MP4")
        }
        jobs.asReversed().take(10).forEach { job ->
            Card(Modifier.fillMaxWidth().padding(bottom = 8.dp)) {
                Column(Modifier.padding(14.dp)) {
                    Text(
                        job.request.project.source.title,
                        maxLines = 1,
                        fontWeight = FontWeight.SemiBold,
                    )
                    Text(
                        job.message
                            ?: job.status.name.lowercase().replaceFirstChar { it.uppercase() },
                        fontSize = 12.sp,
                        color =
                            if (job.status == ExportStatus.FAILED) MaterialTheme.colorScheme.error
                            else MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                    if (job.status in setOf(ExportStatus.QUEUED, ExportStatus.RUNNING)) {
                        LinearProgressIndicator(
                            progress = { job.progress },
                            modifier = Modifier.fillMaxWidth().padding(top = 12.dp),
                        )
                        TextButton(onClick = { ExportHub.cancel(context, job.id) }) {
                            Text("Cancel export")
                        }
                    }
                    if (job.status == ExportStatus.COMPLETED)
                        Row {
                            TextButton(
                                onClick = {
                                    runCatching {
                                            context.startActivity(
                                                Intent(Intent.ACTION_VIEW)
                                                    .setDataAndType(
                                                        Uri.parse(job.request.outputUri),
                                                        "video/mp4",
                                                    )
                                                    .addFlags(
                                                        Intent.FLAG_GRANT_READ_URI_PERMISSION,
                                                    ),
                                            )
                                        }
                                        .onFailure(model::report)
                                },
                            ) {
                                Text("Open")
                            }
                            TextButton(
                                onClick = {
                                    runCatching {
                                            context.startActivity(
                                                Intent.createChooser(
                                                    Intent(Intent.ACTION_SEND)
                                                        .setType("video/mp4")
                                                        .putExtra(
                                                            Intent.EXTRA_STREAM,
                                                            Uri.parse(job.request.outputUri),
                                                        )
                                                        .addFlags(
                                                            Intent.FLAG_GRANT_READ_URI_PERMISSION,
                                                        ),
                                                    "Share video",
                                                ),
                                            )
                                        }
                                        .onFailure(model::report)
                                },
                            ) {
                                Text("Share")
                            }
                        }
                }
            }
        }
    }
}
