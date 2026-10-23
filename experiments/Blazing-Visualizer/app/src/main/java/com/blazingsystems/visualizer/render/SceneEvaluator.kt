package com.blazingsystems.visualizer.render

import com.blazingsystems.visualizer.analysis.ChordEstimator
import com.blazingsystems.visualizer.project.*
import kotlinx.serialization.json.*

data class EvaluatedLayer(val layer: Layer, val scale: Float)

data class EvaluatedScene(
    val scene: Scene,
    val features: FeatureFrame,
    val sourceTimeUs: Long,
    val layers: List<EvaluatedLayer>,
    val activeNotes: List<NoteEvent>,
    val chord: String?,
)

object SceneEvaluator {
    fun evaluate(scene: Scene, features: FeatureFrame, sourceTimeUs: Long): EvaluatedScene {
        val active = features.notes.filter { it.startUs <= sourceTimeUs && sourceTimeUs < it.endUs }
        val layers =
            scene.layers
                .filter { it.visible }
                .map { layer ->
                    var scale = 1f
                    val routed = active.filter { layer.noteRouting.allows(it.pitch) }
                    layer.bindings.forEach { binding ->
                        val value =
                            when (binding.source) {
                                BindingSource.RMS -> features.rms
                                BindingSource.NOTE_ENERGY ->
                                    routed.maxOfOrNull { it.amplitude } ?: 0f
                                BindingSource.SPECTRUM_BAND ->
                                    features.spectrum.getOrElse(binding.band) { 0f }
                            }
                        if (binding.property == "scale")
                            scale += value * binding.amount * scene.animationIntensity
                    }
                    EvaluatedLayer(layer, scale.coerceIn(.05f, 6f))
                }
        return EvaluatedScene(
            scene,
            features,
            sourceTimeUs,
            layers,
            active,
            ChordEstimator.estimate(active, sourceTimeUs),
        )
    }
}

object BuiltinScenes {
    private fun props(vararg p: Pair<String, String>) =
        JsonObject(p.associate { it.first to JsonPrimitive(it.second) })

    fun defaultSpectrum() =
        Scene(
            id = "builtin-orbit",
            name = "Blazing orbit",
            layers =
                listOf(
                    Layer(type = ElementType.BLUR, properties = props("color" to "#FF43228E")),
                    Layer(type = ElementType.PARTICLES),
                    Layer(
                        type = ElementType.SPECTRUM,
                        transform = Transform(y = .47f, width = .8f, height = .8f),
                        properties = props("path" to "circle"),
                    ),
                    Layer(
                        type = ElementType.TEXT,
                        transform = Transform(y = .47f),
                        properties = props("text" to "BLAZING", "fontSize" to "26"),
                    ),
                    Layer(
                        type = ElementType.WAVEFORM,
                        transform = Transform(y = .85f, height = .1f),
                    ),
                ),
        )

    fun noteWheel() =
        Scene(
            id = "builtin-compass",
            name = "Harmonic compass",
            layers =
                listOf(
                    Layer(type = ElementType.BLUR),
                    Layer(type = ElementType.PARTICLES),
                    Layer(
                        type = ElementType.NOTE_WHEEL,
                        transform = Transform(y = .4f, width = .82f, height = .65f),
                    ),
                    Layer(
                        type = ElementType.PIANO_ROLL,
                        transform = Transform(y = .84f, width = .9f, height = .18f),
                    ),
                ),
        )

    fun pianoRoll() =
        Scene(
            id = "builtin-runway",
            name = "Note runway",
            layers =
                listOf(
                    Layer(type = ElementType.BLUR),
                    Layer(
                        type = ElementType.PIANO_ROLL,
                        transform = Transform(y = .55f, width = .94f, height = .8f),
                    ),
                ),
        )

    fun mathematical(mode: MathVisualMode) = Scene(
        id = "builtin-math-${mode.name.lowercase()}",
        name = when (mode) {
            MathVisualMode.LISSAJOUS -> "Harmonic flow"
            MathVisualMode.ORBITS -> "Orbital voices"
            MathVisualMode.WAVES -> "Wave garden"
            MathVisualMode.CHORD_3D -> "Chord sculpture"
            MathVisualMode.RHYTHM -> "Rhythm geometry"
            MathVisualMode.RADIAL -> "Pitch contours"
        },
        layers = listOf(
            Layer(type = ElementType.BLUR),
            Layer(
                type = ElementType.MATH_CURVE,
                transform = Transform(y = .43f, width = .86f, height = .68f),
                properties = props("mode" to mode.name),
            ),
            Layer(
                type = ElementType.PIANO_ROLL,
                transform = Transform(y = .85f, width = .92f, height = .18f),
            ),
        ),
    )

    fun all() = listOf(defaultSpectrum(), noteWheel(), pianoRoll()) +
        listOf(MathVisualMode.LISSAJOUS,MathVisualMode.ORBITS,MathVisualMode.WAVES).map(::mathematical) + MotionScenes.all()
}
