package com.blazesystems.blazenetmonitor;
import org.junit.Test;
import static org.junit.Assert.*;

public final class StatusLabelTest {
    @Test public void oneShadeShowsDownloadFirstWithoutDots() {
        assertEquals("↓ 8.5 Mbps    ↑ 1.2 Mbps",
            StatusLabel.strip("1.2 Mbps","8.5 Mbps"));
    }
    @Test public void healthStatesAreReadableWords() {
        assertEquals("Online",StatusLabel.quality("Green"));
        assertEquals("Slow",StatusLabel.quality("Yellow"));
        assertEquals("Delayed",StatusLabel.quality("Orange"));
        assertEquals("Offline",StatusLabel.quality("Red"));
        assertEquals("Checking",StatusLabel.quality(null));
    }
    @Test public void neverSwapSpeeds() {
        assertTrue(StatusLabel.strip("300 Kbps","40 Mbps").startsWith("↓ 40 Mbps"));
    }
}
