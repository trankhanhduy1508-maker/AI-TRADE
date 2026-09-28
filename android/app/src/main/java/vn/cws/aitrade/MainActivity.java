package vn.cws.aitrade;

import android.annotation.SuppressLint;
import android.app.Activity;
import android.os.Build;
import android.window.OnBackInvokedDispatcher;
import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.graphics.Color;
import android.net.Uri;
import android.net.http.SslError;
import android.os.Bundle;
import android.webkit.SslErrorHandler;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;

public final class MainActivity extends Activity {
    private static final String HOST = "oziktadfeenydvgobudr.supabase.co";
    private static final String APP_PATH = "/functions/v1/cws-ai-trade-site/app/";
    private static final int FILE_PICKER = 1304;
    private WebView web;
    private ValueCallback<Uri[]> fileCallback;

    private boolean isApp(Uri uri) {
        return "https".equalsIgnoreCase(uri.getScheme())
            && HOST.equalsIgnoreCase(uri.getHost())
            && APP_PATH.equals(uri.getPath());
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
        s.setAllowContentAccess(true);
        s.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        s.setSafeBrowsingEnabled(true);
        s.setJavaScriptCanOpenWindowsAutomatically(false);
        s.setSupportMultipleWindows(false);
        s.setMediaPlaybackRequiresUserGesture(true);
        WebView.setWebContentsDebuggingEnabled(false);
        web.setWebViewClient(new WebViewClient() {
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
        // API 33+ consumes back gestures here; the legacy override below is only for API 26–32.
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

    @SuppressLint("GestureBackNavigation") // API 26–32 fallback; modern API uses OnBackInvokedCallback.
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
