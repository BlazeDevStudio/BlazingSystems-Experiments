package com.blazingsystems.visualizer.render

import android.graphics.*
import com.blazingsystems.visualizer.analysis.ChordEstimator
import com.blazingsystems.visualizer.practice.NoteNames
import com.blazingsystems.visualizer.project.*
import java.io.File
import kotlin.math.*
import kotlinx.serialization.json.*
import com.blazingsystems.visualizer.avee.Spectrum2Analyzer

/** Deterministic scene drawing; Canvas pixels feed the same GL pipeline for preview and MP4. */
class ScenePainter(private val assets: File) : AutoCloseable {
    private val paint = Paint(Paint.ANTI_ALIAS_FLAG)
    private val images = linkedMapOf<String, Bitmap>()
    private val mathCurves = MathCurvePainter()
    private val importedPainter=lazy { AveeScenePainter(assets) }
    private var frequencyProfile: JsonObject?=null
    private var bankFrequencies=emptyList<Double>()

    private fun Layer.string(key: String, default: String = "") =
        properties[key]?.jsonPrimitive?.contentOrNull ?: default

    private fun Layer.number(key: String, default: Float) =
        string(key).toFloatOrNull()?.takeIf { it.isFinite() } ?: default

    private fun Layer.color(default: Int = Color.rgb(128, 104, 255)) = runCatching {
        Color.parseColor(string("color"))
    }
        .getOrDefault(default)

    private fun routed(s: EvaluatedScene, layer: Layer): EvaluatedScene {
        if (layer.noteRouting == NoteRouting()) return s
        val notes = s.features.notes.filter { layer.noteRouting.allows(it.pitch) }
        val active = s.activeNotes.filter { layer.noteRouting.allows(it.pitch) }
        return s.copy(
            features = s.features.copy(notes = notes),
            activeNotes = active,
            chord = ChordEstimator.estimate(active, s.sourceTimeUs),
        )
    }

    private fun tinted(color: Int, alpha: Int) =
        Color.argb(alpha.coerceIn(0, 255), Color.red(color), Color.green(color), Color.blue(color))

    fun draw(
        canvas: Canvas,
        s: EvaluatedScene,
        width: Int,
        height: Int,
        videoFrame: Bitmap? = null,
        transparentBackground: Boolean = false,
    ) {
        val imported = s.scene.originalAvee != null && s.scene.aveeCompositionCount > 0
        when {
            videoFrame != null -> {
                canvas.drawColor(Color.BLACK, PorterDuff.Mode.SRC)
                val scale = min(width.toFloat() / videoFrame.width, height.toFloat() / videoFrame.height)
                val w = videoFrame.width * scale
                val h = videoFrame.height * scale
                paint.reset()
                paint.isFilterBitmap = true
                canvas.drawBitmap(videoFrame, null,
                    RectF((width - w) / 2, (height - h) / 2, (width + w) / 2, (height + h) / 2), paint)
                paint.reset()
                paint.isAntiAlias = true
            }
            transparentBackground -> canvas.drawColor(Color.TRANSPARENT, PorterDuff.Mode.CLEAR)
            else -> canvas.drawColor(
                runCatching { Color.parseColor(s.scene.backgroundColor) }
                    .getOrDefault(if (imported) Color.BLACK else Color.rgb(8, 9, 17)),
                PorterDuff.Mode.SRC,
            )
        }
        if(imported) {
            val aspect=s.scene.aveeRenderAspect
            val rh=(if(aspect==null) height.toFloat() else if(s.scene.aveeFrameMode==ExportFrameMode.COVER)
                max(height.toFloat(),width/aspect) else min(height.toFloat(),width/aspect)).roundToInt().coerceAtLeast(1)
            val rw=(if(aspect==null) width.toFloat() else rh*aspect).roundToInt().coerceAtLeast(1)
            val saved=canvas.save();canvas.clipRect(0,0,width,height);canvas.translate((width-rw)/2f,(height-rh)/2f)
            importedPainter.value.draw(canvas,s,rw,rh) { target,layer -> drawNative(target,layer,rw,rh) }
            canvas.restoreToCount(saved)
        } else drawNative(canvas,s,width,height)
    }

