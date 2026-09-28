package vn.cws.aitrade;

import android.app.Activity;
import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.content.pm.PackageInfo;
import android.net.Uri;
import android.os.Build;
import android.provider.Settings;
import android.widget.Button;
import android.widget.TextView;

import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.security.KeyFactory;
import java.security.MessageDigest;
import java.security.PublicKey;
import java.security.interfaces.RSAPublicKey;
import java.security.spec.X509EncodedKeySpec;
import java.util.Base64;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/** User-initiated external-APK update. Never installs silently or trusts a debug signer. */
public final class NativeUpdateCoordinator {
    private static final String MANIFEST =
        "https://github.com/trankhanhduy1508-maker/AI-TRADE/releases/latest/download/cws-autotrade-manifest.json";
    private static final String KEY = BuildConfig.CWS_RELEASE_PUBLIC_KEY_SPKI_B64;
    private static final int META_LIMIT = 32768;
    private static final int MAX_REDIRECTS = 5;
    private final Activity owner;
    private final Button checkButton;
    private final Button installButton;
    private final TextView status;
    private final ExecutorService io = Executors.newSingleThreadExecutor();
    private volatile JSONObject approved;
    private volatile PublicKey approvedKey;
    private volatile boolean disposed;

    public NativeUpdateCoordinator(Activity owner, Button checkButton,
                                   Button installButton, TextView status) {
        this.owner = owner;
        this.checkButton = checkButton;
        this.installButton = installButton;
        this.status = status;
        checkButton.setEnabled(configured());
        installButton.setEnabled(false);
        if (!configured()) status.setText("Kênh cập nhật chưa được ký phát hành.");
    }

    public static boolean configured() {
        return KEY != null && KEY.length() > 300
            && KEY.matches("[A-Za-z0-9+/=]+");
    }

    private void notice(String message) {
        owner.runOnUiThread(() -> {
            if (!disposed && !owner.isFinishing() && !owner.isDestroyed()) {
                status.setText(message);
            }
        });
    }

    public void check() {
        if (disposed || !configured()) return;
        approved = null;
        approvedKey = null;
        checkButton.setEnabled(false);
        installButton.setEnabled(false);
        notice("Đang tải và xác minh bản cập nhật từ kênh chính thức…");
        io.execute(() -> {
            File candidate = null;
            try {
                PublicKey key = ownerKey();
                byte[] manifestBytes = readBounded(new URL(MANIFEST), META_LIMIT);
                JSONObject manifest = new JSONObject(new String(manifestBytes, StandardCharsets.UTF_8));
                if (!"CWS_AUTOTRADE_APK_V1".equals(manifest.optString("schema", ""))) {
                    throw new IOException("INVALID_RELEASE_SCHEMA");
                }
                String appId = manifest.optString("applicationId", "");
                int version = manifest.optInt("versionCode", -1);
                String channel = manifest.optString("channel", "");
                long size = manifest.optLong("apkBytes", -1);
                String sha256 = manifest.optString("apkSha256", "");
                String release = manifest.optString("apkUrl", "");
                long installed = installedVersion();
                NativeUpdatePolicy.requireUpgrade(
                    owner.getPackageName(), installed, appId, version,
                    channel, size, sha256, release);
                if (!MessageDigest.isEqual(
                    MessageDigest.getInstance("SHA-256").digest(key.getEncoded()),
                    fromHex(manifest.optString("publicKeySpkiSha256", "")))) {
                    throw new IOException("RELEASE_KEY_MISMATCH");
                }
                byte[] signature = Base64.getDecoder().decode(
                    manifest.optString("manifestSignature", ""));
                if (signature.length < 256) throw new IOException("BAD_RELEASE_SIGNATURE");
                File base = new File(owner.getCacheDir(), "cws_updates");
                if (!base.isDirectory() && !base.mkdirs()) {
                    throw new IOException("UPDATE_STORAGE_UNAVAILABLE");
                }
                File previous = new File(base, "cws-update.apk");
                if (previous.exists() && !previous.delete()) {
                    throw new IOException("OLD_UPDATE_NOT_CLEARED");
                }
                candidate = File.createTempFile("verified-", ".apk", base);
                download(new URL(release), candidate, size);
                if (!verified(candidate, manifest, key)) {
                    throw new IOException("APK_INTEGRITY_OR_SIGNER_FAILED");
                }
                if (!candidate.renameTo(previous)) {
                    throw new IOException("VERIFIED_UPDATE_STAGING_FAILED");
                }
                candidate = null;
                approved = manifest;
                approvedKey = key;
                notice("Bản cập nhật đã được xác minh. Nhấn Cài đặt để Android hỏi xác nhận.");
                owner.runOnUiThread(() -> {
                    if (!disposed) installButton.setEnabled(true);
                });
            } catch (Exception error) {
                approved = null;
                approvedKey = null;
                notice("Chưa có bản cập nhật hợp lệ hoặc không thể xác minh. Không cài đặt.");
            } finally {
                if (candidate != null) candidate.delete();
                owner.runOnUiThread(() -> {
                    if (!disposed) checkButton.setEnabled(configured());
                });
            }
        });
    }

