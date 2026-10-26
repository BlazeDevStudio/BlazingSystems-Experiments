package com.blazesystems.blazenetmonitor;

import android.app.*;
import android.content.*;
import android.content.pm.ServiceInfo;
import android.os.*;
import java.util.concurrent.*;
import android.provider.Settings;

/** Persistent opt-in user-visible monitor; never starts automatically from boot. */
public final class MonitorService extends Service {
    public static volatile boolean ACTIVE = false;
    public static final String ACTION_START="com.blazesystems.blazenetmonitor.START";
    public static final String ACTION_STOP="com.blazesystems.blazenetmonitor.STOP";
    public static final String ACTION_WIDGET="com.blazesystems.blazenetmonitor.WIDGET";
    private static final String CHANNEL="blazenetmonitor.active";
    private final Handler handler=new Handler(Looper.getMainLooper());
    private ExecutorService probes;
    private FloatingWidget bubble;
    private boolean running=false;
    private int ticks=0;
    private final Runnable poll=new Runnable(){
        @Override public void run(){
            if(!running)return;
            MonitorState.INSTANCE.sample(MonitorService.this);
            if(ticks++%4==0) {
                NotificationManager mgr=getSystemService(NotificationManager.class);
                if(mgr!=null)mgr.notify(101,notification());
            }
            if(ticks%15==1) probeTargets();
            if(bubble!=null)bubble.update(MonitorState.INSTANCE.frame(),getSharedPreferences("settings",0));
            handler.postDelayed(this,1000);
        }
    };
    @Override public void onCreate(){
        super.onCreate();
        probes=Executors.newFixedThreadPool(2);
        bubble=new FloatingWidget(this);
        NotificationChannel ch=new NotificationChannel(CHANNEL,"Active network monitor",NotificationManager.IMPORTANCE_LOW);
        ch.setDescription("Device-wide speeds while you keep BlazeNetMonitor running");
        getSystemService(NotificationManager.class).createNotificationChannel(ch);
    }
    @Override public int onStartCommand(Intent intent,int flags,int startId){
        String action=intent==null?ACTION_START:intent.getAction();
        if(ACTION_STOP.equals(action)){stopSelf();return START_NOT_STICKY;}
        if(ACTION_WIDGET.equals(action)){
            setOverlay(!getSharedPreferences("settings",0).getBoolean("overlay",false));
            if(!running)startMonitor();
        }else if(!running)startMonitor();
        return START_NOT_STICKY; // user must explicitly restart after OS kills process
    }
    private void startMonitor(){
        if(running)return;
        try {
            if(Build.VERSION.SDK_INT>=34)
                startForeground(101,notification(),ServiceInfo.FOREGROUND_SERVICE_TYPE_SPECIAL_USE);
            else startForeground(101,notification());
        }catch(Exception e){
            stopSelf();
            return;
        }
        running=true;
        ACTIVE=true;
        if(getSharedPreferences("settings",0).getBoolean("overlay",false))bubble.show();
        handler.post(poll);
    }
    private void setOverlay(boolean enabled){
        if(enabled&&!Settings.canDrawOverlays(this))return;
        getSharedPreferences("settings",0).edit().putBoolean("overlay",enabled).apply();
        if(enabled)bubble.show();else bubble.hide();
    }
    private void probeTargets(){
        if(probes==null||probes.isShutdown())return;
        for(int i=0;i<2;i++){
            final int index=i;
            probes.execute(()->{
                HealthProbe.Result result=HealthProbe.run(getSharedPreferences("settings",0),index);
                MonitorState.INSTANCE.health(index,result.quality,result.message);
            });
        }
    }
    private Notification notification(){
        MonitorState.Frame frame=MonitorState.INSTANCE.frame();
        boolean bits=getSharedPreferences("settings",0).getBoolean("bits",true);
        String speed="↓ "+TrafficMath.speed(frame.rx,bits)+"   ↑ "+TrafficMath.speed(frame.tx,bits);
        Intent open=new Intent(this,MainActivity.class).addFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP);
        PendingIntent content=PendingIntent.getActivity(this,12,open,PendingIntent.FLAG_IMMUTABLE|PendingIntent.FLAG_UPDATE_CURRENT);
        Intent stop=new Intent(this,MonitorService.class).setAction(ACTION_STOP);
        PendingIntent stopAction=PendingIntent.getService(this,13,stop,PendingIntent.FLAG_IMMUTABLE|PendingIntent.FLAG_UPDATE_CURRENT);
        return new Notification.Builder(this,CHANNEL)
            .setSmallIcon(R.drawable.ic_blaze)
            .setContentTitle("BlazeNetMonitor · Device traffic")
            .setContentText(speed).setStyle(new Notification.BigTextStyle().bigText(speed))
            .setContentIntent(content).setOngoing(true).setOnlyAlertOnce(true)
            .addAction(new Notification.Action.Builder(
                android.R.drawable.ic_menu_close_clear_cancel,"Stop",stopAction).build())
            .build();
    }
    @Override public void onDestroy(){
        running=false;
        ACTIVE=false;
        handler.removeCallbacks(poll);
        if(bubble!=null)bubble.hide();
        if(probes!=null)probes.shutdownNow();
        MonitorState.INSTANCE.save(this);
        super.onDestroy();
    }
    @Override public IBinder onBind(Intent intent){return null;}
}
