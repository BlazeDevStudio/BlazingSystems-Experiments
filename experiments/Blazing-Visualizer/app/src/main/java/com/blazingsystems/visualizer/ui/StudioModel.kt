package com.blazingsystems.visualizer.ui

import android.app.Application
import android.net.Uri
import androidx.lifecycle.*
import com.blazingsystems.visualizer.analysis.*
import com.blazingsystems.visualizer.audio.*
import com.blazingsystems.visualizer.export.*
import com.blazingsystems.visualizer.packs.*
import com.blazingsystems.visualizer.playback.*
import com.blazingsystems.visualizer.practice.*
import com.blazingsystems.visualizer.project.*
import com.blazingsystems.visualizer.render.*
import java.io.File
import java.util.UUID
import kotlinx.coroutines.*
import kotlinx.coroutines.channels.Channel
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import kotlinx.serialization.decodeFromString
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.*

data class StudioState(
    val project: Project? = null,
    val scene: Scene = BuiltinScenes.defaultSpectrum(),
    val queue: List<SourceRef> = emptyList(),
    val library: List<SourceRef> = emptyList(),
    val savedPresets: List<Scene> = emptyList(),
    val playlists: List<Playlist> = emptyList(),
    val notes: List<NoteEvent> = emptyList(),
    val status: String = "Open a track to begin",
    val progress: Float? = null,
    val error: String? = null,
    val compatibility: ImportResult? = null,
)

class StudioModel(app: Application) : AndroidViewModel(app) {
    private val library = LibraryRepository(app)
    private val projects = ProjectStore(File(app.filesDir, "projects"))
    private val draft = File(app.filesDir, "scene-draft.json")
    val player = PlayerController(app)
    val playback = player.state
    private val mutable = MutableStateFlow(StudioState())
    val state: StateFlow<StudioState> = mutable
    val rendered =
        MutableStateFlow(SceneEvaluator.evaluate(mutable.value.scene, FeatureFrame(0), 0))
    val exports = ExportHub.jobs
    private var trackJob: Job? = null
    private val coordinator = TrackCoordinator()
    private val initialized = CompletableDeferred<Unit>()
    private var audioFeatures: AudioFeatures? = null
    private var rawNotes: List<NoteEvent> = emptyList()
    private val saves = Channel<StudioState>(Channel.UNLIMITED)
    private val audio = AudioRepository(app)
    private val analysisLock = Mutex()
    private var preanalysisJob: Job? = null
    private val presets = PresetStore(File(app.filesDir, "presets.json"))
    var pendingExport: ExportRequest? = null

    init {
        ExportHub.initialize(app)
        viewModelScope.launch(Dispatchers.IO) {
            for (s in saves) {
                try {
                    s.project?.let(projects::save)
                    atomicWrite(draft, Json.encodeToString(s.scene).toByteArray())
                    presets.save(s.savedPresets)
                    library.saveLibrary(s.library)
                    library.saveQueue(s.queue)
                    library.savePlaylists(s.playlists)
                } catch (failure: Exception) {
                    mutable.update {
                        it.copy(error = "Could not save changes: ${failure.localizedMessage}")
                    }
                }
            }
        }
        viewModelScope.launch {
            val saved =
                withContext(Dispatchers.IO) {
                    Triple(
                        runCatching { library.loadQueue() }.getOrDefault(emptyList()),
                        runCatching { library.loadPlaylists() }.getOrDefault(emptyList()),
                        projects.list().firstOrNull(),
                    )
                }
            val knownLibrary = withContext(Dispatchers.IO) {
                runCatching { library.loadLibrary() }.getOrDefault(emptyList())
            }
            val mergedLibrary =
                (knownLibrary + saved.first + listOfNotNull(saved.third?.source))
                    .distinctBy { it.uri }
            val scene =
                saved.third?.scene
                    ?: withContext(Dispatchers.IO) {
                        runCatching { Json.decodeFromString<Scene>(draft.readText()) }.getOrNull()
                    }
                    ?: mutable.value.scene
            val storedPresets =
                withContext(Dispatchers.IO) {
                    runCatching { presets.load() }.getOrDefault(emptyList())
                }
            mutable.value =
                mutable.value.copy(
                    queue = saved.first,
                    library = mergedLibrary,
                    playlists = saved.second,
                    project = saved.third,
                    scene = scene,
                    savedPresets = storedPresets,
                )
            initialized.complete(Unit)
            if (knownLibrary != mergedLibrary) persist()
            scheduleBackgroundAnalysis()
            saved.third?.let { select(it.source, false) }
        }
        viewModelScope.launch {
            combine(playback, state.map { it.scene to it.notes }.distinctUntilChanged()) { p, s ->
                    p to s
                }
                .collectLatest { (p, s) ->
                    val f =
                        withContext(Dispatchers.Default) {
                            runCatching { audioFeatures?.at(p.sourceTimeUs, s.second) }.getOrNull()
                                ?: FeatureFrame(p.sourceTimeUs, notes = s.second)
                        }
                    rendered.value = SceneEvaluator.evaluate(s.first, f, p.sourceTimeUs)
                }
        }
        viewModelScope.launch {
            combine(
                    playback.map { it.sourceUri }.distinctUntilChanged(),
                    state.map { it.queue }.distinctUntilChanged(),
                ) { uri, queue ->
                    uri to queue
                }
                .collect { (uri, queue) ->
                    if (uri == playback.value.sourceUri)
                        coordinator.selectionFor(uri, queue)?.let { select(it, false) }
                }
        }
    }

