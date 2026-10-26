package com.blazesystems.blazenetmonitor;
import android.content.Context;
import android.graphics.*;
import android.util.Base64;
import android.view.View;

/** PayPal QR bitstream from the finished Windows v1.0.0 project, not a new recipient. */
public final class DonationQrView extends View {
    public static final String PAYPAL="https://www.paypal.com/qrcodes/p2pqrc/AEBWES36GX9K2";
    private static final String BITS="/hn2Fz/BOYEFkG6rZ4Qrt1t+sWXbpMMu0uwR63NFB/qqqqr+ANkkEAAbZ2zchh7HTwisi5tbZZ7YoHfhv6h3B40LHKKiagj3GV5eyZbqFisSrj9mq7XBfr+noaeB6SSMXj0OssvdZybkL5M1jCnpnHEKrEzhYPq+k6nqbmB5oKf+gnQcfdDNyX/xdy0TGmnveWuSHVclqjgyy918+Ldr4ubOMWbTyRIB/oBivsFFv696JeqQQmEfsTuq3wP/ndbSHMie6R80VW8Et8Mwnf5ektOuAA==";
    private final Paint paint=new Paint(Paint.ANTI_ALIAS_FLAG);
    private final byte[] matrix=Base64.decode(BITS,Base64.DEFAULT);
    public DonationQrView(Context context){super(context);setMinimumHeight(290);setMinimumWidth(290);}
    @Override protected void onMeasure(int width,int height){
        int desired=(int)(300*getResources().getDisplayMetrics().density);
        int w=resolveSize(desired,width);
        setMeasuredDimension(w,w);
    }
    @Override protected void onDraw(Canvas c){
        super.onDraw(c);
        c.drawColor(Color.WHITE);
        // Quiet zone 4 modules on all sides, required for reliable scanners.
        float side=Math.min(getWidth(),getHeight());
        float unit=side/49f;
        float ox=(getWidth()-side)/2f, oy=(getHeight()-side)/2f;
        paint.setColor(Color.BLACK);
        for(int y=0;y<41;y++)for(int x=0;x<41;x++){
            int index=y*41+x;
            if((matrix[index>>3]&(1<<(7-(index&7))))!=0)
                c.drawRect(ox+(x+4)*unit,oy+(y+4)*unit,
                    ox+(x+5)*unit,oy+(y+5)*unit,paint);
        }
    }
}
