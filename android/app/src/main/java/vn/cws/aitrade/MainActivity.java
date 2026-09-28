package vn.cws.aitrade;

import android.annotation.SuppressLint;
import android.app.Activity;
import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.graphics.Color;
import android.net.Uri;
import android.net.http.SslError;
import android.os.Build;
import android.os.Bundle;
import android.webkit.SslErrorHandler;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.window.OnBackInvokedDispatcher;

import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;

public final class MainActivity extends Activity {
    // Static CWS HTML is packaged locally: Supabase's shared Edge gateway
    // returns text/plain for HTML and cannot act as the frontend host.
    // The reserved HTTPS origin avoids file:// access and arbitrary redirects.
    private static final String HOST = "appassets.androidplatform.net";
    private static final String APP_PATH = "/assets/";
    private static final int FILE_PICKER = 1304;
    private static final Set<String> ALLOWED = new HashSet<>(Arrays.asList(
        "index.html", "styles.css", "portfolio.js", "tradingview.js",
        "app.js", "pwa.js", "sw.js", "manifest.webmanifest",
        "icon-192.png", "icon-512.png"
    ));
    private static final String CSP = "default-src 'none'; "
        + "script-src 'self' https://cdnjs.cloudflare.com https://s3.tradingview.com; "
        + "style-src 'self' 'unsafe-inline'; "
        + "connect-src 'self' https://raw.githubusercontent.com https://*.tradingview.com; "
        + "img-src 'self' data: https://s3.tradingview.com; "
        + "frame-src https://*.tradingview.com https://tradingview.com; "
        + "font-src 'self'; manifest-src 'self'; worker-src 'none'; "
        + "base-uri 'none'; object-src 'none'; form-action 'self'";
    private WebView web;
    private ValueCallback<Uri[]> fileCallback;

    private boolean isApp(Uri uri) {
        return "https".equalsIgnoreCase(uri.getScheme())
            && HOST.equalsIgnoreCase(uri.getHost())
            && (APP_PATH.equals(uri.getPath())
                || (APP_PATH + "index.html").equals(uri.getPath()));
    }

    private static String contentType(String filename) {
        if (filename.endsWith(".html")) return "text/html";
        if (filename.endsWith(".css")) return "text/css";
        if (filename.endsWith(".js")) return "application/javascript";
        if (filename.endsWith(".webmanifest")) return "application/manifest+json";
        if (filename.endsWith(".png")) return "image/png";
        return "text/plain";
    }

    private WebResourceResponse blocked() {
        WebResourceResponse result = new WebResourceResponse(
            "text/plain", "UTF-8",
            new ByteArrayInputStream("Not found".getBytes(StandardCharsets.UTF_8))
        );
        result.setStatusCodeAndReasonPhrase(404, "Not Found");
        return result;
    }

    private WebResourceResponse localAsset(Uri uri) {
        if (!"https".equalsIgnoreCase(uri.getScheme())
            || !HOST.equalsIgnoreCase(uri.getHost())) return null;
        String pathname = uri.getPath();
        if (pathname == null || !pathname.startsWith(APP_PATH)) return blocked();
        String name = pathname.substring(APP_PATH.length());
        if (name.isEmpty()) name = "index.html";
        if (!ALLOWED.contains(name)) return blocked();
        try {
            // The WebView owns the returned stream and closes it when finished.
            InputStream body = getAssets().open("www/" + name);
            WebResourceResponse response = new WebResourceResponse(
                contentType(name), name.endsWith(".png") ? null : "UTF-8", body
            );
            Map<String,String> headers = new HashMap<>();
            headers.put("X-Content-Type-Options", "nosniff");
            headers.put("Cache-Control", "no-store");
            if (name.equals("index.html")) {
                headers.put("Content-Security-Policy", CSP);
                headers.put("Referrer-Policy", "no-referrer");
            }
            response.setResponseHeaders(headers);
            return response;
        } catch (IOException ignored) {
            return blocked();
        }
    }

    @Override public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        web = new WebView(this);
        web.setBackgroundColor(Color.rgb(8, 17, 30));
        setContentView(web);
        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setAllowFileAccess(false);
        s.setAllowContentAccess(true); // Explicit user-selected EPUB / JSON.
        s.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        s.setSafeBrowsingEnabled(true);
        s.setJavaScriptCanOpenWindowsAutomatically(false);
        s.setSupportMultipleWindows(false);
        s.setMediaPlaybackRequiresUserGesture(true);
        WebView.setWebContentsDebuggingEnabled(false);
        web.setWebViewClient(new WebViewClient() {
            @Override public WebResourceResponse shouldInterceptRequest(WebView v, WebResourceRequest r) {
                return localAsset(r.getUrl());
            }
            @Override public boolean shouldOverrideUrlLoading(WebView v, WebResourceRequest r) {
                if (!r.isForMainFrame()) return false;
                Uri uri = r.getUrl();
                if (isApp(uri)) return false;
                if ("https".equalsIgnoreCase(uri.getScheme())) {
                    Intent intent = new Intent(Intent.ACTION_VIEW, uri);
                    if (intent.resolveActivity(getPackageManager()) != null) startActivity(intent);
                }
                return true;
            }
            @Override public void onReceivedSslError(WebView v, SslErrorHandler h, SslError e) {
                h.cancel();
            }
            @Override public void onPageFinished(WebView v, String url) {
                if (isApp(Uri.parse(url))) {
                    v.evaluateJavascript(
                        "(function(){document.querySelectorAll('a[target=\"_blank\"]').forEach(function(a){a.removeAttribute('target');});})()",
                        null);
                }
            }
        });
        web.setWebChromeClient(new WebChromeClient() {
            @Override public boolean onShowFileChooser(WebView v, ValueCallback<Uri[]> cb,
                                                         WebChromeClient.FileChooserParams params) {
                if (fileCallback != null) fileCallback.onReceiveValue(null);
                fileCallback = cb;
                try {
                    Intent intent = params.createIntent();
                    intent.addCategory(Intent.CATEGORY_OPENABLE);
                    startActivityForResult(intent, FILE_PICKER);
                } catch (ActivityNotFoundException | SecurityException e) {
                    fileCallback.onReceiveValue(null);
                    fileCallback = null;
                    return false;
                }
                return true;
            }
        });
        if (Build.VERSION.SDK_INT >= 33) {
            getOnBackInvokedDispatcher().registerOnBackInvokedCallback(
                OnBackInvokedDispatcher.PRIORITY_DEFAULT,
                () -> {
                    if (web != null && web.canGoBack()) web.goBack();
                    else finish();
                });
        }
        web.loadUrl("https://" + HOST + APP_PATH);
    }

    @Override protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode == FILE_PICKER && fileCallback != null) {
            fileCallback.onReceiveValue(WebChromeClient.FileChooserParams.parseResult(resultCode, data));
            fileCallback = null;
        }
    }

    @SuppressLint("GestureBackNavigation") // API 26–32 fallback.
    @Override public void onBackPressed() {
        if (web != null && web.canGoBack()) web.goBack();
        else super.onBackPressed();
    }

    @Override protected void onDestroy() {
        if (fileCallback != null) {
            fileCallback.onReceiveValue(null);
            fileCallback = null;
        }
        if (web != null) {
            web.stopLoading();
            web.destroy();
            web = null;
        }
        super.onDestroy();
    }
}
