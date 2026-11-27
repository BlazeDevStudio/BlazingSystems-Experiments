package com.blazesystems.blazerental;

import android.app.admin.DeviceAdminService;
import android.os.Handler;
import android.os.Looper;
import android.os.SystemClock;

public class BlazeDeviceAdminService extends DeviceAdminService {
    private final Handler h=new Handler(Looper.getMainLooper());private long lastSync=0,lastHome=0;
    private final Runnable loop=new Runnable(){public void run(){
        try{
            Policy.applyManagedPolicy(BlazeDeviceAdminService.this);long now=SystemClock.elapsedRealtime();
            if(LeaseStore.isEnrolled(BlazeDeviceAdminService.this)&&now-lastSync>(LeaseStore.isLeaseValid(BlazeDeviceAdminService.this)?15000:4000)){lastSync=now;new Thread(()->LeaseClient.sync(BlazeDeviceAdminService.this)).start();}
            if(!LeaseStore.isAdminWindowActive(BlazeDeviceAdminService.this)&&!LeaseStore.isLeaseValid(BlazeDeviceAdminService.this)&&now-lastHome>2500){lastHome=now;Policy.openHome(BlazeDeviceAdminService.this);}
        }catch(Exception ignored){}h.postDelayed(this,2000);
    }};
    @Override public void onCreate(){super.onCreate();h.post(loop);}
    @Override public void onDestroy(){h.removeCallbacks(loop);super.onDestroy();}
}
