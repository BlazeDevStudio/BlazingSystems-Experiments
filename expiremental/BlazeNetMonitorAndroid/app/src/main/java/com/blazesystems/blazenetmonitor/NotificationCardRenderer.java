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
 * RGB_565 keeps the notification IPC image bounded (720 x 512, ~720 KiB).
 */
final class NotificationCardRenderer {
    static final int WIDTH=720, HEIGHT=512;
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
        text(c,p,"BLAZENETMONITOR  ·  LIVE NETWORK",26,32,36,WHITE,true,670);
        text(c,p,"DOWNLOAD  ↓ "+TrafficMath.speed(f.rx,bits),32,32,88,0xff79CEFF,true,657);
        text(c,p,"UPLOAD  ↑ "+TrafficMath.speed(f.tx,bits),30,32,127,0xffFFBD70,true,657);
        p.setStrokeWidth(2);
        p.setColor(0xff315575);
        c.drawLine(22,146,698,146,p);

        target(c,p,settings,0,f.status[0],f.detail[0],first,160);
        target(c,p,settings,1,f.status[1],f.detail[1],second,276);

        text(c,p,"SESSION   ↓ "+TrafficMath.data(f.sessionRx)+
            "    ↑ "+TrafficMath.data(f.sessionTx),25,28,419,WHITE,false,670);
        text(c,p,"TODAY       ↓ "+TrafficMath.data(f.dayRx)+
            "    ↑ "+TrafficMath.data(f.dayTx),25,28,455,WHITE,false,670);
        text(c,p,"MONTH     ↓ "+TrafficMath.data(f.monthRx)+
            "    ↑ "+TrafficMath.data(f.monthTx),25,28,491,WHITE,false,670);
        return result;
    }

    private static void target(Canvas c,Paint p,SharedPreferences settings,
                               int i,String health,String detail,Bitmap icon,int top){
        p.setColor(PANEL);
        c.drawRoundRect(new RectF(20,top,700,top+108),17,17,p);

        // Explicit 25px colored dot survives Android notification tinting
        // because it is baked into the RGB image, not a smallIcon glyph.
        p.setColor(healthColor(health));
        c.drawCircle(42,top+54,12,p);
        p.setColor(0xff061727);
        p.setStyle(Paint.Style.STROKE);
        p.setStrokeWidth(2.5f);
        c.drawCircle(42,top+54,12,p);
        p.setStyle(Paint.Style.FILL);

        if(icon!=null&&!icon.isRecycled()){
            p.setColor(Color.WHITE);
            c.drawRoundRect(new RectF(66,top+25,122,top+81),9,9,p);
            c.drawBitmap(icon,null,new Rect(70,top+29,118,top+77),p);
        }else {
            // No website logo was fetched; visibly show a globe fallback.
            p.setColor(0xff253F60);
            c.drawRoundRect(new RectF(66,top+25,122,top+81),9,9,p);
            p.setColor(0xffD4EBFC);
            p.setStrokeWidth(2.8f);
            p.setStyle(Paint.Style.STROKE);
            c.drawCircle(94,top+53,17,p);
            c.drawOval(new RectF(86,top+36,102,top+70),p);
            c.drawLine(77,top+53,111,top+53,p);
            p.setStyle(Paint.Style.FILL);
        }

        String title="Target "+(i+1)+" · "+StatusLabel.quality(health);
        text(c,p,title,30,140,top+36,healthColor(health),true,537);
        text(c,p,hostLabel(settings,i),24,140,top+70,WHITE,false,537);
        text(c,p,detail==null?"Checking connection":detail,21,
             140,top+99,MUTED,false,537);
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
