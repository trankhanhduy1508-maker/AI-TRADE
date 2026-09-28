package vn.cws.aitrade;

import android.app.Activity;
import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.content.SharedPreferences;
import android.net.Uri;
import android.os.Bundle;
import android.text.InputType;
import android.view.View;
import android.view.WindowManager;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/** Native, fail-closed DEMO account screen. No OAuth inside a WebView. */
public final class DemoLoginActivity extends Activity {
    // A publishable client key, not a database service key or MT5 credential.
    private static final String PUBLISHABLE_KEY = "sb_publishable_0cpWKAruLpo2lm412LKWKg_QN8RRU-l";
    private static final String API = "/functions/v1/ai-trade-founder-mt5/";
    private static final long AUTH_MAX_AGE_MS = 5 * 60 * 1000L;
    private final ExecutorService network = Executors.newSingleThreadExecutor();
    private EditText login;
    private EditText server;
    private EditText password;
    private Button verifyButton;
    private Button refreshButton;
    private TextView status;
    private TextView account;
    private final Object sessionLock = new Object();
    private NativeEncryptedSession encryptedSession;
    private volatile String accessToken = "";
    private volatile long sessionGeneration = 0L;
    private volatile long accessTokenExpiresAt = 0L;

    @Override public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        encryptedSession = new NativeEncryptedSession(this);
        // Protect broker credential entry from screenshots and screen recordings.
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_SECURE);
        LinearLayout form = new LinearLayout(this);
        form.setOrientation(LinearLayout.VERTICAL);
        form.setPadding(22, 22, 22, 22);
        TextView title = new TextView(this);
        title.setText("CWS AutoTrade | MT5 DEMO");
        title.setTextSize(22);
        form.addView(title);
        status = new TextView(this);
        status.setText("Google chưa đăng nhập. Auto Trade: LOCKED. LIVE: LOCKED.");
        form.addView(status);
        Button googleButton = new Button(this);
        googleButton.setText("Đăng nhập Google");
        googleButton.setOnClickListener(view -> beginGoogleLogin());
        form.addView(googleButton);
        login = input(form, "Login MT5 DEMO", InputType.TYPE_CLASS_NUMBER);
        server = input(form, "Server", InputType.TYPE_CLASS_TEXT);
        server.setText("MetaQuotes-Demo");
        password = input(form, "Password MT5 DEMO",
            InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_PASSWORD);
        verifyButton = new Button(this);
        verifyButton.setText("Xác minh DEMO, không đặt lệnh");
        verifyButton.setEnabled(false);
        verifyButton.setOnClickListener(view -> verifyDemo());
        form.addView(verifyButton);
        refreshButton = new Button(this);
        refreshButton.setText("Làm mới trạng thái");
        refreshButton.setEnabled(false);
        refreshButton.setOnClickListener(view -> refresh());
        form.addView(refreshButton);
        Button logout = new Button(this);
        logout.setText("Đăng xuất");
        logout.setOnClickListener(view -> {
            final String oldBearer;
            synchronized (sessionLock) {
                sessionGeneration++;
                oldBearer = accessToken;
                accessToken = "";
                accessTokenExpiresAt = 0L;
                encryptedSession.clear();
                pending().edit().clear().apply();
            }
            password.setText("");
            verifyButton.setEnabled(false);
            refreshButton.setEnabled(false);
            account.setText("—");
            status.setText("Đã xóa phiên trên máy. Auto Trade: LOCKED.");
            if (!oldBearer.isEmpty()) {
                network.execute(() -> {
                    try {
                        request("POST", "/auth/v1/logout", null, oldBearer, 12000);
                    } catch (Exception ignored) {
                        // Offline logout must still invalidate all locally held credentials.
                    }
                });
            }
        });
        form.addView(logout);
        account = new TextView(this);
        account.setText("Balance: — | Equity: — | Positions: —\nAuto Trade: LOCKED");
        form.addView(account);
        ScrollView scroll = new ScrollView(this);
        scroll.addView(form);
        setContentView(scroll);
        Intent start = getIntent();
        if (start != null && start.getData() != null) {
            handleCallback(start);
        } else {
            restoreSession();
        }
    }

    private EditText input(LinearLayout form, String hint, int type) {
        EditText result = new EditText(this);
        result.setHint(hint);
        result.setInputType(type);
        result.setSingleLine(true);
        form.addView(result);
        return result;
    }

    private SharedPreferences pending() {
        return getPreferences(MODE_PRIVATE);
    }

    private void beginGoogleLogin() {
        synchronized (sessionLock) {
            sessionGeneration++;
            accessToken = "";
            accessTokenExpiresAt = 0L;
            encryptedSession.clear();
        }
        verifyButton.setEnabled(false);
        refreshButton.setEnabled(false);
        account.setText("Balance: — | Equity: — | Positions: —");
        String verifier = NativeDemoAuth.randomUrlSafe(64);
        String nonce = NativeDemoAuth.randomUrlSafe(24);
        pending().edit().putString("verifier", verifier)
            .putString("nonce", nonce)
            .putLong("issued", System.currentTimeMillis()).apply();
        try {
            Intent browser = new Intent(Intent.ACTION_VIEW,
                Uri.parse(NativeDemoAuth.authorizeUrl(nonce, verifier)));
            browser.addCategory(Intent.CATEGORY_BROWSABLE);
            startActivity(browser);
            status.setText("Hoàn tất đăng nhập Google trong trình duyệt Android.");
        } catch (ActivityNotFoundException | SecurityException error) {
            pending().edit().clear().apply();
            status.setText("Không có trình duyệt hỗ trợ. Không mở phiên.");
        }
    }

    @Override protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        setIntent(intent);
        handleCallback(intent);
    }

    private void handleCallback(Intent intent) {
        Uri uri = intent == null ? null : intent.getData();
        if (uri == null) return;
        SharedPreferences prefs = pending();
        String nonce = prefs.getString("nonce", null);
        String verifier = prefs.getString("verifier", null);
        long issued = prefs.getLong("issued", 0L);
        long age = System.currentTimeMillis() - issued;
        boolean valid = age >= 0 && age < AUTH_MAX_AGE_MS
            && verifier != null
            && NativeDemoAuth.matchesCallback(uri.getScheme(), uri.getHost(), uri.getPath(), nonce);
        prefs.edit().clear().apply();
        String code = valid ? uri.getQueryParameter("code") : null;
        if (!valid || code == null || !code.matches("[A-Za-z0-9_-]{16,128}")) {
            status.setText("Callback không hợp lệ hoặc quá hạn. Đăng nhập lại.");
            return;
        }
        status.setText("Đang xác minh Google trên máy chủ…");
        final long generation = sessionGeneration;
        network.execute(() -> {
            try {
                JSONObject body = new JSONObject();
                body.put("auth_code", code);
                body.put("code_verifier", verifier);
                JSONObject result = request("POST", "/auth/v1/token?grant_type=pkce",
                    body, null, 20000);
                String bearer = acceptTokens(result, generation);
                if (bearer == null) return;
                runOnUiThread(() -> {
                    if (generation != sessionGeneration) return;
                    verifyButton.setEnabled(true);
                    refreshButton.setEnabled(true);
                    status.setText("Google Founder đã xác thực. Chỉ đọc MT5 DEMO.");
                    refresh();
                });
            } catch (Exception error) {
                if (generation == sessionGeneration) {
                    synchronized (sessionLock) {
                        if (generation == sessionGeneration) {
                            accessToken = "";
                            accessTokenExpiresAt = 0L;
                            encryptedSession.clear();
                        }
                    }
                    runOnUiThread(() -> {
                        if (generation == sessionGeneration) {
                            verifyButton.setEnabled(false);
                            refreshButton.setEnabled(false);
                            status.setText("Google OAuth/Founder không hợp lệ. Đăng nhập lại.");
                        }
                    });
                }
            }
        });
    }

    /** Only a Google session with an active Founder entitlement is accepted. */
    private String acceptTokens(JSONObject tokens, long generation) throws Exception {
        String bearer = tokens.optString("access_token", "");
        String rotated = tokens.optString("refresh_token", "");
        long expires = tokens.optLong("expires_in", 0L);
        if (bearer.length() < 32 || rotated.length() < 12 || expires <= 60
            || expires > 86400L) throw new IOException("INVALID_GOOGLE_SESSION");
        JSONObject identity = request("GET", API + "status", null, bearer, 18000);
        if (!identity.optBoolean("ok", false)
            || !"GOOGLE_FOUNDER".equals(identity.optString("auth", ""))) {
            throw new IOException("FOUNDER_ENTITLEMENT_REQUIRED");
        }
        synchronized (sessionLock) {
            if (generation != sessionGeneration) return null;
            // Save rotated token BEFORE publishing a valid in-memory access token.
            encryptedSession.save(rotated);
            accessToken = bearer;
            accessTokenExpiresAt = System.currentTimeMillis() + expires * 1000L;
        }
        return bearer;
    }

    private void restoreSession() {
        final String token = encryptedSession.load();
        if (token == null) return;
        final long generation = sessionGeneration;
        status.setText("Đang khôi phục Google Founder…");
        network.execute(() -> {
            try {
                JSONObject body = new JSONObject();
                body.put("refresh_token", token);
                JSONObject response = request("POST", "/auth/v1/token?grant_type=refresh_token",
                    body, null, 20000);
                String bearer = acceptTokens(response, generation);
                if (bearer == null) return;
                runOnUiThread(() -> {
                    if (generation != sessionGeneration) return;
                    verifyButton.setEnabled(true);
                    refreshButton.setEnabled(true);
                    status.setText("Đã khôi phục phiên Google Founder.");
                    refresh();
                });
            } catch (Exception error) {
                synchronized (sessionLock) {
                    if (generation != sessionGeneration) return;
                    encryptedSession.clear();
                    accessToken = "";
                    accessTokenExpiresAt = 0L;
                }
                runOnUiThread(() -> {
                    if (generation == sessionGeneration) {
                        verifyButton.setEnabled(false);
                        refreshButton.setEnabled(false);
                        status.setText("Không thể khôi phục phiên. Đăng nhập Google lại.");
                    }
                });
            }
        });
    }

    /** Invoked on the single network executor, never on the UI thread. */
    private String authorizedToken() throws Exception {
        String bearer = accessToken;
        if (!bearer.isEmpty() && System.currentTimeMillis() + 60_000L
            < accessTokenExpiresAt) return bearer;
        final long generation = sessionGeneration;
        String refresh = encryptedSession.load();
        if (refresh == null) throw new IOException("GOOGLE_SESSION_EXPIRED");
        JSONObject body = new JSONObject();
        body.put("refresh_token", refresh);
        JSONObject response = request("POST", "/auth/v1/token?grant_type=refresh_token",
            body, null, 20000);
        String renewed = acceptTokens(response, generation);
        if (renewed == null) throw new IOException("GOOGLE_SESSION_CHANGED");
        return renewed;
    }

    private void refresh() {
        final long generation = sessionGeneration;
        refreshButton.setEnabled(false);
        status.setText("Đang đọc MT5 DEMO mới từ broker. Không gửi lệnh.");
        network.execute(() -> {
            try {
                if (generation != sessionGeneration) return;
                String bearer = authorizedToken();
                JSONObject current = request("GET", API + "status", null,
                    bearer, 18000);
                if (generation != sessionGeneration || !bearer.equals(accessToken)) return;
                if (!current.optBoolean("ok", false)
                    || !"GOOGLE_FOUNDER".equals(current.optString("auth", ""))) {
                    throw new IOException("FOUNDER_SESSION_REQUIRED");
                }
                JSONObject linked = current.optJSONObject("account");
                if (linked == null) {
                    runOnUiThread(() -> {
                        if (generation != sessionGeneration) return;
                        account.setText("Chưa liên kết tài khoản MT5 DEMO.\n"
                            + "Balance: — | Equity: — | Positions: —"
                            + "\nAuto Trade: LOCKED | LIVE: LOCKED");
                        status.setText("Nhập tài khoản DEMO đã được liên kết.");
                    });
                    return;
                }
                String linkedLogin = linked.optString("login", "");
                String linkedServer = linked.optString("server", "");
                if (!linkedLogin.matches("[1-9][0-9]{4,14}")
                    || !"MetaQuotes-Demo".equals(linkedServer)) {
                    throw new IOException("UNSUPPORTED_BROKER_BINDING");
                }
                // Caller cannot choose an account: backend resolves the bound
                // Founder-owned DEMO account and fetches fresh broker data.
                JSONObject broker = request("POST", API + "snapshot", null,
                    bearer, 125000);
                if (generation != sessionGeneration || !bearer.equals(accessToken)) return;
                if (!broker.optBoolean("ok", false)
                    || !"DEMO_SNAPSHOT_READ_ONLY".equals(broker.optString("status", ""))
                    || !"DEMO".equals(broker.optString("mode", ""))
                    || !linkedLogin.equals(broker.optString("login", ""))
                    || !linkedServer.equals(broker.optString("server", ""))) {
                    throw new IOException("BROKER_SNAPSHOT_INVALID");
                }
                double balance = broker.optDouble("balance", Double.NaN);
                String currency = broker.optString("currency", "");
                if (!Double.isFinite(balance) || !currency.matches("[A-Z]{3,8}")) {
                    throw new IOException("BROKER_BALANCE_INVALID");
                }
                String asOf = broker.optString("asOf", "—");
                final String display = "Login: " + linkedLogin + " | " + linkedServer
                    + "\nBalance: " + balance + " " + currency
                    + "\nEquity: — | Positions: —"
                    + "\nĐọc từ broker lúc: " + asOf
                    + "\nAuto Trade: LOCKED | LIVE: LOCKED";
                runOnUiThread(() -> {
                    if (generation != sessionGeneration) return;
                    account.setText(display);
                    status.setText("MT5 DEMO được xác minh chỉ đọc.");
                });
            } catch (Exception error) {
                runOnUiThread(() -> {
                    if (generation != sessionGeneration) return;
                    account.setText("Balance: — | Equity: — | Positions: —"
                        + "\nKhông có dữ liệu broker mới."
                        + "\nAuto Trade: LOCKED | LIVE: LOCKED");
                    status.setText("Không thể đọc broker DEMO. Không gửi lệnh.");
                });
            } finally {
                runOnUiThread(() -> {
                    if (generation == sessionGeneration) {
                        refreshButton.setEnabled(!accessToken.isEmpty());
                    }
                });
            }
        });
    }

    private void verifyDemo() {
        String id = login.getText().toString().trim();
        String host = server.getText().toString().trim();
        String secret = password.getText().toString();
        password.setText("");
        if (!id.matches("[1-9][0-9]{4,14}") || !"MetaQuotes-Demo".equals(host)
            || secret.length() < 4 || secret.length() > 32) {
            status.setText("UNSUPPORTED_SERVER hoặc thông tin DEMO không hợp lệ.");
            return;
        }
        verifyButton.setEnabled(false);
        status.setText("Đang xác minh MT5 DEMO trên máy chủ. Không gửi lệnh.");
        final long generation = sessionGeneration;
        network.execute(() -> {
            try {
                if (generation != sessionGeneration) return;
                JSONObject payload = new JSONObject();
                payload.put("login", id);
                payload.put("server", host);
                payload.put("password", secret);
                String bearer = authorizedToken();
                JSONObject reply = request("POST", API + "verify-demo", payload,
                    bearer, 125000);
                if (!bearer.equals(accessToken) || generation != sessionGeneration) return;
                if (!reply.optBoolean("ok", false)
                    || !"DEMO_VERIFIED_READ_ONLY".equals(reply.optString("status"))) {
                    throw new IOException("DEMO_NOT_VERIFIED");
                }
                String verifiedAt = reply.optString("verifiedAt", "—");
                String currency = reply.optString("currency", "");
                double balance = reply.optDouble("balance", Double.NaN);
                String balanceText = Double.isFinite(balance) && !currency.isEmpty()
                    ? String.valueOf(balance) + " " + currency : "—";
                runOnUiThread(() -> {
                    if (generation != sessionGeneration) return;
                    status.setText("DEMO đã xác minh chỉ đọc. Auto Trade: LOCKED.");
                    account.setText("Login: " + id + " | Server: " + host
                        + "\nBalance: " + balanceText
                        + " | Equity: — | Positions: —"
                        + "\nBroker readback: " + verifiedAt
                        + "\nAuto Trade: LOCKED | LIVE: LOCKED");
                });
            } catch (Exception error) {
                runOnUiThread(() -> {
                    if (generation == sessionGeneration) {
                        status.setText("Không xác minh được MT5 DEMO. Không gửi lệnh.");
                    }
                });
            } finally {
                runOnUiThread(() -> {
                    if (generation == sessionGeneration) {
                        verifyButton.setEnabled(!accessToken.isEmpty());
                    }
                });
            }
        });
    }

    /** Response size bounded; no redirects, logs, insecure HTTP or secrets in errors. */
    private JSONObject request(String method, String route, JSONObject body,
                               String bearer, int readTimeout) throws Exception {
        URL url = new URL(NativeDemoAuth.SUPABASE_URL + route);
        HttpURLConnection c = (HttpURLConnection) url.openConnection();
        c.setConnectTimeout(12000);
        c.setReadTimeout(readTimeout);
        c.setInstanceFollowRedirects(false);
        c.setRequestMethod(method);
        c.setRequestProperty("apikey", PUBLISHABLE_KEY);
        c.setRequestProperty("Accept", "application/json");
        c.setRequestProperty("Cache-Control", "no-store");
        if (bearer != null) c.setRequestProperty("Authorization", "Bearer " + bearer);
        try {
            if (body != null) {
                c.setDoOutput(true);
            c.setRequestProperty("Content-Type", "application/json");
            try (OutputStream out = c.getOutputStream()) {
                out.write(body.toString().getBytes(StandardCharsets.UTF_8));
            }
            }
            int statusCode = c.getResponseCode();
            if (statusCode < 200 || statusCode >= 300) throw new IOException("HTTP_ERROR");
            try (InputStream stream = c.getInputStream();
                 ByteArrayOutputStream result = new ByteArrayOutputStream()) {
                byte[] buffer = new byte[4096];
                int n;
                while ((n = stream.read(buffer)) != -1) {
                    if (result.size() + n > 32768) throw new IOException("OVERSIZE_RESPONSE");
                    result.write(buffer, 0, n);
                }
                return new JSONObject(result.toString(StandardCharsets.UTF_8.name()));
            }
        } finally {
            c.disconnect();
        }
    }

    @Override protected void onDestroy() {
        synchronized (sessionLock) {
            sessionGeneration++;
            accessToken = "";
            accessTokenExpiresAt = 0L;
        }
        if (password != null) password.setText("");
        network.shutdownNow();
        super.onDestroy();
    }
}