    private fun context() = getApplication<Application>()

    fun dismissError() {
        mutable.value = mutable.value.copy(error = null)
    }

    fun report(failure: Throwable) {
        mutable.update { it.copy(error = failure.localizedMessage ?: "Action failed") }
    }

    private fun persist() {
        saves.trySend(mutable.value)
    }

    fun importTracks(uris: List<Uri>) {
        viewModelScope.launch {
            initialized.await()
            runCatching {
                    val tracks = withContext(Dispatchers.IO) { uris.map { library.open(it) } }
                    if (tracks.isEmpty()) return@runCatching
                    val q = (mutable.value.queue + tracks).distinctBy { it.uri }
                    val all = (mutable.value.library + tracks).distinctBy { it.uri }
                    mutable.value = mutable.value.copy(queue = q, library = all)
                    persist()
                    select(tracks.first(), true)
                    scheduleBackgroundAnalysis()
                }
                .onFailure(::report)
        }
    }

    /** Refreshing Library never rewrites the independently ordered play queue. */
    fun refreshLibrary() {
        viewModelScope.launch {
            initialized.await()
            runCatching {
                val discovered = withContext(Dispatchers.IO) { library.discoverAudio() }
                mutable.update { state ->
                    state.copy(library = (state.library + discovered).distinctBy { it.uri })
                }
                persist()
                scheduleBackgroundAnalysis()
            }.onFailure(::report)
        }
    }

    /**
     * Pre-analyze each discovered track off the playback thread. Selecting a track cancels
     * this lower-priority worker, so the foreground inference gets the next model slot.
     * The hash/model/parameter cache in AnalysisRepository avoids repeat inference.
     */
    private fun scheduleBackgroundAnalysis() {
        preanalysisJob?.cancel()
        preanalysisJob = viewModelScope.launch(Dispatchers.IO) {
            initialized.await()
            val sources = mutable.value.library.toList()
            for (source in sources) {
                ensureActive()
                if (source.uri == mutable.value.project?.source?.uri) continue
                var decoded: DecodedAudio? = null
                try {
                    analysisLock.withLock {
                        ensureActive()
                        if (source.uri != mutable.value.project?.source?.uri) {
                            decoded = audio.get(source)
                            AnalysisRepository(context()).getOrAnalyze(decoded!!)
                        }
                    }
                } catch (cancelled: CancellationException) {
                    throw cancelled
                } catch (_: Exception) {
                    // An inaccessible music file must not stop all other background preparations.
                } finally {
                    decoded?.let { prepared ->
                        val current = mutable.value.project
                        if (current?.source?.uri != source.uri &&
                            current?.source?.contentSha256 != prepared.hash
                        ) {
                            audio.discardDecoded(prepared.hash)
                        }
                    }
                }
                val playingHash = mutable.value.project?.source?.contentSha256
                if (mutable.value.progress == null)
                    audio.compactDecodedCache(listOfNotNull(playingHash).toSet())
            }
        }
    }

