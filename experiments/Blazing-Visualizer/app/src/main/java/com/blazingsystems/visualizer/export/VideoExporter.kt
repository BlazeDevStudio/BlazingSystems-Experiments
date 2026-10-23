package com.blazingsystems.visualizer.export

import android.content.Context
import android.media.*
import android.net.Uri
import android.os.StatFs
import com.blazingsystems.visualizer.analysis.*
import com.blazingsystems.visualizer.audio.*
import com.blazingsystems.visualizer.project.*
import com.blazingsystems.visualizer.render.*
import java.io.*
import java.nio.ByteBuffer
import kotlin.math.*
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.takeWhile

/** MP4 encoder uses source time, never the preview's wall clock or practice speed. */
class VideoExporter(private val context: Context) {
    suspend fun export(request: ExportRequest, progress: (Float) -> Unit = {}): Unit =
        withContext(Dispatchers.Default) {
            val s = request.settings
            validateExportSettings(s)
            val timeline = ExportTimeline(request.clipStartUs, request.clipEndUs, s.fps)
            val estimate =
                timeline.durationUs / 1_000_000.0 * (s.videoBitrate + s.audioBitrate) / 8 * 2.5 +
                    32 * 1024 * 1024
            require(StatFs(context.cacheDir.path).availableBytes > estimate) {
                "Not enough storage for this video"
            }
            AudioRepository(context).acquireDecoded(request.project.source).use { lease ->
                val audio = lease.audio
                SourceIdentity.requireExportMatch(request.project.source.contentSha256, audio.hash)
                require(request.clipEndUs <= audio.durationUs) {
                    "The export range exceeds the track duration"
                }
                val result = AnalysisRepository(context).getOrAnalyze(audio)
                val notes = applyNoteEdits(result.rawNotes, request.project.edits)
                val temporary =
                    File(context.cacheDir, "export-${java.util.UUID.randomUUID()}").apply { mkdirs() }
                var destinationStarted = false
                try {
                    val video = File(temporary, "video.mp4")
                    val sound = File(temporary, "audio.mp4")
                    val complete = File(temporary, "complete.mp4")
                    encodeVideo(request, timeline, audio, notes, video) { progress(it * .78f) }
                    ensureActive()
                    progress(.8f)
                    val audioShiftUs = encodeAudio(audio, timeline, s.audioBitrate, sound)
                    ensureActive()
                    progress(.9f)
                    remux(video, sound, complete, timeline.durationUs, audioShiftUs)
                    ensureActive()
                    progress(.96f)
                    destinationStarted = true
                    context.contentResolver.openOutputStream(Uri.parse(request.outputUri), "wt")?.use {
                        output ->
                        complete.inputStream().use { input ->
                            val buffer = ByteArray(65536)
                            while (true) {
                                ensureActive()
                                val count = input.read(buffer)
                                if (count < 0) break
                                output.write(buffer, 0, count)
                            }
                        }
                    } ?: error("Could not open the export destination")
                    progress(1f)
                } catch (failure: Throwable) {
                    if (destinationStarted)
                        runCatching {
                            android.provider.DocumentsContract.deleteDocument(
                                context.contentResolver,
                                Uri.parse(request.outputUri),
                            )
                        }
                    throw failure
                } finally {
                    temporary.deleteRecursively()
                }
            }
        }

