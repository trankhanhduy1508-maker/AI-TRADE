"""Private, fail-closed EPUB provenance staging for CWS's authored Masterbook.

Extracted chapter text is written only to an explicitly selected *private* local
quarantine directory, not the repository or public Supabase website. Reading a
book does not approve a trading strategy or train numerical model weights.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path, PurePosixPath
import posixpath
import re
import stat
from xml.etree import ElementTree as ET
from zipfile import ZipFile, ZIP_STORED, BadZipFile

from .pipeline import GateError

MAX_ARCHIVE = 20 * 1024 * 1024
MAX_EXPANDED = 40 * 1024 * 1024
MAX_MEMBERS = 2000
NS_DC = "http://purl.org/dc/elements/1.1/"
NS_OPF = "http://www.idpf.org/2007/opf"
NS_XHTML = "http://www.w3.org/1999/xhtml"


def _xml(data: bytes) -> ET.Element:
    # EPUB3 chapter XHTML commonly contains a harmless literal HTML doctype.
    # Strip only that exact form; reject external/system/inline DTD and entities.
    data = re.sub(br"<!DOCTYPE\s+html\s*>", b"", data, flags=re.I)
    if re.search(br"<!\s*(DOCTYPE|ENTITY)\b", data, re.I):
        raise GateError("external or inline EPUB XML entity/doctype is not accepted")
    if b"\xef\xbf\xbd" in data:
        raise GateError("EPUB XML contains Unicode replacement characters")
    try:
        return ET.fromstring(data)
    except ET.ParseError as exc:
        raise GateError("EPUB XML is malformed") from exc


def _inside(opf_path: str, href: str, names: set[str]) -> str:
    if not href or re.match(r"^[a-zA-Z][\w+.-]*:", href) or href.startswith("/"):
        raise GateError("external or absolute EPUB spine path")
    raw = href.split("#", 1)[0].split("?", 1)[0]
    resolved = posixpath.normpath(posixpath.join(posixpath.dirname(opf_path), raw))
    if resolved.startswith("../") or resolved == ".." or resolved not in names:
        raise GateError("EPUB spine path escapes or does not exist")
    return resolved


def inspect_epub(epub: Path, *, source_id: str) -> dict:
    """Read a source, validate its actual manifest/spine and hash each chapter.

    The returned object contains chapter text for private local staging. Callers
    must never print, publish or store this raw return object in a public repo.
    """
    if not re.fullmatch(r"[a-zA-Z0-9_-]{3,80}", source_id):
        raise GateError("invalid source id")
    if not epub.is_file() or epub.stat().st_size > MAX_ARCHIVE or epub.stat().st_size == 0:
        raise GateError("missing, empty or too large EPUB")
    raw_epub = epub.read_bytes()
    try:
        with ZipFile(epub) as z:
            entries = z.infolist()
            if not entries or entries[0].filename != "mimetype" or entries[0].compress_type != ZIP_STORED:
                raise GateError("EPUB mimetype must be the first uncompressed ZIP member")
            if z.read("mimetype") != b"application/epub+zip":
                raise GateError("incorrect EPUB mimetype")
            if len(entries) > MAX_MEMBERS or sum(e.file_size for e in entries) > MAX_EXPANDED:
                raise GateError("EPUB exceeds safe extraction limits")
            names = [e.filename for e in entries]
            if len(names) != len(set(names)):
                raise GateError("duplicate EPUB member names")
            for e in entries:
                normalized = PurePosixPath(e.filename)
                if e.filename.startswith("/") or ".." in normalized.parts or stat.S_ISLNK(e.external_attr >> 16):
                    raise GateError("unsafe EPUB member")
            if z.testzip() is not None:
                raise GateError("EPUB ZIP CRC validation failed")
            container = _xml(z.read("META-INF/container.xml"))
            rootfiles = container.findall(".//{*}rootfile")
            if len(rootfiles) != 1:
                raise GateError("EPUB must identify exactly one OPF")
            opf_path = rootfiles[0].get("full-path", "")
            if opf_path not in names or not opf_path.endswith(".opf"):
                raise GateError("invalid OPF reference")
            opf = _xml(z.read(opf_path))
            def meta(name: str) -> str:
                node = opf.find(".//{" + NS_DC + "}" + name)
                return (node.text or "").strip() if node is not None else ""
            title, creator, language, rights = (meta(v) for v in ("title", "creator", "language", "rights"))
            if not title or not creator or not language:
                raise GateError("EPUB title/creator/language is required")
            manifest = {}
            for item in opf.findall(".//{" + NS_OPF + "}manifest/{" + NS_OPF + "}item"):
                id_ = item.get("id", "")
                if not id_ or id_ in manifest:
                    raise GateError("missing or duplicate EPUB manifest id")
                manifest[id_] = (item.get("href", ""), item.get("media-type", ""))
            spine = opf.findall(".//{" + NS_OPF + "}spine/{" + NS_OPF + "}itemref")
            if not spine or len(spine) > MAX_MEMBERS:
                raise GateError("EPUB spine missing or too large")
            chapters = []
            for item in spine:
                item_id = item.get("idref", "")
                if item_id not in manifest:
                    raise GateError("EPUB spine points to missing manifest item")
                href, mime = manifest[item_id]
                if mime != "application/xhtml+xml":
                    raise GateError("EPUB spine item is not XHTML")
                path = _inside(opf_path, href, set(names))
                root = _xml(z.read(path))
                body = root.find(".//{" + NS_XHTML + "}body")
                if body is None:
                    raise GateError("EPUB spine XHTML missing body")
                text = " ".join(" ".join(body.itertext()).split())
                if "\ufffd" in text:
                    raise GateError("EPUB chapter contains replacement characters")
                if text:
                    chapters.append({"chapter_id": item_id, "source_path": path,
                                     "text_sha256": sha256(text.encode("utf-8")).hexdigest(),
                                     "characters": len(text), "text": text})
            if not chapters:
                raise GateError("EPUB has no extractable chapter text")
    except (KeyError, BadZipFile) as exc:
        raise GateError("EPUB archive is invalid or incomplete") from exc
    return {"schema_version": 1, "source_id": source_id,
            "source_sha256": sha256(raw_epub).hexdigest(), "bytes": len(raw_epub),
            "title": title, "creator": creator, "language": language, "rights_notice": rights,
            "status": "QUARANTINED_RIGHTS_REVIEW", "training_approved": False,
            "broker_orders": False, "chapter_count": len(chapters), "chapters": chapters}


def stage_epub_private(epub: Path, *, source_id: str, private_quarantine: Path) -> dict:
    """Exclusive local staging. Does not grant rights, approve lessons or train ML."""
    audit = inspect_epub(epub, source_id=source_id)
    private_quarantine.mkdir(parents=True, exist_ok=True)
    manifest = private_quarantine / (source_id + "-" + audit["source_sha256"][:12] + ".manifest.json")
    corpus = private_quarantine / (source_id + "-" + audit["source_sha256"][:12] + ".chapters.jsonl")
    if manifest.exists() or corpus.exists():
        raise GateError("source already staged; immutable quarantine prevents overwrite")
    public_metadata = {k: v for k, v in audit.items() if k != "chapters"}
    public_metadata["chapters"] = [{k: v for k, v in c.items() if k != "text"} for c in audit["chapters"]]
    with corpus.open("x", encoding="utf-8") as out:
        for c in audit["chapters"]:
            out.write(json.dumps(c, ensure_ascii=False, sort_keys=True) + "\n")
    with manifest.open("x", encoding="utf-8") as out:
        json.dump(public_metadata, out, ensure_ascii=False, indent=2, sort_keys=True)
        out.write("\n")
    return public_metadata
