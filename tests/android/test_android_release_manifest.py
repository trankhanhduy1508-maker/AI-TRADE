"""Offline tests with disposable keys/fake APK bytes. NOT release evidence."""
import base64
from pathlib import Path

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
import pytest

from scripts.cws_android_release_manifest import canonical, sign_release, apk_digest


def fixtures(tmp_path: Path):
    root = tmp_path / "apk"
    root.mkdir()
    apk = root / "cws-autotrade.apk"
    apk.write_bytes(b"this-is-only-mock-apk-not-a-valid-zip" * 100)
    key_path = tmp_path / "owner" / "signing.pem"
    key_path.parent.mkdir()
    private = rsa.generate_private_key(public_exponent=65537, key_size=3072)
    key_path.write_bytes(private.private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption()
    ))
    uri = "https://github.com/trankhanhduy1508-maker/AI-TRADE/releases/download/v1/cws-autotrade.apk"
    return apk, key_path, private, uri


def test_signed_canonical_manifest_matches_java_verifier(tmp_path):
    apk, key, private, uri = fixtures(tmp_path)
    metadata = sign_release(apk, key, 4, "stable", uri, 3)
    data = canonical("vn.cws.aitrade", metadata["versionCode"],
                     metadata["channel"], metadata["apkSha256"])
    assert data.startswith(b"CWS_AUTOTRADE_APK_V1\nvn.cws.aitrade\n4\nstable\n")
    assert metadata["apkSha256"] == apk_digest(apk)[0]
    assert metadata["apkUrl"] == uri
    assert metadata["apkBytes"] == apk.stat().st_size
    private.public_key().verify(
        base64.b64decode(metadata["manifestSignature"]), data,
        padding.PKCS1v15(), hashes.SHA256()
    )
    assert "password" not in str(metadata).lower()


def test_recovery_is_a_higher_version_code(tmp_path):
    apk, key, _, uri = fixtures(tmp_path)
    data = sign_release(apk, key, 5, "recovery", uri, 4)
    assert data["versionCode"] == 5
    with pytest.raises(ValueError, match="VERSION_CODE_MUST_INCREASE"):
        sign_release(apk, key, 4, "recovery", uri, 4)


@pytest.mark.parametrize("url", [
    "http://github.com/trankhanhduy1508-maker/AI-TRADE/releases/download/v1/cws-autotrade.apk",
    "https://evil.example/cws-autotrade.apk",
    "https://github.com.evil.example/trankhanhduy1508-maker/AI-TRADE/releases/download/v1/cws-autotrade.apk",
    "https://github.com/trankhanhduy1508-maker/AI-TRADE/releases/download/v1/other.apk",
    "https://github.com/trankhanhduy1508-maker/AI-TRADE/releases/download/v1/cws-autotrade.apk?evil=1",
])
def test_untrusted_release_location_rejected(tmp_path, url):
    apk, key, _, _ = fixtures(tmp_path)
    with pytest.raises(ValueError, match="(UNTRUSTED_RELEASE_HOST|INVALID_RELEASE_PATH)"):
        sign_release(apk, key, 4, "stable", url, 3)


def test_key_cannot_be_inside_apk_directory(tmp_path):
    apk, key, _, uri = fixtures(tmp_path)
    inside = apk.parent / "private.pem"
    inside.write_bytes(key.read_bytes())
    with pytest.raises(ValueError, match="SIGNING_KEY_MUST_REMAIN_OUTSIDE_WORKSPACE"):
        sign_release(apk, inside, 4, "stable", uri, 3)


def test_malformed_metadata_and_small_file_rejected(tmp_path):
    apk, key, _, uri = fixtures(tmp_path)
    with pytest.raises(ValueError, match="INVALID_RELEASE_FIELDS"):
        canonical("other.package", 4, "stable", "a" * 64)
    with pytest.raises(ValueError, match="INVALID_RELEASE_FIELDS"):
        canonical("vn.cws.aitrade", 4, "beta", "a" * 64)
    with pytest.raises(ValueError, match="INVALID_RELEASE_FIELDS"):
        canonical("vn.cws.aitrade", -1, "stable", "a" * 64)
    apk.write_bytes(b"too short")
    with pytest.raises(ValueError, match="EMPTY_OR_TRUNCATED_APK"):
        sign_release(apk, key, 4, "stable", uri, 3)


def test_python_manifest_signature_verifies_in_android_java_codec(tmp_path):
    """Cross-language RSA contract; fake APK payload, not an Android package."""
    import shutil
    import subprocess
    import textwrap

    javac, java = shutil.which("javac"), shutil.which("java")
    if javac is None or java is None:
        pytest.skip("JDK required for cross-language release manifest contract")
    apk, key, private, uri = fixtures(tmp_path)
    manifest = sign_release(apk, key, 5, "recovery", uri, 4)
    source = (Path(__file__).resolve().parents[2] / "android_native" /
              "vn/cws/aitrade/NativeReleaseVerifier.java")
    if not source.is_file():
        source = (Path(__file__).resolve().parents[2] / "android/app/src/main/java/vn/cws/aitrade/NativeReleaseVerifier.java")
    public_der = private.public_key().public_bytes(
        serialization.Encoding.DER,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    harness = tmp_path / "NativeManifestCrossCheck.java"
    harness.write_text(textwrap.dedent("""
        import vn.cws.aitrade.NativeReleaseVerifier;
        import java.io.FileInputStream;
        import java.security.KeyFactory;
        import java.security.PublicKey;
        import java.security.spec.X509EncodedKeySpec;
        import java.util.Base64;
        public final class NativeManifestCrossCheck {
            public static void main(String[] a) throws Exception {
                PublicKey key = KeyFactory.getInstance("RSA").generatePublic(
                    new X509EncodedKeySpec(Base64.getDecoder().decode(a[0])));
                try (FileInputStream in = new FileInputStream(a[3])) {
                    boolean valid = NativeReleaseVerifier.verify(
                        "vn.cws.aitrade", 4, "vn.cws.aitrade", 5, "recovery",
                        a[1], Base64.getDecoder().decode(a[2]), key, in);
                    if (!valid) throw new AssertionError("Python signature not Java-verifiable");
                    System.out.println("PASS: Python signed manifest verified by Java");
                }
            }
        }
    """), encoding="utf-8")
    subprocess.run([javac, "-encoding", "UTF-8", "-d", str(tmp_path),
                    str(source), str(harness)], check=True, timeout=30)
    result = subprocess.run([java, "-cp", str(tmp_path),
        "NativeManifestCrossCheck",
        base64.b64encode(public_der).decode("ascii"),
        manifest["apkSha256"], manifest["manifestSignature"], str(apk)],
        check=True, capture_output=True, text=True, timeout=30)
    assert result.stdout.strip() == "PASS: Python signed manifest verified by Java"