    fun addToQueue(source: SourceRef, next: Boolean = false) {
        val current = mutable.value.queue
        if (current.any { it.uri == source.uri }) {
            if (next) playNext(source)
            return
        }
        val playing = playback.value.sourceUri
        val index = if (next && playing != null) {
            (current.indexOfFirst { it.uri == playing } + 1).coerceIn(0, current.size)
        } else current.size
        val updated = current.toMutableList().apply { add(index, source) }
        mutable.update { it.copy(queue = updated, library = (it.library + source).distinctBy { x -> x.uri }) }
        player.insertQueueItem(source, index)
        persist()
    }

    fun moveQueue(uri: String, delta: Int) {
        val current = mutable.value.queue
        val index = current.indexOfFirst { it.uri == uri }
        if (index < 0) return
        val target = (index + delta).coerceIn(0, current.lastIndex)
        if (index == target) return
        player.moveQueueItem(index, target)
        val reordered = current.toMutableList().apply { add(target, removeAt(index)) }
        mutable.update { it.copy(queue = reordered) }
        persist()
    }

    fun playNext(source: SourceRef) {
        val current = mutable.value.queue
        val playing = playback.value.sourceUri
        val nextIndex = if (playing == null) 0 else
            (current.indexOfFirst { it.uri == playing } + 1).coerceIn(0, current.size)
        val index = current.indexOfFirst { it.uri == source.uri }
        if (index < 0) {
            addToQueue(source, next = true)
        } else {
            val target = if (index < nextIndex) (nextIndex - 1).coerceAtLeast(0)
                else nextIndex.coerceAtMost(current.lastIndex)
            moveQueue(source.uri, target - index)
        }
    }

    fun sortQueue(byArtist: Boolean) {
        val next = if (byArtist) mutable.value.queue.sortedWith(
            compareBy<SourceRef> { it.artist.lowercase() }.thenBy { it.title.lowercase() },
        ) else mutable.value.queue.sortedBy { it.title.lowercase() }
        val working = mutable.value.queue.toMutableList()
        next.forEachIndexed { index, source ->
            val from = working.indexOfFirst { it.uri == source.uri }
            if (from != index) {
                player.moveQueueItem(from, index)
                working.add(index, working.removeAt(from))
            }
        }
        mutable.update { it.copy(queue = working) }
        persist()
    }

    fun select(source: SourceRef, startPlayback: Boolean = true) {
        preanalysisJob?.cancel()
        val previous = trackJob
        previous?.cancel()
        trackJob = viewModelScope.launch {
            previous?.join()
            preanalysisJob?.cancel()
            audioFeatures?.close()
            audioFeatures = null
            rawNotes = emptyList()
            val current = mutable.value.project
            val restored =
                if (current?.source?.uri == source.uri) current
                else
                    withContext(Dispatchers.IO) {
                        projects.list().firstOrNull { it.source.uri == source.uri }
                    } ?: Project(source = source, scene = mutable.value.scene)
            coordinator.begin(source.uri)
            mutable.value =
                mutable.value.copy(
                    project = restored,
                    scene = restored.scene,
                    notes = emptyList(),
                    status = "Preparing audio",
                    progress = 0f,
                    error = null,
                )
            if (startPlayback) {
                val q = (mutable.value.queue + source).distinctBy { it.uri }
                if (q != mutable.value.queue) {
                    mutable.update { it.copy(queue = q) }
                    persist()
                }
                player.setQueue(q, q.indexOfFirst { it.uri == source.uri }.coerceAtLeast(0))
            }
            player.setPracticeSpeed(restored.practice.speed)
            player.setLoop(
                restored.practice.loopStartUs.takeIf { restored.practice.loopEnabled },
                restored.practice.loopEndUs.takeIf { restored.practice.loopEnabled },
            )
            try {
                val decoded = audio.get(source) { p -> mutable.update { it.copy(progress = p) } }
                ensureActive()
                val before = mutable.value.project!!
                val changed =
                    before.source.contentSha256 != null &&
                        before.source.contentSha256 != decoded.hash
                val bound =
                    SourceIdentity.bind(
                        before,
                        source.copy(contentSha256 = decoded.hash, durationUs = decoded.durationUs),
                    )
                mutable.update {
                    it.copy(
                        project = bound,
                        scene = bound.scene,
                        status = "Detecting notes on this device",
                        progress = 0f,
                        error =
                            if (changed)
                                "The audio file changed. Old note corrections were cleared; your visualizer was kept."
                            else it.error,
                    )
                }
                audioFeatures = AudioFeatures(decoded)
                persist()
                val result =
                    analysisLock.withLock {
                        AnalysisRepository(context()).getOrAnalyze(decoded) { p ->
                            mutable.update { it.copy(progress = p) }
                        }
                    }
                ensureActive()
                rawNotes = result.rawNotes
                val project = mutable.value.project!!.copy(analysisKey = result.key)
                mutable.update {
                    it.copy(
                        project = project,
                        notes = applyNoteEdits(rawNotes, project.edits),
                        status = "${result.rawNotes.size} estimated notes • tap Practice to follow",
                        progress = null,
                    )
                }
                persist()
            } catch (cancelled: CancellationException) {
                throw cancelled
            } catch (failure: Throwable) {
                report(failure)
                mutable.update {
                    it.copy(status = "Choose the track again to retry", progress = null)
                }
            } finally {
                coordinator.finish(source.uri)
                if (currentCoroutineContext().isActive && coordinator.selectedUri == source.uri)
                    scheduleBackgroundAnalysis()
            }
        }
    }

