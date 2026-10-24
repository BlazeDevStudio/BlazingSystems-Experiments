package com.blazingsystems.visualizer.playback

import androidx.media3.exoplayer.ExoPlayer
import androidx.media3.common.MediaItem
import androidx.media3.common.Player
import androidx.media3.session.MediaSession
import androidx.media3.session.MediaSessionService
import com.blazingsystems.visualizer.audio.PlaybackPcmPreview

@androidx.annotation.OptIn(androidx.media3.common.util.UnstableApi::class)
class PlaybackService : MediaSessionService() {
    private var session: MediaSession? = null

    override fun onCreate() {
        super.onCreate()
        val player = ExoPlayer.Builder(this, StartupSafeRenderersFactory(this)).build()
        player.addListener(object : Player.Listener {
            override fun onMediaItemTransition(mediaItem: MediaItem?, reason: Int) {
                PlaybackPcmPreview.setSource(mediaItem?.localConfiguration?.uri?.toString()
                    ?: mediaItem?.mediaId?.takeIf { it.isNotEmpty() })
            }

            override fun onPositionDiscontinuity(oldPosition: Player.PositionInfo,
                newPosition: Player.PositionInfo, reason: Int) {
                PlaybackPcmPreview.invalidate()
            }
        })
        session = MediaSession.Builder(this, player).build()
    }

    override fun onGetSession(controllerInfo: MediaSession.ControllerInfo) = session

    override fun onDestroy() {
        session?.let {
            it.player.release()
            it.release()
        }
        session = null
        PlaybackPcmPreview.setSource(null)
        super.onDestroy()
    }
}
