package com.blazingsystems.visualizer.render

import android.graphics.*
import com.blazingsystems.visualizer.project.*
import java.io.File
import kotlin.math.*
import kotlinx.serialization.json.*

/** Original bounded compositor for declarative Avee passes; shader effects are approximations. */
class AveeScenePainter(private val assets: File): AutoCloseable {
    private val buffers=linkedMapOf<Int,Bitmap>()
    private val images=linkedMapOf<String,Bitmap>()
    private val paint=Paint(Paint.ANTI_ALIAS_FLAG or Paint.FILTER_BITMAP_FLAG)
    private var dimensions=0 to 0
    private fun JsonElement?.scalar(): String? {
        var value=this
        repeat(6) { value=(value as? JsonObject)?.get("v") ?: return (value as? JsonPrimitive)?.contentOrNull }
        return (value as? JsonPrimitive)?.contentOrNull
    }
    private fun Layer.text(key: String,default: String="")=properties[key].scalar() ?: avee[key].scalar() ?: default
    private fun Layer.number(key: String,default: Float)=text(key).toFloatOrNull()?.takeIf(Float::isFinite) ?: default
    private fun Layer.flag(key: String)=text(key).lowercase() in setOf("1","true")
    private fun bounds(w: Float,h: Float)=RectF(-w/2,-h/2,w/2,h/2)
    private fun blend(name: String)=when(name.lowercase()) { "add","addalpha"->PorterDuff.Mode.ADD;"screen"->PorterDuff.Mode.SCREEN;else->PorterDuff.Mode.SRC_OVER }
    private fun argb(value: String,fallback: Int=Color.WHITE): Int {
        value.toLongOrNull()?.let { return it.toInt() }
        if(value.startsWith('#')) return runCatching { Color.parseColor(value) }.getOrDefault(fallback)
        val v=value.split(Regex("[,\\s]+")).mapNotNull { it.toFloatOrNull()?.takeIf(Float::isFinite) }
        if(v.size!=4) return fallback
        val h=((v[0]*360)%360+360)%360;val s=v[1].coerceIn(0f,1f);val l=v[2].coerceIn(0f,1f)
        val chroma=(1-abs(2*l-1))*s;val x=chroma*(1-abs((h/60)%2-1))
        val rgb=when { h<60->floatArrayOf(chroma,x,0f);h<120->floatArrayOf(x,chroma,0f);h<180->floatArrayOf(0f,chroma,x);h<240->floatArrayOf(0f,x,chroma);h<300->floatArrayOf(x,0f,chroma);else->floatArrayOf(chroma,0f,x) }
        val add=l-chroma/2
        return Color.argb((v[3].coerceIn(0f,1f)*255).roundToInt(),((rgb[0]+add)*255).roundToInt().coerceIn(0,255),((rgb[1]+add)*255).roundToInt().coerceIn(0,255),((rgb[2]+add)*255).roundToInt().coerceIn(0,255))
    }
    private fun tint(color: Int)=ColorMatrixColorFilter(floatArrayOf(
        Color.red(color)/255f,0f,0f,0f,0f,0f,Color.green(color)/255f,0f,0f,0f,
        0f,0f,Color.blue(color)/255f,0f,0f,0f,0f,0f,Color.alpha(color)/255f,0f))
    private fun texture(c: Canvas,image: Bitmap,w: Float,h: Float,color: Int=Color.WHITE,opacity: Int=255,mode: PorterDuff.Mode=PorterDuff.Mode.SRC_OVER) {
        paint.reset();paint.isAntiAlias=true;paint.isFilterBitmap=true;paint.colorFilter=tint(color);paint.alpha=opacity.coerceIn(0,255)
        paint.xfermode=PorterDuffXfermode(mode);c.drawBitmap(image,null,bounds(w,h),paint)
    }
    private fun asset(path: String): Bitmap? {
        if(path.isBlank()) return null
        images[path]?.let { return it }
        val file=runCatching { File(assets,path.removePrefix("local:")).canonicalFile }.getOrNull() ?: return null
        if(!file.path.startsWith(assets.canonicalPath+File.separator) || !file.isFile || file.length()>32L*1024*1024) return null
        val options=BitmapFactory.Options().apply { inJustDecodeBounds=true }
        BitmapFactory.decodeFile(file.path,options)
        if(options.outWidth !in 1..4096 || options.outHeight !in 1..4096) return null
        options.inJustDecodeBounds=false
        while(options.outWidth/options.inSampleSize.coerceAtLeast(1)>2048 || options.outHeight/options.inSampleSize.coerceAtLeast(1)>2048)
            options.inSampleSize=options.inSampleSize.coerceAtLeast(1)*2
        val bitmap=BitmapFactory.decodeFile(file.path,options) ?: return null
        while(images.isNotEmpty() && (images.size>=4 || images.values.sumOf { it.byteCount.toLong() }+bitmap.byteCount>16L*1024*1024)) {
            val old=images.entries.first();old.value.recycle();images.remove(old.key)
        }
        images[path]=bitmap;return bitmap
    }
    fun draw(canvas: Canvas,s: EvaluatedScene,width: Int,height: Int,native: (Canvas,EvaluatedScene)->Unit) {
        if(width !in 1..8192 || height !in 1..8192) return
        val count=s.scene.aveeCompositionCount.coerceIn(1,8)
        val factor=min(1.0,sqrt(8_000_000.0/(width.toDouble()*height*(count-1).coerceAtLeast(1))))
        val bw=(width*factor).roundToInt().coerceAtLeast(1);val bh=(height*factor).roundToInt().coerceAtLeast(1)
        if(dimensions!=(bw to bh)) { buffers.values.forEach { it.recycle() };buffers.clear();dimensions=bw to bh }
        val groups=s.layers.take(128).groupBy { it.layer.composition }
        val visiting=mutableSetOf<Int>();val complete=mutableSetOf<Int>()
        lateinit var render: (Int,Canvas)->Unit
        fun reference(index: Int): Bitmap? {
            if(index !in 1 until count || index in visiting) return null
            val bitmap=buffers.getOrPut(index) { Bitmap.createBitmap(bw,bh,Bitmap.Config.ARGB_8888) }
            if(index !in complete) {
                bitmap.eraseColor(Color.TRANSPARENT)
                val c=Canvas(bitmap);c.scale(bw.toFloat()/width,bh.toFloat()/height);render(index,c)
            }
            return bitmap
        }
        render={ index,c ->
            if(visiting.add(index)) {
                for(e in groups[index].orEmpty()) {
                    val layer=e.layer
                    val type=layer.avee["objType"].scalar() ?: ""
                    val retainedSource=layer.text("customImage").ifBlank { layer.text("TargetImage").ifBlank { layer.text("targetImage") } }
                    // An editor-selected asset overrides the retained import source.
                    val source=if(type=="Image") layer.text("asset").ifBlank { retainedSource } else retainedSource
                    val ref=if(source.startsWith("composition:")) source.substringAfter(':').toIntOrNull()
                        else if(type=="BlurEffect") layer.number("sourceCompositionIndex",1f).toInt() else null
                    // Resolve child textures before allocating the parent layer's blend surface.
                    val image=ref?.let(::reference)
                    val saved=c.saveLayer(0f,0f,width.toFloat(),height.toFloat(),Paint().apply { xfermode=PorterDuffXfermode(blend(layer.text("blendMode"))) })
                    try {
                        if(type !in setOf("Image","BlurEffect","MotionBlurEffect","RgbSplitEffect","MirrorEffect")) {
                            native(c,s.copy(layers=listOf(e)));continue
                        }
                        val t=layer.transform
                        var w=width*t.width*e.scale;var h=height*t.height*e.scale
                        if(layer.flag("scaleIsUniform")) { val size=min(width,height);w=size*t.width*e.scale;h=size*t.height*e.scale }
                        if(!w.isFinite() || !h.isFinite() || w<=0 || h<=0) continue
                        val align=layer.text("alignmentPosition","0.5 0.5").split(Regex("[,\\s]+")).mapNotNull(String::toFloatOrNull)
                        c.translate(width*t.x+(if(align.size==2) .5f-align[0] else 0f)*w,height*t.y+(if(align.size==2) .5f-align[1] else 0f)*h)
                        c.rotate(t.rotation)
                        val color=argb(layer.text("color",layer.text("Color","#FFFFFFFF")))
                        when(type) {
                            "Image" -> {
                                if(layer.text("Shape").equals("Circle",true)) c.clipPath(Path().apply { addCircle(0f,0f,min(w,h)/2,Path.Direction.CW) })
                                if(image!=null) texture(c,image,w,h,color)
                                else if(source.startsWith("internalres:")) procedural(c,source.substringAfter(':'),w,h,color)
                                else asset(layer.text("asset",source))?.let { picture ->
                                    val crop=layer.flag("keepAspectRatioAndCropToFit");val contain=layer.flag("keepAspectRatio")
                                    if(crop || contain) {
                                        val scale=if(crop) max(w/picture.width,h/picture.height) else min(w/picture.width,h/picture.height)
                                        c.clipRect(bounds(w,h));texture(c,picture,picture.width*scale,picture.height*scale,color)
                                    } else texture(c,picture,w,h,color)
                                }
                            }
                            "BlurEffect","MotionBlurEffect" -> if(image!=null) {
                                val strength=s.scene.animationIntensity.coerceIn(0f,2f)
                                texture(c,image,w,h,color)
                                if(strength>0) {
                                    val radius=layer.number("blurRadius",6f).coerceIn(0f,25f)*strength
                                    for(i in 0 until 8) {
                                        val a=i*2*PI/8;val save=c.save()
                                        c.translate((cos(a)*radius).toFloat(),(sin(a)*radius).toFloat())
                                        texture(c,image,w,h,color,24);c.restoreToCount(save)
                                    }
                                }
                            }
                            "RgbSplitEffect" -> if(image!=null) {
                                val shift=w*.008f*s.scene.animationIntensity
                                for((i,channel) in listOf(Color.RED,Color.GREEN,Color.BLUE).withIndex()) {
                                    val save=c.save();c.translate((i-1)*shift,0f)
                                    texture(c,image,w,h,channel,mode=PorterDuff.Mode.ADD);c.restoreToCount(save)
                                }
                            }
                            "MirrorEffect" -> if(image!=null) {
                                val mode=layer.text("mirrorMode","Horizontal")
                                val xs=if(mode.contains("Horizontal")) listOf(-1f,1f) else listOf(1f)
                                val ys=if(mode.contains("Vertical")) listOf(-1f,1f) else listOf(1f)
                                if(layer.flag("flipMirror")) c.scale(-1f,1f)
                                for(x in xs) for(y in ys) {
                                    val save=c.save();c.scale(x,y)
                                    c.clipRect(if(xs.size>1) 0f else -w/2,if(ys.size>1) 0f else -h/2,w/2,h/2)
                                    texture(c,image,w,h,color);c.restoreToCount(save)
                                }
                            }
                        }
                    } finally { c.restoreToCount(saved) }
                }
                visiting.remove(index);complete.add(index)
            }
        }
        render(0,canvas)
    }
    private fun procedural(c: Canvas,name: String,w: Float,h: Float,color: Int) {
        paint.reset();paint.isAntiAlias=true;paint.colorFilter=tint(color)
        when {
            name=="transparent" -> return
            name=="white" || name=="black" -> paint.color=if(name=="white") Color.WHITE else Color.BLACK
            name.contains("vignette") -> paint.shader=RadialGradient(0f,0f,max(1f,min(w,h)*.7f),intArrayOf(Color.TRANSPARENT,Color.BLACK),null,Shader.TileMode.CLAMP)
            name.contains("rainbow") -> paint.shader=LinearGradient(-w/2,0f,w/2,0f,IntArray(7) { Color.HSVToColor(floatArrayOf(it*60f,1f,1f)) },null,Shader.TileMode.CLAMP)
            name.contains("blur") || name.contains("particle") || name.contains("lens_flare") -> paint.shader=RadialGradient(0f,0f,max(1f,min(w,h)/2),intArrayOf(Color.WHITE,Color.TRANSPARENT),null,Shader.TileMode.CLAMP)
            else -> return
        }
        c.drawRect(bounds(w,h),paint);paint.shader=null;paint.colorFilter=null
    }
    override fun close() { buffers.values.forEach { it.recycle() };buffers.clear();images.values.forEach { it.recycle() };images.clear() }
}
