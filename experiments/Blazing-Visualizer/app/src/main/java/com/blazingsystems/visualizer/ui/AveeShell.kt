@file:OptIn(androidx.compose.material3.ExperimentalMaterial3Api::class)

package com.blazingsystems.visualizer.ui

import android.Manifest
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleEventObserver
import androidx.lifecycle.LifecycleOwner
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.*
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.gestures.detectDragGesturesAfterLongPress
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.layout.onSizeChanged
import kotlin.math.abs
import androidx.compose.foundation.lazy.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.*
import androidx.compose.ui.graphics.*
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.*
import androidx.compose.ui.viewinterop.AndroidView
import com.blazingsystems.visualizer.project.*
import com.blazingsystems.visualizer.playback.Playlist
import androidx.media3.common.Player
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
    val micListening by model.tunerRunning.collectAsState()
    val context = LocalContext.current
    val lifecycle = (context as? LifecycleOwner)?.lifecycle
    DisposableEffect(lifecycle) {
        val observer = LifecycleEventObserver { _, event ->
            if (event == Lifecycle.Event.ON_STOP) model.stopTuner()
        }
        lifecycle?.addObserver(observer)
        onDispose { lifecycle?.removeObserver(observer); model.stopTuner() }
    }
    var tab by rememberSaveable { mutableIntStateOf(1) }
    var playbackOptions by remember { mutableStateOf(false) }
    var panel by rememberSaveable { mutableStateOf<String?>(null) }
    var viewportAspect by remember { mutableFloatStateOf(1f) }
    val microphonePermission = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestPermission(),
    ) { granted ->
        if (granted) model.startTuner()
        else model.report(IllegalStateException("Microphone permission denied"))
    }
    val toggleMicrophone = {
        if (micListening) model.stopTuner()
        else if (context.checkSelfPermission(Manifest.permission.RECORD_AUDIO) ==
            PackageManager.PERMISSION_GRANTED) model.startTuner()
        else microphonePermission.launch(Manifest.permission.RECORD_AUDIO)
    }
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
    val accessPreferences = remember { context.getSharedPreferences("music-access", 0) }
    LaunchedEffect(readAudioPermission) {
        if (context.checkSelfPermission(readAudioPermission) == PackageManager.PERMISSION_GRANTED)
            model.refreshLibrary()
        else if (!accessPreferences.getBoolean("requested", false)) {
            accessPreferences.edit().putBoolean("requested", true).apply()
            permission.launch(readAudioPermission)
        }
    }
    DisposableEffect(lifecycle, readAudioPermission) {
        val observer = LifecycleEventObserver { _, event ->
            if (event == Lifecycle.Event.ON_RESUME &&
                context.checkSelfPermission(readAudioPermission) == PackageManager.PERMISSION_GRANTED)
                model.refreshLibrary()
        }
        lifecycle?.addObserver(observer)
        onDispose { lifecycle?.removeObserver(observer) }
    }
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
                        .padding(horizontal = 12.dp, vertical = 4.dp),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
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
                    Box {
                        IconButton(onClick = { playbackOptions = true }) {
                            Icon(Icons.Rounded.MoreVert, "Playback options")
                        }
                        DropdownMenu(expanded = playbackOptions,
                            onDismissRequest = { playbackOptions = false }) {
                            DropdownMenuItem(
                                text = { Text(when (p.repeatMode) {
                                    Player.REPEAT_MODE_ONE -> "Repeat one · tap to turn off"
                                    Player.REPEAT_MODE_ALL -> "Repeat all · tap for one"
                                    else -> "Repeat off · tap for all"
                                }) },
                                leadingIcon = { Icon(if (p.repeatMode == Player.REPEAT_MODE_ONE)
                                    Icons.Rounded.RepeatOne else Icons.Rounded.Repeat, null) },
                                onClick = { model.player.cycleRepeatMode(); playbackOptions = false },
                            )
                            DropdownMenuItem(
                                text = { Text(if (p.shuffle) "Shuffle on · tap to disable"
                                    else "Shuffle off · tap to enable") },
                                leadingIcon = { Icon(Icons.Rounded.Shuffle, null) },
                                onClick = { model.player.toggleShuffle(); playbackOptions = false },
                            )
                        }
                    }
                }
            }
        },
        bottomBar = {
            if (!s.layoutEditing) Column(Modifier.navigationBarsPadding().background(MaterialTheme.colorScheme.surface)) {
                s.progress?.let { value ->
                    LinearProgressIndicator(
                        progress = { value },
                        modifier = Modifier.fillMaxWidth(),
                    )
                }
                Row(
                    Modifier.padding(start = 14.dp, end = 6.dp, top = 4.dp),
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
                    modifier = Modifier.fillMaxWidth().padding(horizontal = 14.dp).height(20.dp),
                )
                Row(
                    Modifier.fillMaxWidth().padding(start = 16.dp, end = 16.dp, bottom = 4.dp),
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
                NavigationBar(containerColor = MaterialTheme.colorScheme.surface, tonalElevation = 0.dp) {
                    listOf(
                        Triple("Library", Icons.Rounded.LibraryMusic, 0),
                        Triple("Visualizer", Icons.Rounded.GraphicEq, 1),
                        Triple("Queue", Icons.Rounded.QueueMusic, 2),
                    ).forEach { (label, symbol, index) ->
                        NavigationBarItem(
                            selected = tab == index,
                            onClick = { tab = index },
                            icon = { Icon(symbol, null) },
                            label = { Text(label) },
                            alwaysShowLabel = true,
                        )
                    }
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
                    BoxWithConstraints(Modifier.fillMaxSize().onSizeChanged { size ->
                        if (size.height > 0) {
                            viewportAspect = size.width.toFloat() / size.height
                            model.setPreviewAspect(viewportAspect)
                        }
                    }, contentAlignment = Alignment.Center) {
                        val exportAspect = (s.project?.export?.width ?: 1).toFloat() /
                            (s.project?.export?.height ?: 1)
                        val frameModifier = if (!s.editingExportLayout) Modifier.fillMaxSize()
                            else if (maxWidth / maxHeight > exportAspect)
                                Modifier.height(maxHeight).aspectRatio(exportAspect)
                            else Modifier.width(maxWidth).aspectRatio(exportAspect)
                        Box(frameModifier) {
                            AndroidView(
                                factory = { SceneView(it).apply {
                                    assets = File(context.filesDir, "assets")
                                    update(rendered)
                                } },
                                update = { it.update(rendered) }, modifier = Modifier.fillMaxSize(),
                            )
                            LayoutOverlay(s.displayScene(), s.layoutEditing, s.editingExportLayout, model) {
                                model.beginLayoutEdit(false, it)
                            }
                        }
                    }
                    if (!s.layoutEditing) Column(
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
                            AssistChip(
                                onClick = toggleMicrophone,
                                label = { Text(if (micListening) "Mic · Live" else "Mic · Off") },
                                leadingIcon = { Icon(Icons.Rounded.Mic, null, Modifier.size(18.dp)) },
                            )
                            Surface(
                                color = MaterialTheme.colorScheme.surface.copy(alpha = .7f),
                                shape = MaterialTheme.shapes.large,
                            ) {
                                Row {
                                    IconButton(onClick = { panel = "presets" }, enabled = s.ready) {
                                        Icon(Icons.Rounded.Dashboard, "Choose visualizer")
                                    }
                                    IconButton(onClick = { panel = "editor" }, enabled = s.ready) {
                                        Icon(Icons.Rounded.Edit, "Edit visualizer")
                                    }
                                    IconButton(onClick = { panel = "export" }, enabled = s.project != null) {
                                        Icon(Icons.Rounded.IosShare, "Export video")
                                    }
                                }
                            }
                        }
                        if (s.project == null && !micListening)
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
                            onSelect = { chosen -> model.setScene(chosen); panel = null },
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
                    "editor" -> ElementEditorSheet(s.scene, model, onArrange = { export ->
                        panel = null
                        model.beginLayoutEdit(export, viewportAspect)
                    })
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
                            onArrange = { panel = null; model.beginLayoutEdit(true, viewportAspect) },
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
    var playlistToDelete by remember { mutableStateOf<Playlist?>(null) }
    var sortMenu by remember { mutableStateOf(false) }
    val tracks = if (queue) s.queue else s.library
    val filteredTracks = tracks.filter {
        it.title.contains(search, true) || it.artist.contains(search, true)
    }
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
            modifier = Modifier.fillMaxWidth().padding(vertical = 12.dp).testTag("track-search"),
        )
        if (queue && s.queue.isNotEmpty())
            TextButton(onClick = { playlistName = "My playlist" }) {
                Icon(Icons.Rounded.PlaylistAdd, "", Modifier.size(18.dp))
                Text("Save queue as playlist")
            }
        LazyColumn(Modifier.weight(1f).testTag("library-list")) {
            // Playlists must remain reachable on a phone even with hundreds
            // of local tracks; previously they were rendered *after* all
            // tracks and their semantics were absent until deep scrolling.
            if (!queue && s.playlists.isNotEmpty())
                item {
                    Text(
                        "Playlists",
                        fontWeight = FontWeight.Bold,
                        modifier = Modifier.padding(top = 8.dp, bottom = 6.dp),
                    )
                }
            if (!queue)
                items(s.playlists, key = { it.id }) { list ->
                    ListItem(
                        headlineContent = { Text(list.name) },
                        supportingContent = { Text("${list.tracks.size} tracks") },
                        modifier = Modifier.clickable { model.openPlaylist(list) },
                        trailingContent = {
                            IconButton(onClick = { playlistToDelete = list }) {
                                Icon(Icons.Rounded.DeleteOutline, "Delete playlist")
                            }
                        },
                    )
                }
            items(filteredTracks, key = { it.uri }) { source ->
                ListItem(
                    headlineContent = {
                        Text(source.title, maxLines = 1, overflow = TextOverflow.Ellipsis)
                    },
                    supportingContent = {
                        Column {
                            Text(source.artist.ifBlank { "Local audio" })
                            s.preparations[source.uri]?.let { Text(it, fontSize = 11.sp,
                                maxLines = 1, overflow = TextOverflow.Ellipsis) }
                        }
                    },
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
                        .clickable { model.select(source, true, fromLibrary = !queue) },
                )
            }
            if (tracks.isNotEmpty() && filteredTracks.isEmpty())
                item {
                    Text(
                        "No tracks match \"$search\". Clear the search to see all tracks.",
                        modifier = Modifier.padding(vertical = 24.dp),
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
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
         }
    }
    playlistToDelete?.let { target ->
        AlertDialog(
            onDismissRequest = { playlistToDelete = null },
            title = { Text("Delete playlist?") },
            text = { Text("Delete \"${target.name}\"? This does not delete your music files.") },
            confirmButton = {
                TextButton(onClick = {
                    model.deletePlaylist(target.id)
                    playlistToDelete = null
                }) { Text("Delete playlist") }
            },
            dismissButton = {
                TextButton(onClick = { playlistToDelete = null }) { Text("Cancel") }
            },
        )
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
