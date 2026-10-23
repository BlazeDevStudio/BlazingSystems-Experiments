package com.blazingsystems.visualizer.playback

import com.blazingsystems.visualizer.project.SourceRef

/** Tracks the displayed source independently of the media player's preparation work. */
class TrackCoordinator {
    var selectedUri: String? = null
        private set

    var loadingUri: String? = null
        private set
    private var requestedPlaybackUri: String? = null

    /** User intent takes precedence while the previous Media3 item is still reported. */
    fun expectPlayback(uri: String) {
        requestedPlaybackUri = uri
        begin(uri)
    }

    fun begin(uri: String) {
        selectedUri = uri
        loadingUri = uri
    }

    fun finish(uri: String) {
        if (loadingUri == uri) loadingUri = null
    }

    fun selectionFor(playingUri: String?, queue: List<SourceRef>): SourceRef? {
        requestedPlaybackUri?.let { requested ->
            if (playingUri != requested) return null
            requestedPlaybackUri = null
        }
        return queue.firstOrNull { it.uri == playingUri && it.uri != selectedUri }
    }
}
