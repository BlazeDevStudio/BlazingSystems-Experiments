package com.blazesystems.blazenetmonitor;
import org.junit.Test;
import static org.junit.Assert.*;
public class TrafficMathTest {
    @Test public void counterResetNeverInflatesTotals() {
        assertEquals(120, TrafficMath.delta(300,420));
        assertEquals(0, TrafficMath.delta(500, 20));
        assertEquals(0, TrafficMath.delta(-1,20));
    }
    @Test public void monotonicTiming() {
        assertEquals(1024.0, TrafficMath.bytesPerSecond(512,500),0.01);
        assertEquals(0.0, TrafficMath.bytesPerSecond(512,0),0.01);
    }
    @Test public void statusIconSpeedCompactUnits() {
        assertEquals("0b",StatusSpeedIcon.shortSpeed(0,true));
        assertEquals("8K",StatusSpeedIcon.shortSpeed(1000,true));
        assertEquals("1.2M",StatusSpeedIcon.shortSpeed(150000,true));
        assertEquals("1.0K",StatusSpeedIcon.shortSpeed(1000,false));
    }
    @Test public void formatsSpeedsAndData() {
        assertEquals("8.0 Kbps", TrafficMath.speed(1000,true));
        assertEquals("1.0 KB/s", TrafficMath.speed(1000,false));
        assertEquals("1.0 KB", TrafficMath.data(1024));
    }
}
