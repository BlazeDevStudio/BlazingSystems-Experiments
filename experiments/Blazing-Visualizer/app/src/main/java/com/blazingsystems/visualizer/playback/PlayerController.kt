package com.blazingsystems.visualizer.playback

import android.content.*
import android.net.Uri
import android.os.*
import android.graphics.Matrix
import android.view.TextureView
import android.view.View
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
    val repeatMode: Int = Player.REPEAT_MODE_ALL,
    val shuffle: Boolean = false,
    val positionVersion: Long = 0,
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
    private var videoView: TextureView? = null
    private val videoLayoutListener = View.OnLayoutChangeListener { _, _, _, _, _, _, _, _, _ ->
        updateVideoTransform()
    }
    private var loop: LoopRange? = null
    private var pendingLoopSeekUs: Long? = null
    private var pending: List<SourceRef>? = null
    private var pendingIndex = 0
    private var pendingAutoPlay = false
    private var restoreOnly = false
    private val preferences = context.getSharedPreferences("playback-mode", Context.MODE_PRIVATE)
    private var desiredRepeat = preferences.getInt("repeat", Player.REPEAT_MODE_ALL)
        .takeIf { it == Player.REPEAT_MODE_OFF || it == Player.REPEAT_MODE_ALL || it == Player.REPEAT_MODE_ONE }
        ?: Player.REPEAT_MODE_ALL
    private var desiredShuffle = preferences.getBoolean("shuffle", false)
    private var desiredSpeed = 1f
    private var practiceSourceUri: String? = null
    private var closed = false
    private var positionVersion = 0L
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
                    if (player.isPlaying && (practiceSourceUri == null ||
                        practiceSourceUri == player.currentMediaItem?.mediaId))
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
                                        ) {
                                            if (events.contains(Player.EVENT_POSITION_DISCONTINUITY)) positionVersion++
                                            flushPreparedSeek(player)
                                            if (events.contains(Player.EVENT_VIDEO_SIZE_CHANGED)) updateVideoTransform()
                                            update()
                                        }
                                    },
                                )
                            }
                        controller!!.repeatMode = desiredRepeat
                        controller!!.shuffleModeEnabled = desiredShuffle
                        videoView?.let { controller!!.setVideoTextureView(it) }
                        updateVideoTransform()
                        val adoptingLive = restoreOnly && controller!!.mediaItemCount > 0
                        if (pending != null && !adoptingLive)
                            applyPending()
                        if (adoptingLive) {
                            desiredSpeed = controller!!.playbackParameters.speed
                            if (practiceSourceUri != controller!!.currentMediaItem?.mediaId) loop = null
                        } else {
                            controller?.playbackParameters = PlaybackParameters(desiredSpeed, 1f)
                            if (practiceSourceUri == null || practiceSourceUri == controller?.currentMediaItem?.mediaId)
                                loop?.let { controller?.seekTo(it.startUs / 1000) }
                        }
                        controller?.let(::flushPreparedSeek)
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

    /** A restored loop is sought only after the chosen audio has been prepared. */
    private fun flushPreparedSeek(player: Player) {
        val target = pendingLoopSeekUs ?: return
        if (player.playbackState != Player.STATE_READY) return
        if (practiceSourceUri != null && player.currentMediaItem?.mediaId != practiceSourceUri) {
            pendingLoopSeekUs = null
            return
        }
        pendingLoopSeekUs = null
        player.seekTo(target / 1000)
    }

    fun setQueue(sources: List<SourceRef>, index: Int = 0) {
        require(sources.isNotEmpty() && index in sources.indices)
        pending = sources
        pendingIndex = index
        pendingAutoPlay = true
        restoreOnly = false
        loop = null
        pendingLoopSeekUs = null
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
        pendingLoopSeekUs = null
        mutableQueue.value = emptyList()
        controller?.clearMediaItems()
        update()
    }

    private fun mediaItem(source: SourceRef) = MediaItem.Builder()
        .setUri(source.uri).setMediaId(source.uri)
        .setMediaMetadata(MediaMetadata.Builder().setTitle(source.title).setArtist(source.artist).build())
        .build()

    /** The visible video and audible audio belong to this one MediaSession. */
    fun attachVideo(view: TextureView) {
        check(Looper.myLooper() == Looper.getMainLooper())
        if (videoView === view) return
        videoView?.let(::detachVideo)
        videoView = view
        view.isOpaque = false
        view.addOnLayoutChangeListener(videoLayoutListener)
        controller?.setVideoTextureView(view)
        updateVideoTransform()
    }

    fun detachVideo(view: TextureView) {
        if (videoView !== view) return
        controller?.clearVideoTextureView(view)
        view.removeOnLayoutChangeListener(videoLayoutListener)
        videoView = null
    }

    private fun updateVideoTransform() {
        val view = videoView ?: return
        val size = controller?.videoSize ?: return
        if (view.width <= 0 || view.height <= 0 || size.width <= 0 || size.height <= 0) return
        val aspect = size.width * size.pixelWidthHeightRatio / size.height
        val viewport = view.width.toFloat() / view.height
        val sx = if (aspect < viewport) aspect / viewport else 1f
        val sy = if (aspect > viewport) viewport / aspect else 1f
        view.setTransform(Matrix().apply { setScale(sx, sy, view.width / 2f, view.height / 2f) })
    }

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
        pendingLoopSeekUs = null
        controller?.seekToNextMediaItem()
    }

    fun previous() {
        loop = null
        pendingLoopSeekUs = null
        controller?.seekToPreviousMediaItem()
    }

    fun seekTo(us: Long) {
        controller?.seekTo(
            us.coerceIn(0, state.value.durationUs.takeIf { it > 0 } ?: Long.MAX_VALUE) / 1000,
        )
        update()
    }

    fun setRepeatMode(mode: Int) {
        require(mode == Player.REPEAT_MODE_OFF || mode == Player.REPEAT_MODE_ONE || mode == Player.REPEAT_MODE_ALL)
        desiredRepeat = mode
        preferences.edit().putInt("repeat", mode).apply()
        controller?.repeatMode = mode
        update()
    }

    fun cycleRepeatMode() = setRepeatMode(when (desiredRepeat) {
        Player.REPEAT_MODE_ALL -> Player.REPEAT_MODE_ONE
        Player.REPEAT_MODE_ONE -> Player.REPEAT_MODE_OFF
        else -> Player.REPEAT_MODE_ALL
    })

    fun setShuffle(enabled: Boolean) {
        desiredShuffle = enabled
        preferences.edit().putBoolean("shuffle", enabled).apply()
        controller?.shuffleModeEnabled = enabled
        update()
    }

    fun toggleShuffle() = setShuffle(!desiredShuffle)

    fun setPracticeSpeed(speed: Float) {
        require(speed.isFinite() && speed in .5f..1.5f)
        desiredSpeed = speed
        controller?.playbackParameters = PlaybackParameters(speed, 1f)
        update()
    }

    fun setLoop(start: Long?, end: Long?) {
        require((start == null) == (end == null))
        loop = if (start == null) null else LoopRange(start, end!!)
        practiceSourceUri = controller?.currentMediaItem?.mediaId ?: pending?.getOrNull(pendingIndex)?.uri
        pendingLoopSeekUs = null
        loop?.let {
            if (controller?.playbackState == Player.STATE_READY) seekTo(it.startUs)
            else pendingLoopSeekUs = it.startUs
        }
    }

    /** Restored settings are bound to their track and do not rewind a live session. */
    fun restorePractice(sourceUri: String, speed: Float, start: Long?, end: Long?, rewind: Boolean = false) {
        require(speed.isFinite() && speed in .5f..1.5f)
        require((start == null) == (end == null))
        val range = if (start == null) null else LoopRange(start, end!!)
        if (controller != null && controller?.currentMediaItem?.mediaId != sourceUri) return
        practiceSourceUri = sourceUri
        desiredSpeed = speed
        loop = range
        pendingLoopSeekUs = null
        controller?.playbackParameters = PlaybackParameters(speed, 1f)
        if (rewind && range != null) {
            if (controller?.playbackState == Player.STATE_READY) seekTo(range.startUs)
            else pendingLoopSeekUs = range.startUs
        }
        update()
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
                    p.repeatMode,
                    p.shuffleModeEnabled,
                    positionVersion,
                )
        }
    }

    override fun close() {
        videoView?.let(::detachVideo)
        closed = true
        handler.removeCallbacks(ticker)
        MediaController.releaseFuture(future)
        controller = null
    }
}
