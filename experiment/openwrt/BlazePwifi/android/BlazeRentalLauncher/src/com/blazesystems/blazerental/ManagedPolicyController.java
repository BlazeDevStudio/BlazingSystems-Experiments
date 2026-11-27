package com.blazesystems.blazerental;

import android.app.Activity;
import android.app.admin.DevicePolicyManager;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.content.pm.ApplicationInfo;
import android.content.pm.PackageManager;
import android.content.pm.ResolveInfo;
import android.os.Build;
import android.os.UserManager;
import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;

public final class ManagedPolicyController {
    private static final String LAUNCHER_ACTIVITY =
            "com.google.android.apps.nexuslauncher.NexusLauncherActivity";
    private static volatile boolean launcherForeground;

    private ManagedPolicyController() {}

    public static ComponentName admin(Context context) {
        return new ComponentName(context, BlazeDeviceAdminReceiver.class);
    }

    public static boolean isDeviceOwner(Context context) {
        DevicePolicyManager dpm = (DevicePolicyManager)
                context.getSystemService(Context.DEVICE_POLICY_SERVICE);
        return dpm != null && dpm.isDeviceOwnerApp(context.getPackageName());
    }

    public static boolean isAdminActive(Context context) {
        DevicePolicyManager dpm = (DevicePolicyManager)
                context.getSystemService(Context.DEVICE_POLICY_SERVICE);
        return dpm != null && dpm.isAdminActive(admin(context));
    }

    public static void enforceLauncherTask(Activity activity) {
        if (activity == null || Build.VERSION.SDK_INT < 21) return;
        DevicePolicyManager dpm = (DevicePolicyManager)
                activity.getSystemService(Context.DEVICE_POLICY_SERVICE);
        if (dpm == null || !dpm.isDeviceOwnerApp(activity.getPackageName())) return;
        boolean restricted = !AndroidRentalPolicyRepository.load(activity).isUnrestricted();
        boolean adminWindow = RentalLeaseStore.isAdminWindowActive(activity);
        try {
            if (restricted && !adminWindow) activity.startLockTask();
            else activity.stopLockTask();
        } catch (Exception ignored) {}
    }

    public static List<String> installedLaunchablePackages(Context context) {
        Intent query = new Intent(Intent.ACTION_MAIN);
        query.addCategory(Intent.CATEGORY_LAUNCHER);
        List<ResolveInfo> found = context.getPackageManager()
                .queryIntentActivities(query, PackageManager.MATCH_ALL);
        LinkedHashSet<String> out = new LinkedHashSet<String>();
        for (ResolveInfo resolve : found) {
            if (resolve.activityInfo == null) continue;
            String pkg = resolve.activityInfo.packageName;
            if (pkg == null || pkg.equals(context.getPackageName())) continue;
            out.add(pkg);
        }
        return new ArrayList<String>(out);
    }

    public static List<String> safeLaunchablePackages(Context context) {
        LinkedHashSet<String> out = new LinkedHashSet<String>();
        RentalPolicy policy = AndroidRentalPolicyRepository.load(context);
        for (String pkg : installedLaunchablePackages(context)) {
            if (policy.isUnrestricted() || policy.isPackageAllowed(pkg)) out.add(pkg);
        }
        return new ArrayList<String>(out);
    }

    public static List<String> lockTaskPackages(Context context) {
        LinkedHashSet<String> out = new LinkedHashSet<String>();
        out.add(context.getPackageName());
        RentalPolicy policy = AndroidRentalPolicyRepository.load(context);
        if (policy.isUnrestricted() || RentalLeaseStore.isLeaseValid(context)) {
            out.addAll(safeLaunchablePackages(context));
        }
        if (RentalLeaseStore.isAdminWindowActive(context)) out.add("com.android.settings");
        return new ArrayList<String>(out);
    }

