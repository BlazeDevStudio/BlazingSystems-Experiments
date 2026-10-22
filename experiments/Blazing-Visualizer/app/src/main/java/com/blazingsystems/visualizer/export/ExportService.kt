package com.blazingsystems.visualizer.export
import android.app.*
import android.content.*
import android.content.pm.ServiceInfo
import android.os.*
import androidx.core.content.ContextCompat
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*
import java.io.File
import java.util.UUID
object ExportHub {
 private val mutable=MutableStateFlow<List<ExportJob>>(emptyList());val jobs:StateFlow<List<ExportJob>> = mutable
 private var initialized=false
 @Synchronized fun initialize(context:Context){if(!initialized){mutable.value=ExportJobStore(File(context.filesDir,"exports")).recover();initialized=true}}
 @Synchronized fun update(context:Context,job:ExportJob){initialize(context);ExportJobStore(File(context.filesDir,"exports")).save(job);mutable.value=(mutable.value.filterNot{it.id==job.id}+job)}
 fun enqueue(context:Context,request:ExportRequest){initialize(context);val job=ExportJob(UUID.randomUUID().toString(),request);update(context,job);ContextCompat.startForegroundService(context,Intent(context,ExportService::class.java).putExtra("job",job.id))}
 fun cancel(context:Context,id:String){context.startService(Intent(context,ExportService::class.java).putExtra("cancel",id))}
}
class ExportService:Service() {
 private val scope=CoroutineScope(SupervisorJob()+Dispatchers.Main.immediate);private val running=linkedMapOf<String,Job>()
 override fun onCreate(){super.onCreate();ExportHub.initialize(this);getSystemService(NotificationManager::class.java).createNotificationChannel(NotificationChannel("export","Video export",NotificationManager.IMPORTANCE_LOW))}
 private fun notification(text:String,progress:Float):Notification=Notification.Builder(this,"export").setSmallIcon(android.R.drawable.ic_menu_save).setContentTitle("Blazing Visualizer").setContentText(text).setOngoing(true).setProgress(100,(progress*100).toInt(),progress<=0).setContentIntent(PendingIntent.getActivity(this,0,packageManager.getLaunchIntentForPackage(packageName),PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT)).build()
 override fun onStartCommand(intent:Intent?,flags:Int,startId:Int):Int {
  val n=notification("Preparing video",0f);if(Build.VERSION.SDK_INT>=35)startForeground(22,n,ServiceInfo.FOREGROUND_SERVICE_TYPE_MEDIA_PROCESSING) else if(Build.VERSION.SDK_INT>=29)startForeground(22,n,ServiceInfo.FOREGROUND_SERVICE_TYPE_DATA_SYNC) else startForeground(22,n)
  intent?.getStringExtra("cancel")?.let{running[it]?.cancel()}
  intent?.getStringExtra("job")?.let{id->if(id !in running){val initial=ExportHub.jobs.value.find{it.id==id};if(initial!=null){running[id]=scope.launch{var current=initial.copy(status=ExportStatus.RUNNING);ExportHub.update(this@ExportService,current)
   try {VideoExporter(this@ExportService).export(initial.request){p->current=current.copy(progress=p);ExportHub.update(this@ExportService,current);getSystemService(NotificationManager::class.java).notify(22,notification("Exporting ${(p*100).toInt()}%",p))};ExportHub.update(this@ExportService,current.copy(status=ExportStatus.COMPLETED,progress=1f))
   }catch(cancelled:CancellationException){ExportHub.update(this@ExportService,current.copy(status=ExportStatus.CANCELLED,message="Export cancelled"))}catch(failure:Throwable){ExportHub.update(this@ExportService,current.copy(status=ExportStatus.FAILED,message=failure.localizedMessage ?: "Export failed"))}finally{running.remove(id);if(running.isEmpty()){stopForeground(STOP_FOREGROUND_REMOVE);stopSelf()}}
  }}}}
  if(running.isEmpty()){stopForeground(STOP_FOREGROUND_REMOVE);stopSelf()};return START_NOT_STICKY
 }
 override fun onBind(intent:Intent?)=null
 override fun onDestroy(){scope.cancel();super.onDestroy()}
 override fun onTimeout(startId:Int,fgsType:Int){scope.cancel();stopSelf()}
}
