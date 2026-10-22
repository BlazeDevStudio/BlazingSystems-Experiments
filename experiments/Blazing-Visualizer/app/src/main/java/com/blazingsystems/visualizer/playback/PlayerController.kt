package com.blazingsystems.visualizer.playback

import android.content.*
import android.net.Uri
import android.os.*
import androidx.core.content.ContextCompat
import androidx.media3.common.*
import androidx.media3.session.*
import com.blazingsystems.visualizer.project.SourceRef
import kotlinx.coroutines.flow.*

data class PlaybackState(
    val sourceTimeUs: Long = 0,
    val durationUs: Long = 0,
    val isPlaying: Boolean = false,
    val speed: Float = 1f,
    val failure: String? = null,
    val sourceUri: String? = null,
    val connected: Boolean = false,
)

data class LoopRange(val startUs: Long, val endUs: Long) {
    init {
        require(startUs >= 0 && endUs > startUs)
    }

    fun rewindIfOutside(position: Long) =
        if (position < startUs || position >= endUs) startUs else position
}

@androidx.annotation.OptIn(androidx.media3.common.util.UnstableApi::class)
class PlayerController(context: Context) : AutoCloseable {
    private val mutable = MutableStateFlow(PlaybackState())
    val state: StateFlow<PlaybackState> = mutable
    private val mutableQueue = MutableStateFlow<List<SourceRef>>(emptyList())
    val queue: StateFlow<List<SourceRef>> = mutableQueue
    private val handler = Handler(Looper.getMainLooper())
    private var controller: MediaController? = null
    private var loop: LoopRange? = null
    private var pending: List<SourceRef>? = null
    private var pendingIndex = 0
    private var pendingAutoPlay = false
    private var restoreOnly = false
    private var desiredSpeed = 1f
    private var closed = false
    private val future =
        MediaController.Builder(
                context,
                SessionToken(context, ComponentName(context, PlaybackService::class.java)),
            )
            .buildAsync()
    private val ticker =
        object : Runnable {
            override fun run() {
                if (closed) return
                controller?.let { player ->
                    val current = player.currentPosition.coerceAtLeast(0) * 1000
                    if (player.isPlaying)
                        loop?.let { range ->
                            val target = range.rewindIfOutside(current)
                            if (current != target) player.seekTo(target / 1000)
                        }
                    update()
                }
                handler.postDelayed(this, 40)
            }
        }

    init {
        future.addListener(
            {
                if (!closed)
                    runCatching {
                        controller =
                            future.get().also {
                                it.addListener(
                                    object : Player.Listener {
                                        override fun onEvents(
                                            player: Player,
                                            events: Player.Events,
                                        ) = update()
                                    },
                                )
                            }
                        if (pending != null && (!restoreOnly || controller!!.mediaItemCount == 0))
                            applyPending()
                        controller?.playbackParameters = PlaybackParameters(desiredSpeed, 1f)
                        loop?.let { controller?.seekTo(it.startUs / 1000) }
                        update()
                        handler.post(ticker)
                    }
                        .onFailure {
                            mutable.value =
                                mutable.value.copy(failure = it.message ?: "Playback unavailable")
                        }
            },
            ContextCompat.getMainExecutor(context),
        )
    }

    fun setQueue(sources: List<SourceRef>, index: Int = 0) {
        require(sources.isNotEmpty() && index in sources.indices)
        pending = sources
        pendingIndex = index
        pendingAutoPlay = true
        restoreOnly = false
        loop = null
        mutableQueue.value = sources
        applyPending()
    }

    /** Cold launch restores ordering without interrupting an existing background session. */
    fun restoreQueue(sources: List<SourceRef>, index: Int = 0) {
        require(sources.isEmpty() || index in sources.indices)
        pending = sources
        pendingIndex = index
        pendingAutoPlay = false
        restoreOnly = true
        mutableQueue.value = sources
        if (controller?.mediaItemCount == 0) applyPending() else update()
    }

    fun clearQueue() {
        pending = emptyList()
        pendingIndex = 0
        pendingAutoPlay = false
        restoreOnly = false
        loop = null
        mutableQueue.value = emptyList()
        controller?.clearMediaItems()
        update()
    }

    private fun mediaItem(source: SourceRef) = MediaItem.Builder()
        .setUri(source.uri).setMediaId(source.uri)
        .setMediaMetadata(MediaMetadata.Builder().setTitle(source.title).setArtist(source.artist).build())
        .build()

    private fun applyPending() {
        val sources = pending ?: return
        controller?.let { player ->
            if (sources.isEmpty()) {
                player.clearMediaItems()
                update()
                return
            }
            player.setMediaItems(
                sources.map(::mediaItem),
                pendingIndex.coerceIn(sources.indices),
                0,
            )
            player.prepare()
            player.playWhenReady = pendingAutoPlay
            update()
        }
    }

