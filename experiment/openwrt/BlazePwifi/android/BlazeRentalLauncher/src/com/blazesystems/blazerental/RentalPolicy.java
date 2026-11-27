package com.blazesystems.blazerental;

import java.util.Collections;
import java.util.HashSet;
import java.util.Set;

/**
 * Immutable launcher access policy. Server signature verification happens before
 * a policy is accepted by RentalPolicyStore.
 */
public final class RentalPolicy {
    public static final String MODE_RENTAL = "rental";
    public static final String MODE_UNRESTRICTED = "unrestricted";

    private static final Set<String> DEFAULT_SENSITIVE_PACKAGES;
    static {
        Set<String> packages = new HashSet<String>();
        packages.add("com.android.settings");
        packages.add("com.android.packageinstaller");
        packages.add("com.google.android.packageinstaller");
        packages.add("com.android.permissioncontroller");
        packages.add("com.google.android.permissioncontroller");
        DEFAULT_SENSITIVE_PACKAGES = Collections.unmodifiableSet(packages);
    }

    private final long revision;
    private final String launcherMode;
    private final Set<String> allowedPackages;
    private final Set<String> hiddenPackages;
    private final Set<String> sensitivePackages;

    public RentalPolicy(long revision,
                        String launcherMode,
                        Set<String> allowedPackages,
                        Set<String> hiddenPackages,
                        Set<String> additionalSensitivePackages) {
        if (revision < 0L) {
            throw new IllegalArgumentException("revision must be >= 0");
        }
        if (!MODE_RENTAL.equals(launcherMode) && !MODE_UNRESTRICTED.equals(launcherMode)) {
            throw new IllegalArgumentException("invalid launcherMode");
        }
        this.revision = revision;
        this.launcherMode = launcherMode;
        this.allowedPackages = immutableValidatedCopy(allowedPackages);
        this.hiddenPackages = immutableValidatedCopy(hiddenPackages);

        Set<String> sensitive = new HashSet<String>(DEFAULT_SENSITIVE_PACKAGES);
        if (additionalSensitivePackages != null) {
            sensitive.addAll(immutableValidatedCopy(additionalSensitivePackages));
        }
        this.sensitivePackages = Collections.unmodifiableSet(sensitive);
    }

    public long getRevision() {
        return revision;
    }

    public String getLauncherMode() {
        return launcherMode;
    }

    public boolean isUnrestricted() {
        return MODE_UNRESTRICTED.equals(launcherMode);
    }

    public Set<String> getAllowedPackages() {
        return allowedPackages;
    }

    public Set<String> getHiddenPackages() {
        return hiddenPackages;
    }

    public Set<String> getSensitivePackages() {
        return sensitivePackages;
    }

    public boolean isPackageAllowed(String packageName) {
        validatePackageName(packageName);
        if (isUnrestricted()) {
            return true;
        }
        if (sensitivePackages.contains(packageName) || hiddenPackages.contains(packageName)) {
            return false;
        }
        return allowedPackages.contains(packageName);
    }

    private static Set<String> immutableValidatedCopy(Set<String> input) {
        Set<String> output = new HashSet<String>();
        if (input == null) {
            return Collections.unmodifiableSet(output);
        }
        for (String packageName : input) {
            validatePackageName(packageName);
            output.add(packageName);
        }
        return Collections.unmodifiableSet(output);
    }

    private static void validatePackageName(String packageName) {
        if (packageName == null || packageName.length() == 0
                || packageName.indexOf(' ') >= 0 || packageName.indexOf('\t') >= 0
                || packageName.indexOf('\n') >= 0 || packageName.indexOf('/') >= 0) {
            throw new IllegalArgumentException("invalid package name");
        }
    }
}
