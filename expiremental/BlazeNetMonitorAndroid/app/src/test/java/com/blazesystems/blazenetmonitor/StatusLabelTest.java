package com.blazesystems.blazenetmonitor;
import org.junit.Test;
import static org.junit.Assert.*;
public final class StatusLabelTest {
    @Test public void keepsTwoHealthIndicatorsInCorrectOrder() {
        assertEquals("🟢  ↑ 1.2 Mbps    ↓ 8.5 Mbps  🔴",
            StatusLabel.strip("Green","1.2 Mbps","8.5 Mbps","Red"));
    }
    @Test public void supportsWarningAndUnknown() {
        assertEquals("🟠",StatusLabel.dot("Orange"));
        assertEquals("🟡",StatusLabel.dot("Yellow"));
        assertEquals("🔵",StatusLabel.dot("Blue"));
        assertEquals("⚪",StatusLabel.dot(null));
    }
    @Test public void neverSwapsSpeeds() {
        String view=StatusLabel.strip("Red","300 Kbps","40 Mbps","Green");
        assertTrue(view.indexOf("300 Kbps")<view.indexOf("40 Mbps"));
        assertTrue(view.startsWith("🔴"));
        assertTrue(view.endsWith("🟢"));
    }
}