    fun removeFromQueue(uri: String) {
        val previous = pending.orEmpty()
        val current =
            controller?.currentMediaItem?.localConfiguration?.uri?.toString()
                ?: previous.getOrNull(pendingIndex)?.uri
        pending = previous.filterNot { it.uri == uri }
        pendingIndex = pending!!.indexOfFirst { it.uri == current }.coerceAtLeast(0)
        controller?.let { p ->
            for (i in p.mediaItemCount - 1 downTo 0) if (
                p.getMediaItemAt(i).localConfiguration?.uri?.toString() == uri
            )
                p.removeMediaItem(i)
        }
        update()
    }

    /** Media3 playlist mutations do not call prepare/play or reset the current item. */
    fun moveQueueItem(from: Int, to: Int) {
        pending?.let { previous ->
            if (from !in previous.indices || to !in previous.indices) return
            val currentUri = controller?.currentMediaItem?.mediaId
                ?: previous.getOrNull(pendingIndex)?.uri
            pending = previous.toMutableList().apply { add(to, removeAt(from)) }
            pendingIndex = pending!!.indexOfFirst { it.uri == currentUri }.coerceAtLeast(0)
        }
        controller?.let { player ->
            if (from in 0 until player.mediaItemCount && to in 0 until player.mediaItemCount)
                player.moveMediaItem(from, to)
        }
        update()
    }

    fun insertQueueItem(source: SourceRef, index: Int) {
        pending.orEmpty().let { previous ->
            val at = index.coerceIn(0, previous.size)
            val currentUri = controller?.currentMediaItem?.mediaId
                ?: previous.getOrNull(pendingIndex)?.uri
            pending = previous.toMutableList().apply { add(at, source) }
            pendingIndex = pending!!.indexOfFirst { it.uri == currentUri }.coerceAtLeast(0)
        }
        controller?.let { player ->
            val at = index.coerceIn(0, player.mediaItemCount)
            player.addMediaItem(
                at,
                MediaItem.Builder().setUri(source.uri).setMediaId(source.uri)
                    .setMediaMetadata(MediaMetadata.Builder()
                        .setTitle(source.title).setArtist(source.artist).build())
                    .build(),
            )
        }
        update()
    }

    fun open(uri: Uri) = setQueue(listOf(SourceRef(uri.toString())))

    fun play() {
        pendingAutoPlay = true
        controller?.prepare()
        controller?.play()
    }

    fun pause() {
        pendingAutoPlay = false
        controller?.pause()
    }

    fun next() {
        loop = null
        controller?.seekToNextMediaItem()
    }

    fun previous() {
        loop = null
        controller?.seekToPreviousMediaItem()
    }

    fun seekTo(us: Long) {
        controller?.seekTo(
            us.coerceIn(0, state.value.durationUs.takeIf { it > 0 } ?: Long.MAX_VALUE) / 1000,
        )
        update()
    }

    fun setPracticeSpeed(speed: Float) {
        require(speed.isFinite() && speed in .5f..1.5f)
        desiredSpeed = speed
        controller?.playbackParameters = PlaybackParameters(speed, 1f)
        update()
    }

    fun setLoop(start: Long?, end: Long?) {
        require((start == null) == (end == null))
        loop = if (start == null) null else LoopRange(start, end!!)
        loop?.let { seekTo(it.startUs) }
    }

    private fun update() {
        controller?.let { p ->
            val known = pending.orEmpty().associateBy { it.uri }
            val actual = (0 until p.mediaItemCount).map { index ->
                val item = p.getMediaItemAt(index)
                val uri = item.localConfiguration?.uri?.toString() ?: item.mediaId
                known[uri] ?: SourceRef(uri, title = item.mediaMetadata.title?.toString().orEmpty(),
                    artist = item.mediaMetadata.artist?.toString().orEmpty())
            }
            pending = actual
            pendingIndex = p.currentMediaItemIndex.coerceAtLeast(0)
            mutableQueue.value = actual
            mutable.value =
                PlaybackState(
                    p.currentPosition.coerceAtLeast(0) * 1000,
                    p.duration.takeUnless { it == C.TIME_UNSET }?.coerceAtLeast(0)?.times(1000)
                        ?: 0,
                    p.isPlaying,
                    p.playbackParameters.speed,
                    p.playerError?.localizedMessage,
                    p.currentMediaItem?.localConfiguration?.uri?.toString(),
                    true,
                )
        }
    }

    override fun close() {
        closed = true
        handler.removeCallbacks(ticker)
        MediaController.releaseFuture(future)
        controller = null
    }
}
