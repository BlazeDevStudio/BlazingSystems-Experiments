package com.blazesystems.blazerental;

import android.content.Context;
import android.content.SharedPreferences;
import android.os.Build;
import android.os.PersistableBundle;
import android.os.SystemClock;

public final class LeaseStore {
    private static final String PREFS="blaze_rental";
    private LeaseStore(){}
    static Context storage(Context c){ return Build.VERSION.SDK_INT>=24?c.createDeviceProtectedStorageContext():c; }
    static SharedPreferences p(Context c){ return storage(c).getSharedPreferences(PREFS,Context.MODE_PRIVATE); }

    public static void acceptProvisioningExtras(Context c,PersistableBundle b){
        if(b==null)return;
        p(c).edit().putString("server",safe(b.getString("server_url")))
                .putString("enroll",safe(b.getString("enrollment_token")))
                .putString("device_name",safe(b.getString("device_name"))).apply();
    }
    public static void saveManualEnrollment(Context c,String serverUrl,String enrollmentToken,String deviceName){
        p(c).edit().putString("server",safe(serverUrl)).putString("enroll",safe(enrollmentToken))
                .putString("device_name",safe(deviceName)).remove("device_id").remove("device_secret")
                .remove("server_now").remove("lease_until").remove("elapsed_sync").apply();
    }
    public static void recordServerState(Context c,long serverNowMs,long leaseUntilMs,String deviceSecret,
                                         String allowed,String adminSalt,String adminHash,int adminRounds,
                                         String preferredVendo,int secondsPerPulse){
        p(c).edit().putLong("server_now",serverNowMs).putLong("lease_until",leaseUntilMs)
                .putLong("elapsed_sync",SystemClock.elapsedRealtime()).putString("device_secret",safe(deviceSecret))
                .putString("allowed_packages",safe(allowed)).putString("admin_salt",safe(adminSalt))
                .putString("admin_hash",safe(adminHash)).putInt("admin_rounds",adminRounds)
                .putString("preferred_vendo",safe(preferredVendo)).putInt("seconds_per_pulse",secondsPerPulse).apply();
        RentalAlarmReceiver.schedule(c,leaseUntilMs-serverNowMs);
    }
    public static boolean isLeaseValid(Context c){
        SharedPreferences s=p(c); long synced=s.getLong("elapsed_sync",0),serverNow=s.getLong("server_now",0),until=s.getLong("lease_until",0),elapsed=SystemClock.elapsedRealtime();
        if(synced<=0||serverNow<=0||until<=serverNow||elapsed<synced)return false;
        return serverNow+(elapsed-synced)<until;
    }
    public static long remainingMs(Context c){
        SharedPreferences s=p(c); long synced=s.getLong("elapsed_sync",0),serverNow=s.getLong("server_now",0),until=s.getLong("lease_until",0),elapsed=SystemClock.elapsedRealtime();
        if(synced<=0||elapsed<synced)return 0;
        return Math.max(0,until-(serverNow+(elapsed-synced)));
    }
    public static void invalidateCachedLeaseAfterBoot(Context c){ p(c).edit().putLong("elapsed_sync",0).apply(); }
    public static String server(Context c){ return p(c).getString("server",""); }
    public static String enrollment(Context c){ return p(c).getString("enroll",""); }
    public static String deviceSecret(Context c){ return p(c).getString("device_secret",""); }
    public static String deviceId(Context c){ return p(c).getString("device_id",""); }
    public static void setDeviceIdentity(Context c,String id,String secret){ p(c).edit().putString("device_id",safe(id)).putString("device_secret",safe(secret)).apply(); }
    public static String deviceName(Context c){ return p(c).getString("device_name","Rental phone"); }
    public static boolean isEnrolled(Context c){ return !deviceSecret(c).isEmpty(); }
    public static String allowedPackages(Context c){ return p(c).getString("allowed_packages","*"); }
    public static String preferredVendo(Context c){ return p(c).getString("preferred_vendo",""); }
    public static int secondsPerPulse(Context c){ return p(c).getInt("seconds_per_pulse",600); }

    public static boolean isAdminWindowActive(Context c){
        return p(c).getLong("admin_unlock_until",0)>SystemClock.elapsedRealtime();
    }
    public static boolean verifyAdminPassword(Context c,String password){
        SharedPreferences s=p(c); long now=SystemClock.elapsedRealtime(),locked=s.getLong("admin_locked_until",0);
        if(now<locked)return false;
        String salt=s.getString("admin_salt",""),stored=s.getString("admin_hash",""); int rounds=s.getInt("admin_rounds",4096);
        if(salt.isEmpty()||stored.isEmpty())return false;
        boolean ok=false; try{ok=stored.equals(Hmac.sha256Iter(password,salt,rounds));}catch(Exception ignored){}
        SharedPreferences.Editor e=s.edit();
        if(ok){ e.putInt("admin_failures",0).putLong("admin_locked_until",0).putLong("admin_unlock_until",now+300000L).apply(); return true; }
        int failures=s.getInt("admin_failures",0)+1;
        if(failures>=5)e.putInt("admin_failures",0).putLong("admin_locked_until",now+900000L); else e.putInt("admin_failures",failures);
        e.apply(); return false;
    }
    private static String safe(String s){ return s==null?"":s.trim(); }
}
