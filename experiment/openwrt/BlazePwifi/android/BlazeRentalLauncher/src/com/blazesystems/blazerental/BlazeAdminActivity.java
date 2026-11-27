package com.blazesystems.blazerental;

import android.app.Activity;
import android.app.AlertDialog;
import android.app.admin.DevicePolicyManager;
import android.app.NotificationManager;
import android.content.DialogInterface;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.content.pm.ResolveInfo;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.net.Uri;
import android.media.RingtoneManager;
import android.os.Bundle;
import android.os.Build;
import android.provider.Settings;
import android.text.InputType;
import android.view.View;
import android.view.ViewGroup;
import android.view.WindowManager;
import android.widget.Button;
import android.widget.CheckBox;
import android.widget.EditText;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;
import org.json.JSONObject;
import com.android.launcher3.R;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashSet;
import java.util.List;

public class BlazeAdminActivity extends Activity {
    private static final int REQUEST_QR = 441;
    private static final int REQUEST_DEVICE_ADMIN = 442;
    private static final int REQUEST_ALARM_DEVICE_BASE = 460;
    private static final int REQUEST_ALARM_FILE_BASE = 470;

    private LinearLayout content;
    private final List<CheckBox> appChecks = new ArrayList<CheckBox>();
    private final List<CheckBox> hiddenAppChecks = new ArrayList<CheckBox>();

    @Override protected void onCreate(Bundle state) {
        super.onCreate(state);
        // Do not let the first password field force the IME open when the
        // secret admin panel appears. The setup page is a dashboard first;
        // administrators explicitly tap a field when they want to type.
        getWindow().setSoftInputMode(WindowManager.LayoutParams.SOFT_INPUT_STATE_ALWAYS_HIDDEN);
        route();
    }

    private void route() {
        if (!RentalLeaseStore.isInitialSetupComplete(this)
                || !RentalLeaseStore.hasAdminVerifier(this)) {
            RentalLeaseStore.beginInitialSetupWindow(this);
            ManagedPolicyController.apply(this);
            showInitialSetup();
        } else if (RentalLeaseStore.isAdminWindowActive(this)) {
            showDashboard();
        } else {
            showPasswordGate();
        }
    }