    fun playPause() {
        val p = playback.value
        if (p.isPlaying) player.pause()
        else if (p.sourceUri == null) mutable.value.project?.let { select(it.source, true) }
        else player.play()
    }

    fun setScene(scene: Scene) {
        NativePackCodec.validateScene(scene)
        val current = mutable.value
        var saved = current.savedPresets
        for (candidate in listOf(current.scene, scene)) if (!candidate.id.startsWith("builtin-"))
            saved = PresetStore.upsert(saved, candidate)
        mutable.value =
            current.copy(
                scene = scene,
                project = current.project?.copy(scene = scene),
                savedPresets = saved,
            )
        persist()
    }

    fun editScene(scene: Scene) {
        setScene(
            if (scene.id.startsWith("builtin-")) scene.copy(id = UUID.randomUUID().toString())
            else scene,
        )
    }

    fun savePreset() {
        val scene = mutable.value.scene
        setScene(
            if (scene.id.startsWith("builtin-"))
                scene.copy(id = UUID.randomUUID().toString(), name = scene.name + " copy")
            else scene,
        )
    }

    fun setLayer(layer: Layer) {
        editScene(
            mutable.value.scene.copy(
                layers = mutable.value.scene.layers.map { if (it.id == layer.id) layer else it },
            ),
        )
    }

    fun removeLayer(id: String) {
        editScene(
            mutable.value.scene.copy(layers = mutable.value.scene.layers.filterNot { it.id == id }),
        )
    }

    fun moveLayer(id: String, delta: Int) {
        val scene = mutable.value.scene
        val list = scene.layers.toMutableList()
        val i = list.indexOfFirst { it.id == id }
        if (i < 0) return
        val target = (i + delta).coerceIn(0, list.lastIndex)
        list.add(target, list.removeAt(i))
        editScene(scene.copy(layers = list))
    }

    fun addLayer(type: ElementType) {
        editScene(
            mutable.value.scene.copy(layers = mutable.value.scene.layers + Layer(type = type)),
        )
    }

    fun editNote(
        edit: NoteEdit,
        target: NoteEditTarget? = mutable.value.project?.let(NoteEditTarget::of),
    ) {
        val p = mutable.value.project ?: return
        val updated =
            runCatching { NoteEditing.apply(p, target ?: return, edit) }
                .onFailure(::report)
                .getOrNull() ?: return
        val notes = applyNoteEdits(rawNotes, updated.edits)
        mutable.update { it.copy(project = updated, notes = notes) }
        persist()
    }

