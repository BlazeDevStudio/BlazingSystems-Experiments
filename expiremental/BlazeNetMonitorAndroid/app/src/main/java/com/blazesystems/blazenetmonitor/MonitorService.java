package com.blazesystems.blazenetmonitor;

import android.app.*;
import android.content.*;
import android.content.pm.ServiceInfo;
import android.os.*;
import android.util.Log;
import java.util.concurrent.*;

/**
 * Dynamic small-icon bitmap notifications render current numerical speeds
 * in two adjacent status-bar slots. SystemUI owns layout/order/monochrome tint.
 * The expanded shade uses OS-owned InboxStyle, never risky custom RemoteViews
 * that can kill apps asynchronously after notify() returns successfully.
 */
public final class MonitorService extends Service {
    public static volatile boolean ACTIVE=false;
    public static final String ACTION_START="com.blazesystems.blazenetmonitor.START";
    public static final String ACTION_STOP="com.blazesystems.blazenetmonitor.STOP";
    private static final int NOTIFICATION_ID=101;
    private static final int DOWNLOAD_NOTIFICATION_ID=102;
    private static final String TAG="BlazeNetMonitor.Service";
    private static final String ERROR_KEY="service_start_error";
    private static final String CHANNEL="blazenetmonitor.active";
    private final Handler handler=new Handler(Looper.getMainLooper());
    private ExecutorService probes;
    private boolean running=false;
    private int ticks=0;

    private final Runnable poll=new Runnable() {
        @Override public void run() {
            if(!running)return;
            try {
                MonitorState.INSTANCE.sample(MonitorService.this);
                ++ticks;
                if(ticks%15==1)probeTargets();
                if(ticks%2==0)publish();
            } catch (RuntimeException e) {
                Log.e(TAG,"Monitor sampling error",e);
                recordError(e.getClass().getSimpleName()+": "+safeMessage(e));
            } finally {
                if(running)handler.postDelayed(this,1000);
            }
        }
    };

    @Override public void onCreate() {
        super.onCreate();
        probes=Executors.newFixedThreadPool(2);
        NotificationChannel channel=new NotificationChannel(
            CHANNEL,"Network speed · At a glance",NotificationManager.IMPORTANCE_LOW);
        channel.setDescription("Network speeds and traffic summary in notification shade");
        channel.setShowBadge(false);
        NotificationManager manager=getSystemService(NotificationManager.class);
        if(manager!=null)manager.createNotificationChannel(channel);
    }

    @Override public int onStartCommand(Intent intent,int flags,int startId) {
        String action=intent==null?ACTION_START:intent.getAction();
        if(ACTION_STOP.equals(action)) {
            stopSelf();
            return START_NOT_STICKY;
        }
        if(!running)startMonitor();
        return START_NOT_STICKY;
    }

    private void startMonitor() {
        if(running)return;
        // Exactly the same standard Notification.Builder path is used on
        // the first start and EVERY subsequent update. No custom views.
        try {
            // Promote within the OS deadline with a static, known-good icon.
            // Live bitmap status icons are posted once foreground operation is active.
            Notification initial=notification(false);
            if(Build.VERSION.SDK_INT>=34)
                startForeground(NOTIFICATION_ID,initial,
                    ServiceInfo.FOREGROUND_SERVICE_TYPE_SPECIAL_USE);
            else startForeground(NOTIFICATION_ID,initial);
        } catch(RuntimeException e) {
            Log.e(TAG,"Foreground monitor start rejected",e);
            recordError(e.getClass().getSimpleName()+": "+safeMessage(e));
            stopSelf();
            return;
        }
        getSharedPreferences("settings",0).edit().remove(ERROR_KEY).apply();
        running=true;
        ACTIVE=true;
        handler.post(poll);
        publish();
    }

    private static String safeMessage(Throwable e) {
        String value=e.getMessage();
        return value==null?"Android rejected the operation":
            value.substring(0,Math.min(180,value.length()));
    }

    private void recordError(String message) {
        getSharedPreferences("settings",0).edit().putString(ERROR_KEY,message).apply();
    }


    private android.graphics.drawable.Icon liveIcon(MonitorState.Frame f,
            boolean bits,boolean upload){
        try{
            return StatusSpeedIcon.icon(upload?f.tx:f.rx,bits,
                f.status[upload?0:1],upload);
        }catch(RuntimeException e){
            Log.e(TAG,"Dynamic status icon failed; keeping static icon",e);
            return android.graphics.drawable.Icon.createWithResource(
                this,R.drawable.ic_notification_status);
        }
    }

