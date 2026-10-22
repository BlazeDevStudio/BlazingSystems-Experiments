package com.blazingsystems.visualizer.playback

import com.blazingsystems.visualizer.project.SourceRef

/** Tracks the displayed source independently of the media player's preparation work. */
class TrackCoordinator {
    var selectedUri: String? = null
        private set

    var loadingUri: String? = null
        private set

    fun begin(uri: String) {
        selectedUri = uri
        loadingUri = uri
    }

    fun finish(uri: String) {
        if (loadingUri == uri) loadingUri = null
    }

    fun selectionFor(playingUri: String?, queue: List<SourceRef>): SourceRef? {
        return queue.firstOrNull { it.uri == playingUri && it.uri != selectedUri }
    }
}
