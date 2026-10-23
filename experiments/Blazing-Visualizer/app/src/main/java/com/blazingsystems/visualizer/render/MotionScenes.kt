package com.blazingsystems.visualizer.render

import com.blazingsystems.visualizer.project.*
import kotlinx.serialization.json.*

object MotionScenes {
    private fun scene(id: String,name: String,mode: MathVisualMode,motion: CurveMotion,seconds: Double=1.5)=Scene(
        id="builtin-motion-$id",name=name,showEquations=false,layers=listOf(
            Layer(type=ElementType.BLUR),
            Layer(type=ElementType.MATH_CURVE,transform=Transform(y=.43f,width=.86f,height=.68f),
                properties=buildJsonObject {
                    put("mode",mode.name);put("motion",motion.name);put("speed",.5)
                    put("trailSeconds",seconds);put("cameraAmount",1.0)
                    put("physicalAxes",true);put("impactHalo",true)
                }),
            Layer(type=ElementType.PIANO_ROLL,transform=Transform(y=.85f,width=.92f,height=.18f)),
        ))
    fun all()=listOf(
        scene("traces","Luminous traces",MathVisualMode.LISSAJOUS,CurveMotion.TRAIL),
        scene("spatial","Chord sculpture",MathVisualMode.CHORD_3D,CurveMotion.OUTLINE),
        scene("reveal","Voice sweep",MathVisualMode.WAVES,CurveMotion.REVEAL,4.0),
        scene("rhythm","Rhythm geometry",MathVisualMode.RHYTHM,CurveMotion.OUTLINE),
        scene("radial","Pitch contours",MathVisualMode.RADIAL,CurveMotion.OUTLINE),
    )
}
