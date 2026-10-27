package com.blazesystems.blazenetmonitor;

/** Readable health labels and speeds in the standard notification shade. */
public final class StatusLabel {
    private StatusLabel() {}
    public static String quality(String health) {
        if("Green".equals(health))return "Online";
        if("Yellow".equals(health))return "Slow";
        if("Orange".equals(health))return "Delayed";
        if("Red".equals(health))return "Offline";
        return "Checking";
    }
    public static String strip(String upload,String download) {
        return "↓ "+download+"    ↑ "+upload;
    }
}
