package com.blazesystems.blazenetmonitor;

import android.app.*;
import android.content.*;
import android.content.pm.ServiceInfo;
import android.os.*;
import android.widget.RemoteViews;
import java.util.concurrent.*;

/**
 * User-started network monitor. The status bar is OS-managed: it displays
 * our small notification icon, NOT arbitrary numbers beside Wi-Fi/battery.
 * Expanded notification replaces Windows' At-a-glance hover.
 */
public final class MonitorService extends Service {
    public static volatile boolean ACTIVE=false;
    public static final String ACTION_START="com.blazesystems.blazenetmonitor.START";
    public static final String ACTION_STOP="com.blazesystems.blazenetmonitor.STOP";
    private static final int NOTIFICATION_ID=101;
    private static final String CHANNEL="blazenetmonitor.active";
    private final Handler handler=new Handler(Looper.getMainLooper());
    private ExecutorService probes;
    private boolean running=false;
    private int ticks=0;
    private final Runnable poll=new Runnable(){
        @Override public void run(){
            if(!running)return;
            MonitorState.INSTANCE.sample(MonitorService.this);
            ticks++;
            if(ticks%15==1)probeTargets();
            // Periodic speed changes are delivered to the collapsed and
            // expanded notification. The OS may throttle their presentation.
            if(ticks%2==0)publish();
            handler.postDelayed(this,1000);
        }
    };
    @Override public void onCreate(){
        super.onCreate();
        probes=Executors.newFixedThreadPool(2);
        NotificationChannel channel=new NotificationChannel(
            CHANNEL,"Network speed · At a glance",NotificationManager.IMPORTANCE_LOW);
        channel.setDescription("Status bar indicator and expanded speed, health and data totals");
        channel.setShowBadge(false);
        getSystemService(NotificationManager.class).createNotificationChannel(channel);
    }
    @Override public int onStartCommand(Intent intent,int flags,int startId){
        String action=intent==null?ACTION_START:intent.getAction();
        if(ACTION_STOP.equals(action)){stopSelf();return START_NOT_STICKY;}
        if(!running)startMonitor();
        return START_NOT_STICKY;
    }
    private void startMonitor(){
        if(running)return;
        try{
            if(Build.VERSION.SDK_INT>=34)
                startForeground(NOTIFICATION_ID,notification(),
                    ServiceInfo.FOREGROUND_SERVICE_TYPE_SPECIAL_USE);
            else startForeground(NOTIFICATION_ID,notification());
        }catch(Exception e){
            stopSelf();
            return;
        }
        running=true;
        ACTIVE=true;
        handler.post(poll);
    }
    private void publish(){
        try{
            NotificationManager manager=getSystemService(NotificationManager.class);
            if(manager!=null)manager.notify(NOTIFICATION_ID,notification());
        }catch(Exception ignored){
            // Notification permission or OEM restrictions can prevent rendering;
            // avoid crashing the traffic collector.
        }
    }
    private void probeTargets(){
        if(probes==null||probes.isShutdown())return;
        for(int i=0;i<2;i++){
            final int index=i;
            probes.execute(()->{
                HealthProbe.Result result=HealthProbe.run(
                    getSharedPreferences("settings",0),index);
                MonitorState.INSTANCE.health(index,result.quality,result.message);
                handler.post(()->{if(running)publish();});
            });
        }
    }
    private String speeds(MonitorState.Frame frame,boolean bits){
        return "↑ "+TrafficMath.speed(frame.tx,bits)+
            "    ↓ "+TrafficMath.speed(frame.rx,bits);
    }