    public void install() {
        if (disposed || approved == null || approvedKey == null) return;
        installButton.setEnabled(false);
        final JSONObject selected = approved;
        final PublicKey key = approvedKey;
        notice("Đang kiểm tra lại tệp trước khi yêu cầu Android cài đặt…");
        io.execute(() -> {
            boolean safe;
            File staged = new File(new File(owner.getCacheDir(), "cws_updates"),
                "cws-update.apk");
            try {
                safe = staged.isFile() && verified(staged, selected, key);
            } catch (Exception error) {
                safe = false;
            }
            if (!safe) {
                approved = null;
                approvedKey = null;
                staged.delete();
                notice("Tệp cập nhật không còn hợp lệ. Đã hủy cài đặt.");
                return;
            }
            owner.runOnUiThread(() -> {
                if (disposed || owner.isFinishing() || owner.isDestroyed()) return;
                if (Build.VERSION.SDK_INT >= 26
                    && !owner.getPackageManager().canRequestPackageInstalls()) {
                    notice("Android yêu cầu bạn bật quyền cài ứng dụng từ nguồn này.");
                    try {
                        Intent setting = new Intent(Settings.ACTION_MANAGE_UNKNOWN_APP_SOURCES,
                            Uri.parse("package:" + owner.getPackageName()));
                        owner.startActivity(setting);
                    } catch (ActivityNotFoundException | SecurityException ignored) {
                        notice("Thiết bị không cho phép cài đặt từ nguồn này.");
                    }
                    installButton.setEnabled(true);
                    return;
                }
                try {
                    Uri uri = Uri.parse("content://" + NativeUpdateProvider.AUTHORITY
                        + NativeUpdateProvider.PATH);
                    Intent installer = new Intent(Intent.ACTION_INSTALL_PACKAGE);
                    installer.setDataAndType(uri, NativeUpdateProvider.MIME);
                    installer.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
                    installer.putExtra(Intent.EXTRA_RETURN_RESULT, true);
                    owner.startActivity(installer);
                    notice("Hãy xác nhận cập nhật trong trình cài đặt Android.");
                } catch (ActivityNotFoundException | SecurityException failure) {
                    notice("Không thể mở trình cài đặt Android.");
                    installButton.setEnabled(true);
                }
            });
        });
    }

    public void close() {
        disposed = true;
        approved = null;
        approvedKey = null;
        io.shutdownNow();
    }

    private PublicKey ownerKey() throws Exception {
        if (!configured()) throw new IOException("RELEASE_KEY_UNCONFIGURED");
        byte[] encoded = Base64.getDecoder().decode(KEY);
        PublicKey key = KeyFactory.getInstance("RSA").generatePublic(
            new X509EncodedKeySpec(encoded));
        if (!(key instanceof RSAPublicKey)
            || ((RSAPublicKey) key).getModulus().bitLength() < 3072) {
            throw new IOException("RELEASE_KEY_TOO_WEAK");
        }
        return key;
    }

    @SuppressWarnings("deprecation")
    private long installedVersion() throws Exception {
        PackageInfo info = owner.getPackageManager().getPackageInfo(owner.getPackageName(), 0);
        if (info == null) throw new IOException("INSTALLED_APP_MISSING");
        return Build.VERSION.SDK_INT >= 28 ? info.getLongVersionCode() : info.versionCode;
    }

