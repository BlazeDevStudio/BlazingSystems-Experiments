package com.blazesystems.blazenetmonitor;

import java.util.Locale;

/** Deterministic cross-Android traffic counter arithmetic. */
public final class TrafficMath {
    private TrafficMath() {}
    public static long delta(long before, long after) {
        return before < 0 || after < 0 || after < before ? 0 : after-before;
    }
    public static double bytesPerSecond(long bytes, long deltaMillis) {
        return deltaMillis <= 0 || bytes < 0 ? 0 : bytes * 1000.0 / deltaMillis;
    }
    public static String speed(double bytesPerSecond, boolean useBits) {
        double v = Math.max(0, bytesPerSecond) * (useBits ? 8 : 1);
        String[] units = useBits ? new String[]{"bps","Kbps","Mbps","Gbps"} :
                new String[]{"B/s","KB/s","MB/s","GB/s"};
        int i = 0;
        while (v >= 1000 && i < 3) { v /= 1000; i++; }
        return String.format(Locale.US, "%.1f %s", v, units[i]);
    }
    public static String data(long bytes) {
        double v = Math.max(0, bytes);
        String[] u = {"B","KB","MB","GB","TB"};
        int i=0;
        while(v>=1024 && i<4){v/=1024;i++;}
        return String.format(Locale.US, i==0?"%.0f %s":"%.1f %s",v,u[i]);
    }
}
