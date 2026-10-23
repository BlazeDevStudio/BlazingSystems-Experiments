package com.blazingsystems.visualizer.audio

import android.content.Context
import android.net.Uri
import com.blazingsystems.visualizer.avee.AveeSpectrumAnalyzer
import com.blazingsystems.visualizer.avee.Spectrum2Analyzer
import com.blazingsystems.visualizer.project.*
import java.io.*
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.security.MessageDigest
import kotlinx.coroutines.*
import kotlinx.serialization.Serializable
import kotlinx.serialization.decodeFromString
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.*
import kotlin.math.*

@Serializable
data class DecodedAudio(
    val hash: String,
    val sampleRate: Int,
    val channels: Int,
    val frames: Long,
    val rootPath: String,
    val hasAudio: Boolean = true,
) {
    val pcmFile
        get() = File(rootPath, "original.pcm")

    val monoFile
        get() = File(rootPath, "mono.f32")

    val durationUs
        get() = frames * 1_000_000 / sampleRate
}

class AudioRepository(private val context: Context) {
    private val root = File(context.cacheDir, "audio-v1").apply { mkdirs() }
    private val leases = DecodedAudioLeases(root)

    /** Prefer acquireDecoded when the hash is not already known: it pins before cache lookup. */
    fun retain(hash: String): AutoCloseable = leases.retain(hash)

    /** Analysis results are stored separately; temporary PCM must not grow without a bound. */
    fun discardDecoded(hash: String) {
        leases.discard(hash)
    }

    fun compactDecodedCache(protected: Set<String>, limitBytes: Long = 256L * 1024 * 1024) {
        val folders = root.listFiles().orEmpty()
            .filter { it.isDirectory && it.name.matches(Regex("[0-9a-f]{64}")) }
        fun size(directory: File) = directory.walkTopDown()
            .filter { it.isFile }.sumOf { it.length() }
        var total = folders.sumOf(::size)
        for (folder in folders.filterNot { it.name in protected }.sortedBy { it.lastModified() }) {
            if (total <= limitBytes) break
            val bytes = size(folder)
            if (leases.discard(folder.name)) total -= bytes
        }
    }

    suspend fun get(source: SourceRef, progress: (Float) -> Unit = {}): DecodedAudio =
        acquireDecoded(source, progress).use { it.audio }

    suspend fun acquireDecoded(
        source: SourceRef,
        progress: (Float) -> Unit = {},
    ): DecodedAudioLease {
        var acquired: DecodedAudioLease? = null
        try {
            return withContext(Dispatchers.IO) {
                leases.decoding {
                    val digest = contentHash(source)
                    val retention = retain(digest)
                    try {
                        DecodedAudioLease(decode(source, digest, progress), retention).also {
                            acquired = it
                        }
                    } catch (failure: Throwable) {
                        retention.close()
                        throw failure
                    }
                }
            }
        } catch (failure: Throwable) {
            // withContext may cancel while returning an otherwise successful acquisition.
            acquired?.close()
            throw failure
        }
    }

    suspend fun sourceHash(source: SourceRef): String = withContext(Dispatchers.IO) { contentHash(source) }

    private suspend fun contentHash(source: SourceRef): String {
        val hash = MessageDigest.getInstance("SHA-256")
        context.contentResolver.openInputStream(Uri.parse(source.uri))!!.use { input ->
            val bytes = ByteArray(65536)
            while (true) {
                currentCoroutineContext().ensureActive()
                val count = input.read(bytes)
                if (count < 0) break
                hash.update(bytes, 0, count)
            }
        }
        return hash.digest().joinToString("") { "%02x".format(it) }
    }

