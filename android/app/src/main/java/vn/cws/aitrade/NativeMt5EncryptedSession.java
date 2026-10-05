package vn.cws.aitrade;

import android.content.Context;
import android.content.SharedPreferences;
import android.security.keystore.KeyGenParameterSpec;
import android.security.keystore.KeyProperties;

import java.nio.charset.StandardCharsets;
import java.security.GeneralSecurityException;
import java.security.Key;
import java.security.KeyStore;
import java.util.Arrays;
import java.util.Base64;

import javax.crypto.Cipher;
import javax.crypto.KeyGenerator;
import javax.crypto.SecretKey;
import javax.crypto.spec.GCMParameterSpec;

/** Stores only the opaque MT5 session token. The broker password is never persisted. */
public final class NativeMt5EncryptedSession {
    private static final String ALIAS = "vn.cws.aitrade.mt5.session.v1";
    private static final String PREF = "cws_mt5_session_encrypted_v1";
    private static final String FIELD = "session";
    private static final byte[] AAD =
        "vn.cws.aitrade|mt5_session|v1".getBytes(StandardCharsets.US_ASCII);
    private static final int IV_SIZE = 12;
    private final SharedPreferences storage;

    public NativeMt5EncryptedSession(Context context) {
        storage = context.getApplicationContext()
            .getSharedPreferences(PREF, Context.MODE_PRIVATE);
    }

    private static synchronized SecretKey key() throws GeneralSecurityException {
        try {
            KeyStore store = KeyStore.getInstance("AndroidKeyStore");
            store.load(null);
            Key existing = store.getKey(ALIAS, null);
            if (existing instanceof SecretKey) return (SecretKey) existing;
            KeyGenerator generator = KeyGenerator.getInstance(
                KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore");
            generator.init(new KeyGenParameterSpec.Builder(
                ALIAS, KeyProperties.PURPOSE_ENCRYPT | KeyProperties.PURPOSE_DECRYPT)
                .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
                .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
                .setKeySize(256)
                .build());
            return generator.generateKey();
        } catch (GeneralSecurityException error) {
            throw error;
        } catch (Exception error) {
            throw new GeneralSecurityException("Android Keystore unavailable", error);
        }
    }

    public void save(String token) throws GeneralSecurityException {
        if (token == null || !token.matches("[A-Za-z0-9_-]{40,128}")) {
            throw new GeneralSecurityException("Invalid MT5 session token");
        }
        byte[] clear = token.getBytes(StandardCharsets.UTF_8);
        try {
            Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
            cipher.init(Cipher.ENCRYPT_MODE, key());
            cipher.updateAAD(AAD);
            byte[] iv = cipher.getIV();
            if (iv == null || iv.length != IV_SIZE) {
                throw new GeneralSecurityException("Invalid GCM IV");
            }
            byte[] encrypted = cipher.doFinal(clear);
            byte[] packed = new byte[1 + IV_SIZE + encrypted.length];
            try {
                packed[0] = 1;
                System.arraycopy(iv, 0, packed, 1, IV_SIZE);
                System.arraycopy(encrypted, 0, packed, 1 + IV_SIZE, encrypted.length);
                String sealed = Base64.getUrlEncoder().withoutPadding().encodeToString(packed);
                if (!storage.edit().putString(FIELD, sealed).commit()) {
                    throw new GeneralSecurityException("Encrypted session write failed");
                }
            } finally {
                Arrays.fill(packed, (byte)0);
                Arrays.fill(encrypted, (byte)0);
                Arrays.fill(iv, (byte)0);
            }
        } finally {
            Arrays.fill(clear, (byte)0);
        }
    }

    public String load() {
        String encoded = storage.getString(FIELD, null);
        if (encoded == null || !encoded.matches("[A-Za-z0-9_-]{40,6000}")) return null;
        byte[] packed;
        try {
            packed = Base64.getUrlDecoder().decode(encoded);
        } catch (IllegalArgumentException error) {
            clearQuietly();
            return null;
        }
        try {
            if (packed.length < 1 + IV_SIZE + 16 || packed[0] != 1) {
                clearQuietly();
                return null;
            }
            byte[] iv = Arrays.copyOfRange(packed, 1, 1 + IV_SIZE);
            byte[] encrypted = Arrays.copyOfRange(packed, 1 + IV_SIZE, packed.length);
            try {
                Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
                cipher.init(Cipher.DECRYPT_MODE, key(), new GCMParameterSpec(128, iv));
                cipher.updateAAD(AAD);
                byte[] clear = cipher.doFinal(encrypted);
                try {
                    String token = new String(clear, StandardCharsets.UTF_8);
                    if (!token.matches("[A-Za-z0-9_-]{40,128}")) {
                        clearQuietly();
                        return null;
                    }
                    return token;
                } finally {
                    Arrays.fill(clear, (byte)0);
                }
            } finally {
                Arrays.fill(iv, (byte)0);
                Arrays.fill(encrypted, (byte)0);
            }
        } catch (Exception error) {
            clearQuietly();
            return null;
        } finally {
            Arrays.fill(packed, (byte)0);
        }
    }

    public void clear() {
        if (!storage.edit().remove(FIELD).commit()) {
            throw new SecurityException("Failed to clear encrypted MT5 session");
        }
    }

    private void clearQuietly() {
        storage.edit().remove(FIELD).commit();
    }
}