    private fun drawNative(canvas: Canvas,s: EvaluatedScene,width: Int,height: Int) {
        paint.shader = null
        paint.style = Paint.Style.FILL
        for (e in s.layers) {
            val layer = e.layer
            val t = layer.transform
            val w = width * t.width * e.scale
            val h = height * t.height * e.scale
            canvas.save()
            canvas.translate(width * t.x, height * t.y)
            canvas.rotate(t.rotation)
            val defaultTint = runCatching { s.scene.paletteColor?.let(Color::parseColor) }.getOrNull() ?: Color.rgb(156, 131, 255)
            val tint = layer.color(defaultTint)
            val intensity = s.scene.animationIntensity.coerceIn(0f, 2f)
            paint.color = tint
            paint.alpha = 255
            paint.shader = null
            paint.style = Paint.Style.FILL
            when (layer.type) {
                ElementType.IMAGE -> {
                    val path = layer.string("asset")
                    val f = File(assets, path)
                    if (
                        path.isNotBlank() &&
                            f.canonicalPath.startsWith(assets.canonicalPath + "/") &&
                            f.isFile
                    ) {
                        val bitmap =
                            images[path]
                                ?: BitmapFactory.decodeFile(f.path)?.also {
                                    if (images.size >= 8) {
                                        images.values.first().recycle()
                                        images.remove(images.keys.first())
                                    }
                                    images[path] = it
                                }
                        if (bitmap != null)
                            canvas.drawBitmap(
                                bitmap,
                                null,
                                RectF(-w / 2, -h / 2, w / 2, h / 2),
                                paint,
                            )
                    }
                }
                ElementType.TEXT -> {
                    paint.typeface = Typeface.create("sans-serif-medium", Typeface.NORMAL)
                    paint.textAlign = Paint.Align.CENTER
                    paint.textSize = layer.number("fontSize", 24f).coerceIn(4f, 160f) * min(w, h) / 420f
                    canvas.drawText(
                        layer.string("text", "BLAZING"),
                        0f,
                        -(paint.ascent() + paint.descent()) / 2,
                        paint,
                    )
                }
                ElementType.SHAPE -> {
                    if (layer.string("shape", "circle") == "rect")
                        canvas.drawRoundRect(-w / 2, -h / 2, w / 2, h / 2, 16f, 16f, paint)
                    else canvas.drawCircle(0f, 0f, min(w, h) / 2, paint)
                }
                ElementType.BLUR -> {
                    if (intensity <= 0f) { canvas.restore(); continue }
                    val radius = max(w, h) * .58f
                    paint.shader =
                        RadialGradient(
                            0f,
                            0f,
                            radius,
                            intArrayOf(tinted(tint, (80 * intensity).toInt()), Color.TRANSPARENT),
                            null,
                            Shader.TileMode.CLAMP,
                        )
                    canvas.drawCircle(0f, 0f, radius, paint)
                    paint.shader = null
                }
                ElementType.PARTICLES -> {
                    if (intensity <= 0f) { canvas.restore(); continue }
                    for (i in 0 until 48) {
                        val phase = (i * 0.61803398875 + s.scene.seed * .031) % 1
                        val age = (s.sourceTimeUs / 1_000_000.0 * .035 + phase) % 1
                        val x = sin(i * 12.9898 + s.scene.seed) * w * .5
                        val y = (.5 - age) * h
                        paint.alpha = (sin(age * PI) * 95 * intensity).toInt().coerceIn(0, 255)
                        canvas.drawCircle(
                            x.toFloat(),
                            y.toFloat(),
                            (1 + i % 3) * min(w, h) / 420f,
                            paint,
                        )
                    }
                }
                ElementType.SPECTRUM -> {
                    val pathMode = layer.string("path", "circle")
                    val circle = pathMode == "circle"
                    val polygon = pathMode == "polygon"
                    val sides = layer.number("sides", 5f).toInt().coerceIn(3, 24)
                    val segment = layer.string("segment")
                    if (segment == "None") { canvas.restore(); continue }
                    val colorTo = runCatching {
                        Color.parseColor(layer.string("colorTo"))
                    }.getOrNull()
                    val config = s.scene.aveeAudio
                    fun param(key: String, fallback: Float): Float =
                        config[key]?.jsonPrimitive?.floatOrNull?.takeIf(Float::isFinite) ?: fallback
                    val imported = config.isNotEmpty() || layer.avee.isNotEmpty()
                    val bank=s.features.aveeSpectrum
                    if(bank.isNotEmpty() && frequencyProfile!=config) {
                        frequencyProfile=config;bankFrequencies=Spectrum2Analyzer(config).frequencies
                    }
                    val bins = if(bank.isNotEmpty()) bank.size else if (imported)
                        param("sampleOutCount", 80f).toInt().coerceIn(24, 192) else 80
                    val low = param("lowerHz", 20f).coerceIn(0f, 8000f)
                    val high = param("higherHz", 11025f).coerceIn(low + 1f, 11025f)
                    val linearity = param("hzLinearFactor", .5f).coerceIn(0f, 1f)
                    val gain = param("outputMultiplier", 1f).coerceIn(.1f, 3f)
                    val lowMagnitude = param("lowerFreqMagnitude", .5f).coerceIn(0f, 1f)
                    val filterRadius = param("filterRadius", 0f).toInt().coerceIn(0, 8)
                    paint.strokeWidth = max(1f, min(w, h) / 300f) *
                        layer.number("barWidth", 1f).coerceIn(.05f, 2f)
                    paint.strokeCap = if (segment == "SharpBars") Paint.Cap.SQUARE
                        else Paint.Cap.ROUND
                    if(imported) paint.strokeWidth=max(1f,(if(circle || polygon) min(w,h)*1.82f/bins else w/bins)*layer.number("barWidth",.7f))
                    val line=if(segment=="Line") Path() else null
                    paint.style=Paint.Style.STROKE
                    for (i in 0 until bins) {
                        val input=if(layer.string("flipInput") in setOf("1","true")) bins-1-i else i
                        val fraction = i.toDouble() / bins
                        val from = if (imported) {
                            val mapped = fraction.pow(2) * (1.0 - linearity) + fraction * linearity
                            val hz = low + (high - low) * mapped
                            (hz / 22050.0 * (2 * s.features.spectrum.size))
                                .coerceIn(0.0, (s.features.spectrum.size - 1).coerceAtLeast(0).toDouble())
                        } else fraction.pow(2) * min(512, s.features.spectrum.size)
                        val frequency = if(bank.isNotEmpty()) bankFrequencies.getOrElse(input){0.0}
                            else from * 22050 / (2*s.features.spectrum.size.coerceAtLeast(1))
                        val bounds = layer.noteRouting.bounds()
                        val allowed = layer.noteRouting == NoteRouting() || frequency in
                            MusicalMath.frequency(bounds.first)*2.0.pow(-.5/12)..MusicalMath.frequency(bounds.last)*2.0.pow(.5/12)
                        val amplitude = if (!allowed) 0f else if(bank.isNotEmpty()) {
                            bank.getOrElse(input){0f}
                        } else if (!imported) {
                            s.features.spectrum.getOrElse(from.toInt()) { 0f }
                        } else {
                            var sum = 0f
                            var count = 0
                            for (offset in -filterRadius..filterRadius) {
                                val index = from.toInt() + offset
                                if (index in s.features.spectrum.indices) {
                                    sum += s.features.spectrum[index]
                                    count++
                                }
                            }
                            val filter = if (count > 0) sum / count else 0f
                            filter * gain * (lowMagnitude +
                                (1f - lowMagnitude) * fraction.toFloat())
                        }
                        val level = (ln(1 + amplitude * 80) / ln(81f)).coerceIn(0f, 1f)
                        val magnitude=layer.number("heightScale",1f)*layer.number("barHeightMultiplier",1f)
                        val scaled = if (imported) {
                            val height = max(abs(layer.number("minHeightScale", 0f)), amplitude * abs(magnitude))
                                .coerceAtMost(abs(layer.number("maxHeightScale", 1f)))
                            height * if (magnitude < 0f) -1f else 1f
                        } else level
                        paint.color = if (colorTo == null) tint else {
                            val portion = i.toFloat() / (bins - 1).coerceAtLeast(1)
                            Color.argb(
                                (Color.alpha(tint) * (1 - portion) + Color.alpha(colorTo) * portion).toInt(),
                                (Color.red(tint) * (1 - portion) + Color.red(colorTo) * portion).toInt(),
                                (Color.green(tint) * (1 - portion) + Color.green(colorTo) * portion).toInt(),
                                (Color.blue(tint) * (1 - portion) + Color.blue(colorTo) * portion).toInt(),
                            )
                        }
                        if (circle || polygon) {
                            val a = i * 2 * PI / bins - PI / 2
                            val sector = 2 * PI / sides
                            val angleOnSide = ((a + PI / 2 + PI) % sector) - sector / 2
                            val radialFactor = if (polygon)
                                cos(PI / sides) / cos(angleOnSide).coerceAtLeast(.1)
                            else 1.0
                            val r = min(w, h) * .29f * radialFactor.toFloat()
                            val length = if(imported) scaled*min(w,h)*.5f else 2 + level * min(w, h) * .2f
                            if(line!=null) {
                                val x=(cos(a)*(r+length)).toFloat();val y=(sin(a)*(r+length)).toFloat()
                                if(i==0) line.moveTo(x,y) else line.lineTo(x,y)
                            } else canvas.drawLine(
                                (cos(a) * r).toFloat(),
                                (sin(a) * r).toFloat(),
                                (cos(a) * (r + length)).toFloat(),
                                (sin(a) * (r + length)).toFloat(),
                                paint,
                            )
                        } else {
                            val x = -w / 2 + i * w / bins
                            val base=if(imported) 0f else h/2
                            val length=if(imported) scaled*h*.5f else level*h
                            if(line!=null) { if(i==0) line.moveTo(x,base-length) else line.lineTo(x,base-length) }
                            else {
                                canvas.drawLine(x,base,x,base-length,paint)
                                if(layer.string("mirror") in setOf("1","true")) canvas.drawLine(x,base,x,base+length,paint)
                            }
                        }
                    }
                    if(line!=null) { if(circle || polygon) line.close();canvas.drawPath(line,paint) }
                }
                ElementType.WAVEFORM -> {
                    val values = s.features.waveform
                    if (values.size > 1) {
                        paint.style = Paint.Style.STROKE
                        paint.strokeWidth = max(.5f, min(w, h) / 400f)
                        val path = Path()
                        values.forEachIndexed { i, v ->
                            val x = -w / 2 + i * w / (values.size - 1)
                            val y = v * h / 2
                            if (i == 0) path.moveTo(x, y) else path.lineTo(x, y)
                        }
                        canvas.drawPath(path, paint)
                    }
                }
                ElementType.NOTE_WHEEL ->
                    wheel(canvas, routed(s, layer), layer, w, h, tint, intensity)
                ElementType.PIANO_ROLL ->
                    piano(
                        canvas, routed(s, layer), layer, w, h, tint,
                        intensity * s.scene.pianoIntensity.coerceIn(0f, 2f),
                    )
                ElementType.MATH_CURVE -> mathCurves.draw(canvas, routed(s, layer), layer, w, h, tint, intensity)
            }
            canvas.restore()
        }
    }

