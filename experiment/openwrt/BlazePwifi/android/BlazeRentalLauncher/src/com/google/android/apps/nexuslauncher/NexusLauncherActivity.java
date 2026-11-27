package com.google.android.apps.nexuslauncher;

import android.content.SharedPreferences;
import android.content.res.Configuration;
import android.os.Bundle;

import com.android.launcher3.AppInfo;
import com.android.launcher3.Launcher;
import com.android.launcher3.R;
import com.android.launcher3.Utilities;
import com.android.launcher3.compat.WallpaperManagerCompat;
import com.android.launcher3.config.FeatureFlags;
import com.android.launcher3.util.ComponentKeyMapper;
import com.android.launcher3.util.ViewOnDrawExecutor;
import com.blazesystems.blazerental.ManagedPolicyController;
import com.blazesystems.blazerental.LauncherAccessController;
import com.blazesystems.blazerental.BlazeRentalUpdateManager;
import com.google.android.libraries.gsa.launcherclient.LauncherClient;

import java.util.List;

public class NexusLauncherActivity extends Launcher {
    private final static String PREF_IS_RELOAD = "pref_reload_workspace";
    private NexusLauncher mLauncher;
    private boolean mIsReload;
    private String mThemeHints;
    private boolean mUpdateHealthScheduled;

    public NexusLauncherActivity() {
        mLauncher = new NexusLauncher(this);
    }

    @Override
    public void onCreate(Bundle savedInstanceState) {
        FeatureFlags.QSB_ON_FIRST_SCREEN = showSmartspace();
        mThemeHints = themeHints();

        SharedPreferences prefs = Utilities.getPrefs(this);
        // BlazeRental owns Launcher3's custom-left surface in v0.5.
        // Keep the legacy external Google overlay disabled to avoid gesture conflicts.
        prefs.edit().putBoolean(SettingsActivity.ENABLE_MINUS_ONE_PREF, false).apply();

        super.onCreate(savedInstanceState);

        if (mIsReload = prefs.getBoolean(PREF_IS_RELOAD, false)) {
            prefs.edit().remove(PREF_IS_RELOAD).apply();

            // Go back to overview after a reload
            showOverviewMode(false);

            // Fix for long press not working
            // This is overwritten in Launcher.onResume
            setWorkspaceLoading(false);
        }
    }

    @Override
    protected void onResume() {
        super.onResume();
        ManagedPolicyController.setLauncherForeground(true);
        ManagedPolicyController.apply(this);
        ManagedPolicyController.enforceLauncherTask(this);
        enforceRentalLanding(0);
    }

    @Override
    protected void onPause() {
        ManagedPolicyController.setLauncherForeground(false);
        super.onPause();
    }

    @Override
    public void onStart() {
        super.onStart();
        boolean themeChanged = !mThemeHints.equals(themeHints());
        if (FeatureFlags.QSB_ON_FIRST_SCREEN != showSmartspace() || themeChanged) {
            if (themeChanged) {
                WallpaperManagerCompat.getInstance(this).updateAllListeners();
            }
            Utilities.getPrefs(this).edit().putBoolean(PREF_IS_RELOAD, true).apply();
            recreate();
        }
    }

    @Override
    public void recreate() {
        if (Utilities.ATLEAST_NOUGAT) {
            super.recreate();
        } else {
            finish();
            startActivity(getIntent());
        }
    }

    @Override
    public void finishBindingItems() {
        super.finishBindingItems();
        // Launcher3 may restore its saved/default Home page near the end of
        // model binding. Make the fail-closed rental landing the final bound
        // state for unpaid devices.
        enforceRentalLanding(0);
        scheduleUpdateHealthPromotion();
    }

    private void scheduleUpdateHealthPromotion() {
        if (mUpdateHealthScheduled || getWorkspace() == null
                || !BlazeRentalUpdateManager.isPending(this)) return;
        mUpdateHealthScheduled = true;
        getWorkspace().postDelayed(new Runnable() {
            @Override public void run() {
                BlazeRentalUpdateManager.markLaunchHealthy(NexusLauncherActivity.this);
                mUpdateHealthScheduled = false;
            }
        }, 30000L);
    }

    @Override
    public void clearPendingExecutor(ViewOnDrawExecutor executor) {
        super.clearPendingExecutor(executor);
        if (mIsReload) {
            mIsReload = false;

            // Call again after the launcher has loaded for proper states
            showOverviewMode(false);

            // Strip empty At A Glance page
            getWorkspace().stripEmptyScreens();
        }
        // Workspace/custom-left creation completes during binding. Re-assert
        // the unpaid landing boundary here as well as onResume so a cold boot
        // cannot briefly settle on the ordinary Launcher3 Home screen.
        enforceRentalLanding(0);
    }

    private void enforceRentalLanding(final int attempt) {
        if (LauncherAccessController.canUseDevice(this) || getWorkspace() == null) return;
        invalidateHasCustomContentToLeft();
        if (getWorkspace().hasCustomContent()) {
            moveToCustomContentScreen(false);
            return;
        }
        // Binding can finish after onResume on slower/first-boot devices.
        // Retry only a few times; every retry re-checks the authoritative
        // access gate and stops immediately once custom content exists.
        if (attempt < 8) {
            getWorkspace().postDelayed(new Runnable() {
                @Override public void run() {
                    enforceRentalLanding(attempt + 1);
                }
            }, 250L + (attempt * 125L));
        }
    }

    private boolean showSmartspace() {
        return Utilities.getPrefs(this).getBoolean(SettingsActivity.SMARTSPACE_PREF, true);
    }

    private String themeHints() {
        return Utilities.getPrefs(this).getString(Utilities.THEME_OVERRIDE_KEY, "");
    }

    @Override
    public void overrideTheme(boolean isDark, boolean supportsDarkText, boolean isTransparent) {
        int flags = Utilities.getDevicePrefs(this).getInt(NexusLauncherOverlay.PREF_PERSIST_FLAGS, 0);
        int orientFlag = getResources().getConfiguration().orientation == Configuration.ORIENTATION_LANDSCAPE ? 16 : 8;
        boolean useGoogleInOrientation = (orientFlag & flags) != 0;
        supportsDarkText &= Utilities.ATLEAST_NOUGAT;
        if (useGoogleInOrientation && isDark) {
            setTheme(R.style.GoogleSearchLauncherThemeDark);
        } else if (useGoogleInOrientation && supportsDarkText) {
            setTheme(R.style.GoogleSearchLauncherThemeDarkText);
        } else if (useGoogleInOrientation && isTransparent) {
            setTheme(R.style.GoogleSearchLauncherThemeTransparent);
        } else if (useGoogleInOrientation) {
            setTheme(R.style.GoogleSearchLauncherTheme);
        } else {
            super.overrideTheme(isDark, supportsDarkText, isTransparent);
        }
    }

    public List<ComponentKeyMapper<AppInfo>> getPredictedApps() {
        return mLauncher.mCallbacks.getPredictedApps();
    }

    public LauncherClient getGoogleNow() {
        return mLauncher.mClient;
    }
}