    private boolean verified(File apk, JSONObject manifest, PublicKey key)
        throws Exception {
        if (apk.length() != manifest.optLong("apkBytes", -1)) return false;
        int version = manifest.optInt("versionCode", -1);
        NativeUpdatePolicy.requireUpgrade(owner.getPackageName(), installedVersion(),
            manifest.optString("applicationId", ""), version,
            manifest.optString("channel", ""), apk.length(),
            manifest.optString("apkSha256", ""), manifest.optString("apkUrl", ""));
        byte[] signature = Base64.getDecoder().decode(
            manifest.optString("manifestSignature", ""));
        try (FileInputStream stream = new FileInputStream(apk)) {
            return NativeReleaseVerifier.verify(
                owner.getPackageName(), installedVersion(),
                manifest.optString("applicationId", ""), version,
                manifest.optString("channel", ""),
                manifest.optString("apkSha256", ""), signature, key, stream)
                && NativePackageSignerGuard.isSameAppUpgrade(owner, apk, version);
        }
    }

    private static byte[] fromHex(String hex) throws IOException {
        if (hex == null || !hex.matches("[a-f0-9]{64}")) {
            throw new IOException("INVALID_RELEASE_KEY_HASH");
        }
        byte[] out = new byte[32];
        for (int i = 0; i < out.length; i++) {
            out[i] = (byte) Integer.parseInt(hex.substring(i * 2, i * 2 + 2), 16);
        }
        return out;
    }

    private static boolean trustedLocation(URL url, boolean initial) {
        if (!"https".equals(url.getProtocol()) || url.getUserInfo() != null
            || url.getPort() != -1) return false;
        if (initial) return "github.com".equals(url.getHost())
            && url.getPath().startsWith(
                "/trankhanhduy1508-maker/AI-TRADE/releases/");
        return "github.com".equals(url.getHost())
            || "release-assets.githubusercontent.com".equals(url.getHost())
            || "objects.githubusercontent.com".equals(url.getHost())
            || "github-releases.githubusercontent.com".equals(url.getHost());
    }

    private static HttpURLConnection connect(URL initial) throws IOException {
        if (!trustedLocation(initial, true)) throw new IOException("UNTRUSTED_UPDATE_HOST");
        URL url = initial;
        for (int hop = 0; hop <= MAX_REDIRECTS; hop++) {
            if (!trustedLocation(url, hop == 0)) {
                throw new IOException("UNTRUSTED_UPDATE_REDIRECT");
            }
            HttpURLConnection connection = (HttpURLConnection) url.openConnection();
            connection.setInstanceFollowRedirects(false);
            connection.setConnectTimeout(15000);
            connection.setReadTimeout(20000);
            connection.setRequestProperty("Accept", "application/octet-stream");
            connection.setRequestProperty("Cache-Control", "no-store");
            int status = connection.getResponseCode();
            if (status == 200) return connection;
            String location = connection.getHeaderField("Location");
            connection.disconnect();
            if (status != 301 && status != 302 && status != 303
                && status != 307 && status != 308) {
                throw new IOException("UPDATE_HTTP_ERROR");
            }
            if (location == null || location.length() > 4000) {
                throw new IOException("UNTRUSTED_UPDATE_REDIRECT");
            }
            url = new URL(url, location);
        }
        throw new IOException("TOO_MANY_RELEASE_REDIRECTS");
    }

    private static byte[] readBounded(URL url, int limit) throws Exception {
        HttpURLConnection connection = connect(url);
        try (InputStream input = connection.getInputStream();
             ByteArrayOutputStream buffer = new ByteArrayOutputStream()) {
            byte[] block = new byte[4096];
            int amount;
            while ((amount = input.read(block)) != -1) {
                if (buffer.size() + amount > limit) {
                    throw new IOException("UPDATE_MANIFEST_OVERSIZE");
                }
                buffer.write(block, 0, amount);
            }
            return buffer.toByteArray();
        } finally {
            connection.disconnect();
        }
    }

    private static void download(URL url, File target, long expectedBytes)
        throws Exception {
        HttpURLConnection connection = connect(url);
        long total = 0L;
        try (InputStream input = connection.getInputStream();
             FileOutputStream output = new FileOutputStream(target)) {
            byte[] block = new byte[32768];
            int amount;
            while ((amount = input.read(block)) != -1) {
                total += amount;
                if (total > expectedBytes || total > NativeUpdatePolicy.MAX_BYTES) {
                    throw new IOException("UPDATE_FILE_TOO_LARGE");
                }
                output.write(block, 0, amount);
            }
            output.getFD().sync();
            if (total != expectedBytes) throw new IOException("UPDATE_FILE_TRUNCATED");
        } finally {
            connection.disconnect();
        }
    }
}