    fun updatePractice(change: (PracticeSettings) -> PracticeSettings) {
        val previous = mutable.value.project ?: return
        val next = change(previous.practice)
        require(next.isValid()) { "Invalid Practice settings" }
        mutable.update { state ->
            if (state.project?.id == previous.id)
                state.copy(project = state.project.copy(practice = next))
            else state
        }
        player.setPracticeSpeed(next.speed)
        if (
            previous.practice.loopStartUs != next.loopStartUs ||
                previous.practice.loopEndUs != next.loopEndUs ||
                previous.practice.loopEnabled != next.loopEnabled
        ) {
            player.setLoop(
                next.loopStartUs.takeIf { next.loopEnabled },
                next.loopEndUs.takeIf { next.loopEnabled },
            )
        }
        persist()
    }

    fun undoNote() {
        val p = mutable.value.project ?: return
        val updated = p.copy(edits = p.edits.dropLast(1))
        mutable.update {
            it.copy(project = updated, notes = applyNoteEdits(rawNotes, updated.edits))
        }
        persist()
    }

    fun removeQueue(uri: String) {
        val q = mutable.value.queue.filterNot { it.uri == uri }
        mutable.update { it.copy(queue = q) }
        player.removeFromQueue(uri)
        persist()
    }

    fun savePlaylist(name: String) {
        if (name.isBlank()) return
        val list =
            mutable.value.playlists +
                Playlist(UUID.randomUUID().toString(), name.trim(), mutable.value.queue)
        mutable.update { it.copy(playlists = list) }
        persist()
    }

    fun openPlaylist(playlist: Playlist) {
        mutable.update { it.copy(queue = playlist.tracks) }
        persist()
        playlist.tracks.firstOrNull()?.let { select(it, true) }
    }

    fun deletePlaylist(id: String) {
        val list = mutable.value.playlists.filterNot { it.id == id }
        mutable.update { it.copy(playlists = list) }
        persist()
    }

    fun exportNotes(uri: Uri, midi: Boolean) {
        val snapshot = mutable.value.notes.toList()
        viewModelScope.launch {
            runCatching {
                    withContext(Dispatchers.IO) {
                        context().contentResolver.openOutputStream(uri, "wt")!!.use {
                            if (midi) NoteExport.writeMidi(snapshot, it)
                            else NoteExport.writeCsv(snapshot, it)
                        }
                    }
                }
                .onFailure(::report)
        }
    }

    fun exportPack(uri: Uri) {
        val scene = mutable.value.scene
        viewModelScope.launch {
            runCatching {
                    withContext(Dispatchers.IO) {
                        context().contentResolver.openOutputStream(uri, "wt")!!.use { out ->
                            NativePackCodec()
                                .write(
                                    VisualizerPack(scene = scene),
                                    AssetResolver {
                                        File(context().filesDir, "assets/$it").inputStream()
                                    },
                                    out,
                                )
                        }
                    }
                }
                .onFailure(::report)
        }
    }

    fun importPack(uri: Uri) {
        viewModelScope.launch {
            runCatching {
                    val imported =
                        withContext(Dispatchers.IO) {
                            val folder =
                                File(context().cacheDir, "import-${UUID.randomUUID()}").apply {
                                    mkdirs()
                                }
                            try {
                                val original = File(folder, "original.viz")
                                context().contentResolver.openInputStream(uri)!!.use { input ->
                                    original.outputStream().use { output ->
                                        val b = ByteArray(65536)
                                        var total = 0L
                                        while (true) {
                                            val n = input.read(b)
                                            if (n < 0) break
                                            total += n
                                            require(total <= NativePackCodec.MAX_INPUT) {
                                                NativePackCodec.LIMITS
                                            }
                                            output.write(b, 0, n)
                                        }
                                    }
                                }
                                val native = runCatching {
                                    NativePackCodec()
                                        .read(original.inputStream(), File(folder, "native"))
                                }
                                    .getOrNull()
                                if (native != null) native
                                else {
                                    val assets = File(folder, "avee").apply { mkdirs() }
                                    val text =
                                        if (original.inputStream().use { it.read() } == 0x50) {
                                            NativePackCodec.extract(original.inputStream(), assets)
                                            val files =
                                                assets
                                                    .walkTopDown()
                                                    .filter {
                                                        it.isFile &&
                                                            it.extension.lowercase() in
                                                                setOf("json", "txt")
                                                    }
                                                    .toList()
                                            require(files.size == 1) {
                                                "Select an Avee JSON preset or a pack with one JSON scene"
                                            }
                                            require(files[0].length() <= 2 * 1024 * 1024)
                                            files[0].readText()
                                        } else {
                                            require(original.length() <= 2 * 1024 * 1024)
                                            original.readText()
                                        }
                                    AveePresetAdapter.read(text, assets)
                                        .copy(originalFile = original)
                                }
                            } catch (f: Throwable) {
                                folder.deleteRecursively()
                                throw f
                            }
                        }
                    if (imported.report.requiresPartialAcceptance)
                        mutable.update { it.copy(compatibility = imported) }
                    else acceptImport(imported)
                }
                .onFailure(::report)
        }
    }