    private suspend fun encodeVideo(
        request: ExportRequest,
        timeline: ExportTimeline,
        audio: DecodedAudio,
        notes: List<NoteEvent>,
        output: File,
        progress: (Float) -> Unit,
    ) {
        val job = currentCoroutineContext()
        val s = request.settings
        val codec = MediaCodec.createEncoderByType(MediaFormat.MIMETYPE_VIDEO_AVC)
        val muxer = MediaMuxer(output.path, MediaMuxer.OutputFormat.MUXER_OUTPUT_MPEG_4)
        var started = false
        var track = -1
        var configured = false
        var primaryFailure: Throwable? = null
        try {
            val format =
                MediaFormat.createVideoFormat(MediaFormat.MIMETYPE_VIDEO_AVC, s.width, s.height)
                    .apply {
                        setInteger(
                            MediaFormat.KEY_COLOR_FORMAT,
                            MediaCodecInfo.CodecCapabilities.COLOR_FormatSurface,
                        )
                        setInteger(MediaFormat.KEY_BIT_RATE, s.videoBitrate)
                        setInteger(MediaFormat.KEY_FRAME_RATE, s.fps)
                        setInteger(MediaFormat.KEY_I_FRAME_INTERVAL, 1)
                    }
            // Let the codec negotiate profile and level together; API 26 rejects an unmatched
            // forced profile.
            codec.configure(format, null, null, MediaCodec.CONFIGURE_FLAG_ENCODE)
            configured = true
            val surface = codec.createInputSurface()
            codec.start()
            val info = MediaCodec.BufferInfo()
            fun drain(waitForEnd: Boolean) {
                var last = System.nanoTime()
                while (true) {
                    job.ensureActive()
                    when (
                        val index = codec.dequeueOutputBuffer(info, if (waitForEnd) 10_000 else 0)
                    ) {
                        MediaCodec.INFO_TRY_AGAIN_LATER -> {
                            if (!waitForEnd) return
                            check(System.nanoTime() - last < 30_000_000_000L) {
                                "Video encoder stopped responding"
                            }
                        }
                        MediaCodec.INFO_OUTPUT_FORMAT_CHANGED -> {
                            check(!started)
                            track = muxer.addTrack(codec.outputFormat)
                            muxer.start()
                            started = true
                            last = System.nanoTime()
                        }
                        else ->
                            if (index >= 0) {
                                try {
                                    val end =
                                        info.flags and MediaCodec.BUFFER_FLAG_END_OF_STREAM != 0
                                    if (
                                        info.size > 0 &&
                                            info.flags and MediaCodec.BUFFER_FLAG_CODEC_CONFIG == 0
                                    ) {
                                        check(started)
                                        val bytes = codec.getOutputBuffer(index)!!
                                        bytes.position(info.offset)
                                        bytes.limit(info.offset + info.size)
                                        muxer.writeSampleData(track, bytes, info)
                                    }
                                    last = System.nanoTime()
                                    if (end) return
                                } finally {
                                    codec.releaseOutputBuffer(index, false)
                                }
                            }
                    }
                }
            }
            try {
                val videoFrames = if (request.project.source.hasVideo)
                    VideoFrameSource(context, Uri.parse(request.project.source.uri)) else null
                videoFrames.use { background ->
                    GlTarget.encoder(surface, s.width, s.height).use { target ->
                        GlSceneRenderer(File(context.filesDir, "assets")).use { renderer ->
                            AudioFeatures(audio).use { features ->
                                for (frame in 0 until timeline.frameCount) {
                                    job.ensureActive()
                                    drain(false)
                                    val time = timeline.sourceTimeUs(frame)
                                    val videoFrame = background?.frameAt(time, s.width, s.height)
                                    try {
                                        renderer.render(
                                            SceneEvaluator.evaluate(
                                                request.project.scene,
                                                features.at(time, notes,request.project.scene.aveeAudio),
                                                time,
                                            ),
                                            target,
                                            videoFrame = videoFrame,
                                        )
                                    } finally { videoFrame?.recycle() }
                                    target.present(timeline.presentationTimeUs(frame))
                                    drain(false)
                                    progress((frame + 1f) / timeline.frameCount)
                                }
                            }
                        }
                    }
                }
                codec.signalEndOfInputStream()
                drain(true)
                check(started) { "Video encoder produced no frames" }
                muxer.writeSampleData(
                    track,
                    ByteBuffer.allocate(0),
                    MediaCodec.BufferInfo().apply {
                        set(0, 0, timeline.durationUs, MediaCodec.BUFFER_FLAG_END_OF_STREAM)
                    },
                )
            } finally {
                surface.release()
            }
        } catch (failure: Throwable) {
            primaryFailure = failure
            throw failure
        } finally {
            if (configured) runCatching { codec.stop() }
            codec.release()
            ExportFinalization.close(
                primaryFailure,
                { if (started) muxer.stop() },
                { muxer.release() },
            )
        }
    }

