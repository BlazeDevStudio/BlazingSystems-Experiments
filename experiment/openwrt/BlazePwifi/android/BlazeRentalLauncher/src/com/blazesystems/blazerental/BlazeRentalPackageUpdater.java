package com.blazesystems.blazerental;

import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageInfo;
import android.content.pm.PackageInstaller;
import android.content.pm.PackageManager;
import android.content.pm.Signature;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.security.MessageDigest;

public final class BlazeRentalPackageUpdater {
    public static final String ACTION_INSTALL_RESULT =
            "com.blazesystems.blazerental.ACTION_INSTALL_RESULT";
    private static final long MAX_APK_BYTES = 128L * 1024L * 1024L;

    private BlazeRentalPackageUpdater() {}

    public static String installAvailable(Context c) {
        return downloadAndInstall(c, BlazeRentalUpdateManager.availableUrl(c),
                BlazeRentalUpdateManager.availableSha(c),
                BlazeRentalUpdateManager.availableVersion(c),
                BlazeRentalUpdateManager.availableCode(c), false);
    }

    public static String installRollbackRescue(Context c) {
        return downloadAndInstall(c, BlazeRentalUpdateManager.rollbackUrl(c),
                BlazeRentalUpdateManager.rollbackSha(c),
                BlazeRentalUpdateManager.rollbackVersion(c),
                BlazeRentalUpdateManager.rollbackCode(c), true);
    }

    public static String downloadAndInstall(Context context, String url, String expectedSha,
                                            String targetVersion, int targetCode,
                                            boolean rescue) {
        try {
            if (url == null || !url.startsWith("https://")) return "HTTPS update URL required";
            if (expectedSha == null || !expectedSha.matches("(?i)^[0-9a-f]{64}$")) {
                return "Valid update SHA-256 required";
            }
            if (targetCode <= BlazeRentalUpdateManager.currentCode(context)) {
                return "Update version code must be higher than the installed build";
            }

            File dir = new File(context.getFilesDir(), "blaze-update");
            if (!dir.exists() && !dir.mkdirs()) return "Unable to create update storage";
            File apk = new File(dir, rescue ? "rollback-rescue.apk" : "candidate.apk");
            String fetch = download(url, apk);
            if (fetch != null) return fetch;
            String actual = sha256(apk);
            if (!expectedSha.equalsIgnoreCase(actual)) {
                apk.delete();
                return "Downloaded APK SHA-256 mismatch";
            }

            String validation = validatePackage(context, apk, targetCode);
            if (validation != null) {
                apk.delete();
                return validation;
            }

            String previous = backupCurrentApk(context, dir);
            BlazeRentalUpdateManager.markInstallPending(context, targetVersion, targetCode,
                    previous, rescue);
            String install = commitInstall(context, apk);
            if (install != null) {
                BlazeRentalUpdateManager.recordInstallFailure(context, install);
                return install;
            }
            return "Update staged with Android PackageInstaller";
        } catch (Exception e) {
            String m = e.getMessage() == null ? e.getClass().getSimpleName() : e.getMessage();
            BlazeRentalUpdateManager.recordInstallFailure(context, m);
            return "Update failed: " + m;
        }
    }

    private static String download(String value, File dest) throws Exception {
        HttpURLConnection c = (HttpURLConnection) new URL(value).openConnection();
        c.setConnectTimeout(10000);
        c.setReadTimeout(30000);
        c.setInstanceFollowRedirects(true);
        int code = c.getResponseCode();
        if (code < 200 || code >= 300) return "Update download HTTP " + code;
        long declared = c.getContentLength();
        if (declared > MAX_APK_BYTES) return "Update APK exceeds size limit";
        InputStream in = c.getInputStream();
        OutputStream out = new FileOutputStream(dest);
        byte[] buffer = new byte[8192];
        long total = 0; int n;
        while ((n = in.read(buffer)) > 0) {
            total += n;
            if (total > MAX_APK_BYTES) { in.close(); out.close(); dest.delete(); return "Update APK exceeds size limit"; }
            out.write(buffer, 0, n);
        }
        out.flush(); out.close(); in.close();
        return total > 0 ? null : "Downloaded APK is empty";
    }

    private static String validatePackage(Context context, File apk, int targetCode) throws Exception {
        PackageManager pm = context.getPackageManager();
        PackageInfo candidate = pm.getPackageArchiveInfo(apk.getAbsolutePath(),
                PackageManager.GET_SIGNATURES);
        if (candidate == null) return "Downloaded file is not a valid APK";
        if (!context.getPackageName().equals(candidate.packageName)) return "APK package identity mismatch";
        if (candidate.versionCode != targetCode) return "APK version code does not match published metadata";
        PackageInfo installed = pm.getPackageInfo(context.getPackageName(),
                PackageManager.GET_SIGNATURES);
        if (!sameSignatures(installed.signatures, candidate.signatures)) {
            return "APK signing certificate does not match installed BlazeRental";
        }
        return null;
    }

    private static boolean sameSignatures(Signature[] a, Signature[] b) {
        if (a == null || b == null || a.length != b.length || a.length == 0) return false;
        for (int i = 0; i < a.length; i++) {
            boolean found = false;
            for (int j = 0; j < b.length; j++) {
                if (a[i].equals(b[j])) { found = true; break; }
            }
            if (!found) return false;
        }
        return true;
    }

    private static String backupCurrentApk(Context c, File dir) {
        try {
            File source = new File(c.getApplicationInfo().sourceDir);
            File dest = new File(dir, "previous.apk");
            InputStream in = new FileInputStream(source);
            OutputStream out = new FileOutputStream(dest);
            byte[] buffer = new byte[8192]; int n;
            while ((n = in.read(buffer)) > 0) out.write(buffer, 0, n);
            out.flush(); out.close(); in.close();
            return dest.getAbsolutePath();
        } catch (Exception ignored) { return ""; }
    }

    private static String commitInstall(Context c, File apk) throws Exception {
        PackageInstaller installer = c.getPackageManager().getPackageInstaller();
        PackageInstaller.SessionParams params =
                new PackageInstaller.SessionParams(PackageInstaller.SessionParams.MODE_FULL_INSTALL);
        params.setAppPackageName(c.getPackageName());
        int id = installer.createSession(params);
        PackageInstaller.Session session = installer.openSession(id);
        InputStream in = new FileInputStream(apk);
        OutputStream out = session.openWrite("base.apk", 0, apk.length());
        byte[] buffer = new byte[8192]; int n;
        while ((n = in.read(buffer)) > 0) out.write(buffer, 0, n);
        session.fsync(out);
        out.close(); in.close();
        Intent result = new Intent(c, BlazeRentalUpdateReceiver.class);
        result.setAction(ACTION_INSTALL_RESULT);
        PendingIntent pending = PendingIntent.getBroadcast(c, id, result,
                PendingIntent.FLAG_UPDATE_CURRENT);
        session.commit(pending.getIntentSender());
        session.close();
        return null;
    }

    private static String sha256(File f) throws Exception {
        MessageDigest d = MessageDigest.getInstance("SHA-256");
        InputStream in = new FileInputStream(f);
        byte[] buffer = new byte[8192]; int n;
        while ((n = in.read(buffer)) > 0) d.update(buffer, 0, n);
        in.close();
        byte[] digest = d.digest();
        StringBuilder s = new StringBuilder();
        for (byte b : digest) s.append(String.format("%02x", b & 0xff));
        return s.toString();
    }
}
