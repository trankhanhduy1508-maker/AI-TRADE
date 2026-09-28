package vn.cws.aitrade;

import android.content.Context;
import android.content.pm.PackageInfo;
import android.content.pm.PackageManager;
import android.content.pm.Signature;
import android.os.Build;

import java.io.File;
import java.util.ArrayList;
import java.util.List;

/** Independent second gate: Android APK signer must match the installed app. */
public final class NativePackageSignerGuard {
    private NativePackageSignerGuard() { }

    @SuppressWarnings("deprecation")
    private static Signature[] signers(PackageInfo info) {
        if (info == null) return null;
        if (Build.VERSION.SDK_INT >= 28) {
            return info.signingInfo == null ? null : info.signingInfo.getApkContentsSigners();
        }
        return info.signatures;
    }

    private static List<byte[]> certificates(Signature[] signatures) {
        if (signatures == null) return null;
        List<byte[]> certificates = new ArrayList<>();
        for (Signature certificate : signatures) {
            if (certificate == null) return null;
            certificates.add(certificate.toByteArray());
        }
        return certificates;
    }

    @SuppressWarnings("deprecation")
    private static long version(PackageInfo item) {
        return Build.VERSION.SDK_INT >= 28 ? item.getLongVersionCode() : item.versionCode;
    }

    @SuppressWarnings("deprecation")
    public static boolean isSameAppUpgrade(Context context, File stagedApk,
                                           long offeredVersion) {
        if (context == null || stagedApk == null || !stagedApk.isFile()
            || offeredVersion <= 0 || offeredVersion > Integer.MAX_VALUE
            || !NativeUpdatePolicy.APPLICATION_ID.equals(context.getPackageName())) {
            return false;
        }
        try {
            PackageManager manager = context.getPackageManager();
            int flags = Build.VERSION.SDK_INT >= 28
                ? PackageManager.GET_SIGNING_CERTIFICATES : PackageManager.GET_SIGNATURES;
            PackageInfo installed = manager.getPackageInfo(context.getPackageName(), flags);
            PackageInfo offered = manager.getPackageArchiveInfo(stagedApk.getAbsolutePath(), flags);
            if (installed == null || offered == null
                || !NativeUpdatePolicy.APPLICATION_ID.equals(installed.packageName)
                || !NativeUpdatePolicy.APPLICATION_ID.equals(offered.packageName)
                || version(installed) >= offeredVersion
                || version(offered) != offeredVersion) {
                return false;
            }
            return NativeUpdatePolicy.sameCertificate(
                certificates(signers(installed)), certificates(signers(offered)));
        } catch (Exception error) {
            return false;
        }
    }
}