    private void showInitialSetup() {
        content = page();
        addBrandHeader();
        content.addView(title("BlazeRental Initial Setup"));
        content.addView(label("Choose daily-driver or rental operation, configure administrator "
                + "protection, and optionally bind this phone to BlazePwifi."));

        section("1 · Administrator");
        final EditText localPassword = field("Create local admin password (8+ characters)", true);
        content.addView(localPassword, full());
        Button savePassword = primary(RentalLeaseStore.hasAdminVerifier(this)
                ? "ADMIN PASSWORD READY" : "SET ADMIN PASSWORD");
        content.addView(savePassword, full());
        savePassword.setEnabled(!RentalLeaseStore.hasAdminVerifier(this));
        savePassword.setOnClickListener(new View.OnClickListener() {
            @Override public void onClick(View v) {
                if (!RentalLeaseStore.setLocalAdminPassword(
                        BlazeAdminActivity.this, localPassword.getText().toString())) {
                    Toast.makeText(BlazeAdminActivity.this,
                            "Use at least 8 characters", Toast.LENGTH_LONG).show();
                    return;
                }
                Toast.makeText(BlazeAdminActivity.this,
                        "Local administrator password saved", Toast.LENGTH_SHORT).show();
                showInitialSetup();
            }
        });

        section("2 · Usage mode");
        content.addView(label("Daily-driver mode keeps normal Launcher3 available without requiring "
                + "BlazePwifi enrollment. Rental mode can be enabled later from the admin panel."));
        Button dailyDriver = primary("USE DEVICE AS IS · NORMAL LAUNCHER");
        content.addView(dailyDriver, full());
        dailyDriver.setOnClickListener(new View.OnClickListener() {
            @Override public void onClick(View v) {
                if (!RentalLeaseStore.hasAdminVerifier(BlazeAdminActivity.this)) {
                    Toast.makeText(BlazeAdminActivity.this,
                            "Set the administrator password first", Toast.LENGTH_LONG).show();
                    return;
                }
                AndroidRentalPolicyRepository.setLocalLauncherMode(
                        BlazeAdminActivity.this, RentalPolicy.MODE_UNRESTRICTED);
                RentalLeaseStore.markInitialSetupComplete(BlazeAdminActivity.this, true);
                ManagedPolicyController.apply(BlazeAdminActivity.this);
                RentalLeaseStore.endAdminWindow(BlazeAdminActivity.this);
                ManagedPolicyController.openHome(BlazeAdminActivity.this);
                finish();
            }
        });

        section("3 · BlazePwifi binding");
        addStatus("Server", emptyAs(RentalLeaseStore.server(this), "Not bound"));
        addStatus("Enrollment", RentalLeaseStore.isEnrolled(this)
                ? "ENROLLED" : RentalLeaseStore.hasEnrollmentConfig(this)
                    ? "READY TO SYNC" : "NOT CONFIGURED");
        Button scan = primary("SCAN BLAZEPWIFI ENROLLMENT QR");
        content.addView(scan, full());
        scan.setOnClickListener(new View.OnClickListener() {
            @Override public void onClick(View v) {
                startActivityForResult(new Intent(BlazeAdminActivity.this,
                        QrEnrollmentScannerActivity.class), REQUEST_QR);
            }
        });
        Button sync = secondary("SYNC / COMPLETE ENROLLMENT");
        content.addView(sync, full());
        sync.setEnabled(RentalLeaseStore.hasEnrollmentConfig(this));
        sync.setOnClickListener(new View.OnClickListener() {
            @Override public void onClick(View v) { syncNow(true); }
        });

        section("4 · Uninstall defence");
        addStatus("Managed security", ManagedPolicyController.isDeviceOwner(this)
                ? "DEVICE OWNER · STRONGEST"
                : ManagedPolicyController.isAdminActive(this)
                    ? "DEVICE ADMIN ACTIVE · MANUAL INSTALL"
                    : "NOT ACTIVE");
        if (!ManagedPolicyController.isDeviceOwner(this)
                && !ManagedPolicyController.isAdminActive(this)) {
            Button activate = secondary("ENABLE DEVICE ADMIN DEFENCE");
            content.addView(activate, full());
            activate.setOnClickListener(new View.OnClickListener() {
                @Override public void onClick(View v) {
                    Intent intent = new Intent(DevicePolicyManager.ACTION_ADD_DEVICE_ADMIN);
                    intent.putExtra(DevicePolicyManager.EXTRA_DEVICE_ADMIN,
                            ManagedPolicyController.admin(BlazeAdminActivity.this));
                    intent.putExtra(DevicePolicyManager.EXTRA_ADD_EXPLANATION,
                            "BlazeRental uses Device Admin to make casual uninstall and bypass harder. "
                                    + "Factory-reset Device Owner provisioning gives stronger protection.");
                    startActivityForResult(intent, REQUEST_DEVICE_ADMIN);
                }
            });
        }

        section("5 · Rental special access");
        specialAccessButtons();

        Button finish = primary("FINISH INITIAL SETUP");
        content.addView(finish, full());
        finish.setOnClickListener(new View.OnClickListener() {
            @Override public void onClick(View v) {
                if (!RentalLeaseStore.hasAdminVerifier(BlazeAdminActivity.this)) {
                    Toast.makeText(BlazeAdminActivity.this,
                            "Set the administrator password first", Toast.LENGTH_LONG).show();
                    return;
                }
                if (!RentalLeaseStore.isEnrolled(BlazeAdminActivity.this)) {
                    Toast.makeText(BlazeAdminActivity.this,
                            "Bind and enroll this phone with BlazePwifi first", Toast.LENGTH_LONG).show();
                    return;
                }
                RentalLeaseStore.markInitialSetupComplete(BlazeAdminActivity.this, true);
                ManagedPolicyController.apply(BlazeAdminActivity.this);
                showDashboard();
            }
        });
        setContentView(wrap(content));
    }

    private void showPasswordGate() {
        LinearLayout root = page();
        root.addView(title("BlazeRental Admin"));
        root.addView(label("Administrator authentication is required."));
        final EditText password = field("Admin password", true);
        root.addView(password, full());
        Button unlock = primary("UNLOCK ADMIN");
        root.addView(unlock, full());
        unlock.setOnClickListener(new View.OnClickListener() {
            @Override public void onClick(View v) {
                if (RentalLeaseStore.verifyAdminPassword(BlazeAdminActivity.this,
                        password.getText().toString())) {
                    ManagedPolicyController.apply(BlazeAdminActivity.this);
                    showDashboard();
                } else {
                    Toast.makeText(BlazeAdminActivity.this,
                            "Invalid password or admin entry temporarily locked",
                            Toast.LENGTH_LONG).show();
                }
            }
        });
        setContentView(wrap(root));
    }

