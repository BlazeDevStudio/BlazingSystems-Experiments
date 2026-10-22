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
    private val handler = Handler(Looper.getMainLooper())
    private var controller: MediaController? = null
    private var loop: LoopRange? = null
    private var pending: List<SourceRef>? = null
    private var pendingIndex = 0
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
                        pending
                            ?.takeIf { it.isNotEmpty() }
                            ?.let { setQueue(it, pendingIndex.coerceAtMost(it.lastIndex)) }
                        controller?.playbackParameters = PlaybackParameters(desiredSpeed, 1f)
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
        loop = null
        controller?.let { player ->
            player.setMediaItems(
                sources.map {
                    MediaItem.Builder()
                        .setUri(it.uri)
                        .setMediaId(it.uri)
                        .setMediaMetadata(
                            MediaMetadata.Builder().setTitle(it.title).setArtist(it.artist).build(),
                        )
                        .build()
                },
                index,
                0,
            )
            player.prepare()
            player.play()
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

    fun open(uri: Uri) = setQueue(listOf(SourceRef(uri.toString())))

    fun play() {
        controller?.play()
    }

    fun pause() {
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
            mutable.value =
                PlaybackState(
                    p.currentPosition.coerceAtLeast(0) * 1000,
                    p.duration.takeUnless { it == C.TIME_UNSET }?.coerceAtLeast(0)?.times(1000)
                        ?: 0,
                    p.isPlaying,
                    p.playbackParameters.speed,
                    p.playerError?.localizedMessage,
                    p.currentMediaItem?.localConfiguration?.uri?.toString(),
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
