package com.blazesystems.blazenetmonitor;

import android.content.Context;
import android.content.SharedPreferences;
import android.net.TrafficStats;
import android.os.SystemClock;
import java.text.SimpleDateFormat;
import java.util.ArrayDeque;
import java.util.Date;
import java.util.Locale;

/**
 * TrafficStats counts device-wide traffic since boot, all interfaces combined,
 * not one selected Wi-Fi/LAN interface or app-specific totals.
 * No fake per-app attribution. Counter resets/unsupported states are guarded.
 */
public final class MonitorState {
    public static final MonitorState INSTANCE = new MonitorState();
    public static final class Frame {
        public final double rx, tx;
        public final long sessionRx, sessionTx, dayRx, dayTx, monthRx, monthTx;
        public final float[] down, up;
        public final String[] status, detail;
        Frame(double rx,double tx,long sessionRx,long sessionTx,long dayRx,long dayTx,
              long monthRx,long monthTx,float[] down,float[] up,String[] status,String[] detail) {
            this.rx=rx;this.tx=tx;this.sessionRx=sessionRx;this.sessionTx=sessionTx;
            this.dayRx=dayRx;this.dayTx=dayTx;this.monthRx=monthRx;this.monthTx=monthTx;
            this.down=down;this.up=up;this.status=status;this.detail=detail;
        }
    }
    private final ArrayDeque<Float> down = new ArrayDeque<>();
    private final ArrayDeque<Float> up = new ArrayDeque<>();
    private final String[] health={"Waiting","Waiting"};
    private final String[] detail={"No sample","No sample"};
    private double rxRate=0,txRate=0;
    private long sessionRx=0,sessionTx=0,dayRx=0,dayTx=0,monthRx=0,monthTx=0;
    private long priorRx=-1,priorTx=-1,priorTime=-1,lastSave=0;
    private String day="", month="";
    private final SimpleDateFormat dayFormat=new SimpleDateFormat("yyyy-MM-dd",Locale.US);
    private final SimpleDateFormat monthFormat=new SimpleDateFormat("yyyy-MM",Locale.US);
    private MonitorState(){}
    public synchronized void sample(Context context) {
        SharedPreferences p=context.getSharedPreferences("meter",Context.MODE_PRIVATE);
        long now=SystemClock.elapsedRealtime(), currentRx=TrafficStats.getTotalRxBytes(),
                currentTx=TrafficStats.getTotalTxBytes();
        if(priorTime<0){
            day=p.getString("day","");
            month=p.getString("month","");
            dayRx=p.getLong("dayRx",0);dayTx=p.getLong("dayTx",0);
            monthRx=p.getLong("monthRx",0);monthTx=p.getLong("monthTx",0);
            // Do not attribute bytes from before the monitoring process started.
            priorTime=now;priorRx=currentRx;priorTx=currentTx;
            refreshKeys();return;
        }
        refreshKeys();
        long rx=TrafficMath.delta(priorRx,currentRx);
        long tx=TrafficMath.delta(priorTx,currentTx);
        long elapsed=now-priorTime;
        // A very long pause (device suspension) is not an instantaneous speed spike;
        // its aggregate bytes still count if the counters are monotonic.
        rxRate=TrafficMath.bytesPerSecond(rx,elapsed);
        txRate=TrafficMath.bytesPerSecond(tx,elapsed);
        if(elapsed<=0){rxRate=0;txRate=0;}
        sessionRx=safeAdd(sessionRx,rx); sessionTx=safeAdd(sessionTx,tx);
        dayRx=safeAdd(dayRx,rx); dayTx=safeAdd(dayTx,tx);
        monthRx=safeAdd(monthRx,rx);monthTx=safeAdd(monthTx,tx);
        priorRx=currentRx;priorTx=currentTx;priorTime=now;
        down.addLast((float)Math.min(1.0e9,rxRate));up.addLast((float)Math.min(1.0e9,txRate));
        while(down.size()>120)down.removeFirst();
        while(up.size()>120)up.removeFirst();
        if(now-lastSave>10000){persist(p);lastSave=now;}
    }
    private long safeAdd(long a,long b){return b>Long.MAX_VALUE-a?Long.MAX_VALUE:a+b;}
    private void refreshKeys(){
        String newDay=dayFormat.format(new Date()),newMonth=monthFormat.format(new Date());
        if(!newMonth.equals(month)){month=newMonth;monthRx=0;monthTx=0;}
        if(!newDay.equals(day)){day=newDay;dayRx=0;dayTx=0;}
    }
    private void persist(SharedPreferences p){
        p.edit().putString("day",day).putString("month",month)
        .putLong("dayRx",dayRx).putLong("dayTx",dayTx)
        .putLong("monthRx",monthRx).putLong("monthTx",monthTx).apply();
    }
    public synchronized void save(Context c){persist(c.getSharedPreferences("meter",0));}
    public synchronized void health(int index,String quality,String message){
        if(index>=0&&index<2){health[index]=quality;detail[index]=message;}
    }
    public synchronized Frame frame(){
        float[] d=new float[down.size()],u=new float[up.size()];
        int i=0;for(float x:down)d[i++]=x;
        i=0;for(float x:up)u[i++]=x;
        return new Frame(rxRate,txRate,sessionRx,sessionTx,dayRx,dayTx,monthRx,monthTx,
                d,u,health.clone(),detail.clone());
    }
}
