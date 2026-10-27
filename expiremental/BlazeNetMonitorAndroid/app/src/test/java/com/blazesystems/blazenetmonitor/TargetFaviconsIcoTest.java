package com.blazesystems.blazenetmonitor;
import org.junit.Test;
import static org.junit.Assert.*;

public final class TargetFaviconsIcoTest {
    @Test public void acceptsBoundedPngFrame() {
        byte[] png={(byte)137,80,78,71,13,10,26,10,4,3,2};
        byte[] ico=new byte[22+png.length];
        ico[2]=1;ico[4]=1;ico[14]=(byte)png.length;ico[18]=22;
        System.arraycopy(png,0,ico,22,png.length);
        assertArrayEquals(png,TargetFavicons.icoPngFrame(ico));
    }
    @Test public void rejectsBadOffsetsAndPayloads() {
        byte[] bad=new byte[40];bad[2]=1;bad[4]=1;bad[14]=11;bad[18]=100;
        assertNull(TargetFavicons.icoPngFrame(bad));
        bad[18]=22;
        assertNull(TargetFavicons.icoPngFrame(bad));
        assertNull(TargetFavicons.icoPngFrame(null));
    }
}
