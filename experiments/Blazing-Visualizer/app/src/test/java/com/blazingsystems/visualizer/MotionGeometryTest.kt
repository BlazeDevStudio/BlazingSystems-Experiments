package com.blazingsystems.visualizer

import com.blazingsystems.visualizer.render.*
import org.junit.Assert.*
import org.junit.Test

class MotionGeometryTest {
    @Test fun traceAgeFadesAndSeekingDoesNotDependOnPreviousFrames() {
        val a=MotionGeometry.trace(MathVisualMode.LISSAJOUS,listOf(1.0,1.5),listOf(1.0,1.0),2_500_000,CurveMotion.TRAIL)
        assertTrue(a.points.first().opacity<a.points.last().opacity)
        MotionGeometry.trace(MathVisualMode.LISSAJOUS,listOf(1.0),listOf(1.0),9_000_000,CurveMotion.REVEAL)
        assertEquals(a,MotionGeometry.trace(MathVisualMode.LISSAJOUS,listOf(1.0,1.5),listOf(1.0,1.0),2_500_000,CurveMotion.TRAIL))
    }
    @Test fun revealProgressResetsAndAllVoicesContributeToSpatialChords() {
        assertTrue(MotionGeometry.progress(3_990_000,1.0,4.0)>.99)
        assertTrue(MotionGeometry.progress(4_010_000,1.0,4.0)<.01)
        val a=MotionGeometry.trace(MathVisualMode.CHORD_3D,listOf(1.0,1.25,1.875),List(3){1.0},1_000_000,CurveMotion.OUTLINE)
        val b=MotionGeometry.trace(MathVisualMode.CHORD_3D,listOf(1.0,1.25,1.5,1.875),List(4){1.0},1_000_000,CurveMotion.OUTLINE)
        assertNotEquals(a.points,b.points)
        assertTrue(b.points.maxOf { it.depth }-b.points.minOf { it.depth }>.1)
    }
    @Test fun zeroIntensityFreezesMotionAndNoteReleaseIsFinite() {
        val a=MotionGeometry.trace(MathVisualMode.CHORD_3D,listOf(1.0,1.25,1.5),List(3){1.0},1_000_000,CurveMotion.TRAIL,intensity=0.0)
        val b=MotionGeometry.trace(MathVisualMode.CHORD_3D,listOf(1.0,1.25,1.5),List(3){1.0},2_000_000,CurveMotion.TRAIL,intensity=0.0)
        assertEquals(a,b)
        assertEquals(1.0,MotionGeometry.envelope(500_000,0,1_000_000),0.0)
        assertTrue(MotionGeometry.envelope(1_100_000,0,1_000_000) in 0.0..1.0)
        assertEquals(0.0,MotionGeometry.envelope(1_500_000,0,1_000_000),0.0)
    }
}
