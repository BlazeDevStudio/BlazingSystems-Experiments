package com.blazesystems.blazenetmonitor;

import android.app.Application;
import android.content.SharedPreferences;
import android.util.Log;
import java.util.Date;
import java.util.Locale;

/** Keeps a bounded, local copy of unexpected Java crashes for user diagnosis. */
public final class BlazeApplication extends Application {
    private static final String TAG="BlazeNetMonitor.Crash";
    private static final String PREFS="crash_diagnostics";
    private static final String KEY="last_exception";
    @Override public void onCreate() {
        super.onCreate();
        final Thread.UncaughtExceptionHandler previous=
            Thread.getDefaultUncaughtExceptionHandler();
        Thread.setDefaultUncaughtExceptionHandler((thread,error)->{
            try {
                String text=String.format(Locale.US,"BlazeNetMonitor Android %s | %s | %s\n",
                    "0.1.3-preview.1",new Date(),thread.getName())+
                    Log.getStackTraceString(error);
                if(text.length()>10000)text=text.substring(0,10000);
                getSharedPreferences(PREFS,MODE_PRIVATE).edit()
                    .putString(KEY,text).commit();
            }catch(Throwable ignored){}
            if(previous!=null)previous.uncaughtException(thread,error);
            else System.exit(2);
        });
    }
    public static String crashReport(android.content.Context c) {
        return c.getSharedPreferences(PREFS,MODE_PRIVATE).getString(KEY,"");
    }
    public static void clearCrash(android.content.Context c) {
        c.getSharedPreferences(PREFS,MODE_PRIVATE).edit().remove(KEY).apply();
    }
}