    private suspend fun decode(
        source: SourceRef,
        digest: String,
        progress: (Float) -> Unit,
    ): DecodedAudio {
        val folder = File(root, digest)
        val metadata = File(folder, "audio.json")
        if (metadata.isFile) {
            val audio =
                Json.decodeFromString<DecodedAudio>(metadata.readText())
                    .copy(rootPath = folder.path)
            if (audio.pcmFile.isFile && audio.monoFile.isFile) return audio
            folder.deleteRecursively()
        }
        val staging = File(root, "$digest.pending")
        staging.deleteRecursively()
        staging.mkdirs()
        try {
            var resampler: PcmResampler? = null
            var rate = 0
            var channels = 0
            var frames = 0L
            var hasAudio = true
            DataOutputStream(BufferedOutputStream(FileOutputStream(File(staging, "mono.f32"))))
                .use { mono ->
                    BufferedOutputStream(FileOutputStream(File(staging, "original.pcm"))).use {
                        pcm ->
                        PcmDecoder(context).decode(Uri.parse(source.uri)).collect { chunk ->
                            currentCoroutineContext().ensureActive()
                            if (resampler == null) {
                                rate = chunk.sampleRate
                                channels = chunk.channels
                                resampler = PcmResampler(rate, channels)
                                hasAudio = !chunk.synthesizedSilence
                            }
                            require(rate == chunk.sampleRate && channels == chunk.channels) {
                                "Audio format changed mid-track"
                            }
                            val bytes =
                                ByteBuffer.allocate(chunk.samples.size * 2)
                                    .order(ByteOrder.LITTLE_ENDIAN)
                            chunk.samples.forEach {
                                bytes.putShort((it.coerceIn(-1f, 1f) * 32767).toInt().toShort())
                            }
                            pcm.write(bytes.array())
                            resampler!!.feed(chunk.samples).forEach {
                                mono.writeInt(
                                    Integer.reverseBytes(java.lang.Float.floatToRawIntBits(it)),
                                )
                            }
                            frames += chunk.samples.size / channels
                            progress(
                                (frames * 1_000_000f /
                                        rate /
                                        source.durationUs.coerceAtLeast(1))
                                    .coerceIn(0f, 1f),
                            )
                        }
                        resampler?.feed(FloatArray(0), true)?.forEach {
                            mono.writeInt(
                                Integer.reverseBytes(java.lang.Float.floatToRawIntBits(it)),
                            )
                        }
                    }
                }
            require(frames > 0) { "The track is empty" }
            val decoded = DecodedAudio(digest, rate, channels, frames, folder.path, hasAudio)
            File(staging, "audio.json").writeText(Json.encodeToString(decoded))
            check(staging.renameTo(folder)) { "Could not finalize decoded audio" }
            return decoded
        } catch (failure: Throwable) {
            staging.deleteRecursively()
            throw failure
        }
    }
}

class AudioFeatures(private val audio: DecodedAudio) : AutoCloseable {
    private val file = RandomAccessFile(audio.monoFile, "r")
    private val analyzer = AveeSpectrumAnalyzer()
    private var bank: Spectrum2Analyzer?=null
    private val targets=linkedMapOf<Long,List<Float>>()
    private fun preceding(timeUs: Long,count: Int): FloatArray {
        val start=timeUs.coerceAtLeast(0)*22050/1_000_000-count
        val padding=(-start).coerceIn(0,count.toLong()).toInt()
        file.seek(start.coerceAtLeast(0)*4)
        val bytes=ByteArray((count-padding)*4)
        var received=0
        while(received<bytes.size) {
            val n=file.read(bytes,received,bytes.size-received);if(n<0) break;received+=n
        }
        val buffer=ByteBuffer.wrap(bytes).order(ByteOrder.LITTLE_ENDIAN)
        return FloatArray(count) { i -> if(i>=padding && (i-padding)*4+4<=received) buffer.float else 0f }
    }
    private fun configured(timeUs: Long,profile: JsonObject): Pair<List<Float>,Float> {
        if(bank?.settings!=profile) { bank=Spectrum2Analyzer(profile);targets.clear() }
        val b=bank!!;val tick=timeUs.coerceAtLeast(0)/20_000;val blend=.4*b.response
        val history=ceil(8/blend).toInt().coerceIn(12,64)
        val values=DoubleArray(b.count);var weight=1.0;var total=0.0
        for(age in 0 until history) {
            val key=tick-age
            val target=if(key<0) null else targets[key] ?: b.analyze(preceding(key*20_000,b.inputCount)).also {
                targets[key]=it;if(targets.size>160) targets.remove(targets.keys.first())
            }
            if(target!=null) for(i in values.indices) values[i]+=target[i]*weight
            total+=weight;weight*=1-blend
        }
        val valuesOut=values.map { (it/total).toFloat() }
        return valuesOut to b.beat(valuesOut)
    }

    @Synchronized
    fun at(timeUs: Long, notes: List<NoteEvent> = emptyList(),profile: JsonObject=JsonObject(emptyMap())): FeatureFrame {
        val start = (timeUs.coerceAtLeast(0) * 22050 / 1_000_000).coerceAtMost(file.length() / 4)
        file.seek(start * 4)
        val bytes = ByteArray(2048 * 4)
        val count = file.read(bytes)
        val buffer = ByteBuffer.wrap(bytes).order(ByteOrder.LITTLE_ENDIAN)
        val pcm = FloatArray(2048) { if (it * 4 + 4 <= count) buffer.float else 0f }
        val f = analyzer.analyze(pcm, 22050)
        val extra=if(profile["sampleProvider"]?.jsonPrimitive?.content=="Spectrum2") configured(timeUs,profile)
            else emptyList<Float>() to f.rms.coerceIn(0f,1f)
        return FeatureFrame(timeUs, f.rms, f.spectrum, f.waveform, notes,aveeSpectrum=extra.first,beat=extra.second)
    }

    @Synchronized override fun close() = file.close()
}