    fun acceptImport(imported: ImportResult? = mutable.value.compatibility) {
        imported ?: return
        viewModelScope.launch {
            runCatching {
                    val installed =
                        withContext(Dispatchers.IO) {
                            val assets = File(context().filesDir, "assets").apply { mkdirs() }
                            val prefix = UUID.randomUUID().toString()
                            val target = File(assets, prefix).apply { mkdirs() }
                            if (imported.assetDirectory.isDirectory)
                                imported.assetDirectory.copyRecursively(target, true)
                            imported.originalFile?.let {
                                val original =
                                    File(context().filesDir, "original-presets/$prefix.viz")
                                original.parentFile!!.mkdirs()
                                it.copyTo(original, true)
                            }
                            imported.scene.copy(
                                id = UUID.randomUUID().toString(),
                                layers =
                                    imported.scene.layers.map { layer ->
                                        val old = layer.properties["asset"]?.jsonPrimitive?.content
                                        val newProps =
                                            if (old != null)
                                                JsonObject(
                                                    layer.properties +
                                                        ("asset" to JsonPrimitive("$prefix/$old")),
                                                )
                                            else layer.properties
                                        layer.copy(properties = newProps)
                                    },
                            )
                        }
                    setScene(installed)
                    mutable.update { it.copy(compatibility = null) }
                }
                .onFailure(::report)
        }
    }

    fun cancelImport() {
        mutable.update { it.copy(compatibility = null) }
    }

    fun attachImage(layer: Layer, uri: Uri) {
        viewModelScope.launch {
            runCatching {
                    val path =
                        withContext(Dispatchers.IO) {
                            val name = "${UUID.randomUUID()}.image"
                            val f = File(context().filesDir, "assets/$name")
                            f.parentFile!!.mkdirs()
                            try {
                                context().contentResolver.openInputStream(uri)!!.use { input ->
                                    f.outputStream().use { out ->
                                        val b = ByteArray(65536)
                                        var n: Int
                                        var total = 0L
                                        while (input.read(b).also { n = it } >= 0) {
                                            total += n
                                            require(total <= 32 * 1024 * 1024) {
                                                "Image exceeds 32 MiB"
                                            }
                                            out.write(b, 0, n)
                                        }
                                    }
                                }
                                AssetChecks.validateImage(f)
                                name
                            } catch (failure: Throwable) {
                                f.delete()
                                throw failure
                            }
                        }
                    setLayer(
                        layer.copy(
                            properties =
                                JsonObject(layer.properties + ("asset" to JsonPrimitive(path))),
                        ),
                    )
                }
                .onFailure(::report)
        }
    }

    fun prepareExport(startUs: Long, endUs: Long, settings: ExportSettings) {
        val p = mutable.value.project ?: error("Open a track first")
        require(p.source.contentSha256 != null && mutable.value.progress == null) {
            "Wait for note analysis to finish"
        }
        validateExportSettings(settings)
        ExportTimeline(startUs, endUs, settings.fps)
        require(endUs <= p.source.durationUs)
        pendingExport =
            ExportRequest(
                p.copy(scene = mutable.value.scene, export = settings),
                startUs,
                endUs,
                "",
            )
    }

    fun finishExport(uri: Uri) {
        val snapshot = pendingExport ?: return
        pendingExport = null
        ExportHub.enqueue(context(), snapshot.copy(outputUri = uri.toString()))
    }

    override fun onCleared() {
        trackJob?.cancel()
        preanalysisJob?.cancel()
        audioFeatures?.close()
        player.close()
        saves.close()
        super.onCleared()
    }
}
