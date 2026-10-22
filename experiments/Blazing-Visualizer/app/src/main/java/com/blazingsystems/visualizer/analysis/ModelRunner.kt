package com.blazingsystems.visualizer.analysis

import android.content.Context
import java.nio.ByteBuffer
import java.nio.ByteOrder
import org.tensorflow.lite.Interpreter

class ModelRunner(context: Context) : AutoCloseable {
    private val modelBytes = context.assets.open("models/nmp.tflite").use { it.readBytes() }
    val modelHash = sha256(modelBytes)
    private val interpreter: Interpreter

    init {
        check(modelHash == MODEL_SHA256) { "Bundled model checksum mismatch" }
        val buffer =
            ByteBuffer.allocateDirect(modelBytes.size).order(ByteOrder.nativeOrder()).apply {
                put(modelBytes)
                rewind()
            }
        interpreter = Interpreter(buffer, Interpreter.Options().setNumThreads(2))
        check(interpreter.signatureKeys.contains("serving_default"))
        check(interpreter.getSignatureInputs("serving_default").toSet() == setOf("input_2"))
        check(
            interpreter.getSignatureOutputs("serving_default").toSet() ==
                setOf("note", "onset", "contour"),
        )
        check(
            interpreter
                .getInputTensorFromSignature("input_2", "serving_default")
                .shape()
                .contentEquals(intArrayOf(1, 43844, 1)),
        )
        for ((name, bins) in listOf("note" to 88, "onset" to 88, "contour" to 264)) check(
            interpreter
                .getOutputTensorFromSignature(name, "serving_default")
                .shape()
                .contentEquals(intArrayOf(1, 172, bins)),
        )
    }

    fun run(window: FloatArray): ModelOutputs {
        require(window.size == 43844)
        val input =
            ByteBuffer.allocateDirect(window.size * 4).order(ByteOrder.nativeOrder()).apply {
                asFloatBuffer().put(window)
            }
        val note = arrayOf(Array(172) { FloatArray(88) })
        val onset = arrayOf(Array(172) { FloatArray(88) })
        val contour = arrayOf(Array(172) { FloatArray(264) })
        interpreter.runSignature(
            mapOf("input_2" to input),
            mapOf("note" to note, "onset" to onset, "contour" to contour),
            "serving_default",
        )
        return ModelOutputs(note[0], onset[0], contour[0])
    }

    override fun close() = interpreter.close()

    companion object {
        const val MODEL_SHA256 = "3db297d54af8e01c6e5618245c956b1d71b6a2b978cb2dedb527173186552676"
    }
}
