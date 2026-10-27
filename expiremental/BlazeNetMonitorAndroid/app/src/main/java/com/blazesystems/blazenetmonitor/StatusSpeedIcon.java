package com.blazesystems.blazenetmonitor;

import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.Typeface;
import android.graphics.drawable.Icon;
import java.util.Locale;

/**
 * Monochrome dynamic small notification icons, as in other speed meters.
 * The OS scales and tints each icon into a small status-bar slot.
 * Two notifications provide left-dot upload and download right-dot indicators.
 */
public final class StatusSpeedIcon {
    private StatusSpeedIcon(){}

    public static String shortSpeed(double bytesPerSecond,boolean bits){
        double value=Math.max(0,bytesPerSecond)*(bits?8d:1d);
        String[] units=bits?new String[]{"b","K","M","G"}:
            new String[]{"B","K","M","G"};
        int tier=0;
        while(value>=1000&&tier<3){value/=1000;tier++;}
        if(value>=999.5&&tier<3){value/=1000;tier++;}
        String number=value<10&&tier>0?
            String.format(Locale.US,"%.1f",value):
            String.format(Locale.US,"%.0f",value);
        return number+units[tier];
    }

    public static Bitmap bitmap(double bytesPerSecond,boolean bits,
                                String health,boolean upload){
        final int size=96;
        Bitmap bitmap=Bitmap.createBitmap(size,size,Bitmap.Config.ALPHA_8);
        Canvas canvas=new Canvas(bitmap);
        canvas.drawColor(Color.TRANSPARENT,android.graphics.PorterDuff.Mode.CLEAR);
        Paint p=new Paint(Paint.ANTI_ALIAS_FLAG);
        p.setColor(Color.WHITE);
        p.setTextAlign(Paint.Align.CENTER);
        p.setTypeface(Typeface.create("sans-serif-condensed",Typeface.BOLD));
        String value=shortSpeed(bytesPerSecond,bits);
        p.setTextSize(value.length()>5?39f:value.length()>4?47f:54f);
        canvas.drawText(value,48,56,p);
        p.setTextSize(27f);
        canvas.drawText(upload?"↑":"↓",48,88,p);
        // Status icons are monochrome: filled=good, ring=degraded,
        // crossed=unreachable. Exact colors remain visible in app.
        float x=upload?11:85,y=13;
        p.setStyle(Paint.Style.STROKE);p.setStrokeWidth(3f);
        if("Green".equals(health)){
            p.setStyle(Paint.Style.FILL);canvas.drawCircle(x,y,8,p);
        }else if("Red".equals(health)){
            canvas.drawCircle(x,y,8,p);
            canvas.drawLine(x-5,y-5,x+5,y+5,p);
            canvas.drawLine(x+5,y-5,x-5,y+5,p);
        }else if("Yellow".equals(health)||"Orange".equals(health)){
            canvas.drawCircle(x,y,8,p);
            if("Orange".equals(health))canvas.drawLine(x,y-4,x,y+4,p);
        }else canvas.drawCircle(x,y,5,p);
        return bitmap;
    }

    public static Icon icon(double bytesPerSecond,boolean bits,
                            String quality,boolean upload){
        return Icon.createWithBitmap(bitmap(bytesPerSecond,bits,quality,upload));
    }
}
