package com.blazesystems.blazenetmonitor;

import android.app.*;
import android.content.*;
import android.content.pm.ServiceInfo;
import android.os.*;
import android.util.Log;
import java.util.concurrent.*;

/**
 * The system STATUS BAR can show our monochrome small notification icon only.
 * The live speed/target status is rendered by the OS-owned notification template
 * in the SHADE. Avoid ALL custom RemoteViews: invalid RemoteViews may kill
 * Android processes asynchronously (RemoteServiceException / Bad notification)
 * after notify() has already returned successfully.
 */
public final class MonitorService extends Service {
    public static volatile boolean ACTIVE=false;
    public static final String ACTION_START="com.blazesystems.blazenetmonitor.START";
    public static final String ACTION_STOP="com.blazesystems.blazenetmonitor.STOP";
    private static final int NOTIFICATION_ID=101;
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
            Notification initial=notification();
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
    }

    private static String safeMessage(Throwable e) {
        String value=e.getMessage();
        return value==null?"Android rejected the operation":
            value.substring(0,Math.min(180,value.length()));
    }

    private void recordError(String message) {
        getSharedPreferences("settings",0).edit().putString(ERROR_KEY,message).apply();
    }

    private static String dot(String health) {
        if("Green".equals(health))return "🟢";
        if("Yellow".equals(health))return "🟡";
        if("Orange".equals(health))return "🟠";
        if("Red".equals(health))return "🔴";
        if("Blue".equals(health))return "🔵";
        return "⚪";
    }

    private String speed(MonitorState.Frame f,boolean bits) {
        return "↑ "+TrafficMath.speed(f.tx,bits)+
            "    ↓ "+TrafficMath.speed(f.rx,bits);
    }

    /** OS template (InboxStyle), not user-supplied RemoteViews. */
    private Notification notification() {
        MonitorState.Frame f=MonitorState.INSTANCE.frame();
        boolean bits=getSharedPreferences("settings",0).getBoolean("bits",true);
        String strip=dot(f.status[0])+"  "+speed(f,bits)+"  "+dot(f.status[1]);
        PendingIntent open=PendingIntent.getActivity(this,12,
            new Intent(this,MainActivity.class).addFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP),
            PendingIntent.FLAG_IMMUTABLE|PendingIntent.FLAG_UPDATE_CURRENT);
        PendingIntent stop=PendingIntent.getService(this,13,
            new Intent(this,MonitorService.class).setAction(ACTION_STOP),
            PendingIntent.FLAG_IMMUTABLE|PendingIntent.FLAG_UPDATE_CURRENT);

        Notification.InboxStyle details=new Notification.InboxStyle()
            .setBigContentTitle("At a glance · "+speed(f,bits))
            .addLine(dot(f.status[0])+" Target 1  "+f.detail[0])
            .addLine(dot(f.status[1])+" Target 2  "+f.detail[1])
            .addLine("Session  ↓ "+TrafficMath.data(f.sessionRx)+
                "  ↑ "+TrafficMath.data(f.sessionTx))
            .addLine("Today     ↓ "+TrafficMath.data(f.dayRx)+
                "  ↑ "+TrafficMath.data(f.dayTx))
            .addLine("Month   ↓ "+TrafficMath.data(f.monthRx)+
                "  ↑ "+TrafficMath.data(f.monthTx));

        return new Notification.Builder(this,CHANNEL)
            .setSmallIcon(R.drawable.ic_notification_status)
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
            if(manager!=null)manager.notify(NOTIFICATION_ID,notification());
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
        MonitorState.INSTANCE.save(this);
        super.onDestroy();
    }

    @Override public IBinder onBind(Intent intent){return null;}
}
