@file:OptIn(androidx.compose.material3.ExperimentalMaterial3Api::class)

package com.blazingsystems.visualizer.ui

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.*
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.gestures.detectDragGesturesAfterLongPress
import androidx.compose.ui.input.pointer.pointerInput
import kotlin.math.abs
import androidx.compose.foundation.lazy.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.*
import androidx.compose.ui.graphics.*
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.*
import androidx.compose.ui.viewinterop.AndroidView
import com.blazingsystems.visualizer.project.*
import com.blazingsystems.visualizer.render.*
import java.io.File
import java.util.UUID

internal fun time(us: Long): String {
    val seconds = us.coerceAtLeast(0) / 1_000_000
    return "%d:%02d".format(seconds / 60, seconds % 60)
}

@Composable
fun AveeShell(model: StudioModel) {
    val s by model.state.collectAsState()
    val p by model.playback.collectAsState()
    val rendered by model.rendered.collectAsState()
    val jobs by model.exports.collectAsState()
    val context = LocalContext.current
    var tab by rememberSaveable { mutableIntStateOf(1) }
    var panel by rememberSaveable { mutableStateOf<String?>(null) }
    val readAudioPermission = if (Build.VERSION.SDK_INT >= 33)
        Manifest.permission.READ_MEDIA_AUDIO else Manifest.permission.READ_EXTERNAL_STORAGE
    val permission = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestPermission(),
    ) { granted -> if (granted) model.refreshLibrary() }
    val refresh = {
        if (context.checkSelfPermission(readAudioPermission) == PackageManager.PERMISSION_GRANTED)
            model.refreshLibrary()
        else permission.launch(readAudioPermission)
    }
    LaunchedEffect(readAudioPermission) { refresh() }
    val audio =
        rememberLauncherForActivityResult(ActivityResultContracts.OpenMultipleDocuments()) { uris ->
            uris.forEach {
                runCatching {
                    context.contentResolver.takePersistableUriPermission(
                        it,
                        Intent.FLAG_GRANT_READ_URI_PERMISSION,
                    )
                }
            }
            model.importTracks(uris)
        }
    val import =
        rememberLauncherForActivityResult(ActivityResultContracts.OpenDocument()) {
            it?.let(model::importPack)
        }
    val savePack =
        rememberLauncherForActivityResult(
            ActivityResultContracts.CreateDocument("application/zip"),
        ) {
            it?.let(model::exportPack)
        }
    val midi =
        rememberLauncherForActivityResult(ActivityResultContracts.CreateDocument("audio/midi")) {
            it?.let { u -> model.exportNotes(u, true) }
        }
    val csv =
        rememberLauncherForActivityResult(ActivityResultContracts.CreateDocument("text/csv")) {
            it?.let { u -> model.exportNotes(u, false) }
        }
    val video =
        rememberLauncherForActivityResult(ActivityResultContracts.CreateDocument("video/mp4")) {
            it?.let(model::finishExport)
        }
    Scaffold(
        containerColor = MaterialTheme.colorScheme.background,
        topBar = {
            Column {
                Row(
                    Modifier.fillMaxWidth()
                        .statusBarsPadding()
                        .padding(horizontal = 20.dp, vertical = 10.dp),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Surface(
                        color = MaterialTheme.colorScheme.primaryContainer,
                        shape = MaterialTheme.shapes.medium,
                    ) {
                        Text(
                            "BV",
                            Modifier.padding(10.dp),
                            fontWeight = FontWeight.Black,
                            color = MaterialTheme.colorScheme.primary,
                        )
                    }
                    Spacer(Modifier.width(12.dp))
                    Text(
                        "Blazing Visualizer",
                        modifier = Modifier.weight(1f),
                        fontWeight = FontWeight.Bold,
                        fontSize = 17.sp,
                        maxLines = 1,
                    )
                    IconButton(onClick = { audio.launch(arrayOf("audio/*")) }) {
                        Icon(Icons.Rounded.LibraryMusic, "Open music")
                    }
                }
                PrimaryTabRow(selectedTabIndex = tab) {
                    listOf("Library", "Visualizer", "Queue").forEachIndexed { i, label ->
                        Tab(selected = tab == i, onClick = { tab = i }, text = { Text(label) })
                    }
                }
            }
        },
        bottomBar = {
            Column(Modifier.navigationBarsPadding().background(MaterialTheme.colorScheme.surface)) {
                s.progress?.let { value ->
                    LinearProgressIndicator(
                        progress = { value },
                        modifier = Modifier.fillMaxWidth(),
                    )
                }
                Row(
                    Modifier.padding(start = 20.dp, end = 8.dp, top = 12.dp),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Column(Modifier.weight(1f)) {
                        Text(
                            s.project?.source?.title ?: "Your music. In full color.",
                            maxLines = 1,
                            overflow = TextOverflow.Ellipsis,
                            fontWeight = FontWeight.SemiBold,
                        )
                        Text(
                            s.project?.source?.artist?.takeIf { it.isNotBlank() } ?: s.scene.name,
                            maxLines = 1,
                            fontSize = 12.sp,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                    }
                    IconButton(
                        onClick = { model.player.previous() },
                        enabled = s.queue.isNotEmpty(),
                    ) {
                        Icon(Icons.Rounded.SkipPrevious, "Previous track")
                    }
                    FilledIconButton(onClick = model::playPause, enabled = s.project != null) {
                        Icon(
                            if (p.isPlaying) Icons.Rounded.Pause else Icons.Rounded.PlayArrow,
                            if (p.isPlaying) "Pause" else "Play",
                        )
                    }
                    IconButton(onClick = { model.player.next() }, enabled = s.queue.isNotEmpty()) {
                        Icon(Icons.Rounded.SkipNext, "Next track")
                    }
                }
                var dragging by remember { mutableStateOf<Float?>(null) }
                val duration =
                    (p.durationUs.takeIf { it > 0 } ?: s.project?.source?.durationUs ?: 1)
                        .coerceAtLeast(1)
                Slider(
                    value =
                        dragging
                            ?: (p.sourceTimeUs.toDouble() / duration).toFloat().coerceIn(0f, 1f),
                    onValueChange = { dragging = it },
                    onValueChangeFinished = {
                        dragging?.let { model.player.seekTo((it * duration).toLong()) }
                        dragging = null
                    },
                    enabled = s.project != null,
                    modifier = Modifier.fillMaxWidth().padding(horizontal = 20.dp).height(28.dp),
                )
                Row(
                    Modifier.fillMaxWidth().padding(start = 22.dp, end = 22.dp, bottom = 10.dp),
                    horizontalArrangement = Arrangement.SpaceBetween,
                ) {
                    Text(
                        time(p.sourceTimeUs),
                        fontSize = 10.sp,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                    Spacer(Modifier.weight(1f))
                    Text(
                        time(duration),
                        fontSize = 10.sp,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                }
            }
        },
    ) { padding ->
        Box(Modifier.fillMaxSize().padding(padding)) {
            when (tab) {
                0,
                2 -> LibraryScreen(
                    s, model, tab == 2,
                    onOpen = { audio.launch(arrayOf("audio/*")) },
                    onRefresh = refresh,
                )
                else -> {
                    AndroidView(
                        factory = {
                            SceneView(it).apply {
                                assets = File(context.filesDir, "assets")
                                update(rendered)
                            }
                        },
                        update = { it.update(rendered) },
                        modifier = Modifier.fillMaxSize(),
                    )
                    Column(
                        Modifier.fillMaxSize().padding(12.dp),
                        verticalArrangement = Arrangement.SpaceBetween,
                    ) {
                        Row(
                            Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                        ) {
                            AssistChip(
                                onClick = { panel = "practice" },
                                label = { Text("Practice") },
                                leadingIcon = {
                                    Icon(Icons.Rounded.Piano, "", Modifier.size(18.dp))
                                },
                            )
                            Surface(
                                color = MaterialTheme.colorScheme.surface.copy(alpha = .7f),
                                shape = MaterialTheme.shapes.large,
                            ) {
                                Row {
                                    IconButton(onClick = { panel = "presets" }) {
                                        Icon(Icons.Rounded.Dashboard, "Choose visualizer")
                                    }
                                    IconButton(onClick = { panel = "editor" }) {
                                        Icon(Icons.Rounded.Edit, "Edit visualizer")
                                    }
                                    IconButton(onClick = { panel = "export" }) {
                                        Icon(Icons.Rounded.IosShare, "Export video")
                                    }
                                }
                            }
                        }
                        if (s.project == null)
                            Surface(
                                color = MaterialTheme.colorScheme.surface.copy(alpha = .8f),
                                shape = MaterialTheme.shapes.large,
                            ) {
                                Column(Modifier.padding(20.dp)) {
                                    Text(
                                        "See what you hear.",
                                        fontSize = 24.sp,
                                        fontWeight = FontWeight.Bold,
                                    )
                                    Text(
                                        "Open your music. Follow its notes. Make it yours.",
                                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                                    )
                                    Spacer(Modifier.height(12.dp))
                                    Button(onClick = { audio.launch(arrayOf("audio/*")) }) {
                                        Icon(Icons.Rounded.Add, "", Modifier.size(18.dp))
                                        Text("Open music")
                                    }
                                }
                            }
                    }
                }
            }
        }
    }
    if (panel != null)
        ModalBottomSheet(
            onDismissRequest = { panel = null },
            containerColor = MaterialTheme.colorScheme.surface,
        ) {
            Column(Modifier.fillMaxWidth().heightIn(max = 620.dp).navigationBarsPadding()) {
                when (panel) {
                    "presets" ->
                        PresetChooserSheet(
                            s.scene,
                            s.savedPresets,
                            onSave = model::savePreset,
                            onSelect = model::setScene,
                            onImport = {
                                import.launch(
                                    arrayOf(
                                        "application/zip",
                                        "application/json",
                                        "text/plain",
                                        "application/octet-stream",
                                        "*/*",
                                    ),
                                )
                            },
                            onExport = { savePack.launch("${s.scene.name}.blazeviz") },
                        )
                    "editor" -> ElementEditorSheet(s.scene, model)
                    "practice" ->
                        PracticeSheet(
                            s,
                            p,
                            model,
                            onMidi = { midi.launch("notes.mid") },
                            onCsv = { csv.launch("notes.csv") },
                        )
                    "export" ->
                        ExportSheet(
                            s,
                            p,
                            jobs,
                            model,
                            onSave = { start, end, settings ->
                                runCatching {
                                        model.prepareExport(start, end, settings)
                                        video.launch("Blazing-${System.currentTimeMillis()}.mp4")
                                    }
                                    .onFailure(model::report)
                            },
                        )
                }
            }
        }
    s.error?.let {
        AlertDialog(
            onDismissRequest = model::dismissError,
            title = { Text("Blazing Visualizer") },
            text = { Text(it) },
            confirmButton = { TextButton(onClick = model::dismissError) { Text("OK") } },
        )
    }
    s.compatibility?.let { result ->
        AlertDialog(
            onDismissRequest = model::cancelImport,
            title = { Text("Avee preset compatibility") },
            text = {
                Column(Modifier.verticalScroll(rememberScrollState()).heightIn(max = 360.dp)) {
                    Text("A preview can be imported with these differences:")
                    result.report.unsupported.forEach { Text("• $it", fontSize = 13.sp) }
                    result.report.missingAssets.forEach {
                        Text("Missing: $it", color = MaterialTheme.colorScheme.error)
                    }
                    Text("The original preset is retained when you import.", fontSize = 12.sp)
                }
            },
            confirmButton = {
                TextButton(onClick = { model.acceptImport(result) }) { Text("Import preview") }
            },
            dismissButton = { TextButton(onClick = model::cancelImport) { Text("Cancel") } },
        )
    }
}

@Composable
private fun LibraryScreen(
    s: StudioState, model: StudioModel, queue: Boolean,
    onOpen: () -> Unit, onRefresh: () -> Unit,
) {
    var search by rememberSaveable { mutableStateOf("") }
    var playlistName by rememberSaveable { mutableStateOf<String?>(null) }
    var sortMenu by remember { mutableStateOf(false) }
    val tracks = if (queue) s.queue else s.library
    Column(Modifier.fillMaxSize().padding(horizontal = 20.dp)) {
        Spacer(Modifier.height(18.dp))
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text(
                if (queue) "Up next" else "Your library",
                fontSize = 26.sp,
                fontWeight = FontWeight.Bold,
                modifier = Modifier.weight(1f),
            )
            if (queue) {
                Box {
                    IconButton(onClick = { sortMenu = true }) {
                        Icon(Icons.Rounded.SortByAlpha, "Sort queue")
                    }
                    DropdownMenu(expanded = sortMenu, onDismissRequest = { sortMenu = false }) {
                        DropdownMenuItem(text = { Text("Title A–Z") }, onClick = {
                            model.sortQueue(false); sortMenu = false
                        })
                        DropdownMenuItem(text = { Text("Artist A–Z") }, onClick = {
                            model.sortQueue(true); sortMenu = false
                        })
                    }
                }
            } else IconButton(onClick = onRefresh) { Icon(Icons.Rounded.Refresh, "Refresh library") }
            FilledTonalIconButton(onClick = onOpen) { Icon(Icons.Rounded.Add, "Import music") }
        }
        OutlinedTextField(
            search,
            { search = it },
            label = { Text("Search tracks") },
            singleLine = true,
            modifier = Modifier.fillMaxWidth().padding(vertical = 12.dp),
        )
        if (queue && s.queue.isNotEmpty())
            TextButton(onClick = { playlistName = "My playlist" }) {
                Icon(Icons.Rounded.PlaylistAdd, "", Modifier.size(18.dp))
                Text("Save queue as playlist")
            }
        LazyColumn(Modifier.weight(1f)) {
            items(
                tracks.filter {
                    it.title.contains(search, true) || it.artist.contains(search, true)
                },
                key = { it.uri },
            ) { source ->
                ListItem(
                    headlineContent = {
                        Text(source.title, maxLines = 1, overflow = TextOverflow.Ellipsis)
                    },
                    supportingContent = { Text(source.artist.ifBlank { "Local audio" }) },
                    leadingContent = {
                        Icon(
                            if (source.uri == s.project?.source?.uri) Icons.Rounded.GraphicEq
                            else Icons.Rounded.MusicNote,
                            null,
                            tint = MaterialTheme.colorScheme.primary,
                        )
                    },
                    trailingContent = {
                        if (queue) {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Icon(Icons.Rounded.DragHandle, "Long press track to reorder")
                                IconButton(onClick = { model.removeQueue(source.uri) }) {
                                    Icon(Icons.Rounded.Close, "Remove from queue")
                                }
                            }
                        } else {
                            Row {
                                IconButton(onClick = { model.addToQueue(source) }) {
                                    Icon(Icons.Rounded.PlaylistAdd, "Add to queue")
                                }
                                IconButton(onClick = { model.playNext(source) }) {
                                    Icon(Icons.Rounded.QueuePlayNext, "Play next")
                                }
                            }
                        }
                    },
                    modifier = Modifier
                        .then(if (queue) Modifier.pointerInput(source.uri) {
                            var drag = 0f
                            val threshold = 52.dp.toPx()
                            detectDragGesturesAfterLongPress(
                                onDragStart = { drag = 0f },
                                onDrag = { change, amount ->
                                    change.consume()
                                    drag += amount.y
                                    if (abs(drag) > threshold) {
                                        model.moveQueue(source.uri, if (drag > 0) 1 else -1)
                                        drag = 0f
                                    }
                                },
                            )
                        } else Modifier)
                        .clickable { model.select(source, true) },
                )
            }
            if (tracks.isEmpty())
                item {
                    Column(Modifier.padding(vertical = 40.dp)) {
                        Text("Your tracks live here.", fontWeight = FontWeight.SemiBold)
                        Text(
                            "Choose audio files from your device to start listening and detecting notes.",
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                        Button(onClick = onOpen, modifier = Modifier.padding(top = 18.dp)) {
                            Text("Open music")
                        }
                    }
                }
            if (!queue && s.playlists.isNotEmpty())
                item {
                    Text(
                        "Playlists",
                        fontWeight = FontWeight.Bold,
                        modifier = Modifier.padding(top = 18.dp),
                    )
                }
            if (!queue)
                items(s.playlists, key = { it.id }) { list ->
                    ListItem(
                        headlineContent = { Text(list.name) },
                        supportingContent = { Text("${list.tracks.size} tracks") },
                        modifier = Modifier.clickable { model.openPlaylist(list) },
                        trailingContent = {
                            IconButton(onClick = { model.deletePlaylist(list.id) }) {
                                Icon(Icons.Rounded.DeleteOutline, "Delete playlist")
                            }
                        },
                    )
                }
        }
    }
    playlistName?.let { name ->
        AlertDialog(
            onDismissRequest = { playlistName = null },
            title = { Text("Save playlist") },
            text = { OutlinedTextField(name, { playlistName = it }, label = { Text("Name") }) },
            confirmButton = {
                TextButton(
                    onClick = {
                        model.savePlaylist(name)
                        playlistName = null
                    },
                ) {
                    Text("Save")
                }
            },
            dismissButton = { TextButton(onClick = { playlistName = null }) { Text("Cancel") } },
        )
    }
}

@Composable
private fun PresetChooserSheet(
    scene: Scene,
    saved: List<Scene>,
    onSave: () -> Unit,
    onSelect: (Scene) -> Unit,
    onImport: () -> Unit,
    onExport: () -> Unit,
) {
    Column(Modifier.verticalScroll(rememberScrollState()).padding(20.dp)) {
        Text("Visualizers", fontSize = 25.sp, fontWeight = FontWeight.Bold)
        Text(
            "Start with a look. Shape every layer.",
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        Spacer(Modifier.height(18.dp))
        (BuiltinScenes.all() + saved)
            .distinctBy { it.id }
            .forEach { preset ->
                Card(
                    onClick = { onSelect(preset) },
                    modifier = Modifier.fillMaxWidth().padding(bottom = 10.dp),
                ) {
                    Row(Modifier.padding(18.dp), verticalAlignment = Alignment.CenterVertically) {
                        Icon(
                            if (preset.layers.any { it.type == ElementType.NOTE_WHEEL })
                                Icons.Rounded.Hub
                            else if (preset.layers.any { it.type == ElementType.PIANO_ROLL })
                                Icons.Rounded.Piano
                            else Icons.Rounded.GraphicEq,
                            null,
                            Modifier.size(38.dp),
                            tint = MaterialTheme.colorScheme.primary,
                        )
                        Spacer(Modifier.width(18.dp))
                        Column {
                            Text(preset.name, fontWeight = FontWeight.SemiBold)
                            Text(
                                "${preset.layers.size} editable layers",
                                fontSize = 12.sp,
                                color = MaterialTheme.colorScheme.onSurfaceVariant,
                            )
                        }
                    }
                }
            }
        TextButton(onClick = onSave) { Text("Save current preset") }
        TextButton(
            onClick = {
                onSelect(scene.copy(id = UUID.randomUUID().toString(), name = scene.name + " copy"))
            },
        ) {
            Icon(Icons.Rounded.ContentCopy, null, Modifier.size(18.dp))
            Text("Duplicate current visualizer")
        }
        Row {
            OutlinedButton(onClick = onImport, modifier = Modifier.weight(1f)) {
                Text("Import preset")
            }
            Spacer(Modifier.width(8.dp))
            Button(onClick = onExport, modifier = Modifier.weight(1f)) { Text("Export pack") }
        }
        Text(
            "BlazeViz packs include the scene and images. Avee JSON/ZIP imports show a compatibility report.",
            fontSize = 12.sp,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            modifier = Modifier.padding(top = 12.dp),
        )
    }
}
