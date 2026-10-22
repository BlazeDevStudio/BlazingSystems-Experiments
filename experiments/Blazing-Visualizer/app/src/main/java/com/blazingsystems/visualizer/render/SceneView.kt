package com.blazingsystems.visualizer.render
import android.content.Context
import android.view.*
import java.io.File
/** Sleeps between updates. A generation owns its own EGL context and ends before replacement. */
class SceneView(context:Context):SurfaceView(context),SurfaceHolder.Callback {
 private val lock=Object();private var generation=0;private var worker:Thread?=null
 @Volatile private var current:EvaluatedScene?=null
 var assets=File(context.filesDir,"assets")
 init{holder.addCallback(this)}
 fun update(scene:EvaluatedScene){synchronized(lock){if(current!=scene){current=scene;lock.notifyAll()}}}
 override fun surfaceCreated(h:SurfaceHolder){}
 override fun surfaceChanged(h:SurfaceHolder,format:Int,width:Int,height:Int){stop();if(width<=0 || height<=0)return;val token=synchronized(lock){++generation}
  worker=Thread({runCatching{GlTarget.encoder(h.surface,width,height).use {target->GlSceneRenderer(assets).use{renderer->var last:EvaluatedScene?=null;while(true){val next=synchronized(lock){while(token==generation && current==last)lock.wait();if(token!=generation)null else current};if(next==null)break;renderer.render(next,target);target.present();last=next}}}}},"Visualizer preview").also{it.start()}
 }
 override fun surfaceDestroyed(h:SurfaceHolder)=stop()
 private fun stop(){synchronized(lock){generation++;lock.notifyAll()};worker?.join(1500);worker=null}
}