    private fun wheel(
        c: Canvas, s: EvaluatedScene, layer: Layer, w: Float, h: Float,
        tint: Int, intensity: Float,
    ) {
        val r = min(w, h) * .37f
        val active = s.activeNotes.map { it.pitch % 12 }.toSet()
        val points =
            (0..11).map {
                val a = it * PI / 6 - PI / 2
                PointF((cos(a) * r).toFloat(), (sin(a) * r).toFloat())
            }
        paint.style = Paint.Style.STROKE
        paint.strokeWidth = w / 650
        paint.color = tinted(tint, 60)
        c.drawCircle(0f, 0f, r, paint)
        for (a in active) for (b in active) if (a < b) {
            paint.color = tinted(tint, 150)
            paint.strokeWidth = w / 260
            c.drawLine(points[a].x, points[a].y, points[b].x, points[b].y, paint)
        }
        points.forEachIndexed { i, p ->
            paint.style = Paint.Style.FILL
            paint.color = if (i in active) tint else Color.rgb(36, 35, 57)
            if (i in active && intensity > 0f) {
                paint.shader =
                    RadialGradient(
                        p.x,
                        p.y,
                        r * .25f,
                        intArrayOf(tinted(tint, (150 * intensity).toInt()), Color.TRANSPARENT),
                        null,
                        Shader.TileMode.CLAMP,
                    )
                c.drawCircle(p.x, p.y, r * .25f, paint)
                paint.shader = null
            }
            c.drawCircle(p.x, p.y, r * .105f, paint)
            paint.color = if (i in active) Color.WHITE else Color.rgb(152, 151, 179)
            paint.textSize = r * .105f
            paint.textAlign = Paint.Align.CENTER
            paint.typeface = Typeface.create("sans-serif-medium", Typeface.NORMAL)
            c.drawText(
                NoteNames.name(60 + i).dropLast(1),
                p.x,
                p.y - (paint.ascent() + paint.descent()) / 2,
                paint,
            )
        }
        val label = ChordEstimator.displayLabel(
            s.activeNotes, s.sourceTimeUs,
            layer.string("emptyText", "FOLLOW THE NOTES"),
        )
        paint.color = Color.WHITE
        if(s.chord==null && s.activeNotes.isNotEmpty()) {
            val rows=label.split(" · ").chunked(4).map { it.joinToString(" · ") }
            paint.textSize=r*.14f
            rows.forEachIndexed { i,text -> c.drawText(text,0f,(i-(rows.size-1)/2f)*r*.22f+r*.04f,paint) }
        } else {
            paint.textSize = min(r * .25f, r * 1.4f / (label.length * .56f).coerceAtLeast(1f))
            c.drawText(label, 0f, r * .04f, paint)
        }
        paint.textSize = r * .085f
        paint.color = Color.rgb(156, 151, 177)
        c.drawText(
            if (s.chord != null) "ESTIMATED CHORD"
            else if (s.activeNotes.isNotEmpty()) "DETECTED NOTES" else "",
            0f,
            r * .46f,
            paint,
        )
    }

