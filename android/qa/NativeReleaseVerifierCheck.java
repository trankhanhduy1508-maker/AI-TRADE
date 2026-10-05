import vn.cws.aitrade.NativeReleaseVerifier;
import java.io.ByteArrayInputStream;
import java.nio.charset.StandardCharsets;
import java.security.KeyPair;
import java.security.KeyPairGenerator;
import java.security.MessageDigest;
import java.security.Signature;
import java.util.HexFormat;

public class NativeReleaseVerifierCheck {
    static byte[] sign(KeyPair keys,String payload) throws Exception {
        Signature signer=Signature.getInstance("SHA256withRSA");
        signer.initSign(keys.getPrivate());
        signer.update(payload.getBytes(StandardCharsets.UTF_8));
        return signer.sign();
    }
    static void check(boolean ok){if(!ok)throw new AssertionError();}
    public static void main(String[] args) throws Exception {
        String pkg="vn.cws.aitrade";
        byte[] apk="offline-test-package-not-an-apk".getBytes(StandardCharsets.UTF_8);
        String sha=HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(apk));
        KeyPairGenerator generator=KeyPairGenerator.getInstance("RSA");generator.initialize(2048);
        KeyPair release=generator.generateKeyPair();KeyPair attacker=generator.generateKeyPair();
        byte[] sig=sign(release,NativeReleaseVerifier.canonical(pkg,4,"stable",sha));
        check(NativeReleaseVerifier.verify(pkg,3,pkg,4,"stable",sha,sig,release.getPublic(),new ByteArrayInputStream(apk)));
        check(!NativeReleaseVerifier.verify(pkg,4,pkg,4,"stable",sha,sig,release.getPublic(),new ByteArrayInputStream(apk)));
        check(!NativeReleaseVerifier.verify(pkg,3,"evil.pkg",4,"stable",sha,sig,release.getPublic(),new ByteArrayInputStream(apk)));
        check(!NativeReleaseVerifier.verify(pkg,3,pkg,4,"beta",sha,sig,release.getPublic(),new ByteArrayInputStream(apk)));
        check(!NativeReleaseVerifier.verify(pkg,3,pkg,4,"stable",sha,sig,attacker.getPublic(),new ByteArrayInputStream(apk)));
        check(!NativeReleaseVerifier.verify(pkg,3,pkg,4,"stable",sha,sig,release.getPublic(),new ByteArrayInputStream("tampered".getBytes(StandardCharsets.UTF_8))));
        byte[] recoverySig=sign(release,NativeReleaseVerifier.canonical(pkg,5,"recovery",sha));
        check(NativeReleaseVerifier.verify(pkg,4,pkg,5,"recovery",sha,recoverySig,release.getPublic(),new ByteArrayInputStream(apk)));
        check(!NativeReleaseVerifier.verify(pkg,5,pkg,4,"stable",sha,sig,release.getPublic(),new ByteArrayInputStream(apk)));
        byte[] corrupted=sig.clone();corrupted[4]^=1;
        check(!NativeReleaseVerifier.verify(pkg,3,pkg,4,"stable",sha,corrupted,release.getPublic(),new ByteArrayInputStream(apk)));
        System.out.println("PASS: signed APK metadata, digest, monotonic stable/recovery policy (9 checks; mock bytes only)");
    }
}
