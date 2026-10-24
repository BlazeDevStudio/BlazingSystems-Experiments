package com.blazingsystems.visualizer.audio

import com.blazingsystems.visualizer.project.FeatureFrame
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.flow.*
import kotlinx.serialization.json.JsonObject

internal data class QuickPreviewPosition(
    val uri: String,
    val sourceTimeUs: Long,
    val discontinuity: Long = 0,
    val profile: JsonObject = JsonObject(emptyMap()),
)

private data class QuickRequest(val uri: String, val bucket: Long, val profile: JsonObject)

/** Source-time scheduling is separate from Android decoding so latency can be reproduced. */
internal fun quickPreviewPlayback(
    positions: StateFlow<QuickPreviewPosition?>,
    decode: (String, Long, Long, JsonObject) -> Flow<FeatureFrame>,
    failed: (String, Exception) -> Unit,
): Flow<QuickPreviewFrames> {
    var previous: QuickRequest? = null
    var cache = QuickPreviewFrames()
    return positions.map { position -> position?.let {
        QuickRequest(it.uri, it.sourceTimeUs / 1_000_000, it.profile)
    } }.distinctUntilChanged().transformLatest { request ->
        if (request == null) {
            previous = null
            cache = QuickPreviewFrames()
            emit(cache)
            return@transformLatest
        }
        val old = previous
        if (old == null || old.uri != request.uri || request.bucket < old.bucket ||
            request.bucket - old.bucket > 1 || old.profile != request.profile) {
            cache = QuickPreviewFrames(request.uri)
            emit(cache)
        }
        previous = request
        try {
            decode(request.uri, (request.bucket * 1_000_000 - 250_000).coerceAtLeast(0),
                2_000_000, request.profile).collect { frame ->
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
