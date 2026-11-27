package com.blazesystems.blazerental;

import android.bluetooth.BluetoothAdapter;
import android.content.Context;
import android.hardware.camera2.CameraCharacteristics;
import android.hardware.camera2.CameraManager;
import android.media.AudioManager;
import android.os.Build;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;

public final class QuickControlController {
    public static final String VOLUME_DOWN = "volume_down";
    public static final String VOLUME_UP = "volume_up";
    public static final String FLOATING_TIMER = "floating_timer";
    public static final String NETWORK_STATUS = "network_status";
    public static final String BLUETOOTH_TOGGLE = "bluetooth_toggle";
    public static final String FLASHLIGHT = "flashlight";

    private static final List<String> SAFE_CONTROLS = Collections.unmodifiableList(
            Arrays.asList(VOLUME_DOWN, VOLUME_UP, FLOATING_TIMER,
                    NETWORK_STATUS, BLUETOOTH_TOGGLE, FLASHLIGHT));

    private QuickControlController() {}

    public static List<String> safeControls() { return SAFE_CONTROLS; }

    public static boolean containsDangerousSettingsBridge() {
        for (String id : SAFE_CONTROLS) {
            if (id.contains("settings") || id.contains("developer")
                    || id.contains("install") || id.contains("package")) return true;
        }
        return false;
    }

    public static void adjustVolume(Context context, int direction) {
        AudioManager audio = (AudioManager) context.getSystemService(Context.AUDIO_SERVICE);
        if (audio != null) audio.adjustVolume(direction, AudioManager.FLAG_SHOW_UI);
    }

    public static boolean isBluetoothEnabled() {
        BluetoothAdapter adapter = BluetoothAdapter.getDefaultAdapter();
        return adapter != null && adapter.isEnabled();
    }

    public static boolean setBluetoothEnabled(boolean enabled) {
        BluetoothAdapter adapter = BluetoothAdapter.getDefaultAdapter();
        if (adapter == null) return false;
        try { return enabled ? adapter.enable() : adapter.disable(); }
        catch (SecurityException ignored) { return false; }
    }

    public static boolean setTorch(Context context, boolean enabled) {
        if (Build.VERSION.SDK_INT < 23) return false;
        CameraManager manager = (CameraManager) context.getSystemService(Context.CAMERA_SERVICE);
        if (manager == null) return false;
        try {
            for (String id : manager.getCameraIdList()) {
                CameraCharacteristics cc = manager.getCameraCharacteristics(id);
                Boolean flash = cc.get(CameraCharacteristics.FLASH_INFO_AVAILABLE);
                Integer facing = cc.get(CameraCharacteristics.LENS_FACING);
                if (Boolean.TRUE.equals(flash)
                        && (facing == null || facing == CameraCharacteristics.LENS_FACING_BACK)) {
                    manager.setTorchMode(id, enabled);
                    context.getSharedPreferences("blaze_rental_ui", Context.MODE_PRIVATE)
                            .edit().putBoolean("torch_enabled", enabled).apply();
                    return true;
                }
            }
        } catch (Exception ignored) {}
        return false;
    }

    public static boolean torchEnabled(Context context) {
        return context.getSharedPreferences("blaze_rental_ui", Context.MODE_PRIVATE)
                .getBoolean("torch_enabled", false);
    }

    public static void setFloatingTimer(Context context, boolean enabled) {
        context.getSharedPreferences("blaze_rental_ui", Context.MODE_PRIVATE)
                .edit().putBoolean("floating_timer", enabled).apply();
        if (enabled) FloatingTimerService.ensure(context);
        else FloatingTimerService.stop(context);
    }
}