    private void showDashboard() {
        content = page();
        addBrandHeader();
        content.addView(title("BlazeRental Control Center"));
        content.addView(label("Native BlazeRental administration · v" + appVersionName() + " Launcher Edition"));

        section("Dashboard");
        addStatus("Security", ManagedPolicyController.isDeviceOwner(this)
                ? "Device Owner" : ManagedPolicyController.isAdminActive(this)
                    ? "Device Admin" : "Manual install · lower security");
        addStatus("Rental", RentalLeaseStore.isLeaseValid(this) ? "PAID" : "LOCKED");
        addStatus("Server", emptyAs(RentalLeaseStore.server(this), "Not bound"));
        addStatus("Device ID", emptyAs(RentalLeaseStore.deviceId(this), "Not enrolled"));
        addStatus("Policy revision", String.valueOf(AndroidRentalPolicyRepository.revision(this)));

        section("Apps");
        buildAppInventory();
        Button saveApps = secondary("SAVE APP ALLOW / HIDE POLICY");
        content.addView(saveApps, full());
        saveApps.setOnClickListener(new View.OnClickListener() {
            @Override public void onClick(View v) { saveAppPolicy(); }
        });

        section("Binding");
        Button scan = secondary("SCAN NEW BLAZEPWIFI QR");
        content.addView(scan, full());
        scan.setOnClickListener(new View.OnClickListener() {
            @Override public void onClick(View v) {
                startActivityForResult(new Intent(BlazeAdminActivity.this,
                        QrEnrollmentScannerActivity.class), REQUEST_QR);
            }
        });

        Button transfer = secondary("TRANSFER TO ANOTHER SERVER / RUN INITIAL SETUP");
        content.addView(transfer, full());
        transfer.setOnClickListener(new View.OnClickListener() {
            @Override public void onClick(View v) {
                new AlertDialog.Builder(BlazeAdminActivity.this)
                        .setTitle("Transfer rental phone?")
                        .setMessage("This clears the local server binding and lease. "
                                + "The administrator password is kept so the phone remains protected.")
                        .setPositiveButton("Transfer", new DialogInterface.OnClickListener() {
                            @Override public void onClick(DialogInterface d, int which) {
                                RentalLeaseStore.prepareTransfer(BlazeAdminActivity.this);
                                AndroidRentalPolicyRepository.clear(BlazeAdminActivity.this);
                                ManagedPolicyController.apply(BlazeAdminActivity.this);
                                showInitialSetup();
                            }
                        }).setNegativeButton("Cancel", null).show();
            }
        });

        section("Rental mode");
        final CheckBox unrestricted = new CheckBox(this);
        unrestricted.setText("Use device as is (unrestricted launcher)");
        unrestricted.setTextColor(Color.WHITE);
        unrestricted.setChecked(AndroidRentalPolicyRepository.load(this).isUnrestricted());
        content.addView(unrestricted, full());
        unrestricted.setOnClickListener(new View.OnClickListener() {
            @Override public void onClick(View v) {
                String mode = unrestricted.isChecked()
                        ? RentalPolicy.MODE_UNRESTRICTED : RentalPolicy.MODE_RENTAL;
                if (!RentalLeaseStore.isEnrolled(BlazeAdminActivity.this)) {
                    AndroidRentalPolicyRepository.setLocalLauncherMode(
                            BlazeAdminActivity.this, mode);
                    ManagedPolicyController.apply(BlazeAdminActivity.this);
                    Toast.makeText(BlazeAdminActivity.this,
                            unrestricted.isChecked() ? "Daily-driver mode enabled" :
                                    "Rental mode enabled locally",
                            Toast.LENGTH_SHORT).show();
                    return;
                }
                sendPatch("{\"launcher_mode\":\"" + mode + "\"}");
            }
        });

        section("Rental time alarms");
        content.addView(label("Audible warnings use the Android ALARM stream and temporarily raise it "
                + "to the configured minimum even when the phone is muted. Grant DND override for "
                + "the strongest Total Silence protection."));
        addAlarmControls(RentalAlarmConfig.KIND_NEAR_END);
        addAlarmControls(RentalAlarmConfig.KIND_URGENT);
        addAlarmControls(RentalAlarmConfig.KIND_TIME_UP);
        addStatus("Silent / DND protection", hasDndOverride()
                ? "FULL · alarm can temporarily override Total Silence"
                : "ALARM STREAM FORCED · grant DND override for Total Silence");
        if (Build.VERSION.SDK_INT >= 23 && !hasDndOverride()) {
            Button dnd = secondary("GRANT DND ALARM OVERRIDE");
            content.addView(dnd, full());
            dnd.setOnClickListener(new View.OnClickListener() {
                @Override public void onClick(View v) {
                    try {
                        startActivity(new Intent(Settings.ACTION_NOTIFICATION_POLICY_ACCESS_SETTINGS));
                    } catch (Exception ignored) {}
                }
            });
        }
        Button stopAlarm = secondary("STOP CURRENT ALARM TEST");
        content.addView(stopAlarm, full());
        stopAlarm.setOnClickListener(new View.OnClickListener() {
            @Override public void onClick(View v) {
                BlazeAlarmPlayer.stop(BlazeAdminActivity.this);
            }
        });

        section("Security");
        Button password = secondary("CHANGE ADMIN PASSWORD");
        content.addView(password, full());
        password.setOnClickListener(new View.OnClickListener() {
            @Override public void onClick(View v) { promptPasswordChange(); }
        });

        Button gesture = secondary("ADMIN SECRET TIMER-HOLD DURATION");
        content.addView(gesture, full());
        gesture.setOnClickListener(new View.OnClickListener() {
            @Override public void onClick(View v) { chooseGestureDuration(); }
        });

        section("Notifications / overlay");
        specialAccessButtons();

        section("Software update");
        addStatus("BlazeRental build", BlazeRentalUpdateManager.statusLine(this));
        if (BlazeRentalUpdateManager.lastError(this).length() > 0) {
            addStatus("Last update error", BlazeRentalUpdateManager.lastError(this));
        }

        Button checkUpdate = secondary("CHECK BLAZEPWIFI FOR UPDATE");
        content.addView(checkUpdate, full());
        checkUpdate.setOnClickListener(new View.OnClickListener() {
            @Override public void onClick(View v) { syncNow(false); }
        });

        Button installUpdate = primary("INSTALL AVAILABLE UPDATE");
        content.addView(installUpdate, full());
        installUpdate.setEnabled(BlazeRentalUpdateManager.hasAvailableUpdate(this));
        installUpdate.setOnClickListener(new View.OnClickListener() {
            @Override public void onClick(View v) { runSoftwareUpdate(false); }
        });

        Button rollbackUpdate = secondary("ROLL BACK TO LAST STABLE RESCUE");
        content.addView(rollbackUpdate, full());
        rollbackUpdate.setEnabled(BlazeRentalUpdateManager.hasRollbackRescue(this));
        rollbackUpdate.setOnClickListener(new View.OnClickListener() {
            @Override public void onClick(View v) { runSoftwareUpdate(true); }
        });

        section("Diagnostics");
        addStatus("Package", getPackageName());
        addStatus("Android", Build.VERSION.RELEASE + " / API " + Build.VERSION.SDK_INT);
        addStatus("Launcher engine", "Launcher3 o-mr1 derivative");
        addStatus("Notification mirror", hasNotificationAccess() ? "GRANTED" : "MISSING");
        addStatus("Floating overlay",
                Build.VERSION.SDK_INT < 23 || Settings.canDrawOverlays(this) ? "GRANTED" : "MISSING");

        Button close = primary("RETURN TO LAUNCHER");
        content.addView(close, full());
        close.setOnClickListener(new View.OnClickListener() {
            @Override public void onClick(View v) {
                RentalLeaseStore.endAdminWindow(BlazeAdminActivity.this);
                ManagedPolicyController.apply(BlazeAdminActivity.this);
                ManagedPolicyController.openHome(BlazeAdminActivity.this);
                finish();
            }
        });
        setContentView(wrap(content));
    }

