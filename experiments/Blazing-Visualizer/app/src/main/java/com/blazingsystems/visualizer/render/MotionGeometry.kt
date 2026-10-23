package com.blazingsystems.visualizer.render

import kotlin.math.*

enum class CurveMotion { OUTLINE, TRAIL, REVEAL }
data class MotionPoint(val x: Double,val y: Double,val opacity: Double=1.0,val depth: Double=0.0)
data class MotionTrace(val points: List<MotionPoint>,val head: MotionPoint?,val progress: Double)

/** Pure source-clock geometry, shared by preview, seeking, and offline export. */
object MotionGeometry {
    fun progress(timeUs: Long,speed: Double,seconds: Double): Double {
        val value=timeUs.coerceAtLeast(0)/1e6*speed.coerceIn(0.0,4.0)/seconds.coerceIn(.1,8.0)
        return value-floor(value)
    }
    fun envelope(timeUs: Long,startUs: Long,endUs: Long): Double {
        if(timeUs<startUs || endUs<=startUs) return 0.0
        val attack=((timeUs-startUs)/35_000.0).coerceIn(0.0,1.0)
        val release=if(timeUs<endUs) 1.0 else (1-(timeUs-endUs)/350_000.0).coerceIn(0.0,1.0)
        return attack*attack*(3-2*attack)*release*release*(3-2*release)
    }
    private fun point(mode: MathVisualMode,ratios: List<Double>,weights: List<Double>,theta: Double,time: Double,camera: Double): MotionPoint {
        if(mode==MathVisualMode.CHORD_3D) {
            val axis=DoubleArray(3);val totals=DoubleArray(3)
            for(i in ratios.indices) {
                val k=i%3
                axis[k]+=weights[i]*(if(k==0) cos(ratios[i]*theta) else sin(ratios[i]*theta))
                totals[k]+=weights[i]
            }
            for(i in 0..2) axis[i]/=totals[i].coerceAtLeast(1e-9)
            if(ratios.size==1) axis[1]=sin(theta)
            val yaw=.35+time*.27*camera;val pitch=-.28+sin(time*.17)*.2*camera
            val x=axis[0]*cos(yaw)+axis[2]*sin(yaw)
            val z=-axis[0]*sin(yaw)+axis[2]*cos(yaw)
            val y=axis[1]*cos(pitch)-z*sin(pitch)
            val depth=((axis[1]*sin(pitch)+z*cos(pitch))/sqrt(3.0)).coerceIn(-1.0,1.0)
            val scale=.78/(1+.18*depth)
            return MotionPoint(x*scale,y*scale,depth=depth)
        }
        if(mode==MathVisualMode.RADIAL) {
            val total=weights.sum().coerceAtLeast(1e-9)
            val modulation=ratios.indices.sumOf { weights[it]*sin((it+4)*theta+2*PI*log2(ratios[it])) }/total
            val radius=.83+.13*modulation+.035*cos(2*theta)
            return MotionPoint(radius*cos(theta),radius*sin(theta))
        }
        val p=MusicalMath.point(mode,ratios,weights,theta)
        return MotionPoint(p.x,p.y)
    }
    fun trace(mode: MathVisualMode,ratios: List<Double>,weights: List<Double>,sourceTimeUs: Long,
        motion: CurveMotion,speed: Double=1.0,trailSeconds: Double=1.5,camera: Double=1.0,
        intensity: Double=1.0,startUs: Long=0,maxSamples: Int=384): MotionTrace {
        require(ratios.isNotEmpty() && ratios.size==weights.size && ratios.size<=12)
        require(ratios.all { it.isFinite() && it>0 } && weights.all { it.isFinite() && it>=0 })
        val moving=intensity.isFinite() && intensity>0
        val time=if(moving) sourceTimeUs.coerceAtLeast(0)/1e6 else 0.0
        val rate=speed.takeIf(Double::isFinite)?.coerceIn(0.0,4.0) ?: 1.0
        val duration=trailSeconds.takeIf(Double::isFinite)?.coerceIn(.1,8.0) ?: 1.5
        val style=if(moving) motion else CurveMotion.OUTLINE
        val span=if(mode==MathVisualMode.RADIAL) 2*PI else 2*PI*min(4.0,64/ratios.max())
        val headPhase=(time*2*PI*rate)%span
        val progress=if(style==CurveMotion.REVEAL) progress(sourceTimeUs,rate,duration) else 1.0
        val count=maxSamples.coerceIn(2,512)
        val available=(time-startUs/1e6).coerceAtLeast(0.0)
        val points=List(count) { i ->
            val u=i.toDouble()/(count-1)
            val position=if(style==CurveMotion.REVEAL) u*progress else u
            val theta=when(style) {
                CurveMotion.OUTLINE,CurveMotion.REVEAL -> span*position
                CurveMotion.TRAIL -> headPhase-min(duration,available)*(1-u)*2*PI*rate
            }
            var p=point(mode,ratios,weights,theta,time,camera.coerceIn(0.0,2.0))
            if(mode==MathVisualMode.WAVES) p=p.copy(x=-1+2*position)
            p.copy(opacity=if(style==CurveMotion.TRAIL) .02+.98*u*u else 1.0)
        }
        val head=when {
            !moving || (mode==MathVisualMode.RADIAL && style==CurveMotion.OUTLINE) -> null
            style==CurveMotion.OUTLINE -> point(mode,ratios,weights,headPhase,time,camera).let {
                if(mode==MathVisualMode.WAVES) it.copy(x=-1+2*headPhase/span) else it
            }
            else -> points.last()
        }
        return MotionTrace(points,head,progress)
    }
}
