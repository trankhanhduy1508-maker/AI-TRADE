package vn.cws.aitrade;

import android.content.Context;
import android.content.SharedPreferences;
import android.security.keystore.KeyGenParameterSpec;
import android.security.keystore.KeyProperties;
import android.util.Base64;

import java.nio.charset.StandardCharsets;
import java.security.GeneralSecurityException;
import java.security.Key;
import java.security.KeyStore;
import java.util.Arrays;

import javax.crypto.Cipher;
import javax.crypto.KeyGenerator;
import javax.crypto.SecretKey;
import javax.crypto.spec.GCMParameterSpec;

/** Persist only the rotated Google refresh token using this app's Android Keystore. */
public final class NativeEncryptedSession {
    private static final String ALIAS = "vn.cws.aitrade.auth.refresh.v1";
    private static final String PREF = "cws_auth_encrypted_v1";
    private static final String FIELD = "refresh";
    private static final byte[] AAD =
        "vn.cws.aitrade|google_refresh|v1".getBytes(StandardCharsets.US_ASCII);
    private static final int IV_SIZE = 12;
    private static final int MAX_TOKEN_LENGTH = 4096;
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
        if (token == null || token.length() < 12 || token.length() > MAX_TOKEN_LENGTH
            || !token.matches("[A-Za-z0-9_.-]+")) {
            throw new GeneralSecurityException("Invalid refresh token format");
        }
        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
        cipher.init(Cipher.ENCRYPT_MODE, key());
        cipher.updateAAD(AAD);
        byte[] iv = cipher.getIV();
        if (iv == null || iv.length != IV_SIZE) {
            throw new GeneralSecurityException("Invalid Android Keystore IV");
        }
        byte[] ciphertext = cipher.doFinal(token.getBytes(StandardCharsets.UTF_8));
        byte[] packed = new byte[1 + IV_SIZE + ciphertext.length];
        packed[0] = 1;
        System.arraycopy(iv, 0, packed, 1, IV_SIZE);
        System.arraycopy(ciphertext, 0, packed, 1 + IV_SIZE, ciphertext.length);
        boolean saved = storage.edit().putString(
            FIELD, Base64.encodeToString(packed, Base64.NO_WRAP)).commit();
        Arrays.fill(packed, (byte) 0);
        Arrays.fill(ciphertext, (byte) 0);
        if (!saved) throw new GeneralSecurityException("Encrypted session write failed");
    }

    public String load() {
        String encoded = storage.getString(FIELD, null);
        if (encoded == null || encoded.length() > 6000) return null;
        try {
            byte[] packed = Base64.decode(encoded, Base64.NO_WRAP);
            if (packed.length < 1 + IV_SIZE + 16 || packed[0] != 1) {
                throw new GeneralSecurityException("Invalid encrypted session");
            }
            byte[] iv = Arrays.copyOfRange(packed, 1, 1 + IV_SIZE);
            byte[] ciphertext = Arrays.copyOfRange(packed, 1 + IV_SIZE, packed.length);
            Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
            cipher.init(Cipher.DECRYPT_MODE, key(), new GCMParameterSpec(128, iv));
            cipher.updateAAD(AAD);
            byte[] plaintext = cipher.doFinal(ciphertext);
            String token = new String(plaintext, StandardCharsets.UTF_8);
            Arrays.fill(plaintext, (byte) 0);
            Arrays.fill(ciphertext, (byte) 0);
            Arrays.fill(packed, (byte) 0);
            if (token.length() < 12 || token.length() > MAX_TOKEN_LENGTH
                || !token.matches("[A-Za-z0-9_.-]+")) {
                throw new GeneralSecurityException("Decrypted session invalid");
            }
            return token;
        } catch (Exception error) {
            clear();
            return null;
        }
    }

    public void clear() {
        storage.edit().remove(FIELD).commit();
    }
}
