package vn.cws.aitrade;

import android.content.Context;
import android.content.SharedPreferences;
import android.security.keystore.KeyGenParameterSpec;
import android.security.keystore.KeyProperties;

import java.security.GeneralSecurityException;
import java.security.Key;
import java.security.KeyStore;

import javax.crypto.KeyGenerator;
import javax.crypto.SecretKey;

/** Persist only the rotated Google refresh token using this app's Android Keystore. */
public final class NativeEncryptedSession {
    private static final String ALIAS = "vn.cws.aitrade.auth.refresh.v1";
    private static final String PREF = "cws_auth_encrypted_v1";
    private static final String FIELD = "refresh";
    private final SharedPreferences storage;

    public NativeEncryptedSession(Context context) {
        this.storage = context.getApplicationContext().getSharedPreferences(PREF, Context.MODE_PRIVATE);
    }

    private static synchronized SecretKey key() throws GeneralSecurityException {
        try {
            KeyStore store = KeyStore.getInstance("AndroidKeyStore");
            store.load(null);
            Key existing = store.getKey(ALIAS, null);
            if (existing instanceof SecretKey) return (SecretKey) existing;
            KeyGenerator generator = KeyGenerator.getInstance(
                KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore");
            generator.init(new KeyGenParameterSpec.Builder(ALIAS,
                KeyProperties.PURPOSE_ENCRYPT | KeyProperties.PURPOSE_DECRYPT)
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
        // AES-GCM ciphertext only. The AndroidKeyStore SecretKey cannot be
        // serialized or exported; this preference survives in-place updates.
        String sealed = NativeSessionCodec.seal(token, key());
        if (!storage.edit().putString(FIELD, sealed).commit()) {
            throw new GeneralSecurityException("Encrypted session write failed");
        }
    }

    public String load() {
        String encoded = storage.getString(FIELD, null);
        if (encoded == null) return null;
        try {
            return NativeSessionCodec.open(encoded, key());
        } catch (Exception error) {
            clear();
            return null;
        }
    }

    public void clear() {
        if (!storage.edit().remove(FIELD).commit()) {
            throw new SecurityException("Failed to clear encrypted local session");
        }
    }
}
