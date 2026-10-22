package com.blazingsystems.visualizer.packs

import com.blazingsystems.visualizer.project.*
import java.io.*
import java.security.MessageDigest
import java.util.UUID
import java.util.zip.*
import kotlinx.serialization.Serializable
import kotlinx.serialization.decodeFromString
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.*

@Serializable
data class VisualizerPack(
    val schemaVersion: Int = 1,
    val scene: Scene,
    val assets: Map<String, String> = emptyMap(),
)

data class CompatibilityReport(
    val supported: List<String> = emptyList(),
    val unsupported: List<String> = emptyList(),
    val missingAssets: List<String> = emptyList(),
) {
    val requiresPartialAcceptance
        get() = unsupported.isNotEmpty() || missingAssets.isNotEmpty()
}

data class ImportResult(
    val scene: Scene,
    val assetDirectory: File,
    val report: CompatibilityReport = CompatibilityReport(),
    val originalFile: File? = null,
)

fun interface AssetResolver {
    fun open(relativePath: String): InputStream
}

object AssetChecks {
    fun validateImage(file: File) {
        val options = android.graphics.BitmapFactory.Options().apply { inJustDecodeBounds = true }
        android.graphics.BitmapFactory.decodeFile(file.path, options)
        require(options.outWidth in 1..4096 && options.outHeight in 1..4096) {
            NativePackCodec.LIMITS
        }
    }
}

fun boundedJson(text: String): JsonElement {
    require(text.length <= 2 * 1024 * 1024) { "JSON data is too large" }
    var depth = 0
    var quoted = false
    var escaped = false
    for (character in text) {
        if (quoted) {
            if (escaped) escaped = false
            else if (character == '\\') escaped = true else if (character == '"') quoted = false
        } else
            when (character) {
                '"' -> quoted = true
                '[',
                '{' -> {
                    depth++
                    require(depth <= 64) { "JSON nesting exceeds 64 levels" }
                }
                ']',
                '}' -> depth--
            }
    }
    return Json.parseToJsonElement(text)
}

class NativePackCodec {
    private val json = Json {
        encodeDefaults = true
        ignoreUnknownKeys = true
    }

    fun write(pack: VisualizerPack, assets: AssetResolver, output: OutputStream) {
        require(pack.schemaVersion == 1)
        validateScene(pack.scene)
        val refs =
            pack.scene.layers
                .mapNotNull { it.properties["asset"]?.jsonPrimitive?.content }
                .toSet() + pack.assets.keys
        val checksums = linkedMapOf<String, String>()
        var total = 0L
        ZipOutputStream(output).use { zip ->
            fun entry(name: String, bytes: ByteArray) {
                zip.putNextEntry(ZipEntry(name).apply { time = 0 })
                zip.write(bytes)
                zip.closeEntry()
            }
            entry("scene.json", json.encodeToString(pack.scene).toByteArray())
            for (path in refs.sorted()) {
                safePath(path)
                zip.putNextEntry(ZipEntry("assets/$path").apply { time = 0 })
                val hash = MessageDigest.getInstance("SHA-256")
                assets.open(path).use { input ->
                    val buffer = ByteArray(65536)
                    while (true) {
                        val count = input.read(buffer)
                        if (count < 0) break
                        total += count
                        require(total <= MAX_EXPANDED) { LIMITS }
                        hash.update(buffer, 0, count)
                        zip.write(buffer, 0, count)
                    }
                }
                zip.closeEntry()
                checksums[path] = hash.digest().joinToString("") { "%02x".format(it) }
            }
            entry(
                "manifest.json",
                buildJsonObject {
                    put("schemaVersion", 1)
                    put("scenePath", "scene.json")
                    put("assets", JsonObject(checksums.mapValues { JsonPrimitive(it.value) }))
                }
                    .toString()
                    .toByteArray(),
            )
        }
    }

