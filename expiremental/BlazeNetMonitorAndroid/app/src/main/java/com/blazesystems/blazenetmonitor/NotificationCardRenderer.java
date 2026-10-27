package com.blazesystems.blazenetmonitor;

import android.content.Context;
import android.content.SharedPreferences;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.Rect;
import android.graphics.RectF;

/**
 * Standard BigPictureStyle image; never RemoteViews.
 * Two large independently colored health dots and two actual site favicon
 * bitmaps when available. A clearly recognizable globe is the honest
 * fallback for sites without a decodable HTTPS PNG icon.
 * RGB_565 keeps the notification IPC image bounded (720 x 426, ~600 KiB).
 */
final class NotificationCardRenderer {
    static final int WIDTH=720, HEIGHT=426;
    private static final int WHITE=0xffF4F8FF, MUTED=0xffB0C8DE;
    private static final int PANEL=0xff142F50;
    private NotificationCardRenderer(){}

    static int healthColor(String quality) {
        if("Green".equals(quality))return 0xff4FE596;
        if("Yellow".equals(quality))return 0xffFFE07A;
        if("Orange".equals(quality))return 0xffFFAD59;
        if("Red".equals(quality))return 0xffFF6D7C;
        return 0xffA8B8D0;
    }

    static String hostLabel(SharedPreferences settings,int i){
        String input=settings.getString("target"+i,i==0?
            "https://www.google.com":"https://www.cloudflare.com");
        String host=TargetFavicons.publicHostname(input);
        return host.isEmpty()?"Site icon unavailable":host;
    }

    static Bitmap render(Context context,MonitorState.Frame f,boolean bits,
                         SharedPreferences settings,Bitmap first,Bitmap second){
        Bitmap result=Bitmap.createBitmap(WIDTH,HEIGHT,Bitmap.Config.RGB_565);
        Canvas c=new Canvas(result);
        c.drawColor(0xff091B31);
        Paint p=new Paint(Paint.ANTI_ALIAS_FLAG);
        p.setTypeface(android.graphics.Typeface.create("sans-serif",1));
        text(c,p,"BLAZENETMONITOR  ·  LIVE NETWORK",25,30,30,WHITE,true,675);
        text(c,p,"DOWNLOAD  ↓ "+TrafficMath.speed(f.rx,bits),30,30,67,0xff79CEFF,true,660);
        text(c,p,"UPLOAD  ↑ "+TrafficMath.speed(f.tx,bits),29,30,105,0xffFFBD70,true,660);
        p.setStrokeWidth(2);
        p.setColor(0xff315575);
        c.drawLine(22,116,698,116,p);

        target(c,p,settings,0,f.status[0],f.detail[0],first,122);
        target(c,p,settings,1,f.status[1],f.detail[1],second,217);

        text(c,p,"SESSION   ↓ "+TrafficMath.data(f.sessionRx)+
            "    ↑ "+TrafficMath.data(f.sessionTx),23,28,347,WHITE,false,670);
        text(c,p,"TODAY       ↓ "+TrafficMath.data(f.dayRx)+
            "    ↑ "+TrafficMath.data(f.dayTx),23,28,381,WHITE,false,670);
        text(c,p,"MONTH     ↓ "+TrafficMath.data(f.monthRx)+
            "    ↑ "+TrafficMath.data(f.monthTx),23,28,415,WHITE,false,670);
        return result;
    }

    private static void target(Canvas c,Paint p,SharedPreferences settings,
                               int i,String health,String detail,Bitmap icon,int top){
        p.setColor(PANEL);
        c.drawRoundRect(new RectF(20,top,700,top+90),17,17,p);

        // Explicit 25px colored dot survives Android notification tinting
        // because it is baked into the RGB image, not a smallIcon glyph.
        p.setColor(healthColor(health));
        c.drawCircle(42,top+45,12,p);
        p.setColor(0xff061727);
        p.setStyle(Paint.Style.STROKE);
        p.setStrokeWidth(2.5f);
        c.drawCircle(42,top+45,12,p);
        p.setStyle(Paint.Style.FILL);

        if(icon!=null&&!icon.isRecycled()){
            p.setColor(Color.WHITE);
            c.drawRoundRect(new RectF(66,top+16,122,top+72),9,9,p);
            c.drawBitmap(icon,null,new Rect(70,top+20,118,top+68),p);
        }else {
            // No website logo was fetched; visibly show a globe fallback.
            p.setColor(0xff253F60);
            c.drawRoundRect(new RectF(66,top+16,122,top+72),9,9,p);
            p.setColor(0xffD4EBFC);
            p.setStrokeWidth(2.8f);
            p.setStyle(Paint.Style.STROKE);
            c.drawCircle(94,top+44,17,p);
            c.drawOval(new RectF(86,top+27,102,top+61),p);
            c.drawLine(77,top+44,111,top+44,p);
            p.setStyle(Paint.Style.FILL);
        }

        String title="Target "+(i+1)+" · "+StatusLabel.quality(health);
        text(c,p,title,28,140,top+28,healthColor(health),true,537);
        text(c,p,hostLabel(settings,i),22,140,top+54,WHITE,false,537);
        text(c,p,detail==null?"Checking connection":detail,20,
             140,top+79,MUTED,false,537);
    }

    private static void text(Canvas c,Paint p,String value,float size,float x,
                             float y,int color,boolean bold,int max){
        p.setColor(color);p.setTextSize(size);
        p.setTypeface(android.graphics.Typeface.create("sans-serif",
            bold?android.graphics.Typeface.BOLD:android.graphics.Typeface.NORMAL));
        String v=value==null?"":value;
        while(v.length()>1&&p.measureText(v)>max)
            v=v.substring(0,v.length()-1);
        if(value!=null&&v.length()<value.length()&&v.length()>3)
            v=v.substring(0,v.length()-3)+"...";
        c.drawText(v,x,y,p);
    }
}
