package com.blazesystems.blazenetmonitor;

import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.Typeface;
import android.graphics.drawable.Icon;
import java.util.Locale;

/** Download-only numeric monochrome status icon. Full details are in shade. */
public final class StatusSpeedIcon {
    private StatusSpeedIcon() {}

    public static String shortSpeed(double bytesPerSecond,boolean bits){
        if(Double.isNaN(bytesPerSecond)||bytesPerSecond<=0)return bits?"0b":"0B";
        double value=bytesPerSecond*(bits?8d:1d);
        if(Double.isInfinite(value))return "MAX";
        String[] units=bits?new String[]{"b","K","M","G"}:
            new String[]{"B","K","M","G"};
        int tier=0;
        while(value>=1000&&tier<3){value/=1000;tier++;}
        if(value>=999.5&&tier<3){value/=1000;tier++;}
        String number=value<4&&tier>0?
            String.format(Locale.US,"%.1f",value):
            String.format(Locale.US,"%.0f",value);
        return number+units[tier];
    }

    public static Bitmap bitmap(double bytesPerSecond,boolean bits){
        final int size=96;
        Bitmap bitmap=Bitmap.createBitmap(size,size,Bitmap.Config.ALPHA_8);
        Canvas canvas=new Canvas(bitmap);
        canvas.drawColor(Color.TRANSPARENT,android.graphics.PorterDuff.Mode.CLEAR);
        Paint p=new Paint(Paint.ANTI_ALIAS_FLAG);
        p.setColor(Color.WHITE);
        p.setTextAlign(Paint.Align.CENTER);
        p.setTypeface(Typeface.create("sans-serif-condensed",Typeface.BOLD));
        String value=shortSpeed(bytesPerSecond,bits);
        p.setTextSize(72f);
        while(p.measureText(value)>90f && p.getTextSize()>28f)
            p.setTextSize(p.getTextSize()-2f);
        Paint.FontMetrics fm=p.getFontMetrics();
        canvas.drawText(value,size/2f,(size-(fm.ascent+fm.descent))/2f,p);
        return bitmap;
    }

    public static Icon icon(double bytesPerSecond,boolean bits){
        return Icon.createWithBitmap(bitmap(bytesPerSecond,bits));
    }
}
