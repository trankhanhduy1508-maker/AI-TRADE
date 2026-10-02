import vn.cws.aitrade.NativeSessionCodec;
import java.security.GeneralSecurityException;
import java.util.Base64;
import javax.crypto.KeyGenerator;
import javax.crypto.SecretKey;

public final class NativeSessionCodecCheck {
    private static void ok(boolean value) { if (!value) throw new AssertionError(); }
    private static void blocked(Checked action) throws Exception {
        try { action.run(); } catch (GeneralSecurityException expected) { return; }
        throw new AssertionError("Expected fail-closed session check");
    }
    private interface Checked { void run() throws Exception; }
    public static void main(String[] args) throws Exception {
        KeyGenerator generator = KeyGenerator.getInstance("AES");
        generator.init(256);
        SecretKey main = generator.generateKey();
        SecretKey other = generator.generateKey();
        String token = "v1.SecureRefreshToken_1234567890";
        String sealed = NativeSessionCodec.seal(token, main);
        ok(token.equals(NativeSessionCodec.open(sealed, main)));
        ok(!sealed.equals(NativeSessionCodec.seal(token, main)));
        blocked(() -> NativeSessionCodec.open(sealed, other));
        byte[] tampered = Base64.getUrlDecoder().decode(sealed);
        tampered[tampered.length - 1] ^= 1;
        blocked(() -> NativeSessionCodec.open(Base64.getUrlEncoder().withoutPadding().encodeToString(tampered), main));
        byte[] wrongVersion = Base64.getUrlDecoder().decode(sealed);
        wrongVersion[0] = 2;
        blocked(() -> NativeSessionCodec.open(Base64.getUrlEncoder().withoutPadding().encodeToString(wrongVersion), main));
        blocked(() -> NativeSessionCodec.open("__not-base64---*", main));
        blocked(() -> NativeSessionCodec.open(null, main));
        blocked(() -> NativeSessionCodec.seal("short", main));
        blocked(() -> NativeSessionCodec.seal(token, null));
        blocked(() -> NativeSessionCodec.open("A".repeat(6001), main));
        System.out.println("PASS: 10 offline AES-GCM session wire-format checks; Android Keystore/device NOT tested");
    }
}