    /** Second live icon provides the download value alongside upload in
      * the OS-managed status bar. Some OEMs collapse, re-order or suppress
      * icons; no accessibility/overlay injection is used. */
    private Notification downloadNotification(MonitorState.Frame f,boolean bits){
        PendingIntent open=PendingIntent.getActivity(this,12,
            new Intent(this,MainActivity.class).addFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP),
            PendingIntent.FLAG_IMMUTABLE|PendingIntent.FLAG_UPDATE_CURRENT);
        String text="↓ "+TrafficMath.speed(f.rx,bits);
        return new Notification.Builder(this,CHANNEL)
            .setSmallIcon(liveIcon(f,bits,false))
            .setContentTitle("BlazeNetMonitor · Download")
            .setContentText(text)
            .setContentIntent(open)
            .setOngoing(true).setOnlyAlertOnce(true).setShowWhen(false)
            .setCategory(Notification.CATEGORY_SERVICE)
            .build();
    }

    private String speed(MonitorState.Frame f,boolean bits) {
        return "↑ "+TrafficMath.speed(f.tx,bits)+
            "    ↓ "+TrafficMath.speed(f.rx,bits);
    }

    /** OS template (InboxStyle), not user-supplied RemoteViews. */
    private Notification notification(boolean dynamicIcon) {
        MonitorState.Frame f=MonitorState.INSTANCE.frame();
        boolean bits=getSharedPreferences("settings",0).getBoolean("bits",true);
        String strip=StatusLabel.strip(f.status[0],
            TrafficMath.speed(f.tx,bits),TrafficMath.speed(f.rx,bits),f.status[1]);
        PendingIntent open=PendingIntent.getActivity(this,12,
            new Intent(this,MainActivity.class).addFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP),
            PendingIntent.FLAG_IMMUTABLE|PendingIntent.FLAG_UPDATE_CURRENT);
        PendingIntent stop=PendingIntent.getService(this,13,
            new Intent(this,MonitorService.class).setAction(ACTION_STOP),
            PendingIntent.FLAG_IMMUTABLE|PendingIntent.FLAG_UPDATE_CURRENT);

        Notification.InboxStyle details=new Notification.InboxStyle()
            .setBigContentTitle("At a glance · "+speed(f,bits))
            .addLine(StatusLabel.dot(f.status[0])+" Target 1  "+f.detail[0])
            .addLine(StatusLabel.dot(f.status[1])+" Target 2  "+f.detail[1])
            .addLine("Session  ↓ "+TrafficMath.data(f.sessionRx)+
                "  ↑ "+TrafficMath.data(f.sessionTx))
            .addLine("Today     ↓ "+TrafficMath.data(f.dayRx)+
                "  ↑ "+TrafficMath.data(f.dayTx))
            .addLine("Month   ↓ "+TrafficMath.data(f.monthRx)+
                "  ↑ "+TrafficMath.data(f.monthTx));

        return new Notification.Builder(this,CHANNEL)
            .setSmallIcon(dynamicIcon?liveIcon(f,bits,true):
                android.graphics.drawable.Icon.createWithResource(
                    this,R.drawable.ic_notification_status))
            .setContentTitle("BlazeNetMonitor")
            .setContentText(strip)
            .setStyle(details)
            .setContentIntent(open)
            .setOngoing(true).setOnlyAlertOnce(true).setShowWhen(false)
            .setCategory(Notification.CATEGORY_SERVICE)
            .addAction(new Notification.Action.Builder(
                android.R.drawable.ic_menu_close_clear_cancel,"Stop",stop).build())
            .build();
    }

    private void publish() {
        try {
            NotificationManager manager=getSystemService(NotificationManager.class);
            if(manager!=null) {
                MonitorState.Frame frame=MonitorState.INSTANCE.frame();
                boolean bits=getSharedPreferences("settings",0).getBoolean("bits",true);
                manager.notify(NOTIFICATION_ID,notification(true));
                manager.notify(DOWNLOAD_NOTIFICATION_ID,downloadNotification(frame,bits));
            }
        } catch(RuntimeException e) {
            Log.e(TAG,"Notification update failed",e);
            recordError("Notification error: "+safeMessage(e));
            // Do not stop an already running service; no risky alternate
            // rendering path that can cause an async Bad notification crash.
        }
    }

    private void probeTargets() {
        if(probes==null||probes.isShutdown())return;
        for(int i=0;i<2;i++) {
            final int index=i;
            probes.execute(()->{
                HealthProbe.Result result=HealthProbe.run(
                    getSharedPreferences("settings",0),index);
                MonitorState.INSTANCE.health(index,result.quality,result.message);
                handler.post(()->{if(running)publish();});
            });
        }
    }

    @Override public void onDestroy() {
        running=false;
        ACTIVE=false;
        handler.removeCallbacks(poll);
        if(probes!=null)probes.shutdownNow();
        NotificationManager manager=getSystemService(NotificationManager.class);
        if(manager!=null)manager.cancel(DOWNLOAD_NOTIFICATION_ID);
        MonitorState.INSTANCE.save(this);
        super.onDestroy();
    }

    @Override public IBinder onBind(Intent intent){return null;}
}