    fun read(input: InputStream, destination: File): ImportResult {
        destination.mkdirs()
        val staging = File(destination, ".import-${UUID.randomUUID()}").apply { mkdirs() }
        try {
            extract(input, staging)
            val manifest = File(staging, "manifest.json")
            require(manifest.isFile && manifest.length() <= 2 * 1024 * 1024) {
                "A schema-1 manifest.json is required"
            }
            val metadata = boundedJson(manifest.readText()).jsonObject
            require(metadata["schemaVersion"]?.jsonPrimitive?.intOrNull == 1) {
                "Unsupported preset schema; version 1 is required"
            }
            require(metadata["scenePath"]?.jsonPrimitive?.content == "scene.json")
            val sceneFile = File(staging, "scene.json")
            require(sceneFile.isFile && sceneFile.length() <= 2 * 1024 * 1024) {
                "Scene missing or too large"
            }
            boundedJson(sceneFile.readText())
            val scene = json.decodeFromString<Scene>(sceneFile.readText())
            validateScene(scene)
            val assets = metadata["assets"]?.jsonObject ?: JsonObject(emptyMap())
            for ((name, checksum) in assets) {
                safePath(name)
                val file = File(staging, "assets/$name")
                require(file.isFile) { "Missing asset: $name" }
                val hash = MessageDigest.getInstance("SHA-256")
                file.inputStream().use { stream ->
                    val buffer = ByteArray(65536)
                    while (true) {
                        val count = stream.read(buffer)
                        if (count < 0) break
                        hash.update(buffer, 0, count)
                    }
                }
                require(
                    hash.digest().joinToString("") { "%02x".format(it) } ==
                        checksum.jsonPrimitive.content,
                ) {
                    "Asset checksum mismatch: $name"
                }
            }
            for (layer in scene.layers) {
                val path = layer.properties["asset"]?.jsonPrimitive?.content ?: continue
                require(path in assets) { "Unlisted asset: $path" }
                if (layer.type == ElementType.IMAGE)
                    AssetChecks.validateImage(File(staging, "assets/$path"))
            }
            val installed = File(destination, UUID.randomUUID().toString())
            check(staging.renameTo(installed)) { "Could not finalize import" }
            return ImportResult(scene, File(installed, "assets"))
        } catch (failure: Throwable) {
            staging.deleteRecursively()
            throw failure
        }
    }

    companion object {
        const val MAX_INPUT = 64L * 1024 * 1024
        const val MAX_EXPANDED = 128L * 1024 * 1024
        const val LIMITS =
            "Preset limits: 64 MiB archive, 128 MiB expanded, 1,024 entries, images up to 4,096 pixels per edge"

        fun safePath(path: String) {
            require(
                path.isNotBlank() &&
                    path.length <= 240 &&
                    !path.startsWith('/') &&
                    !path.contains('\\') &&
                    !path.contains(':') &&
                    path.split('/').none { it.isEmpty() || it == "." || it == ".." },
            ) {
                "Unsafe archive path: $path"
            }
        }

        fun extract(input: InputStream, destination: File) {
            var compressed = 0L
            var expanded = 0L
            var count = 0
            val names = HashSet<String>()
            val bounded =
                object : FilterInputStream(input) {
                    override fun read(): Int {
                        val value = super.read()
                        if (value >= 0) compressed++
                        require(compressed <= MAX_INPUT) { LIMITS }
                        return value
                    }

                    override fun read(bytes: ByteArray, offset: Int, length: Int): Int {
                        val n = super.read(bytes, offset, length)
                        if (n > 0) compressed += n
                        require(compressed <= MAX_INPUT) { LIMITS }
                        return n
                    }
                }
            ZipInputStream(bounded).use { zip ->
                while (true) {
                    val entry = zip.nextEntry ?: break
                    require(++count <= 1024) { LIMITS }
                    val name = entry.name.trimEnd('/')
                    safePath(name)
                    require(names.add(name)) { "Duplicate archive path" }
                    val file = File(destination, name)
                    require(file.canonicalPath.startsWith(destination.canonicalPath + "/"))
                    if (entry.isDirectory) file.mkdirs()
                    else {
                        file.parentFile!!.mkdirs()
                        file.outputStream().buffered().use { out ->
                            val buffer = ByteArray(65536)
                            while (true) {
                                val n = zip.read(buffer)
                                if (n < 0) break
                                expanded += n
                                require(expanded <= MAX_EXPANDED) { LIMITS }
                                out.write(buffer, 0, n)
                            }
                        }
                    }
                    zip.closeEntry()
                }
            }
        }

        fun validateScene(scene: Scene) {
            require(
                scene.name.length <= 200 &&
                    scene.layers.size <= 128 &&
                    scene.layers.map { it.id }.distinct().size == scene.layers.size,
            ) {
                "Invalid layer count or IDs"
            }
            require(scene.animationIntensity.isFinite() && scene.animationIntensity in 0f..2f)
            require(scene.pianoIntensity.isFinite() && scene.pianoIntensity in 0f..2f)
            require(scene.designAspect.isFinite() && scene.designAspect in .1f..10f)
            require(scene.aveeAudio.toString().length <= 4096)
            require(scene.backgroundColor.matches(Regex("#[0-9a-fA-F]{6}([0-9a-fA-F]{2})?")))
            scene.paletteColor?.let { require(it.matches(Regex("#[0-9a-fA-F]{6}([0-9a-fA-F]{2})?"))) }
            scene.layers.forEach { layer ->
                require(layer.noteRouting.isValid()) { "Invalid MIDI note range" }
                val t = layer.transform
                require(
                    listOf(t.x, t.y, t.width, t.height, t.rotation).all(Float::isFinite) &&
                        t.x in -4f..4f &&
                        t.y in -4f..4f &&
                        t.width in .001f..4f &&
                        t.height in .001f..4f,
                ) {
                    "Invalid transform"
                }
                require(layer.properties.toString().length <= 16384 && layer.name.length <= 200)
                layer.properties["asset"]?.jsonPrimitive?.content?.let(::safePath)
                require(
                    layer.bindings.all {
                        it.property == "scale" &&
                            it.amount.isFinite() &&
                            it.amount in -10f..10f &&
                            it.band in 0..1023
                    },
                ) {
                    "Unsupported binding"
                }
            }
        }
    }
}