    private suspend fun encodeAudio(
        audio: DecodedAudio,
        timeline: ExportTimeline,
        bitrate: Int,
        output: File,
    ): Long {
        val job = currentCoroutineContext()
        require(audio.channels in 1..2) { "Video export supports mono and stereo audio" }
        val codec = MediaCodec.createEncoderByType(MediaFormat.MIMETYPE_AUDIO_AAC)
        val muxer = MediaMuxer(output.path, MediaMuxer.OutputFormat.MUXER_OUTPUT_MPEG_4)
        var started = false
        var track = -1
        var primaryFailure: Throwable? = null
        val prefix = AacAlignment.prefix(audio.sampleRate)
        try {
            val format =
                MediaFormat.createAudioFormat(
                        MediaFormat.MIMETYPE_AUDIO_AAC,
                        audio.sampleRate,
                        audio.channels,
                    )
                    .apply {
                        setInteger(
                            MediaFormat.KEY_AAC_PROFILE,
                            MediaCodecInfo.CodecProfileLevel.AACObjectLC,
                        )
                        setInteger(MediaFormat.KEY_BIT_RATE, bitrate)
                        setInteger(MediaFormat.KEY_MAX_INPUT_SIZE, 16384)
                    }
            codec.configure(format, null, null, MediaCodec.CONFIGURE_FLAG_ENCODE)
            codec.start()
            RandomAccessFile(audio.pcmFile, "r").use { pcm ->
                val startFrame = timeline.startUs * audio.sampleRate / 1_000_000
                val count =
                    (timeline.durationUs * audio.sampleRate / 1_000_000).coerceAtMost(
                        audio.frames - startFrame,
                    )
                val totalFrames =
                    count + prefix.size + 8192 // Flush the encoder's delayed tail with silence.
                pcm.seek(startFrame * audio.channels * 2)
                var sent = 0L
                var inputEnded = false
                var done = false
                var last = System.nanoTime()
                val info = MediaCodec.BufferInfo()
                while (!done) {
                    job.ensureActive()
                    if (!inputEnded) {
                        val index = codec.dequeueInputBuffer(10_000)
                        if (index >= 0) {
                            val input = codec.getInputBuffer(index)!!
                            input.clear()
                            val frames =
                                min(
                                        input.capacity() / (audio.channels * 2).toLong(),
                                        totalFrames - sent,
                                    )
                                    .toInt()
                            val bytes = ByteArray(frames * audio.channels * 2)
                            val prefixFrames =
                                min(frames.toLong(), (prefix.size - sent).coerceAtLeast(0)).toInt()
                            val b =
                                java.nio.ByteBuffer.wrap(bytes)
                                    .order(java.nio.ByteOrder.LITTLE_ENDIAN)
                            for (i in 0 until prefixFrames) repeat(audio.channels) {
                                b.putShort((prefix[(sent + i).toInt()] * 32767).toInt().toShort())
                            }
                            val musicOffset = (sent - prefix.size).coerceAtLeast(0)
                            val musicFrames =
                                min(
                                        (frames - prefixFrames).toLong(),
                                        (count - musicOffset).coerceAtLeast(0),
                                    )
                                    .toInt()
                            if (musicFrames > 0)
                                pcm.readFully(
                                    bytes,
                                    prefixFrames * audio.channels * 2,
                                    musicFrames * audio.channels * 2,
                                )
                            // Remaining bytes stay zero: the calibration prefix and codec tail are
                            // discarded at remux.
                            input.put(bytes)
                            val pts = sent * 1_000_000 / audio.sampleRate
                            sent += frames
                            inputEnded = sent >= totalFrames
                            codec.queueInputBuffer(
                                index,
                                0,
                                bytes.size,
                                pts,
                                if (inputEnded) MediaCodec.BUFFER_FLAG_END_OF_STREAM else 0,
                            )
                        }
                    }
                    when (val index = codec.dequeueOutputBuffer(info, 10_000)) {
                        MediaCodec.INFO_OUTPUT_FORMAT_CHANGED -> {
                            val f = codec.outputFormat
                            f.setInteger("encoder-delay", 0)
                            f.setInteger("encoder-padding", 0)
                            track = muxer.addTrack(f)
                            muxer.start()
                            started = true
                            last = System.nanoTime()
                        }
                        else ->
                            if (index >= 0) {
                                try {
                                    if (
                                        info.size > 0 &&
                                            info.flags and MediaCodec.BUFFER_FLAG_CODEC_CONFIG ==
                                                0 &&
                                            info.presentationTimeUs >= 0
                                    ) {
                                        check(started)
                                        val bytes = codec.getOutputBuffer(index)!!
                                        bytes.position(info.offset)
                                        bytes.limit(info.offset + info.size)
                                        muxer.writeSampleData(track, bytes, info)
                                    }
                                    done = info.flags and MediaCodec.BUFFER_FLAG_END_OF_STREAM != 0
                                    last = System.nanoTime()
                                } finally {
                                    codec.releaseOutputBuffer(index, false)
                                }
                            }
                    }
                    check(System.nanoTime() - last < 30_000_000_000L) {
                        "Audio encoder stopped responding"
                    }
                }
                check(started)
            }
        } catch (failure: Throwable) {
            primaryFailure = failure
            throw failure
        } finally {
            runCatching { codec.stop() }
            codec.release()
            ExportFinalization.close(
                primaryFailure,
                { if (started) muxer.stop() },
                { muxer.release() },
            )
        }
        val decoded = ArrayList<Float>()
        PcmDecoder(context)
            .decode(Uri.fromFile(output))
            .takeWhile { decoded.size < AacAlignment.PREFIX_FRAMES + 8192 }
            .collect { chunk ->
                require(chunk.sampleRate == audio.sampleRate) { "AAC sample rate changed" }
                for (frame in 0 until chunk.samples.size / chunk.channels) {
                    var sample = 0f
                    for (channel in 0 until chunk.channels) sample +=
                        chunk.samples[frame * chunk.channels + channel]
                    decoded += sample / chunk.channels
                }
            }
        job.ensureActive()
        val delay = AacAlignment.measureDelay(decoded.toFloatArray(), audio.sampleRate)
        return (AacAlignment.PREFIX_FRAMES + delay) * 1_000_000L / audio.sampleRate
    }

