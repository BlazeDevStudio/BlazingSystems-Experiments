package com.blazesystems.blazenetmonitor;
import android.content.Context;
import android.graphics.*;
import android.view.View;
import android.content.SharedPreferences;
import java.util.*;

/** Lightweight scalable Canvas graph; no WebView and no chart dependencies. */
public final class SpeedGraph extends View {
    private float[] rx=new float[0],tx=new float[0];
    private String style="Smooth";
    private final Paint paint=new Paint(Paint.ANTI_ALIAS_FLAG);
    private final int[] palette={Color.rgb(52,195,255),Color.rgb(255,157,59)};
    SpeedGraph(Context c){super(c);setMinimumHeight(dp(155));}
    private int dp(int x){return Math.round(getResources().getDisplayMetrics().density*x);}
    void data(MonitorState.Frame f,String style){
        this.rx=f.down;this.tx=f.up;this.style=style;invalidate();
    }
    @Override protected void onMeasure(int w,int h){
        super.onMeasure(w,MeasureSpec.makeMeasureSpec(dp(168),MeasureSpec.EXACTLY));
    }
    @Override protected void onDraw(Canvas canvas){
        super.onDraw(canvas);
        canvas.drawColor(Color.rgb(8,25,50));
        float width=getWidth(),height=getHeight(),top=dp(18),base=height-dp(23),left=dp(8),right=width-dp(8);
        paint.setStyle(Paint.Style.STROKE);paint.setStrokeWidth(dp(1));
        paint.setColor(Color.rgb(35,56,83));
        for(int i=0;i<4;i++){float y=top+(base-top)*i/3f;canvas.drawLine(left,y,right,y,paint);}
        float max=1024;
        for(float n:rx)max=Math.max(max,n);
        for(float n:tx)max=Math.max(max,n);
        drawSeries(canvas,rx,palette[0],left,right,top,base,max);
        drawSeries(canvas,tx,palette[1],left,right,top,base,max);
        paint.setStyle(Paint.Style.FILL);paint.setColor(Color.LTGRAY);paint.setTextSize(dp(10));
        canvas.drawText("RECENT TRAFFIC · "+style,dp(9),height-dp(7),paint);
        paint.setColor(palette[0]);canvas.drawText("↓",right-dp(34),height-dp(7),paint);
        paint.setColor(palette[1]);canvas.drawText("↑",right-dp(17),height-dp(7),paint);
    }
    private void drawSeries(Canvas c,float[] values,int color,float left,float right,float top,float base,float max){
        if(values.length<2)return;
        float span=right-left;
        float[] xx=new float[values.length],yy=new float[values.length];
        for(int i=0;i<values.length;i++){
            xx[i]=left+span*i/(values.length-1f);
            yy[i]=base-Math.min(values[i]/max,1f)*(base-top);
        }
        paint.setColor(color);paint.setStrokeWidth(dp(1.7f));paint.setStrokeCap(Paint.Cap.ROUND);
        paint.setStyle(Paint.Style.STROKE);
        Path path=new Path();path.moveTo(xx[0],yy[0]);
        boolean smooth="Smooth".equals(style);
        for(int i=1;i<values.length;i++){
            if("Steps".equals(style)){
                path.lineTo(xx[i],yy[i-1]);path.lineTo(xx[i],yy[i]);
            }else if(smooth){
                float mid=(xx[i-1]+xx[i])/2;
                path.cubicTo(mid,yy[i-1],mid,yy[i],xx[i],yy[i]);
            }else path.lineTo(xx[i],yy[i]);
        }
        if("Dots".equals(style)){
            paint.setStyle(Paint.Style.FILL);
            for(int i=0;i<values.length;i+=Math.max(1,values.length/70))
                c.drawCircle(xx[i],yy[i],dp(1.6f),paint);
        }else if("Bars".equals(style)||"Impulse".equals(style)){
            for(int i=0;i<values.length;i+=Math.max(1,values.length/80))
                c.drawLine(xx[i],base,xx[i],yy[i],paint);
        }else if("Filled".equals(style)){
            path.lineTo(xx[values.length-1],base);path.lineTo(left,base);path.close();
            paint.setStyle(Paint.Style.FILL);paint.setColor((color&0x00ffffff)|0x55000000);
            c.drawPath(path,paint);
            paint.setStyle(Paint.Style.STROKE);paint.setColor(color);
            c.drawPath(path,paint);
        }else c.drawPath(path,paint);
    }
    private int dp(float x){return Math.round(getResources().getDisplayMetrics().density*x);}
}
