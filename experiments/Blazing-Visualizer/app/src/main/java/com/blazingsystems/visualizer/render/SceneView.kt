package com.blazingsystems.visualizer.render

import android.content.Context
import android.graphics.SurfaceTexture
import android.view.Surface
import android.view.TextureView
import java.io.File

/** A normal view layer; video can sit underneath its transparent pixels in Compose order. */
class SceneView(context: Context) : TextureView(context), TextureView.SurfaceTextureListener {
    private val lock = Object()
    private var current: EvaluatedScene? = null
    private var transparent = false
    private var active: SurfaceRun? = null
    var assets = File(context.filesDir, "assets")

    private class SurfaceRun(val texture: SurfaceTexture, var width: Int, var height: Int) {
        val healthId = PreviewCanvasHealth.available()
        var running = true
        var destroyed = false
        var finished = false
    }

    private data class Frame(
        val scene: EvaluatedScene,
        val width: Int,
        val height: Int,
        val transparent: Boolean,
    )

    init { surfaceTextureListener = this }

    /** Called by AndroidView's UI-thread update; audio remains opaque by default. */
    fun update(scene: EvaluatedScene, transparentBackground: Boolean = false) {
        isOpaque = !transparentBackground
        synchronized(lock) {
            if (current != scene || transparent != transparentBackground) {
                current = scene
                transparent = transparentBackground
                lock.notifyAll()
            }
        }
    }

    override fun onSurfaceTextureAvailable(texture: SurfaceTexture, width: Int, height: Int) {
        val run = SurfaceRun(texture, width, height)
        synchronized(lock) {
            active?.running = false
            active = run
            lock.notifyAll()
        }
        Thread({ render(run) }, "Visualizer preview").start()
    }

    override fun onSurfaceTextureSizeChanged(texture: SurfaceTexture, width: Int, height: Int) {
        synchronized(lock) {
            active?.takeIf { it.texture === texture }?.let {
                it.width = width
                it.height = height
                lock.notifyAll()
            }
        }
    }

    override fun onSurfaceTextureDestroyed(texture: SurfaceTexture): Boolean {
        val releaseNow = synchronized(lock) {
            val run = active?.takeIf { it.texture === texture }
            if (run == null) true else {
                active = null
                run.running = false
                run.destroyed = true
                PreviewCanvasHealth.destroyed(run.healthId)
                lock.notifyAll()
                run.finished
            }
        }
        if (releaseNow) texture.release()
        // The render thread releases after its EGL surface, even if a driver call is still ending.
        return false
    }

    override fun onSurfaceTextureUpdated(texture: SurfaceTexture) = Unit

    private fun nextFrame(run: SurfaceRun, last: Frame?): Frame? = synchronized(lock) {
        while (run.running) {
            val scene = current
            if (scene != null && run.width > 0 && run.height > 0) {
                val next = Frame(scene, run.width, run.height, transparent)
                if (next != last) return@synchronized next
            }
            lock.wait()
        }
        null
    }

    private fun render(run: SurfaceRun) {
        var surface: Surface? = null
        var target: GlTarget? = null
        var renderer: GlSceneRenderer? = null
        try {
            val window = Surface(run.texture).also { surface = it }
            var last: Frame? = null
            while (true) {
                val frame = nextFrame(run, last) ?: break
                if (target?.width != frame.width || target?.height != frame.height) {
                    renderer?.close()
                    renderer = null
                    target?.close()
                    target = null
                    target = GlTarget.encoder(window, frame.width, frame.height)
                    renderer = GlSceneRenderer(assets)
                }
                renderer!!.render(frame.scene, target!!, transparentBackground = frame.transparent)
                target.present()
                PreviewCanvasHealth.presented(run.healthId, frame.scene)
                last = frame
            }
        } catch (failure: Exception) {
            if (!run.destroyed) {
                PreviewCanvasHealth.failed(run.healthId, failure.localizedMessage ?: failure.javaClass.simpleName)
                android.util.Log.e("VisualizerCanvas", "Preview rendering stopped", failure)
            }
            // A disappearing surface may interrupt a frame; its resources still belong to this run.
        } finally {
            try { renderer?.close() } finally {
                try { target?.close() } finally {
                    surface?.release()
                    synchronized(lock) {
                        run.finished = true
                        if (run.destroyed) run.texture.release()
                    }
                }
            }
        }
    }
}