    private void addAlarmControls(final int kind) {
        addStatus(RentalAlarmConfig.title(kind), RentalAlarmConfig.summary(this, kind));

        Button timing = secondary(RentalAlarmConfig.title(kind).toUpperCase()
                + " · TIMING / VOLUME");
        content.addView(timing, full());
        timing.setOnClickListener(new View.OnClickListener() {
            @Override public void onClick(View v) { configureAlarmTiming(kind); }
        });

        Button sound = secondary(RentalAlarmConfig.title(kind).toUpperCase()
                + " · SOUND / TEST");
        content.addView(sound, full());
        sound.setOnClickListener(new View.OnClickListener() {
            @Override public void onClick(View v) { chooseAlarmSound(kind); }
        });
    }

    private void configureAlarmTiming(final int kind) {
        LinearLayout box = new LinearLayout(this);
        box.setOrientation(LinearLayout.VERTICAL);
        box.setPadding(dp(18), dp(8), dp(18), dp(4));

        final CheckBox enabled = new CheckBox(this);
        enabled.setText("Alarm enabled");
        enabled.setChecked(RentalAlarmConfig.enabled(this, kind));
        box.addView(enabled, full());

        final EditText threshold = field(
                kind == RentalAlarmConfig.KIND_TIME_UP
                        ? "Fixed at 00:00"
                        : "Trigger seconds remaining", false);
        threshold.setInputType(InputType.TYPE_CLASS_NUMBER);
        threshold.setEnabled(kind != RentalAlarmConfig.KIND_TIME_UP);
        threshold.setText(kind == RentalAlarmConfig.KIND_TIME_UP
                ? "0" : String.valueOf(RentalAlarmConfig.thresholdSeconds(this, kind)));
        box.addView(threshold, full());

        final EditText duration = field("Ring duration (1–60 seconds)", false);
        duration.setInputType(InputType.TYPE_CLASS_NUMBER);
        duration.setText(String.valueOf(RentalAlarmConfig.durationSeconds(this, kind)));
        box.addView(duration, full());

        final EditText volume = field("Forced alarm volume (25–100%)", false);
        volume.setInputType(InputType.TYPE_CLASS_NUMBER);
        volume.setText(String.valueOf(RentalAlarmConfig.volumePercent(this, kind)));
        box.addView(volume, full());

        new AlertDialog.Builder(this)
                .setTitle(RentalAlarmConfig.title(kind))
                .setView(box)
                .setPositiveButton("Save", new DialogInterface.OnClickListener() {
                    @Override public void onClick(DialogInterface dialog, int which) {
                        try {
                            long sec = kind == RentalAlarmConfig.KIND_TIME_UP
                                    ? 0L : Long.parseLong(threshold.getText().toString());
                            long durationSec = Long.parseLong(duration.getText().toString());
                            int volumePct = Integer.parseInt(volume.getText().toString());

                            if (kind == RentalAlarmConfig.KIND_NEAR_END
                                    && sec <= RentalAlarmConfig.thresholdSeconds(
                                            BlazeAdminActivity.this,
                                            RentalAlarmConfig.KIND_URGENT)) {
                                Toast.makeText(BlazeAdminActivity.this,
                                        "Near End must trigger before the Urgent alarm",
                                        Toast.LENGTH_LONG).show();
                                return;
                            }
                            if (kind == RentalAlarmConfig.KIND_URGENT
                                    && sec >= RentalAlarmConfig.thresholdSeconds(
                                            BlazeAdminActivity.this,
                                            RentalAlarmConfig.KIND_NEAR_END)) {
                                Toast.makeText(BlazeAdminActivity.this,
                                        "Urgent alarm must be closer to 00:00 than Near End",
                                        Toast.LENGTH_LONG).show();
                                return;
                            }
                            RentalAlarmConfig.setEnabled(BlazeAdminActivity.this,
                                    kind, enabled.isChecked());
                            if (kind != RentalAlarmConfig.KIND_TIME_UP) {
                                RentalAlarmConfig.setThresholdSeconds(
                                        BlazeAdminActivity.this, kind, sec);
                            }
                            RentalAlarmConfig.setDurationSeconds(
                                    BlazeAdminActivity.this, kind, durationSec);
                            RentalAlarmConfig.setVolumePercent(
                                    BlazeAdminActivity.this, kind, volumePct);
                            RentalAlarmReceiver.schedule(BlazeAdminActivity.this,
                                    RentalLeaseStore.remainingMs(BlazeAdminActivity.this));
                            showDashboard();
                        } catch (Exception ignored) {
                            Toast.makeText(BlazeAdminActivity.this,
                                    "Check the alarm values", Toast.LENGTH_LONG).show();
                        }
                    }
                })
                .setNegativeButton("Cancel", null)
                .show();
    }