    public static void apply(Context context) {
        DevicePolicyManager dpm = (DevicePolicyManager)
                context.getSystemService(Context.DEVICE_POLICY_SERVICE);
        if (dpm == null || !dpm.isDeviceOwnerApp(context.getPackageName())) return;
        ComponentName admin = admin(context);
        try { dpm.setUninstallBlocked(admin, context.getPackageName(), true); }
        catch (Exception ignored) {}
        RentalPolicy policy = AndroidRentalPolicyRepository.load(context);
        boolean unrestricted = policy.isUnrestricted();
        boolean adminWindow = RentalLeaseStore.isAdminWindowActive(context);
        List<String> allow = lockTaskPackages(context);
        try { dpm.setLockTaskPackages(admin, allow.toArray(new String[allow.size()])); }
        catch (Exception ignored) {}

        try {
            IntentFilter filter = new IntentFilter(Intent.ACTION_MAIN);
            filter.addCategory(Intent.CATEGORY_HOME);
            filter.addCategory(Intent.CATEGORY_DEFAULT);
            dpm.addPersistentPreferredActivity(admin, filter,
                    new ComponentName(context.getPackageName(), LAUNCHER_ACTIVITY));
        } catch (Exception ignored) {}

        if (!unrestricted) {
            restrict(dpm, admin, UserManager.DISALLOW_ADD_USER);
            restrict(dpm, admin, UserManager.DISALLOW_SAFE_BOOT);
            restrict(dpm, admin, UserManager.DISALLOW_FACTORY_RESET);
            // Production rental phones disable debugging. Keep ADB available only on
            // explicitly debuggable CI/development builds so Device Owner emulator
            // validation can continue after policy application.
            if (!isDebuggableBuild(context)) {
                restrict(dpm, admin, UserManager.DISALLOW_DEBUGGING_FEATURES);
            } else {
                clearRestriction(dpm, admin, UserManager.DISALLOW_DEBUGGING_FEATURES);
            }
            restrict(dpm, admin, UserManager.DISALLOW_INSTALL_UNKNOWN_SOURCES);
        } else {
            clearRestriction(dpm, admin, UserManager.DISALLOW_ADD_USER);
            clearRestriction(dpm, admin, UserManager.DISALLOW_SAFE_BOOT);
            clearRestriction(dpm, admin, UserManager.DISALLOW_FACTORY_RESET);
            clearRestriction(dpm, admin, UserManager.DISALLOW_DEBUGGING_FEATURES);
            clearRestriction(dpm, admin, UserManager.DISALLOW_INSTALL_UNKNOWN_SOURCES);
        }

        if (Build.VERSION.SDK_INT >= 23) {
            try { dpm.setStatusBarDisabled(admin, !unrestricted && !adminWindow); }
            catch (Exception ignored) {}
            try { dpm.setKeyguardDisabled(admin, !unrestricted); }
            catch (Exception ignored) {}
        }
    }

    public static void setLauncherForeground(boolean foreground) {
        launcherForeground = foreground;
    }

    public static boolean isLauncherForeground() {
        return launcherForeground;
    }

    public static void openHome(Context context) {
        if (RentalLeaseStore.isAdminWindowActive(context) || launcherForeground) return;
        Intent home = new Intent(Intent.ACTION_MAIN);
        home.addCategory(Intent.CATEGORY_HOME);
        home.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP);
        try { context.startActivity(home); } catch (Exception ignored) {}
    }

    private static boolean isDebuggableBuild(Context context) {
        try {
            return (context.getApplicationInfo().flags & ApplicationInfo.FLAG_DEBUGGABLE) != 0;
        } catch (Exception ignored) {
            return false;
        }
    }

    private static void restrict(DevicePolicyManager dpm, ComponentName admin, String restriction) {
        try { dpm.addUserRestriction(admin, restriction); } catch (Exception ignored) {}
    }

    private static void clearRestriction(DevicePolicyManager dpm, ComponentName admin, String restriction) {
        try { dpm.clearUserRestriction(admin, restriction); } catch (Exception ignored) {}
    }
}
