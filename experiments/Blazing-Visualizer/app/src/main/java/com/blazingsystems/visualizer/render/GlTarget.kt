package com.blazingsystems.visualizer.render

import android.opengl.*
import android.view.Surface
import java.nio.ByteBuffer

class GlTarget private constructor(val width: Int, val height: Int, surface: Surface?) :
    AutoCloseable {
    private val display = EGL14.eglGetDisplay(EGL14.EGL_DEFAULT_DISPLAY)
    private var context = EGL14.EGL_NO_CONTEXT
    private var eglSurface = EGL14.EGL_NO_SURFACE

    init {
        check(width > 0 && height > 0)
        check(EGL14.eglInitialize(display, IntArray(2), 0, IntArray(2), 1))
        val config = arrayOfNulls<android.opengl.EGLConfig>(1)
        val count = IntArray(1)
        val attributes =
            mutableListOf(
                EGL14.EGL_RED_SIZE,
                8,
                EGL14.EGL_GREEN_SIZE,
                8,
                EGL14.EGL_BLUE_SIZE,
                8,
                EGL14.EGL_ALPHA_SIZE,
                8,
                EGL14.EGL_RENDERABLE_TYPE,
                EGL14.EGL_OPENGL_ES2_BIT,
                EGL14.EGL_SURFACE_TYPE,
                if (surface == null) EGL14.EGL_PBUFFER_BIT else EGL14.EGL_WINDOW_BIT,
            )
        if (surface != null) attributes += listOf(0x3142, 1)
        attributes += EGL14.EGL_NONE
        check(
            EGL14.eglChooseConfig(display, attributes.toIntArray(), 0, config, 0, 1, count, 0) &&
                count[0] > 0,
        ) {
            "No EGL configuration"
        }
        context =
            EGL14.eglCreateContext(
                display,
                config[0],
                EGL14.EGL_NO_CONTEXT,
                intArrayOf(EGL14.EGL_CONTEXT_CLIENT_VERSION, 2, EGL14.EGL_NONE),
                0,
            )
        check(context != EGL14.EGL_NO_CONTEXT)
        eglSurface =
            if (surface == null)
                EGL14.eglCreatePbufferSurface(
                    display,
                    config[0],
                    intArrayOf(EGL14.EGL_WIDTH, width, EGL14.EGL_HEIGHT, height, EGL14.EGL_NONE),
                    0,
                )
            else
                EGL14.eglCreateWindowSurface(
                    display,
                    config[0],
                    surface,
                    intArrayOf(EGL14.EGL_NONE),
                    0,
                )
        check(eglSurface != EGL14.EGL_NO_SURFACE)
        makeCurrent()
    }

    fun makeCurrent() {
        check(EGL14.eglMakeCurrent(display, eglSurface, eglSurface, context)) {
            "EGL context unavailable"
        }
    }

    fun present(presentationTimeUs: Long = 0) {
        EGLExt.eglPresentationTimeANDROID(display, eglSurface, presentationTimeUs * 1000)
        check(EGL14.eglSwapBuffers(display, eglSurface)) { "EGL frame could not be presented" }
    }

    fun readPixels(): ByteArray {
        makeCurrent()
        val b = ByteBuffer.allocateDirect(width * height * 4)
        GLES20.glReadPixels(0, 0, width, height, GLES20.GL_RGBA, GLES20.GL_UNSIGNED_BYTE, b)
        return ByteArray(b.capacity()).also { b.get(it) }
    }

    override fun close() {
        EGL14.eglMakeCurrent(
            display,
            EGL14.EGL_NO_SURFACE,
            EGL14.EGL_NO_SURFACE,
            EGL14.EGL_NO_CONTEXT,
        )
        if (eglSurface != EGL14.EGL_NO_SURFACE) EGL14.eglDestroySurface(display, eglSurface)
        if (context != EGL14.EGL_NO_CONTEXT) EGL14.eglDestroyContext(display, context)
        EGL14.eglReleaseThread()
        EGL14.eglTerminate(display)
    }

    companion object {
        fun pbuffer(width: Int, height: Int) = GlTarget(width, height, null)

        fun encoder(surface: Surface, width: Int, height: Int) = GlTarget(width, height, surface)
    }
}