    private void chooseAlarmSound(final int kind) {
        final String[] options = {
                "Use built-in Blaze alarm",
                "Choose device alarm sound",
                "Choose custom audio file",
                "Test current alarm"
        };
        new AlertDialog.Builder(this)
                .setTitle(RentalAlarmConfig.title(kind) + " sound")
                .setItems(options, new DialogInterface.OnClickListener() {
                    @Override public void onClick(DialogInterface dialog, int which) {
                        if (which == 0) {
                            RentalAlarmConfig.setSound(BlazeAdminActivity.this,
                                    kind, RentalAlarmConfig.MODE_BUILTIN, "");
                            showDashboard();
                        } else if (which == 1) {
                            Intent picker = new Intent(RingtoneManager.ACTION_RINGTONE_PICKER);
                            picker.putExtra(RingtoneManager.EXTRA_RINGTONE_TYPE,
                                    RingtoneManager.TYPE_ALARM);
                            picker.putExtra(RingtoneManager.EXTRA_RINGTONE_SHOW_DEFAULT, true);
                            picker.putExtra(RingtoneManager.EXTRA_RINGTONE_SHOW_SILENT, false);
                            String current = RentalAlarmConfig.soundUri(
                                    BlazeAdminActivity.this, kind);
                            if (current.length() > 0) {
                                picker.putExtra(RingtoneManager.EXTRA_RINGTONE_EXISTING_URI,
                                        Uri.parse(current));
                            }
                            startActivityForResult(picker,
                                    REQUEST_ALARM_DEVICE_BASE + kind);
                        } else if (which == 2) {
                            Intent file = new Intent(Intent.ACTION_OPEN_DOCUMENT);
                            file.addCategory(Intent.CATEGORY_OPENABLE);
                            file.setType("audio/*");
                            file.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION
                                    | Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION);
                            startActivityForResult(file, REQUEST_ALARM_FILE_BASE + kind);
                        } else {
                            Toast.makeText(BlazeAdminActivity.this,
                                    "Testing " + RentalAlarmConfig.title(kind),
                                    Toast.LENGTH_SHORT).show();
                            BlazeAlarmPlayer.play(BlazeAdminActivity.this, kind);
                        }
                    }
                }).show();
    }

    private boolean hasDndOverride() {
        if (Build.VERSION.SDK_INT < 23) return true;
        try {
            NotificationManager nm = (NotificationManager)
                    getSystemService(NOTIFICATION_SERVICE);
            return nm != null && nm.isNotificationPolicyAccessGranted();
        } catch (Exception ignored) {
            return false;
        }
    }

    private void specialAccessButtons() {
        Button grantNotifications = secondary("GRANT NOTIFICATION ACCESS");
        content.addView(grantNotifications, full());
        grantNotifications.setOnClickListener(new View.OnClickListener() {
            @Override public void onClick(View v) {
                try { startActivity(new Intent("android.settings.ACTION_NOTIFICATION_LISTENER_SETTINGS")); }
                catch (Exception e) {
                    try { startActivity(new Intent("android.settings.NOTIFICATION_LISTENER_SETTINGS")); }
                    catch (Exception ignored) {}
                }
            }
        });

        Button grantOverlay = secondary("GRANT FLOATING TIMER OVERLAY");
        content.addView(grantOverlay, full());
        grantOverlay.setOnClickListener(new View.OnClickListener() {
            @Override public void onClick(View v) {
                if (Build.VERSION.SDK_INT < 23) return;
                try {
                    startActivity(new Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION,
                            Uri.parse("package:" + getPackageName())));
                } catch (Exception ignored) {}
            }
        });
    }

    private void syncNow(final boolean returnToSetup) {
        Toast.makeText(this, "Synchronizing with BlazePwifi...", Toast.LENGTH_SHORT).show();
        new Thread(new Runnable() {
            @Override public void run() {
                final boolean ok = LeaseClient.sync(BlazeAdminActivity.this);
                runOnUiThread(new Runnable() {
                    @Override public void run() {
                        Toast.makeText(BlazeAdminActivity.this,
                                ok ? "BlazePwifi synchronization complete" : "Server rejected synchronization",
                                Toast.LENGTH_LONG).show();
                        if (returnToSetup) showInitialSetup();
                        else if (ok) showDashboard();
                    }
                });
            }
        }).start();
    }

    private void runSoftwareUpdate(final boolean rollback) {
        final String title = rollback ? "Rollback BlazeRental?" : "Install BlazeRental update?";
        final String message = rollback
                ? "The rescue APK uses a higher version code but restores the previous stable BlazeRental code. Device Owner state and app data are preserved."
                : "BlazeRental will download the published APK, verify SHA-256, package identity and signing certificate, then use Android PackageInstaller.";
        new AlertDialog.Builder(this)
                .setTitle(title).setMessage(message)
                .setPositiveButton(rollback ? "Rollback" : "Install",
                        new DialogInterface.OnClickListener() {
                    @Override public void onClick(DialogInterface d, int which) {
                        Toast.makeText(BlazeAdminActivity.this,
                                rollback ? "Preparing rollback rescue..." : "Preparing update...",
                                Toast.LENGTH_LONG).show();
                        new Thread(new Runnable() {
                            @Override public void run() {
                                final String result = rollback
                                        ? BlazeRentalPackageUpdater.installRollbackRescue(BlazeAdminActivity.this)
                                        : BlazeRentalPackageUpdater.installAvailable(BlazeAdminActivity.this);
                                runOnUiThread(new Runnable() {
                                    @Override public void run() {
                                        Toast.makeText(BlazeAdminActivity.this,
                                                result == null ? "Update request submitted" : result,
                                                Toast.LENGTH_LONG).show();
                                        showDashboard();
                                    }
                                });
                            }
                        }, rollback ? "BlazeRental-rollback" : "BlazeRental-update").start();
                    }
                }).setNegativeButton("Cancel", null).show();
    }

    private void buildAppInventory() {
        appChecks.clear();
        hiddenAppChecks.clear();
        Intent query = new Intent(Intent.ACTION_MAIN);
        query.addCategory(Intent.CATEGORY_LAUNCHER);
        final PackageManager pm = getPackageManager();
        List<ResolveInfo> apps = pm.queryIntentActivities(query, PackageManager.MATCH_ALL);
        Collections.sort(apps, new Comparator<ResolveInfo>() {
            @Override public int compare(ResolveInfo a, ResolveInfo b) {
                return String.valueOf(a.loadLabel(pm))
                        .compareToIgnoreCase(String.valueOf(b.loadLabel(pm)));
            }
        });
        RentalPolicy policy = AndroidRentalPolicyRepository.load(this);
        for (ResolveInfo resolve : apps) {
            if (resolve.activityInfo == null) continue;
            final String pkg = resolve.activityInfo.packageName;
            if (pkg == null || pkg.equals(getPackageName())) continue;

            LinearLayout card = card();
            TextView appName = label(String.valueOf(resolve.loadLabel(pm)));
            appName.setTextColor(Color.WHITE);
            appName.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
            card.addView(appName);
            TextView packageName = label(pkg);
            packageName.setTextSize(12f);
            card.addView(packageName);

            LinearLayout choices = new LinearLayout(this);
            choices.setOrientation(LinearLayout.HORIZONTAL);
            final CheckBox allow = new CheckBox(this);
            allow.setText("ALLOW");
            allow.setTextColor(Color.rgb(180, 220, 255));
            allow.setTag(pkg);
            allow.setChecked(policy.getAllowedPackages().contains(pkg)
                    && !policy.getHiddenPackages().contains(pkg));
            final CheckBox hide = new CheckBox(this);
            hide.setText("HIDE");
            hide.setTextColor(Color.rgb(255, 180, 180));
            hide.setTag(pkg);
            hide.setChecked(policy.getHiddenPackages().contains(pkg)
                    || policy.getSensitivePackages().contains(pkg));

            allow.setOnClickListener(new View.OnClickListener() {
                @Override public void onClick(View v) {
                    if (allow.isChecked()) hide.setChecked(false);
                }
            });
            hide.setOnClickListener(new View.OnClickListener() {
                @Override public void onClick(View v) {
                    if (hide.isChecked()) allow.setChecked(false);
                }
            });

            appChecks.add(allow);
            hiddenAppChecks.add(hide);
            choices.addView(allow, new LinearLayout.LayoutParams(
                    0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));
            choices.addView(hide, new LinearLayout.LayoutParams(
                    0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));
            card.addView(choices);
            content.addView(card, full());
        }
    }

    private void saveAppPolicy() {
        HashSet<String> allowed = new HashSet<String>();
        HashSet<String> hidden = new HashSet<String>();
        for (CheckBox box : appChecks) {
            if (box.isChecked()) allowed.add((String) box.getTag());
        }
        for (CheckBox box : hiddenAppChecks) {
            if (box.isChecked()) hidden.add((String) box.getTag());
        }
        try {
            AppPolicySelection selection = AppPolicySelection.of(allowed, hidden);
            JSONObject patch = new JSONObject();
            patch.put("allowed_packages", selection.allowedCsv());
            patch.put("hidden_packages", selection.hiddenCsv());
            sendPatch(patch.toString());
        } catch (Exception e) {
            Toast.makeText(this, "Unable to build app allow/hide policy",
                    Toast.LENGTH_SHORT).show();
        }
    }

    private void promptPasswordChange() {
        final EditText input = field("New administrator password", true);
        new AlertDialog.Builder(this)
                .setTitle("Change admin password")
                .setView(input)
                .setPositiveButton("Save", new DialogInterface.OnClickListener() {
                    @Override public void onClick(DialogInterface d, int which) {
                        try {
                            JSONObject patch = new JSONObject();
                            patch.put("admin_password", input.getText().toString());
                            sendPatch(patch.toString());
                        } catch (Exception ignored) {}
                    }
                }).setNegativeButton("Cancel", null).show();
    }

    private void chooseGestureDuration() {
        final String[] values = {"3 seconds", "5 seconds", "7 seconds"};
        new AlertDialog.Builder(this).setTitle("Secret timer-hold duration")
                .setItems(values, new DialogInterface.OnClickListener() {
                    @Override public void onClick(DialogInterface d, int which) {
                        long value = which == 0 ? 3000L : which == 1 ? 5000L : 7000L;
                        try {
                            JSONObject patch = new JSONObject();
                            patch.put("admin_gesture_value", String.valueOf(value));
                            sendPatch(patch.toString());
                        } catch (Exception ignored) {
                            Toast.makeText(BlazeAdminActivity.this,
                                    "Unable to update admin gesture", Toast.LENGTH_SHORT).show();
                        }
                    }
                }).show();
    }

    private void sendPatch(final String patchJson) {
        final long revision = AndroidRentalPolicyRepository.revision(this);
        Toast.makeText(this, "Applying policy...", Toast.LENGTH_SHORT).show();
        new Thread(new Runnable() {
            @Override public void run() {
                final JSONObject response = RentalPolicyClient.policyPatch(
                        BlazeAdminActivity.this, revision, patchJson);
                final boolean ok = response != null && response.optBoolean("ok", false);
                if (ok) LeaseClient.sync(BlazeAdminActivity.this);
                runOnUiThread(new Runnable() {
                    @Override public void run() {
                        Toast.makeText(BlazeAdminActivity.this,
                                ok ? "Policy updated" :
                                        response == null ? "Server unavailable" :
                                                response.optString("error", "Policy rejected"),
                                Toast.LENGTH_LONG).show();
                        if (ok) showDashboard();
                    }
                });
            }
        }).start();
    }

    private boolean hasNotificationAccess() {
        String enabled = Settings.Secure.getString(getContentResolver(),
                "enabled_notification_listeners");
        return enabled != null && enabled.contains(getPackageName());
    }

    @Override protected void onActivityResult(int request, int result, Intent data) {
        super.onActivityResult(request, result, data);

        if (request > REQUEST_ALARM_DEVICE_BASE
                && request <= REQUEST_ALARM_DEVICE_BASE + RentalAlarmConfig.KIND_TIME_UP) {
            int kind = request - REQUEST_ALARM_DEVICE_BASE;
            if (result == RESULT_OK && data != null) {
                Uri uri = (Uri) data.getParcelableExtra(
                        RingtoneManager.EXTRA_RINGTONE_PICKED_URI);
                if (uri != null) {
                    RentalAlarmConfig.setSound(this, kind,
                            RentalAlarmConfig.MODE_DEVICE, uri.toString());
                }
            }
            showDashboard();
            return;
        }

        if (request > REQUEST_ALARM_FILE_BASE
                && request <= REQUEST_ALARM_FILE_BASE + RentalAlarmConfig.KIND_TIME_UP) {
            int kind = request - REQUEST_ALARM_FILE_BASE;
            if (result == RESULT_OK && data != null && data.getData() != null) {
                Uri uri = data.getData();
                try {
                    getContentResolver().takePersistableUriPermission(uri,
                            Intent.FLAG_GRANT_READ_URI_PERMISSION);
                } catch (Exception ignored) {}
                RentalAlarmConfig.setSound(this, kind,
                        RentalAlarmConfig.MODE_CUSTOM, uri.toString());
            }
            showDashboard();
            return;
        }
        if (request == REQUEST_QR && result == RESULT_OK) {
            if (!RentalLeaseStore.isInitialSetupComplete(this)) showInitialSetup();
            else showDashboard();
        } else if (request == REQUEST_DEVICE_ADMIN) {
            showInitialSetup();
        }
    }

    private void addBrandHeader() {
        ImageView logo = new ImageView(this);
        logo.setImageResource(R.drawable.blaze_lcm_brand);
        logo.setAdjustViewBounds(true);
        logo.setScaleType(ImageView.ScaleType.CENTER_INSIDE);
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, dp(112));
        lp.setMargins(0, 0, 0, dp(12));
        content.addView(logo, lp);
    }

    private ScrollView wrap(View child) {
        ScrollView scroll = new ScrollView(this);
        scroll.setFillViewport(true);
        scroll.setBackgroundColor(Color.rgb(8, 13, 24));
        scroll.addView(child);
        return scroll;
    }

    private LinearLayout page() {
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(dp(18), dp(24), dp(18), dp(40));
        root.setFocusableInTouchMode(true);
        root.requestFocus();
        return root;
    }

    private LinearLayout card() {
        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.VERTICAL);
        card.setPadding(dp(14), dp(12), dp(14), dp(12));
        GradientDrawable bg = new GradientDrawable();
        bg.setColor(Color.rgb(20, 30, 49));
        bg.setCornerRadius(dp(12));
        card.setBackground(bg);
        return card;
    }

    private void section(String name) {
        TextView v = title(name);
        v.setTextSize(18f);
        v.setPadding(0, dp(24), 0, dp(8));
        content.addView(v);
    }

    private void addStatus(String key, String value) {
        LinearLayout card = card();
        TextView k = label(key);
        k.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        k.setTextColor(Color.WHITE);
        TextView v = label(value);
        card.addView(k);
        card.addView(v);
        content.addView(card, full());
    }

    private EditText field(String hint, boolean password) {
        EditText input = new EditText(this);
        input.setHint(hint);
        input.setTextColor(Color.WHITE);
        input.setHintTextColor(Color.rgb(120, 139, 164));
        input.setBackgroundColor(Color.rgb(15, 23, 42));
        input.setPadding(dp(12), dp(10), dp(12), dp(10));
        if (password) input.setInputType(
                InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_PASSWORD);
        return input;
    }

    private String appVersionName() {
        try {
            String version = getPackageManager().getPackageInfo(getPackageName(), 0).versionName;
            return version == null || version.trim().length() == 0 ? "unknown" : version.trim();
        } catch (Exception ignored) {
            return "unknown";
        }
    }

    private TextView title(String text) {
        TextView v = new TextView(this);
        v.setText(text);
        v.setTextColor(Color.WHITE);
        v.setTextSize(25f);
        v.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        return v;
    }

    private TextView label(String text) {
        TextView v = new TextView(this);
        v.setText(text);
        v.setTextColor(Color.rgb(180, 194, 217));
        v.setTextSize(14f);
        v.setPadding(0, dp(5), 0, dp(5));
        return v;
    }

    private Button primary(String text) {
        Button b = new Button(this);
        b.setText(text);
        b.setTextColor(Color.WHITE);
        b.setBackgroundColor(Color.rgb(70, 95, 255));
        return b;
    }

    private Button secondary(String text) {
        Button b = primary(text);
        b.setBackgroundColor(Color.rgb(30, 41, 59));
        return b;
    }

    private LinearLayout.LayoutParams full() {
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        lp.setMargins(0, dp(7), 0, dp(7));
        return lp;
    }

    private String emptyAs(String value, String fallback) {
        return value == null || value.length() == 0 ? fallback : value;
    }

    private int dp(int value) {
        return Math.round(value * getResources().getDisplayMetrics().density);
    }
}