object AveePresetAdapter {
    /** Many presets are plain JSON; others are ZIPs holding JSON or text .viz.
     * Non-JSON proprietary .viz is rejected explicitly rather than misrendered.
     * Existing archive bounds, traversal and image guards are preserved.
     */
    fun loadPresetText(original: File, assets: File): String {
        val zipped = original.inputStream().use { it.read() == 0x50 && it.read() == 0x4b }
        val file = if (zipped) {
            NativePackCodec.extract(original.inputStream(), assets)
            val candidates = assets.walkTopDown().filter {
                it.isFile && it.extension.lowercase() in setOf("json", "txt", "viz") &&
                    it.length() in 2..(2L * 1024 * 1024) &&
                    it.inputStream().buffered().use { stream ->
                        var first = stream.read()
                        while (first in listOf(9, 10, 13, 32)) first = stream.read()
                        first == '{'.code
                    }
            }.toList()
            require(candidates.size == 1) {
                "This archive needs exactly one JSON Avee preset. Binary or multiple .viz files " +
                    "cannot be imported automatically; extract and select one supported template."
            }
            candidates.single()
        } else original
        require(file.length() <= 2L * 1024 * 1024) { "Avee preset JSON exceeds 2 MiB" }
        val text = file.readText()
        require(text.trimStart().startsWith("{")) {
            "Unsupported binary Avee .viz format. A JSON-compatible preset is required."
        }
        return text
    }

