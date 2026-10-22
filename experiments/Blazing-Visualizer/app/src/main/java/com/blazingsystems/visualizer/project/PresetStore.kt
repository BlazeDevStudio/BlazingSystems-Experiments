package com.blazingsystems.visualizer.project

import java.io.File
import kotlinx.serialization.decodeFromString
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json

class PresetStore(private val file: File) {
    @Synchronized
    fun load(): List<Scene> =
        if (file.isFile) Json.decodeFromString(file.readText()) else emptyList()

    @Synchronized
    fun save(scenes: List<Scene>) = atomicWrite(file, Json.encodeToString(scenes).toByteArray())

    companion object {
        fun upsert(scenes: List<Scene>, scene: Scene) =
            scenes.filterNot { it.id == scene.id } + scene
    }
}