    private fun piano(
        c: Canvas, s: EvaluatedScene, layer: Layer, w: Float, h: Float, tint: Int, intensity: Float,
    ) {
        val bounds = layer.noteRouting.bounds()
        val first = if (layer.noteRouting == NoteRouting()) 48 else bounds.first / 12 * 12
        val last = if (layer.noteRouting == NoteRouting()) 83 else
            (bounds.last / 12 * 12 + 11).coerceAtMost(127)
        val whites = (first..last).filter { it % 12 !in setOf(1, 3, 6, 8, 10) }
        val kw = w / whites.size
        val keyHeight = min(h * .4f, w * .22f)
        val base = h / 2 - keyHeight
        val active = s.activeNotes.map { it.pitch }.toSet()
        fun partColor(key: String, fallback: Int) = runCatching { Color.parseColor(layer.string(key)) }.getOrDefault(fallback)
        fun depth(pitch: Int): Float {
            val onset = s.activeNotes.filter { it.pitch == pitch }.maxOfOrNull { it.startUs } ?: return 0f
            val age = (s.sourceTimeUs-onset).coerceAtLeast(0)/1e6
            return (sin(min(1.0,age/.25)*PI)*exp(-age*10)*min(7f,keyHeight*.09f)*intensity).toFloat()
        }
        // Upcoming bars travel toward the keyboard in source time, unaffected by playback speed.
        val rangeUs = 3_000_000.0
        val area = h - keyHeight
        val whiteIndex = whites.withIndex().associate { it.value to it.index }
        fun x(pitch: Int): Float {
            val white = whiteIndex[pitch]
            return if (white != null) -w / 2 + white * kw
            else -w / 2 + (whites.count { it < pitch } - .32f) * kw
        }
        s.features.notes
            .filter {
                it.pitch in first..last &&
                    it.endUs > s.sourceTimeUs &&
                    it.startUs < s.sourceTimeUs + rangeUs
            }
            .forEach { n ->
                val top =
                    (base - (n.endUs - s.sourceTimeUs) / rangeUs * area)
                        .toFloat()
                        .coerceAtLeast(-h / 2)
                val bottom =
                    (base - (n.startUs - s.sourceTimeUs) / rangeUs * area)
                        .toFloat()
                        .coerceIn(-h / 2, base)
                if (bottom > top) {
                    paint.color =
                        if (n.pitch in active) tint else tinted(tint, 90)
                    c.drawRoundRect(
                        x(n.pitch) + 1,
                        top,
                        x(n.pitch) + kw * .86f,
                        bottom,
                        kw * .13f,
                        kw * .13f,
                        paint,
                    )
                }
            }
        whites.forEach { p ->
            paint.color = if (p in active) partColor("activeKeyColor",tint) else partColor("whiteKeyColor",Color.rgb(219,220,232))
            c.drawRoundRect(x(p) + 1, base + depth(p), x(p) + kw - 1, h / 2, 2f, 2f, paint)
            if (p % 12 == 0) {
                paint.textSize = kw * .4f
                paint.textAlign = Paint.Align.CENTER
                paint.color = Color.DKGRAY
                c.drawText(NoteNames.name(p), x(p) + kw / 2, h / 2 - kw * .25f, paint)
            }
        }
        (first..last)
            .filter { it % 12 in setOf(1, 3, 6, 8, 10) }
            .forEach { p ->
                paint.color = if (p in active) partColor("activeKeyColor",tint) else partColor("blackKeyColor",Color.rgb(23,23,35))
                c.drawRoundRect(
                    x(p),
                    base + depth(p),
                    x(p) + kw * .64f,
                    base + keyHeight * .63f,
                    2f,
                    2f,
                    paint,
                )
            }
        // Deterministic, pitch-specific impacts. No active MIDI event => no glow or sparks.
        if (intensity > 0f) for (note in s.activeNotes) {
            if (note.pitch !in first..last) continue
            val elapsed = (s.sourceTimeUs - note.startUs).coerceAtLeast(0)
            val falloff = (.2f + .8f*exp(-elapsed/120000f)) * intensity
            val centerX = x(note.pitch) + kw * .42f
            val centerY = base + keyHeight * .17f
            val radius = kw * 1.8f
            c.save()
            val black = note.pitch % 12 in setOf(1,3,6,8,10)
            val left = x(note.pitch) + if (black) 0f else 1f
            val right = x(note.pitch) + if (black) kw*.64f else kw-1f
            c.clipRect(left,-h/2,right,h/2)
            if (!black) for (p in first..last) if (p % 12 in setOf(1,3,6,8,10))
                c.clipOutRect(x(p),base,x(p)+kw*.64f,base+keyHeight*.63f)
            paint.shader = RadialGradient(
                centerX, centerY, radius,
                intArrayOf(tinted(partColor("glowColor",tint), (145 * falloff).toInt()), Color.TRANSPARENT),
                null, Shader.TileMode.CLAMP,
            )
            c.drawCircle(centerX, centerY, radius, paint)
            paint.shader = null
            if (elapsed < 500_000) for (i in 0 until 6) {
                val phase = (note.pitch * 13 + i * 19 + s.scene.seed) * .73
                val angle = phase + elapsed * .000004
                val distance = kw * (.2 + (elapsed / 500_000f) * (1 + i % 3))
                paint.color = tinted(partColor("sparkColor",Color.WHITE), (220 * falloff).toInt())
                c.drawCircle(
                    centerX + (cos(angle) * distance).toFloat(),
                    centerY - (sin(angle) * distance).toFloat(),
                    (kw * .075f).coerceAtLeast(1f), paint,
                )
            }
            c.restore()
        }
    }

    override fun close() {
        if(importedPainter.isInitialized()) importedPainter.value.close()
        images.values.forEach { it.recycle() }
        images.clear()
    }
}
