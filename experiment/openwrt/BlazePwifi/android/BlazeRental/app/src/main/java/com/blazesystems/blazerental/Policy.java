package com.blazesystems.blazerental;

import android.app.Activity;
import android.app.admin.DevicePolicyManager;
import android.content.*;
import android.content.pm.PackageManager;
import android.content.pm.ResolveInfo;
import android.os.Build;
import android.os.UserManager;
import android.provider.Settings;
import java.util.*;

public final class Policy {
    private Policy(){}
    public static ComponentName admin(Context c){ return new ComponentName(c,BlazeDeviceAdminReceiver.class); }
    public static boolean isDeviceOwner(Context c){
        DevicePolicyManager d=(DevicePolicyManager)c.getSystemService(Context.DEVICE_POLICY_SERVICE);
        return d!=null&&d.isDeviceOwnerApp(c.getPackageName());
    }
    public static List<String> launchablePackages(Context c){
        PackageManager pm=c.getPackageManager(); Intent q=new Intent(Intent.ACTION_MAIN); q.addCategory(Intent.CATEGORY_LAUNCHER);
        List<ResolveInfo> rs=pm.queryIntentActivities(q,PackageManager.MATCH_ALL); TreeSet<String> out=new TreeSet<>();
        for(ResolveInfo r:rs){
            if(r.activityInfo==null)continue; String p=r.activityInfo.packageName;
            if(p==null||p.equals(c.getPackageName())||p.equals("com.android.settings")||p.contains("packageinstaller")||p.contains("permissioncontroller"))continue;
            out.add(p);
        }
        return new ArrayList<>(out);
    }
    public static List<String> effectiveAllowedPackages(Context c){
        LinkedHashSet<String> out=new LinkedHashSet<>(); out.add(c.getPackageName());
        if(!LeaseStore.isLeaseValid(c))return new ArrayList<>(out);
        String configured=LeaseStore.allowedPackages(c); List<String> installed=launchablePackages(c);
        if(configured==null||configured.isEmpty()||configured.equals("*"))out.addAll(installed);
        else{Set<String>wanted=new HashSet<>(Arrays.asList(configured.split(",")));for(String p:installed)if(wanted.contains(p))out.add(p);}
        return new ArrayList<>(out);
    }
    public static String inventoryCsv(Context c){ return android.text.TextUtils.join(",",launchablePackages(c)); }
    public static void applyManagedPolicy(Context c){
        DevicePolicyManager d=(DevicePolicyManager)c.getSystemService(Context.DEVICE_POLICY_SERVICE);
        if(d==null||!d.isDeviceOwnerApp(c.getPackageName()))return;
        ComponentName a=admin(c); boolean adminWindow=LeaseStore.isAdminWindowActive(c); List<String> allow=effectiveAllowedPackages(c);
        if(adminWindow&&!allow.contains("com.android.settings"))allow.add("com.android.settings");
        try{d.setLockTaskPackages(a,allow.toArray(new String[0]));}catch(Exception ignored){}
        if(Build.VERSION.SDK_INT>=28){try{d.setLockTaskFeatures(a,DevicePolicyManager.LOCK_TASK_FEATURE_NONE);}catch(Exception ignored){}}
        try{IntentFilter f=new IntentFilter(Intent.ACTION_MAIN);f.addCategory(Intent.CATEGORY_HOME);f.addCategory(Intent.CATEGORY_DEFAULT);d.addPersistentPreferredActivity(a,f,new ComponentName(c,MainActivity.class));}catch(Exception ignored){}
        restrict(d,a,UserManager.DISALLOW_ADD_USER);restrict(d,a,UserManager.DISALLOW_SAFE_BOOT);restrict(d,a,UserManager.DISALLOW_FACTORY_RESET);restrict(d,a,UserManager.DISALLOW_DEBUGGING_FEATURES);restrict(d,a,UserManager.DISALLOW_INSTALL_UNKNOWN_SOURCES);
        try{d.setStatusBarDisabled(a,!adminWindow);}catch(Exception ignored){} try{d.setKeyguardDisabled(a,true);}catch(Exception ignored){}
    }
    private static void restrict(DevicePolicyManager d,ComponentName a,String r){try{d.addUserRestriction(a,r);}catch(Exception ignored){}}
    public static void openHome(Context c){
        if(LeaseStore.isAdminWindowActive(c))return;
        Intent i=new Intent(c,MainActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_CLEAR_TOP|Intent.FLAG_ACTIVITY_SINGLE_TOP);
        try{c.startActivity(i);}catch(Exception ignored){}
    }
    public static boolean launchPackage(Context c,String pkg){
        if(!effectiveAllowedPackages(c).contains(pkg))return false; Intent i=c.getPackageManager().getLaunchIntentForPackage(pkg);if(i==null)return false;
        i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);try{c.startActivity(i);return true;}catch(Exception e){return false;}
    }
    public static void enterAdminSettings(Activity a){
        if(!isDeviceOwner(a)||!LeaseStore.isAdminWindowActive(a))return; try{a.stopLockTask();}catch(Exception ignored){} applyManagedPolicy(a);
        try{a.startActivity(new Intent(Settings.ACTION_SETTINGS));}catch(Exception ignored){}
    }
}
