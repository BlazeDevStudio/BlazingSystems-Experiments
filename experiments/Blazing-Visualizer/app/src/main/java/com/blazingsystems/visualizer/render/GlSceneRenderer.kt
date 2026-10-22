package com.blazingsystems.visualizer.render

import android.graphics.*
import android.opengl.*
import java.io.File
import java.nio.*

class GlSceneRenderer(assets: File) : AutoCloseable {
    private val painter = ScenePainter(assets)
    private var bitmap: Bitmap? = null
    private var program = 0
    private var texture = 0
    private val vertices =
        ByteBuffer.allocateDirect(16 * 4).order(ByteOrder.nativeOrder()).asFloatBuffer().apply {
            put(floatArrayOf(-1f, -1f, 0f, 1f, 1f, -1f, 1f, 1f, -1f, 1f, 0f, 0f, 1f, 1f, 1f, 0f))
            position(0)
        }

    fun render(scene: EvaluatedScene, target: GlTarget) {
        target.makeCurrent()
        if (program == 0) {
            fun shader(type: Int, source: String): Int {
                val s = GLES20.glCreateShader(type)
                GLES20.glShaderSource(s, source)
                GLES20.glCompileShader(s)
                val ok = IntArray(1)
                GLES20.glGetShaderiv(s, GLES20.GL_COMPILE_STATUS, ok, 0)
                check(ok[0] != 0) { GLES20.glGetShaderInfoLog(s) }
                return s
            }
            val v =
                shader(
                    GLES20.GL_VERTEX_SHADER,
                    "attribute vec2 p; attribute vec2 uv; varying vec2 tex; void main(){gl_Position=vec4(p,0.,1.);tex=uv;}",
                )
            val f =
                shader(
                    GLES20.GL_FRAGMENT_SHADER,
                    "precision mediump float; uniform sampler2D img; varying vec2 tex; void main(){gl_FragColor=texture2D(img,tex);}",
                )
            program = GLES20.glCreateProgram()
            GLES20.glAttachShader(program, v)
            GLES20.glAttachShader(program, f)
            GLES20.glLinkProgram(program)
            GLES20.glDeleteShader(v)
            GLES20.glDeleteShader(f)
            val ok = IntArray(1)
            GLES20.glGetProgramiv(program, GLES20.GL_LINK_STATUS, ok, 0)
            check(ok[0] != 0)
            val ids = IntArray(1)
            GLES20.glGenTextures(1, ids, 0)
            texture = ids[0]
        }
        if (bitmap?.width != target.width || bitmap?.height != target.height) {
            bitmap?.recycle()
            bitmap = Bitmap.createBitmap(target.width, target.height, Bitmap.Config.ARGB_8888)
        }
        painter.draw(Canvas(bitmap!!), scene, target.width, target.height)
        GLES20.glViewport(0, 0, target.width, target.height)
        GLES20.glUseProgram(program)
        GLES20.glActiveTexture(GLES20.GL_TEXTURE0)
        GLES20.glBindTexture(GLES20.GL_TEXTURE_2D, texture)
        GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_MIN_FILTER, GLES20.GL_LINEAR)
        GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_MAG_FILTER, GLES20.GL_LINEAR)
        GLES20.glTexParameteri(
            GLES20.GL_TEXTURE_2D,
            GLES20.GL_TEXTURE_WRAP_S,
            GLES20.GL_CLAMP_TO_EDGE,
        )
        GLES20.glTexParameteri(
            GLES20.GL_TEXTURE_2D,
            GLES20.GL_TEXTURE_WRAP_T,
            GLES20.GL_CLAMP_TO_EDGE,
        )
        GLUtils.texImage2D(GLES20.GL_TEXTURE_2D, 0, bitmap, 0)
        val p = GLES20.glGetAttribLocation(program, "p")
        val uv = GLES20.glGetAttribLocation(program, "uv")
        vertices.position(0)
        GLES20.glEnableVertexAttribArray(p)
        GLES20.glVertexAttribPointer(p, 2, GLES20.GL_FLOAT, false, 16, vertices)
        vertices.position(2)
        GLES20.glEnableVertexAttribArray(uv)
        GLES20.glVertexAttribPointer(uv, 2, GLES20.GL_FLOAT, false, 16, vertices)
        GLES20.glUniform1i(GLES20.glGetUniformLocation(program, "img"), 0)
        GLES20.glDrawArrays(GLES20.GL_TRIANGLE_STRIP, 0, 4)
        check(GLES20.glGetError() == GLES20.GL_NO_ERROR) { "Visualizer rendering failed" }
    }

    override fun close() {
        bitmap?.recycle()
        painter.close()
        if (texture != 0) GLES20.glDeleteTextures(1, intArrayOf(texture), 0)
        if (program != 0) GLES20.glDeleteProgram(program)
    }
}
