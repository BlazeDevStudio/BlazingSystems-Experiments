package com.blazingsystems.visualizer.render

import android.graphics.*
import com.blazingsystems.visualizer.project.*
import kotlin.math.*
import kotlinx.serialization.json.*

/** Original analytical motion; no previous-frame feedback or video tracing. */
class MathCurvePainter {
    private val paint=Paint(Paint.ANTI_ALIAS_FLAG)
    private fun alpha(color: Int,amount: Double)=Color.argb(amount.toInt().coerceIn(0,255),Color.red(color),Color.green(color),Color.blue(color))
    private fun Layer.text(key: String,fallback: String="")=(properties[key] as? JsonPrimitive)?.contentOrNull ?: fallback
    private fun Layer.number(key: String,fallback: Double,min: Double,max: Double)=text(key).toDoubleOrNull()?.takeIf(Double::isFinite)?.coerceIn(min,max) ?: fallback

    fun draw(c: Canvas,s: EvaluatedScene,layer: Layer,width: Float,height: Float,tint: Int,intensity: Float) {
        val strength=intensity.coerceIn(0f,2f)
        val mode=runCatching { MathVisualMode.valueOf(layer.text("mode","LISSAJOUS")) }.getOrDefault(MathVisualMode.LISSAJOUS)
        val motion=runCatching { CurveMotion.valueOf(layer.text("motion","OUTLINE")) }.getOrDefault(CurveMotion.OUTLINE)
        val speed=layer.number("speed",1.0,0.0,4.0)
        val seconds=layer.number("trailSeconds",1.5,.1,8.0)
        val camera=layer.number("cameraAmount",1.0,0.0,2.0)
        val now=s.sourceTimeUs
        val reveal=mode==MathVisualMode.WAVES && motion==CurveMotion.REVEAL && strength>0
        val progress=if(reveal) MotionGeometry.progress(now,speed,seconds) else 1.0
        val sweepStart=if(reveal && speed>0) now-(progress*seconds/speed*1e6).toLong() else now
        val history=(s.features.notes+s.activeNotes).distinctBy { it.id }
        fun envelope(n: NoteEvent)=if(strength==0f) {
            if(n.startUs<=now && now<n.endUs) 1.0 else 0.0
        } else MotionGeometry.envelope(now,n.startUs,n.endUs)
        val eligible=history.filter { n -> n.startUs<=now &&
            (if(reveal) n.endUs>=sweepStart else envelope(n)>.001) }
        val voices=eligible.groupBy { it.pitch }.values.map { group ->
            group.maxWith(compareBy<NoteEvent> { if(now<it.endUs) 1 else 0 }.thenBy { it.startUs })
        }.sortedBy { it.pitch }.take(12)
        if(voices.isEmpty()) return
        val ratios=voices.map { MusicalMath.ratio(it.pitch,voices.first().pitch) }
        val weights=voices.map { it.amplitude.toDouble().coerceIn(.01,1.0)*if(reveal) 1.0 else envelope(it) }
        val physical=layer.text("physicalAxes")=="true" || mode in setOf(MathVisualMode.CHORD_3D,MathVisualMode.RADIAL,MathVisualMode.RHYTHM)
        val w=if(physical) min(width,height)*.43f else width*.43f
        val h=if(physical) min(width,height)*(if(s.scene.showEquations) .32f else .43f)
            else height*(if(s.scene.showEquations) .32f else .43f)
        val hsv=FloatArray(3);Color.colorToHSV(tint,hsv)
        fun color(i: Int)=if(i==0) tint else Color.HSVToColor(floatArrayOf((hsv[0]+i*43)%360,hsv[1].coerceAtLeast(.4f),hsv[2]))
        if(mode==MathVisualMode.RHYTHM) rhythm(c,layer,voices,w,h,width,now,speed,strength,::color)
        else {
            val separate=reveal || mode==MathVisualMode.RADIAL
            val count=if(mode==MathVisualMode.LISSAJOUS) max(1,voices.size-1) else if(separate) voices.size else 1
            for(i in 0 until count) {
                val r=when {
                    mode==MathVisualMode.LISSAJOUS -> if(voices.size==1) listOf(1.0) else listOf(1.0,ratios[i+1])
                    reveal -> listOf(ratios[i])
                    mode==MathVisualMode.RADIAL -> listOf(MusicalMath.ratio(voices[i].pitch,48))
                    else -> ratios
                }
                val a=if(r.size==weights.size && !separate) weights else List(r.size) { if(separate) weights[i] else 1.0 }
                val opacity=if(reveal) 1.0 else if(separate) envelope(voices[i]) else voices.maxOf(::envelope)
                val radial=if(mode==MathVisualMode.RADIAL) .3f+.65f*(i+1)/count else 1f
                val scaleY=if(reveal) .8f/count else radial
                val offset=if(reveal) (i-(count-1)/2f)*h*1.65f/count else 0f
                val trace=MotionGeometry.trace(mode,r,a,now,motion,speed,seconds,camera,strength.toDouble(),
                    startUs=if(separate) voices[i].startUs else voices.maxOf { it.startUs },maxSamples=if(count>4) 192 else 384)
                if(reveal) {
                    val guide=MotionGeometry.trace(mode,r,a,0,CurveMotion.OUTLINE,intensity=0.0)
                    stroke(c,guide.points,w,h*scaleY,offset,color(i),.08,1f)
                }
                val points=if(reveal) trace.points.mapIndexed { index,p ->
                    val position=progress*index/(trace.points.size-1)
                    val sampleTime=if(speed>0) sweepStart+(position*seconds/speed*1e6).toLong() else now
                    val audible=history.any { it.pitch==voices[i].pitch && it.startUs<=sampleTime && sampleTime<it.endUs }
                    p.copy(opacity=if(audible) 1.0 else 0.0)
                } else trace.points
                if(strength>0) stroke(c,points,w*radial,h*scaleY,offset,color(i),opacity*.13*strength,max(3f,width/75)*strength)
                stroke(c,points,w*radial,h*scaleY,offset,color(i),opacity*.9,max(1.2f,width/260))
                trace.head?.let { p ->
                    if(!reveal || points.last().opacity>0) head(c,p,w*radial,h*scaleY,offset,color(i),width,strength,opacity)
                }
            }
            if(reveal) {
                paint.shader=null;paint.style=Paint.Style.STROKE;paint.color=alpha(tint,60.0)
                paint.strokeWidth=max(1f,width/500)
                val x=((-1+2*progress)*w).toFloat();c.drawLine(x,-h,x,h,paint)
            }
            if(mode==MathVisualMode.ORBITS) {
                paint.style=Paint.Style.STROKE;paint.strokeWidth=max(1f,width/550)
                for(i in voices.indices) {
                    val radius=min(w,h)*(.35f+.6f*(i+1)/voices.size)
                    paint.color=alpha(tint,30.0);c.drawCircle(0f,0f,radius,paint)
                    if(strength>0) {
                        val angle=now/1e6*2*PI*speed*ratios[i]
                        paint.style=Paint.Style.FILL;paint.color=color(i)
                        c.drawCircle((cos(angle)*radius).toFloat(),(sin(angle)*radius).toFloat(),width*.008f,paint)
                        paint.style=Paint.Style.STROKE
                    }
                }
            }
        }
        if(strength>0 && layer.text("impactHalo")=="true") {
            val age=(now-voices.maxOf { it.startUs })/1e6
            if(age in 0.0..0.5) {
                paint.shader=null;paint.style=Paint.Style.FILL;paint.color=alpha(tint,130*(1-age/.5)*strength)
                val radius=min(w,h)*(1+age*.7)
                repeat(48) { i -> val angle=i*2*PI/48;c.drawCircle((cos(angle)*radius).toFloat(),(sin(angle)*radius).toFloat(),max(1f,width/350),paint) }
            }
        }
        if(s.scene.showEquations) equations(c,mode,ratios,width,height,tint)
    }

