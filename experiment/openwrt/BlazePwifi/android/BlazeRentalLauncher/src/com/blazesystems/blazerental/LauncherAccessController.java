package com.blazesystems.blazerental;

import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.content.pm.ResolveInfo;
import com.android.launcher3.AppInfo;
import java.util.ArrayList;

public final class LauncherAccessController {
    private LauncherAccessController() {}

    public static boolean isRentalRestricted(Context context) {
        return !AndroidRentalPolicyRepository.load(context).isUnrestricted();
    }

    public static boolean canUseDevice(Context context) {
        return !isRentalRestricted(context) || RentalLeaseStore.isLeaseValid(context);
    }

    public static boolean canOpenAppDrawer(Context context) {
        return canUseDevice(context);
    }

    public static boolean isPackageVisible(Context context, String packageName) {
        RentalPolicy policy = AndroidRentalPolicyRepository.load(context);
        if (policy.isUnrestricted()) return true;
        return RentalLeaseStore.isLeaseValid(context) && policy.isPackageAllowed(packageName);
    }

    public static boolean canLaunchIntent(Context context, Intent intent) {
        if (intent == null) return false;
        RentalPolicy policy = AndroidRentalPolicyRepository.load(context);
        if (policy.isUnrestricted()) return true;
        if (!RentalLeaseStore.isLeaseValid(context)) return false;

        String packageName = intent.getComponent() == null
                ? intent.getPackage() : intent.getComponent().getPackageName();
        if (packageName == null || packageName.length() == 0) {
            try {
                ResolveInfo resolved = context.getPackageManager()
                        .resolveActivity(intent, PackageManager.MATCH_DEFAULT_ONLY);
                if (resolved != null && resolved.activityInfo != null) {
                    packageName = resolved.activityInfo.packageName;
                }
            } catch (Exception ignored) {}
        }
        return packageName != null && packageName.length() > 0
                && policy.isPackageAllowed(packageName);
    }

    public static ArrayList<AppInfo> filterApps(Context context, ArrayList<AppInfo> apps) {
        RentalPolicy policy = AndroidRentalPolicyRepository.load(context);
        if (policy.isUnrestricted()) return apps;
        ArrayList<AppInfo> filtered = new ArrayList<AppInfo>();
        // Keep the operator-allowed app model populated even while unpaid. The
        // real All Apps transition remains lease-gated by canOpenAppDrawer(),
        // so a newly paid session can open the drawer without stale/empty data.
        for (AppInfo app : apps) {
            if (app != null && app.componentName != null
                    && policy.isPackageAllowed(app.componentName.getPackageName())) {
                filtered.add(app);
            }
        }
        return filtered;
    }
}
