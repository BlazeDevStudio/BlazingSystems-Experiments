package com.blazesystems.blazerental;

import java.util.Collections;
import java.util.Set;
import java.util.TreeSet;

public final class AppPolicySelection {
    private final Set<String> allowed;
    private final Set<String> hidden;

    private AppPolicySelection(Set<String> allowed, Set<String> hidden) {
        this.allowed = Collections.unmodifiableSet(allowed);
        this.hidden = Collections.unmodifiableSet(hidden);
    }

    public static AppPolicySelection of(Set<String> requestedAllowed, Set<String> requestedHidden) {
        TreeSet<String> hidden = clean(requestedHidden);
        TreeSet<String> allowed = clean(requestedAllowed);
        allowed.removeAll(hidden);
        return new AppPolicySelection(allowed, hidden);
    }

    public Set<String> getAllowed() { return allowed; }
    public Set<String> getHidden() { return hidden; }

    public String allowedCsv() { return join(allowed); }
    public String hiddenCsv() { return join(hidden); }

    private static TreeSet<String> clean(Set<String> input) {
        TreeSet<String> out = new TreeSet<String>();
        if (input == null) return out;
        for (String value : input) {
            if (value == null) continue;
            String pkg = value.trim();
            if (pkg.length() == 0 || pkg.indexOf(' ') >= 0
                    || pkg.indexOf('/') >= 0 || pkg.indexOf('\n') >= 0
                    || pkg.indexOf('\t') >= 0) {
                throw new IllegalArgumentException("invalid package name");
            }
            out.add(pkg);
        }
        return out;
    }

    private static String join(Set<String> values) {
        StringBuilder out = new StringBuilder();
        for (String value : values) {
            if (out.length() > 0) out.append(',');
            out.append(value);
        }
        return out.toString();
    }
}