    private fun stroke(c: Canvas,points: List<MotionPoint>,w: Float,h: Float,y: Float,color: Int,opacity: Double,thickness: Float) {
        paint.shader=null;paint.style=Paint.Style.STROKE;paint.strokeCap=Paint.Cap.ROUND;paint.strokeWidth=thickness
        if(points.all { it.opacity==1.0 } && points.all { it.depth==0.0 }) {
            val path=Path();points.forEachIndexed { i,p -> if(i==0) path.moveTo((p.x*w).toFloat(),y-(p.y*h).toFloat()) else path.lineTo((p.x*w).toFloat(),y-(p.y*h).toFloat()) }
            paint.color=alpha(color,255*opacity);c.drawPath(path,paint)
        } else for(i in 1 until points.size) {
            val a=points[i-1];val b=points[i]
            val value=min(a.opacity,b.opacity)*opacity*(.75+.25*b.depth)
            if(value<=0) continue
            paint.color=alpha(color,255*value)
            c.drawLine((a.x*w).toFloat(),y-(a.y*h).toFloat(),(b.x*w).toFloat(),y-(b.y*h).toFloat(),paint)
        }
    }
    private fun head(c: Canvas,p: MotionPoint,w: Float,h: Float,y: Float,color: Int,width: Float,strength: Float,opacity: Double) {
        if(strength<=0) return
        val x=(p.x*w).toFloat();val py=y-(p.y*h).toFloat();val radius=max(4f,width*.03f)*strength
        paint.style=Paint.Style.FILL;paint.shader=RadialGradient(x,py,radius,intArrayOf(alpha(color,190*opacity),Color.TRANSPARENT),null,Shader.TileMode.CLAMP)
        c.drawCircle(x,py,radius,paint);paint.shader=null;paint.color=alpha(Color.WHITE,255*opacity)
        c.drawCircle(x,py,max(1.3f,width*.004f),paint)
    }
    private fun rhythm(c: Canvas,layer: Layer,voices: List<NoteEvent>,w: Float,h: Float,width: Float,now: Long,speed: Double,strength: Float,color: (Int)->Int) {
        val authored=layer.text("rhythmDivisions","2,3,4,5,6,7").split(',').mapNotNull { it.trim().toIntOrNull()?.takeIf { v->v in 1..16 } }
        val time=if(strength>0) now/1e6 else 0.0
        val turns=time*speed
        var center=0.0
        for(i in 0 until min(voices.size,6)) {
            val vertices=authored.getOrElse(i) { i+2 }
            val radius=min(w,h)*(.42f+.53f*(i+1)/min(voices.size,6))
            paint.shader=null;paint.style=Paint.Style.STROKE;paint.strokeWidth=max(1f,width/400);paint.color=alpha(color(i),110.0)
            val path=Path()
            repeat(vertices+1) { v -> val angle=v*2*PI/vertices-PI/2;val x=(cos(angle)*radius).toFloat();val y=(sin(angle)*radius).toFloat();if(v==0)path.moveTo(x,y)else path.lineTo(x,y) }
            c.drawPath(path,paint)
            repeat(vertices) { v ->
                val angle=v*2*PI/vertices-PI/2;val x=(cos(angle)*radius).toFloat();val y=(sin(angle)*radius).toFloat()
                val crossing=floor(turns-v.toDouble()/vertices)+v.toDouble()/vertices
                val age=if(speed>0 && crossing>=0) (turns-crossing)/speed else 100.0
                val pulse=if(strength>0) exp(-age/.07)*strength else 0.0
                center=max(center,pulse)
                paint.style=Paint.Style.FILL;paint.color=alpha(color(i),180+60*pulse)
                c.drawCircle(x,y,max(2f,width*.006f)*(1+pulse.toFloat()),paint)
                if(age in 0.0..0.35 && strength>0) {
                    paint.style=Paint.Style.STROKE;paint.color=alpha(color(i),170*(1-age/.35)*strength)
                    c.drawCircle(x,y,(width*(.012+age*.12)).toFloat(),paint)
                }
            }
        }
        if(strength>0) {
            val angle=turns*2*PI-PI/2
            paint.style=Paint.Style.STROKE;paint.color=alpha(Color.WHITE,205.0);paint.strokeWidth=max(1.2f,width/260)
            c.drawLine(0f,0f,(cos(angle)*w).toFloat(),(sin(angle)*h).toFloat(),paint)
            paint.style=Paint.Style.FILL;paint.color=alpha(Color.WHITE,150+100*center)
            c.drawCircle(0f,0f,max(2f,width*.01f)*(1+center.toFloat()),paint)
        }
    }
    private fun equations(c: Canvas,mode: MathVisualMode,ratios: List<Double>,w: Float,h: Float,tint: Int) {
        paint.shader=null;paint.style=Paint.Style.FILL;paint.color=alpha(tint,230.0)
        paint.typeface=Typeface.MONOSPACE;paint.textAlign=Paint.Align.CENTER;paint.textSize=(w/42).coerceAtLeast(6f)
        val formula=when(mode) {
            MathVisualMode.LISSAJOUS -> "x = cos(θ), yⱼ = sin(rⱼθ)"
            MathVisualMode.ORBITS -> "z = Σ aⱼ exp(i rⱼθ) / Σ aⱼ"
            MathVisualMode.WAVES -> "y = Σ aⱼ sin(rⱼθ) / Σ aⱼ"
            MathVisualMode.CHORD_3D -> "xyz = grouped weighted note oscillators"
            MathVisualMode.RHYTHM -> "hit rates = authored divisions × visual rotations/s"
            MathVisualMode.RADIAL -> "ρ = 0.83 + 0.13 Σ aⱼ sin((j+4)θ+2πlog₂rⱼ)/Σaⱼ + 0.035cos2θ"
        }
        c.drawText(formula,0f,h*.36f,paint)
        c.drawText("f(m) = 440 × 2^((m−69)/12); θ is visual phase",0f,h*.42f,paint)
        paint.textSize*=.8f
        c.drawText((if(ratios.size>6) "r (first 6/${ratios.size}): " else "r: ")+ratios.take(6).joinToString(" : ") { "%.3f".format(java.util.Locale.US,it) },0f,h*.47f,paint)
    }
}
