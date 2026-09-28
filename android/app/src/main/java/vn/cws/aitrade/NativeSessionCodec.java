package vn.cws.aitrade;

import java.nio.charset.StandardCharsets;
import java.security.GeneralSecurityException;
import java.util.Arrays;
import java.util.Base64;

import javax.crypto.Cipher;
import javax.crypto.SecretKey;
import javax.crypto.spec.GCMParameterSpec;

/** Pure-Java wire format; hardware-backed key ownership stays in Android Keystore. */
public final class NativeSessionCodec {
    private static final byte[] AAD =
        "vn.cws.aitrade|google_refresh|v1".getBytes(StandardCharsets.US_ASCII);
    private static final int IV_SIZE = 12;
    private NativeSessionCodec() { }

    public static String seal(String token, SecretKey key) throws GeneralSecurityException {
        if (key == null || token == null || !token.matches("[A-Za-z0-9_.-]{12,4096}")) {
            throw new GeneralSecurityException("Invalid refresh session");
        }
        byte[] clear = token.getBytes(StandardCharsets.UTF_8);
        try {
            Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
            cipher.init(Cipher.ENCRYPT_MODE, key);
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
                return Base64.getUrlEncoder().withoutPadding().encodeToString(packed);
            } finally {
                Arrays.fill(packed, (byte) 0);
                Arrays.fill(encrypted, (byte) 0);
            }
        } finally {
            Arrays.fill(clear, (byte) 0);
        }
    }

    public static String open(String encoded, SecretKey key) throws GeneralSecurityException {
        if (key == null || encoded == null || encoded.length() > 6000
            || !encoded.matches("[A-Za-z0-9_-]+")) {
            throw new GeneralSecurityException("Invalid encrypted session format");
        }
        byte[] packed;
        try {
            packed = Base64.getUrlDecoder().decode(encoded);
        } catch (IllegalArgumentException invalid) {
            throw new GeneralSecurityException("Invalid encrypted session encoding", invalid);
        }
        try {
            if (packed.length < 1 + IV_SIZE + 16 || packed[0] != 1) {
                throw new GeneralSecurityException("Invalid encrypted session version");
            }
            byte[] iv = Arrays.copyOfRange(packed, 1, 1 + IV_SIZE);
            byte[] ciphertext = Arrays.copyOfRange(packed, 1 + IV_SIZE, packed.length);
            try {
                Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
                cipher.init(Cipher.DECRYPT_MODE, key, new GCMParameterSpec(128, iv));
                cipher.updateAAD(AAD);
                byte[] clear = cipher.doFinal(ciphertext);
                try {
                    String token = new String(clear, StandardCharsets.UTF_8);
                    if (!token.matches("[A-Za-z0-9_.-]{12,4096}")) {
                        throw new GeneralSecurityException("Invalid decrypted refresh token");
                    }
                    return token;
                } finally {
                    Arrays.fill(clear, (byte) 0);
                }
            } finally {
                Arrays.fill(ciphertext, (byte) 0);
                Arrays.fill(iv, (byte) 0);
            }
        } finally {
            Arrays.fill(packed, (byte) 0);
        }
    }
}