    private suspend fun remux(
        video: File,
        audio: File,
        output: File,
        durationUs: Long,
        audioShiftUs: Long,
    ) {
        val job = currentCoroutineContext()
        val extractors =
            listOf(video, audio).map { file ->
                MediaExtractor().apply {
                    setDataSource(file.path)
                    selectTrack(0)
                }
            }
        val muxer = MediaMuxer(output.path, MediaMuxer.OutputFormat.MUXER_OUTPUT_MPEG_4)
        var started = false
        var primaryFailure: Throwable? = null
        try {
            val tracks = extractors.map { muxer.addTrack(it.getTrackFormat(0)) }
            muxer.start()
            started = true
            val buffer = ByteBuffer.allocateDirect(4 * 1024 * 1024)
            extractors.forEachIndexed { i, extractor ->
                var writtenSamples = 0
                while (true) {
                    job.ensureActive()
                    buffer.clear()
                    val size = extractor.readSampleData(buffer, 0)
                    if (size < 0) break
                    val pts =
                        if (i == 1)
                            AacAlignment.sourcePts(extractor.sampleTime, audioShiftUs, durationUs)
                                ?: -1L
                        else extractor.sampleTime
                    if (pts >= 0 && pts < durationUs) {
                        val flags =
                            if (extractor.sampleFlags and MediaExtractor.SAMPLE_FLAG_SYNC != 0)
                                MediaCodec.BUFFER_FLAG_KEY_FRAME
                            else 0
                        val info = MediaCodec.BufferInfo().apply { set(0, size, pts, flags) }
                        muxer.writeSampleData(tracks[i], buffer, info)
                        writtenSamples++
                    }
                    extractor.advance()
                }
                require(writtenSamples >= 2) {
                    "Choose a longer clip for this audio/video encoder."
                }
                muxer.writeSampleData(
                    tracks[i],
                    ByteBuffer.allocate(0),
                    MediaCodec.BufferInfo().apply {
                        set(0, 0, durationUs, MediaCodec.BUFFER_FLAG_END_OF_STREAM)
                    },
                )
            }
        } catch (failure: Throwable) {
            primaryFailure = failure
            throw failure
        } finally {
            extractors.forEach { it.release() }
            ExportFinalization.close(
                primaryFailure,
                { if (started) muxer.stop() },
                { muxer.release() },
            )
        }
    }
}
