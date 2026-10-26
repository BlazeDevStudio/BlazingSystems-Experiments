package com.blazesystems.blazenetmonitor;

import android.content.*;
import android.graphics.Color;
import android.graphics.PixelFormat;
import android.graphics.drawable.GradientDrawable;
import android.os.Build;
import android.provider.Settings;
import android.view.*;
import android.widget.*;
/** Movable opt-in overlay, shown only after SYSTEM_ALERT_WINDOW permission. */
final class FloatingWidget {
    private final Context context;
    private final WindowManager wm;
    private WindowManager.LayoutParams params;
    private TextView text;
    private boolean shown;
    FloatingWidget(Context c){
        context=c;
        wm=(WindowManager)c.getSystemService(Context.WINDOW_SERVICE);
    }
    private int dp(float n){return (int)(n*context.getResources().getDisplayMetrics().density+.5f);}
    void show(){
        if(shown||Build.VERSION.SDK_INT<26||!Settings.canDrawOverlays(context))return;
        text=new TextView(context);
        text.setTextColor(Color.WHITE);
        text.setTextSize(12f);
        text.setPadding(dp(12),dp(9),dp(12),dp(9));
        text.setText("↓ 0.0 Kbps    ↑ 0.0 Kbps\nBlazeNetMonitor");
        GradientDrawable bg=new GradientDrawable();
        bg.setColor(Color.argb(237,0,26,61));bg.setCornerRadius(dp(12));
        bg.setStroke(dp(1),Color.rgb(0,102,255));text.setBackground(bg);
        params=new WindowManager.LayoutParams(dp(213),dp(66),
             WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY,
             WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE,
             PixelFormat.TRANSLUCENT);
        params.gravity=Gravity.TOP|Gravity.START;params.x=dp(12);params.y=dp(105);
        text.setOnTouchListener(new View.OnTouchListener(){
            float startX,startY;int fromX,fromY;long down;
            @Override public boolean onTouch(View v,android.view.MotionEvent e){
                if(e.getAction()==MotionEvent.ACTION_DOWN){
                    startX=e.getRawX();startY=e.getRawY();fromX=params.x;fromY=params.y;
                    down=System.currentTimeMillis();return true;
                }
                if(e.getAction()==MotionEvent.ACTION_MOVE){
                    params.x=Math.max(0,fromX+Math.round(e.getRawX()-startX));
                    params.y=Math.max(0,fromY+Math.round(e.getRawY()-startY));
                    try{wm.updateViewLayout(text,params);}catch(Exception ignored){}
                    return true;
                }
                if(e.getAction()==MotionEvent.ACTION_UP){
                    float delta=Math.abs(e.getRawX()-startX)+Math.abs(e.getRawY()-startY);
                    if(delta<dp(9)&&System.currentTimeMillis()-down<450){
                        Intent open=new Intent(context,MainActivity.class)
                            .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_SINGLE_TOP);
                        try{context.startActivity(open);}catch(Exception ignored){}
                    }
                    return true;
                }
                return false;
            }
        });
        try{wm.addView(text,params);shown=true;}catch(Exception ignored){shown=false;}
    }
    void update(MonitorState.Frame frame,android.content.SharedPreferences pref){
        if(!shown||text==null)return;
        boolean bits=pref.getBoolean("bits",true);
        text.setText("↓ "+TrafficMath.speed(frame.rx,bits)+"   ↑ "+TrafficMath.speed(frame.tx,bits)
            +"\nBlazeNetMonitor · device");
    }
    void hide(){
        if(!shown)return;
        shown=false;
        try{wm.removeView(text);}catch(Exception ignored){}
        text=null;
    }
}
