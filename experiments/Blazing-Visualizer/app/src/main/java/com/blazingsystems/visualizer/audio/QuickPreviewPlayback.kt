package com.blazingsystems.visualizer.audio

import com.blazingsystems.visualizer.project.FeatureFrame
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.*
import kotlinx.serialization.json.JsonObject

internal data class QuickPreviewPosition(
    val uri: String,
    val sourceTimeUs: Long,
    val discontinuity: Long = 0,
    val profile: JsonObject = JsonObject(emptyMap()),
)

private data class QuickRequest(val uri: String, val discontinuity: Long, val profile: JsonObject)

/** Source-time scheduling is separate from Android decoding so latency can be reproduced. */
@OptIn(ExperimentalCoroutinesApi::class)
internal fun quickPreviewPlayback(
    positions: StateFlow<QuickPreviewPosition?>,
    decode: (String, Long, Long?, JsonObject) -> Flow<FeatureFrame>,
    failed: (String, Exception) -> Unit,
): Flow<QuickPreviewFrames> {
    return positions.map { position -> position?.let {
        QuickRequest(it.uri, it.discontinuity, it.profile)
    } }.distinctUntilChanged().transformLatest { request ->
        var cache = QuickPreviewFrames(request?.uri, positionVersion = request?.discontinuity ?: 0)
        emit(cache)
        if (request == null) {
            return@transformLatest
        }
        try {
            // Pay decoder startup once, not again at every playback second.
            // Begin at the actual playhead: starting behind it compounds startup latency.
            val start = positions.value?.sourceTimeUs ?: return@transformLatest
            decode(request.uri, start, null, request.profile).collect { frame ->
                // Backpressure bounds streaming decode and keeps the playhead in the
                // 96-frame cache, including while paused. Seeks cancel this wait too.
                while (frame.sourceTimeUs > (positions.value?.sourceTimeUs ?: 0) + 1_000_000) {
                    delay(20)
                }
                cache = cache.withFrame(request.uri, frame)
                emit(cache)
            }
        } catch (cancelled: CancellationException) {
            throw cancelled
        } catch (failure: Exception) {
            failed(request.uri, failure)
        }
    }
}
