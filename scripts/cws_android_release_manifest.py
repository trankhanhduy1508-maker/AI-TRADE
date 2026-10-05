"""Create a signed CWS AutoTrade stable/recovery manifest for an approved APK.

The release workflow must independently verify Android APK signing identity and
extract package versionCode before calling this signer. It never creates a key,
changes the app's permissions, builds an APK, or uploads an artifact. The owner
supplies an existing protected RSA private key outside the repository.
"""
from __future__ import annotations

import argparse
import base64
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import re
from urllib.parse import urlsplit

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

ROOT = Path(__file__).resolve().parents[1]
APPLICATION_ID = "vn.cws.aitrade"
ALLOWED_DOWNLOAD_PREFIX = (
    "https://github.com/trankhanhduy1508-maker/AI-TRADE/releases/download/"
)


def canonical(app_id: str, version_code: int, channel: str, digest: str) -> bytes:
    if (app_id != APPLICATION_ID or isinstance(version_code, bool)
            or not isinstance(version_code, int) or not 0 < version_code <= 2147483647
            or channel not in {"stable", "recovery"}
            or re.fullmatch(r"[a-f0-9]{64}", digest) is None):
        raise ValueError("INVALID_RELEASE_FIELDS")
    return ("CWS_AUTOTRADE_APK_V1\n" + app_id + "\n" + str(version_code)
            + "\n" + channel + "\n" + digest + "\n").encode("utf-8")


def apk_digest(path: Path) -> tuple[str, int]:
    digest = sha256()
    size = 0
    with path.open("rb") as stream:
        while block := stream.read(1024 * 1024):
            size += len(block)
            if size > 250 * 1024 * 1024:
                raise ValueError("APK_EXCEEDS_RELEASE_SIZE_CAP")
            digest.update(block)
    if size < 100:
        raise ValueError("EMPTY_OR_TRUNCATED_APK")
    return digest.hexdigest(), size


def verified_release_uri(uri: str, apk_name: str) -> str:
    if not isinstance(uri, str) or not uri.startswith(ALLOWED_DOWNLOAD_PREFIX):
        raise ValueError("UNTRUSTED_RELEASE_HOST")
    parsed = urlsplit(uri)
    if (parsed.scheme != "https" or parsed.netloc != "github.com"
            or parsed.username or parsed.password or parsed.query or parsed.fragment
            or not parsed.path.startswith(
                "/trankhanhduy1508-maker/AI-TRADE/releases/download/"
            ) or not re.fullmatch(r"[A-Za-z0-9_.-]{4,80}", apk_name)
            or not parsed.path.endswith("/" + apk_name)
            or parsed.path.count("/") != 6
            or not re.fullmatch(
                r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}",
                parsed.path.rsplit("/", 2)[-2]
            )):
        raise ValueError("INVALID_RELEASE_PATH")
    return uri


def sign_release(apk: Path, key_path: Path, version_code: int,
                 channel: str, download_uri: str, previous_version: int) -> dict:
    apk = apk.resolve(strict=True)
    key_path = key_path.resolve(strict=True)
    if (key_path == apk or key_path == ROOT or key_path.is_relative_to(ROOT)
            or key_path.is_relative_to(apk.parent)):
        raise ValueError("SIGNING_KEY_MUST_REMAIN_OUTSIDE_WORKSPACE")
    if (isinstance(previous_version, bool) or not isinstance(previous_version, int)
            or previous_version < 0 or version_code <= previous_version):
        raise ValueError("VERSION_CODE_MUST_INCREASE")
    uri = verified_release_uri(download_uri, apk.name)
    digest, size = apk_digest(apk)
    message = canonical(APPLICATION_ID, version_code, channel, digest)
    password = os.environ.get("CWS_MANIFEST_KEY_PASSWORD")
    secret = key_path.read_bytes()
    key = serialization.load_pem_private_key(
        secret, password=password.encode() if password else None
    )
    if not isinstance(key, rsa.RSAPrivateKey) or key.key_size < 3072:
        raise ValueError("RSA_RELEASE_KEY_TOO_WEAK")
    signature = key.sign(message, padding.PKCS1v15(), hashes.SHA256())
    public_der = key.public_key().public_bytes(
        serialization.Encoding.DER,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return {
        "schema": "CWS_AUTOTRADE_APK_V1",
        "applicationId": APPLICATION_ID,
        "versionCode": version_code,
        "channel": channel,
        "apkUrl": uri,
        "apkBytes": size,
        "apkSha256": digest,
        "signatureAlgorithm": "SHA256withRSA",
        "manifestSignature": base64.b64encode(signature).decode("ascii"),
        "publicKeySpkiSha256": sha256(public_der).hexdigest(),
        "createdAt": datetime.now(timezone.utc).isoformat(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apk", required=True, type=Path)
    parser.add_argument("--signing-key-file", required=True, type=Path)
    parser.add_argument("--version-code", required=True, type=int)
    parser.add_argument("--previous-version-code", required=True, type=int)
    parser.add_argument("--channel", required=True, choices=("stable", "recovery"))
    parser.add_argument("--download-uri", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    # Human release approval and Android APK identity/signature verification
    # are external preconditions, not something a metadata script can fake.
    document = sign_release(args.apk, args.signing_key_file, args.version_code,
                            args.channel, args.download_uri,
                            args.previous_version_code)
    args.output.write_text(json.dumps(document, sort_keys=True, indent=2) + "\n",
                           encoding="utf-8")
    print("PASS: signed release manifest written; Android E2E not verified here")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
