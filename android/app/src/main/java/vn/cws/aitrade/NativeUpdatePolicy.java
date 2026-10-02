package vn.cws.aitrade;

import java.net.URI;
import java.net.URISyntaxException;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.Arrays;
import java.util.List;

/** Exact same-owner APK update gate, independent of Android platform services. */
public final class NativeUpdatePolicy {
    public static final String APPLICATION_ID = "vn.cws.aitrade";
    private static final String PREFIX =
        "/trankhanhduy1508-maker/AI-TRADE/releases/download/";
    public static final long MAX_BYTES = 250L * 1024L * 1024L;
    private NativeUpdatePolicy() { }

    public static URI releaseUrl(String text) {
        if (text == null || text.length() > 350 || text.contains("%")) {
            throw new IllegalArgumentException("INVALID_RELEASE_URL");
        }
        try {
            URI uri = new URI(text);
            if (!"https".equals(uri.getScheme())
                || !"github.com".equals(uri.getHost())
                || uri.getPort() != -1 || uri.getUserInfo() != null
                || uri.getRawQuery() != null || uri.getRawFragment() != null
                || uri.getPath() == null || !uri.getPath().startsWith(PREFIX)) {
                throw new IllegalArgumentException("INVALID_RELEASE_HOST");
            }
            String relative = uri.getPath().substring(PREFIX.length());
            if (!relative.matches("[A-Za-z0-9][A-Za-z0-9._-]{0,79}/"
                + "cws-autotrade(?:-[0-9]+)?\\.apk")) {
                throw new IllegalArgumentException("INVALID_RELEASE_PATH");
            }
            return uri;
        } catch (URISyntaxException bad) {
            throw new IllegalArgumentException("INVALID_RELEASE_URL", bad);
        }
    }

    public static void requireUpgrade(String installedPackage, long installedVersion,
                                      String offeredPackage, long offeredVersion,
                                      String channel, long size, String sha256,
                                      String downloadUrl) {
        if (!APPLICATION_ID.equals(installedPackage)
            || !APPLICATION_ID.equals(offeredPackage)
            || installedVersion < 1 || offeredVersion <= installedVersion
            || offeredVersion > Integer.MAX_VALUE
            || !("stable".equals(channel) || "recovery".equals(channel))
            || size < 100_000 || size > MAX_BYTES
            || sha256 == null || !sha256.matches("[0-9a-f]{64}")) {
            throw new IllegalArgumentException("UNSAFE_APK_UPDATE_METADATA");
        }
        releaseUrl(downloadUrl);
    }

    /** Reject v1/v2 multiple-signer ambiguity; Android OS checks signing too. */
    public static boolean sameCertificate(List<byte[]> installedSignatures,
                                          List<byte[]> archiveSignatures) {
        if (installedSignatures == null || archiveSignatures == null
            || installedSignatures.size() != 1 || archiveSignatures.size() != 1) {
            return false;
        }
        byte[] before = installedSignatures.get(0);
        byte[] after = archiveSignatures.get(0);
        if (before == null || after == null || before.length < 128 || after.length < 128) {
            return false;
        }
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] oldHash = digest.digest(before);
            byte[] newHash = digest.digest(after);
            return MessageDigest.isEqual(oldHash, newHash);
        } catch (NoSuchAlgorithmException unsupported) {
            return false;
        }
    }
}
