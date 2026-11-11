package com.blazesystems.threadharbor

import org.junit.Assert.assertArrayEquals
import org.junit.Assert.assertEquals
import org.junit.Assert.fail
import org.junit.Test
import java.io.ByteArrayInputStream
import java.io.ByteArrayOutputStream
import java.io.IOException

class StreamCopyTest {
    @Test fun emptyFileProducesEmptyOutput() {
        val output = ByteArrayOutputStream()
        val copied = copyStreams(ByteArrayInputStream(byteArrayOf()), output)
        assertEquals(0L, copied)
        assertEquals(0, output.size())
    }

    @Test fun copiesAcrossMultiple64KChunksExactly() {
        val original = ByteArray(196608 + 37) { i -> ((i * 37 + 13) % 256).toByte() }
        val output = ByteArrayOutputStream()
        val copied = copyStreams(ByteArrayInputStream(original), output)
        assertEquals(original.size.toLong(), copied)
        assertArrayEquals(original, output.toByteArray())
    }

    @Test fun checkpointStopsNextWriteInsteadOfCompletingPartialFile() {
        val source = ByteArray(196608 + 37) { 0x5a.toByte() }
        val output = ByteArrayOutputStream()
        var checks = 0
        try {
            copyStreams(ByteArrayInputStream(source), output) {
                checks++
                if (checks == 2) throw IOException("Simulated user cancellation")
            }
            fail("Expected cancellation")
        } catch (expected: IOException) {
            assertEquals("Simulated user cancellation", expected.message)
            assertEquals(65536, output.size())
        }
    }
}
