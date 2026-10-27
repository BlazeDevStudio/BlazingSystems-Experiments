package com.blazesystems.blazenetmonitor;
import org.junit.Test;
import static org.junit.Assert.*;

public final class StatusSpeedIconTest {
    @Test public void statusIconShowsShortDownloadValue() {
        assertEquals("0b",StatusSpeedIcon.shortSpeed(0,true));
        assertEquals("0B",StatusSpeedIcon.shortSpeed(0,false));
        assertEquals("1.2M",StatusSpeedIcon.shortSpeed(150000,true));
        assertEquals("500K",StatusSpeedIcon.shortSpeed(500000,false));
    }
    @Test public void nonfiniteOrNegativeSpeedsAreSafe() {
        assertEquals("0b",StatusSpeedIcon.shortSpeed(Double.NaN,true));
        assertEquals("0B",StatusSpeedIcon.shortSpeed(-123,false));
    }
}
