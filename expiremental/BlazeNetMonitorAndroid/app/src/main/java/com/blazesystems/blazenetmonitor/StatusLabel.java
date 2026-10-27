package com.blazesystems.blazenetmonitor;

/** Plain text-only notification indicators, safe in Android's standard template. */
public final class StatusLabel {
    private StatusLabel() {}
    public static String dot(String health) {
        if("Green".equals(health))return "🟢";
        if("Yellow".equals(health))return "🟡";
        if("Orange".equals(health))return "🟠";
        if("Red".equals(health))return "🔴";
        if("Blue".equals(health))return "🔵";
        return "⚪";
    }
    public static String strip(String left,String upload,String download,String right) {
        return dot(left)+"  ↑ "+upload+"    ↓ "+download+"  "+dot(right);
    }
}
