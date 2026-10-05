package vn.cws.aitrade;

import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.PublicKey;
import java.security.Signature;
import java.util.Locale;

/** Strict verification policy for future stable/recovery APK updates. No installer. */
public final class NativeReleaseVerifier {
    private NativeReleaseVerifier() { }

    public static String canonical(String applicationId, long versionCode,
                                   String channel, String sha256) {
        if (applicationId == null || !applicationId.matches("[a-zA-Z0-9_.]+")
            || versionCode <= 0 || versionCode > Integer.MAX_VALUE
            || !("stable".equals(channel) || "recovery".equals(channel))
            || sha256 == null || !sha256.matches("[0-9a-f]{64}")) {
            throw new IllegalArgumentException("invalid release fields");
        }
        return "CWS_AUTOTRADE_APK_V1\n" + applicationId + "\n" + versionCode
            + "\n" + channel + "\n" + sha256 + "\n";
    }

    public static boolean verify(String installedAppId, long installedVersion,
                                 String offeredAppId, long offeredVersion,
                                 String channel, String expectedSha256,
                                 byte[] manifestSignature, PublicKey releaseKey,
                                 InputStream apk) {
        if (installedAppId == null || !installedAppId.equals(offeredAppId)
            || offeredVersion <= installedVersion || releaseKey == null
            || manifestSignature == null || manifestSignature.length < 64
            || apk == null) return false;
        try {
            String message = canonical(offeredAppId, offeredVersion,
                channel, expectedSha256);
            Signature verifier = Signature.getInstance("SHA256withRSA");
            verifier.initVerify(releaseKey);
            verifier.update(message.getBytes(StandardCharsets.UTF_8));
            if (!verifier.verify(manifestSignature)) return false;
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] buffer = new byte[16384];
            int n;
            while ((n = apk.read(buffer)) != -1) digest.update(buffer, 0, n);
            byte[] bytes = digest.digest();
            StringBuilder actual = new StringBuilder(64);
            for (byte b : bytes) actual.append(String.format(Locale.ROOT, "%02x", b & 255));
            return expectedSha256.equals(actual.toString());
        } catch (Exception failure) {
            // Any malformed metadata, interrupted download or signature failure
            // blocks installation. The Android package manager must separately
            // verify APK signing identity and require user installation consent.
            return false;
        }
    }
}
