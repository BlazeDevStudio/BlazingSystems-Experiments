package com.blazesystems.blazerental;

import android.Manifest;
import android.app.Activity;
import android.content.pm.PackageManager;
import android.hardware.Camera;
import android.net.Uri;
import android.graphics.Color;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.view.SurfaceHolder;
import android.view.SurfaceView;
import android.widget.FrameLayout;
import android.widget.TextView;
import android.widget.Toast;
import com.google.zxing.BinaryBitmap;
import com.google.zxing.PlanarYUVLuminanceSource;
import com.google.zxing.Result;
import com.google.zxing.common.HybridBinarizer;
import com.google.zxing.qrcode.QRCodeReader;
import org.json.JSONObject;

public class QrEnrollmentScannerActivity extends Activity
        implements SurfaceHolder.Callback, Camera.PreviewCallback {
    private static final int CAMERA_PERMISSION = 742;
    private FrameLayout root;
    private SurfaceView surface;
    private Camera camera;
    private boolean decoded;
    private int frames;

    @Override protected void onCreate(Bundle state) {
        super.onCreate(state);
        root = new FrameLayout(this);
        root.setBackgroundColor(Color.BLACK);
        surface = new SurfaceView(this);
        FrameLayout.LayoutParams preview = new FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.MATCH_PARENT, FrameLayout.LayoutParams.MATCH_PARENT,
                Gravity.CENTER);
        root.addView(surface, preview);

        View scanFrame = new View(this);
        GradientDrawable frame = new GradientDrawable();
        frame.setColor(Color.TRANSPARENT);
        frame.setStroke(dp(3), 0xff52e4ff);
        frame.setCornerRadius(dp(18));
        scanFrame.setBackground(frame);
        int side = Math.round(getResources().getDisplayMetrics().widthPixels * 0.72f);
        FrameLayout.LayoutParams fp = new FrameLayout.LayoutParams(side, side, Gravity.CENTER);
        root.addView(scanFrame, fp);
        TextView hint = new TextView(this);
        hint.setText("Scan BlazePwifi enrollment QR");
        hint.setTextSize(18f);
        hint.setGravity(Gravity.CENTER);
        hint.setTextColor(0xffffffff);
        hint.setBackgroundColor(0xaa000000);
        FrameLayout.LayoutParams hp = new FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.MATCH_PARENT, dp(56), Gravity.BOTTOM);
        root.addView(hint, hp);
        setContentView(root);

        if (android.os.Build.VERSION.SDK_INT >= 23
                && checkSelfPermission(Manifest.permission.CAMERA) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(new String[]{Manifest.permission.CAMERA}, CAMERA_PERMISSION);
        } else {
            startSurface();
        }
    }

    private void startSurface() {
        surface.getHolder().addCallback(this);
    }

    @Override public void surfaceCreated(SurfaceHolder holder) {
        try {
            camera = Camera.open();
            camera.setDisplayOrientation(90);
            camera.setPreviewDisplay(holder);
            camera.setPreviewCallback(this);
            camera.startPreview();
            try { camera.autoFocus(null); } catch (Exception ignored) {}
        } catch (Exception e) {
            Toast.makeText(this, "Camera unavailable", Toast.LENGTH_LONG).show();
            finish();
        }
    }

    @Override public void surfaceChanged(SurfaceHolder holder, int format, int width, int height) {
        if (camera == null || root == null) return;
        try {
            Camera.Size size = camera.getParameters().getPreviewSize();
            // Portrait display rotates the camera preview 90 degrees, so the
            // visible aspect is height:width. Fit it inside the screen without
            // stretching; black bars are preferable to a distorted scanner.
            float aspect = (float) size.height / (float) size.width;
            int availableW = root.getWidth();
            int availableH = root.getHeight();
            if (availableW <= 0 || availableH <= 0) return;
            int previewW = availableW;
            int previewH = Math.round(previewW / aspect);
            if (previewH > availableH) {
                previewH = availableH;
                previewW = Math.round(previewH * aspect);
            }
            FrameLayout.LayoutParams lp = new FrameLayout.LayoutParams(
                    Math.max(1, previewW), Math.max(1, previewH), Gravity.CENTER);
            surface.setLayoutParams(lp);
        } catch (Exception ignored) {}
    }
    @Override public void surfaceDestroyed(SurfaceHolder holder) { stopCamera(); }

    @Override public void onPreviewFrame(byte[] data, Camera source) {
        if (decoded || data == null || (++frames % 4) != 0) return;
        try {
            Camera.Size size = source.getParameters().getPreviewSize();
            PlanarYUVLuminanceSource lum = new PlanarYUVLuminanceSource(
                    data, size.width, size.height, 0, 0, size.width, size.height, false);
            Result result = new QRCodeReader().decode(new BinaryBitmap(new HybridBinarizer(lum)));
            if (result != null && result.getText() != null) {
                decoded = true;
                handlePayload(result.getText());
            }
        } catch (Exception ignored) {}
    }

    private void handlePayload(String raw) {
        try {
            String server;
            String token;
            String certPin = "";
            String name = "Rental phone";
            if (raw.trim().startsWith("{")) {
                JSONObject json = new JSONObject(raw);
                server = json.optString("server_url", "");
                token = json.optString("enrollment_token", "");
                certPin = json.optString("server_cert_sha256", "");
                name = json.optString("device_name", name);
            } else {
                Uri uri = Uri.parse(raw);
                if (!"blazepwifi".equalsIgnoreCase(uri.getScheme())) throw new IllegalArgumentException();
                server = uri.getQueryParameter("server");
                token = uri.getQueryParameter("token");
                String suppliedPin = uri.getQueryParameter("pin");
                if (suppliedPin != null) certPin = suppliedPin;
                String supplied = uri.getQueryParameter("name");
                if (supplied != null && supplied.length() > 0) name = supplied;
            }
            if (server == null || !(server.startsWith("http://") || server.startsWith("https://"))
                    || token == null || token.indexOf('.') <= 0) {
                throw new IllegalArgumentException();
            }
            RentalLeaseStore.saveManualEnrollment(this, server, token, name, certPin);
            final Activity self = this;
            new Thread(new Runnable() {
                @Override public void run() {
                    final boolean ok = LeaseClient.sync(self);
                    if (ok) LeaseClient.sync(self);
                    runOnUiThread(new Runnable() {
                        @Override public void run() {
                            if (ok) {
                                Toast.makeText(self, "BlazePwifi binding complete",
                                        Toast.LENGTH_LONG).show();
                                setResult(RESULT_OK);
                                finish();
                            } else {
                                decoded = false;
                                Toast.makeText(self, "Enrollment rejected; scan a fresh QR",
                                        Toast.LENGTH_LONG).show();
                            }
                        }
                    });
                }
            }).start();
        } catch (Exception e) {
            decoded = false;
            Toast.makeText(this, "Not a valid BlazePwifi enrollment QR",
                    Toast.LENGTH_SHORT).show();
        }
    }

    @Override public void onRequestPermissionsResult(int requestCode, String[] permissions,
                                                     int[] results) {
        super.onRequestPermissionsResult(requestCode, permissions, results);
        if (requestCode == CAMERA_PERMISSION && results.length > 0
                && results[0] == PackageManager.PERMISSION_GRANTED) {
            startSurface();
        } else {
            Toast.makeText(this, "Camera permission is required for QR binding",
                    Toast.LENGTH_LONG).show();
            finish();
        }
    }

    private void stopCamera() {
        if (camera == null) return;
        try { camera.setPreviewCallback(null); camera.stopPreview(); camera.release(); }
        catch (Exception ignored) {}
        camera = null;
    }

    @Override protected void onPause() {
        stopCamera();
        super.onPause();
    }

    private int dp(int value) {
        return Math.round(value * getResources().getDisplayMetrics().density);
    }
}
