package com.blazingsystems.visualizer.render

import com.blazingsystems.visualizer.project.*
import kotlin.math.*
import kotlinx.serialization.json.*

/** Normalized positions, with uniform physical scale when fitting to a new aspect. */
object SceneLayouts {
    fun fit(scene: Scene, targetAspect: Float): Scene {
        require(targetAspect.isFinite() && targetAspect > 0 && scene.designAspect.isFinite() && scene.designAspect > 0)
        val sx = min(1f, scene.designAspect / targetAspect)
        val sy = min(1f, targetAspect / scene.designAspect)
        return scene.copy(designAspect = targetAspect, layers = scene.layers.map { layer ->
            val t = layer.transform
            layer.copy(transform = t.copy(x = .5f + (t.x - .5f)*sx, y = .5f + (t.y - .5f)*sy, width = t.width*sx, height = t.height*sy))
        })
    }

    /** Fill the frame, cropping edges instead of shrinking into a letterboxed strip. */
    fun cover(scene: Scene, targetAspect: Float): Scene {
        require(targetAspect.isFinite() && targetAspect > 0 &&
            scene.designAspect.isFinite() && scene.designAspect > 0)
        val sx = max(1f, scene.designAspect / targetAspect)
        val sy = max(1f, targetAspect / scene.designAspect)
        return scene.copy(designAspect = targetAspect, layers = scene.layers.map { layer ->
            val t = layer.transform
            layer.copy(transform = t.copy(
                x = .5f + (t.x - .5f) * sx, y = .5f + (t.y - .5f) * sy,
                width = t.width * sx, height = t.height * sy,
            ))
        })
    }

    /** Invert a viewport-fit transform before storing the user's real edit. */
    fun unfitTransform(display: Transform, sourceAspect: Float, viewportAspect: Float): Transform {
        require(sourceAspect.isFinite() && sourceAspect > 0f &&
            viewportAspect.isFinite() && viewportAspect > 0f)
        val sx = min(1f, sourceAspect / viewportAspect)
        val sy = min(1f, viewportAspect / sourceAspect)
        return display.copy(
            x = .5f + (display.x - .5f) / sx,
            y = .5f + (display.y - .5f) / sy,
            width = (display.width / sx).coerceIn(.001f, 4f),
            height = (display.height / sy).coerceIn(.001f, 4f),
        )
    }

    /** Note-aware cover, anchoring the piano to a 2% safe bottom margin. */
    fun optimize(scene: Scene, targetAspect: Float): Scene {
        val covered = cover(scene, targetAspect)
        return covered.copy(layers = covered.layers.map { layer ->
            if (!layer.visible || layer.type != ElementType.PIANO_ROLL) layer else {
                val t = layer.transform
                layer.copy(transform = t.copy(y = .98f - t.height / 2f))
            }
        })
    }

    fun forExport(project: Project, settings: ExportSettings = project.export): Scene {
        val source = if (project.exportLayout == ExportLayoutMode.SEPARATE) project.scene.copy(
            designAspect = project.exportDesignAspect,
            layers = project.scene.layers.map { it.copy(transform = project.exportTransforms[it.id] ?: it.transform) },
        ) else project.scene
        val aspect = settings.width.toFloat() / settings.height
        return when (project.exportFrameMode) {
            ExportFrameMode.CONTAIN -> fit(source, aspect)
            ExportFrameMode.COVER -> cover(source, aspect)
            ExportFrameMode.STRETCH -> source.copy(designAspect = aspect)
            ExportFrameMode.OPTIMIZE -> optimize(source, aspect)
        }
    }

    fun move(t: Transform, dx: Float, dy: Float) = t.copy(x = (t.x + dx).coerceIn(-.5f, 1.5f), y = (t.y + dy).coerceIn(-.5f, 1.5f))
    fun resize(t: Transform, dw: Float, dh: Float) = t.copy(width = (t.width + dw).coerceIn(.05f, 2f), height = (t.height + dh).coerceIn(.05f, 2f))

    fun hitTest(scene: Scene, x: Float, y: Float, aspect: Float): String? = scene.layers.asReversed().firstOrNull { layer ->
        if (!layer.visible || layer.type in setOf(ElementType.BLUR, ElementType.PARTICLES)) return@firstOrNull false
        val t = layer.transform
        val a = Math.toRadians(t.rotation.toDouble())
        val dx = (x - t.x) * aspect; val dy = y - t.y
        val rx = cos(a)*dx + sin(a)*dy; val ry = -sin(a)*dx + cos(a)*dy
        if (layer.type == ElementType.TEXT) {
            val font = (layer.properties["fontSize"]?.jsonPrimitive?.content?.toFloatOrNull() ?: 24f).coerceIn(4f,160f)
            val count = layer.properties["text"]?.jsonPrimitive?.content?.length ?: 7
            val scale = min(t.width*aspect, t.height)*font/420f
            abs(rx) <= count*.65f*scale/2 && abs(ry) <= scale*1.4f/2
        } else abs(rx) <= t.width*aspect/2 && abs(ry) <= t.height/2
    }?.id
}
