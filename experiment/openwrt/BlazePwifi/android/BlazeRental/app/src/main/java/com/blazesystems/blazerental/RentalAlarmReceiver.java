package com.blazesystems.blazerental;

import android.app.AlarmManager;
import android.app.PendingIntent;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.os.SystemClock;

public class RentalAlarmReceiver extends BroadcastReceiver {
    private static final int REQ=9301;

    public static void schedule(Context c,long remainingMs){
        AlarmManager a=(AlarmManager)c.getSystemService(Context.ALARM_SERVICE);
        if(a==null)return;
        long delay=Math.max(1000L,Math.min(remainingMs>0?remainingMs:15000L,60000L));
        Intent i=new Intent(c,RentalAlarmReceiver.class);
        PendingIntent p=PendingIntent.getBroadcast(c,REQ,i,PendingIntent.FLAG_UPDATE_CURRENT|PendingIntent.FLAG_IMMUTABLE);
        a.setAndAllowWhileIdle(AlarmManager.ELAPSED_REALTIME_WAKEUP,SystemClock.elapsedRealtime()+delay,p);
    }

    @Override public void onReceive(Context c,Intent i){
        final PendingResult pending=goAsync();
        new Thread(()->{
            try{
                if(LeaseStore.isEnrolled(c)) LeaseClient.sync(c);
                Policy.applyManagedPolicy(c);
                if(!LeaseStore.isLeaseValid(c)) Policy.openHome(c);
                schedule(c,LeaseStore.remainingMs(c));
            }finally{pending.finish();}
        }).start();
    }
}