    fun read(text: String, assets: File): ImportResult {
        val root = boundedJson(text).jsonObject
        val compositions = root["compositions"]?.let {
            require(it is JsonArray) { "Avee compositions must be an array" }
            it
        } ?: if (root["elements"] is JsonArray) JsonArray(listOf(JsonObject(root)))
            else error("No Avee compositions or elements found in this preset")
        val supported = mutableListOf<String>()
        val unsupported = mutableListOf<String>()
        val missing = mutableListOf<String>()
        val layers = mutableListOf<Layer>()
        var audioProvider = JsonObject(emptyMap())
        var providerCount = 0
        if (compositions.size != 1) unsupported += "Multiple compositions / offscreen passes"
        for (composition in compositions) for (element in
            composition.jsonObject["elements"]?.jsonArray ?: JsonArray(emptyList())) {
            val item = element.jsonObject
            fun value(key: String) = item[key]?.let {
                if (it is JsonObject && "v" in it) it["v"] else it
            }
            val type =
                item["objType"]?.jsonPrimitive?.content
                    ?: item["v"]?.jsonPrimitive?.content
                    ?: "Unknown"
            if (type == "AudioProvider") {
                providerCount++
                if (providerCount == 1) {
                    audioProvider = buildJsonObject {
                        listOf("sampleProvider", "sampleOutCount", "lowerHz", "higherHz",
                            "hzLinearFactor", "smooth", "filterRadius", "filterStrength",
                            "lowerFreqMagnitude", "outputMultiplier", "beatSmooth").forEach { key ->
                            value(key)?.let { if (it is JsonPrimitive) put(key, it) }
                        }
                    }
                    supported += "AudioProvider FFT band mapping and response parameters"
                } else unsupported += "Multiple AudioProvider routing is approximated"
                continue
            }
            if (type == "AppLogo") {
                supported += "Source-app branding intentionally excluded"
                continue
            }
            val native =
                when (type) {
                    "Text" -> ElementType.TEXT
                    "Image" -> ElementType.IMAGE
                    "Bars", "Spectrum" -> ElementType.SPECTRUM
                    "Waveform" -> ElementType.WAVEFORM
                    "Particles" -> ElementType.PARTICLES
                    "BlurEffect" -> ElementType.BLUR
                    "MotionBlurEffect" -> {
                        unsupported += "Temporal motion blur approximated by a glow"
                        ElementType.BLUR
                    }
                    else -> {
                        unsupported += "Element $type"
                        continue
                    }
                }
            val known =
                setOf(
                    "v",
                    "objType",
                    "ver",
                    "_id",
                    "_name",
                    "visible",
                    "position",
                    "scale",
                    "rotation",
                    "text",
                    "fontSize",
                    "color",
                    "customImage",
                    "ShapePath",
                )
            item.keys.filterNot { it in known }.forEach { unsupported += "$type.$it" }
            fun pair(key: String, default: Float): List<Float> {
                val pair = when (val v = value(key)) {
                    is JsonArray -> v.mapNotNull {
                        (it as? JsonPrimitive)?.content?.toFloatOrNull()
                    }
                    is JsonObject -> listOfNotNull(
                        (v["x"] as? JsonPrimitive)?.content?.toFloatOrNull(),
                        (v["y"] as? JsonPrimitive)?.content?.toFloatOrNull(),
                    )
                    is JsonPrimitive -> v.content.trim().split(Regex("[,;\\s]+"))
                        .mapNotNull { it.toFloatOrNull() }
                    else -> emptyList()
                }
                return pair.takeIf { it.size == 2 && it.all(Float::isFinite) }
                    ?: listOf(default, default)
            }
            val position = pair("position", .5f)
            val scale = pair("scale", 1f)
            val rawRotation = (value("rotation") as? JsonPrimitive)?.floatOrNull
            val rotation = rawRotation?.takeIf { it.isFinite() && it in -180f..180f } ?: 0f
            if (rawRotation != null && rawRotation != rotation)
                unsupported += "$type.rotation outside supported degrees"
            val properties = buildJsonObject {
                value("text")?.let { put("text", it) }
                value("fontSize")?.let { put("fontSize", it) }
                value("color")?.jsonPrimitive?.longOrNull?.let {
                    put("color", "#%08X".format(it.toInt()))
                }
                value("customImage")
                    ?.jsonPrimitive
                    ?.content
                    ?.takeIf { it.isNotBlank() }
                    ?.let { path ->
                        if (path.startsWith("local:")) {
                            val relative = path.removePrefix("local:")
                            NativePackCodec.safePath(relative)
                            val file = File(assets, relative)
                            if (file.isFile) AssetChecks.validateImage(file) else missing += path
                            put("asset", relative)
                        } else {
                            unsupported += "Image resource $path"
                            missing += path
                        }
                    }
                if (native == ElementType.SPECTRUM) {
                    put(
                        "path",
                        if (value("ShapePath")?.jsonPrimitive?.content == "Circle") "circle"
                        else "bars",
                    )
                    unsupported += "Bars shader / DSP styling is approximated"
                }
            }
            supported += "$type static transform and visibility"
            layers +=
                Layer(
                    type = native,
                    name = item["_name"]?.jsonPrimitive?.content ?: type,
                    visible = when ((value("visible") as? JsonPrimitive)?.content?.lowercase()) {
                        "0", "false" -> false
                        else -> true
                    },
                    transform =
                        Transform(
                            position[0],
                            position[1],
                            scale[0].coerceIn(.001f, 4f),
                            scale[1].coerceIn(.001f, 4f),
                            rotation,
                        ),
                    properties = properties,
                )
         }
        unsupported += "Avee font metrics, blending and DSP may look different"
        return ImportResult(
            Scene(name = "Imported Avee preset", layers = layers, aveeAudio = audioProvider),
            assets,
            CompatibilityReport(supported, unsupported.distinct(), missing.distinct()),
        )
    }
}
