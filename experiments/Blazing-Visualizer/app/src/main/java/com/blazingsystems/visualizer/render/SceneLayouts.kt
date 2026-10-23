package com.blazingsystems.visualizer.render

import com.blazingsystems.visualizer.project.*
import kotlin.math.*
import kotlinx.serialization.json.*

/** Normalized positions, with uniform physical scale when fitting to a new aspect. */
object SceneLayouts {
    fun fit(scene: Scene, targetAspect: Float): Scene {
        require(targetAspect.isFinite() && targetAspect > 0 && scene.designAspect.isFinite() && scene.designAspect > 0)
        if(scene.originalAvee!=null) return scene.copy(designAspect=targetAspect,
            aveeRenderAspect=scene.aveeRenderAspect ?: scene.designAspect,aveeFrameMode=ExportFrameMode.CONTAIN)
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
        if(scene.originalAvee!=null) return scene.copy(designAspect=targetAspect,
            aveeRenderAspect=scene.aveeRenderAspect ?: scene.designAspect,aveeFrameMode=ExportFrameMode.COVER)
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

    /** Reflow a note display plus keyboard; custom compositions retain cover geometry. */
    fun optimize(scene: Scene, targetAspect: Float): Scene {
        if(scene.originalAvee!=null) return scene.copy(designAspect=targetAspect,aveeRenderAspect=null,aveeFrameMode=null)
        val foreground=scene.layers.filter { it.visible && it.type !in setOf(ElementType.BLUR,ElementType.PARTICLES) }
        val piano=foreground.singleOrNull { it.type==ElementType.PIANO_ROLL && it.transform.height<.4f }
        val main=foreground.singleOrNull { it.type in setOf(ElementType.NOTE_WHEEL,ElementType.MATH_CURVE) }
        if(foreground.size==2 && piano!=null && main!=null) return scene.copy(designAspect=targetAspect,
            layers=scene.layers.map {
                when(it.id) {
                    piano.id -> it.copy(transform=it.transform.copy(x=.5f,y=.86f,width=.94f,height=.24f))
                    main.id -> it.copy(transform=it.transform.copy(x=.5f,y=.39f,width=.94f,height=.72f))
                    else -> it
                }
            })
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
            ExportFrameMode.STRETCH -> source.copy(designAspect = aspect,aveeRenderAspect=null,aveeFrameMode=null)
            ExportFrameMode.OPTIMIZE -> if(project.exportLayout==ExportLayoutMode.SEPARATE) fit(source,aspect) else optimize(source, aspect)
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