    /** Left health dot, upload, download, right health dot.
      * This is the COLLAPSED notification row, not the OS-owned status-bar strip. */
    private RemoteViews compact(MonitorState.Frame frame,boolean bits){
        RemoteViews row=new RemoteViews(getPackageName(),R.layout.notification_speed_strip);
        row.setTextViewText(R.id.strip_dot_left,"●");
        row.setTextViewText(R.id.strip_upload,
            "↑ "+TrafficMath.speed(frame.tx,bits));
        row.setTextViewText(R.id.strip_download,
            "↓ "+TrafficMath.speed(frame.rx,bits));
        row.setTextViewText(R.id.strip_dot_right,"●");
        row.setTextColor(R.id.strip_dot_left,healthColor(frame.status[0]));
        row.setTextColor(R.id.strip_dot_right,healthColor(frame.status[1]));
        return row;
    }
    private static int healthColor(String value){
        if("Green".equals(value))return 0xff46bd86;
        if("Yellow".equals(value))return 0xffe6b64e;
        if("Orange".equals(value))return 0xffff9d3b;
        if("Red".equals(value))return 0xfff06e77;
        return 0xff9baac0;
    }
    private RemoteViews expanded(MonitorState.Frame frame,boolean bits){
        RemoteViews views=new RemoteViews(getPackageName(),R.layout.notification_glance);
        views.setTextViewText(R.id.notif_speed,speeds(frame,bits));
        views.setTextViewText(R.id.notif_target1,
            "● Target 1 · "+frame.status[0]+"  ·  "+frame.detail[0]);
        views.setTextViewText(R.id.notif_target2,
            "● Target 2 · "+frame.status[1]+"  ·  "+frame.detail[1]);
        views.setTextColor(R.id.notif_target1,healthColor(frame.status[0]));
        views.setTextColor(R.id.notif_target2,healthColor(frame.status[1]));
        views.setTextViewText(R.id.notif_session,
            "Session   ↓ "+TrafficMath.data(frame.sessionRx)+
            "    ↑ "+TrafficMath.data(frame.sessionTx));
        views.setTextViewText(R.id.notif_today,
            "Today     ↓ "+TrafficMath.data(frame.dayRx)+
            "    ↑ "+TrafficMath.data(frame.dayTx));
        views.setTextViewText(R.id.notif_month,
            "Month    ↓ "+TrafficMath.data(frame.monthRx)+
            "    ↑ "+TrafficMath.data(frame.monthTx));
        return views;
    }
    private Notification notification(){
        MonitorState.Frame frame=MonitorState.INSTANCE.frame();
        boolean bits=getSharedPreferences("settings",0).getBoolean("bits",true);
        String speed=speeds(frame,bits);
        PendingIntent open=PendingIntent.getActivity(this,12,
            new Intent(this,MainActivity.class).addFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP),
            PendingIntent.FLAG_IMMUTABLE|PendingIntent.FLAG_UPDATE_CURRENT);
        PendingIntent stop=PendingIntent.getService(this,13,
            new Intent(this,MonitorService.class).setAction(ACTION_STOP),
            PendingIntent.FLAG_IMMUTABLE|PendingIntent.FLAG_UPDATE_CURRENT);
        return new Notification.Builder(this,CHANNEL)
            .setSmallIcon(R.drawable.ic_notification_status)
            .setContentTitle("BlazeNetMonitor · At a glance")
            .setContentText(speed)
            .setStyle(new Notification.DecoratedCustomViewStyle())
            .setCustomContentView(compact(frame,bits))
            .setCustomBigContentView(expanded(frame,bits))
            .setContentIntent(open)
            .setOngoing(true)
            .setOnlyAlertOnce(true)
            .setShowWhen(false)
            .setCategory(Notification.CATEGORY_SERVICE)
            .addAction(new Notification.Action.Builder(
                android.R.drawable.ic_menu_close_clear_cancel,"Stop",stop).build())
            .build();
    }
    @Override public void onDestroy(){
        running=false;
        ACTIVE=false;
        handler.removeCallbacks(poll);
        if(probes!=null)probes.shutdownNow();
        MonitorState.INSTANCE.save(this);
        super.onDestroy();
    }
    @Override public IBinder onBind(Intent intent){return null;}
}
