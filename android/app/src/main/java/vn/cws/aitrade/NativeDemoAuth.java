package vn.cws.aitrade;

import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.security.SecureRandom;
import java.util.Base64;

/** Platform-neutral PKCE contract used by the native Android DEMO login. */
public final class NativeDemoAuth {
    public static final String SUPABASE_URL = "https://oziktadfeenydvgobudr.supabase.co";
    public static final String CALLBACK_SCHEME = "vn.cws.aitrade";
    public static final String CALLBACK_HOST = "auth";
    private static final SecureRandom RANDOM = new SecureRandom();

    private NativeDemoAuth() { }

    public static String randomUrlSafe(int bytes) {
        if (bytes < 24 || bytes > 96) throw new IllegalArgumentException("invalid nonce length");
        byte[] value = new byte[bytes];
        RANDOM.nextBytes(value);
        return Base64.getUrlEncoder().withoutPadding().encodeToString(value);
    }

    public static String challenge(String verifier) {
        if (verifier == null || verifier.length() < 43 || verifier.length() > 128
            || !verifier.matches("[A-Za-z0-9_~.\\-]+")) {
            throw new IllegalArgumentException("invalid PKCE verifier");
        }
        try {
            byte[] hash = MessageDigest.getInstance("SHA-256")
                .digest(verifier.getBytes(StandardCharsets.US_ASCII));
            return Base64.getUrlEncoder().withoutPadding().encodeToString(hash);
        } catch (NoSuchAlgorithmException e) {
            throw new IllegalStateException("SHA-256 unavailable", e);
        }
    }

    public static String redirectUri(String nonce) {
        if (nonce == null || !nonce.matches("[A-Za-z0-9_-]{32,128}")) {
            throw new IllegalArgumentException("invalid callback nonce");
        }
        return CALLBACK_SCHEME + "://" + CALLBACK_HOST + "/callback/" + nonce;
    }

    public static String authorizeUrl(String nonce, String verifier) {
        String redirect = redirectUri(nonce);
        return SUPABASE_URL + "/auth/v1/authorize?provider=google"
            + "&redirect_to=" + URLEncoder.encode(redirect, StandardCharsets.UTF_8)
            + "&code_challenge=" + challenge(verifier)
            + "&code_challenge_method=s256";
    }

    public static boolean matchesCallback(String scheme, String host, String path,
                                          String expectedNonce) {
        if (expectedNonce == null) return false;
        return CALLBACK_SCHEME.equals(scheme)
            && CALLBACK_HOST.equals(host)
            && ("/callback/" + expectedNonce).equals(path);
    }
}
