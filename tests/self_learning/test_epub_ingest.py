"""EPUB fixtures are invented for input validation, never training evidence."""
import json
from pathlib import Path
from zipfile import ZipFile, ZIP_STORED
import pytest
from src.self_learning.epub_ingest import inspect_epub, stage_epub_private
from src.self_learning.pipeline import GateError

CONTAINER=b'''<?xml version="1.0"?><container xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="EPUB/content.opf" media-type="application/oebps-package+xml"/></rootfiles></container>'''
OPF=b'''<package xmlns="http://www.idpf.org/2007/opf" xmlns:dc="http://purl.org/dc/elements/1.1/"><metadata><dc:title>Test book</dc:title><dc:creator>CWS</dc:creator><dc:language>vi</dc:language></metadata><manifest><item id="ch1" href="text/ch001.xhtml" media-type="application/xhtml+xml" /></manifest><spine><itemref idref="ch1"/></spine></package>'''
CHAPTER=b'''<html xmlns="http://www.w3.org/1999/xhtml"><body><h1>Learning</h1><p>Research ideas require actual market evidence.</p></body></html>'''

def fixture(tmp_path: Path, *, opf=OPF, chapter=CHAPTER, order=True):
    p=tmp_path/'book.epub'
    with ZipFile(p,'w') as z:
        if order:
            z.writestr('mimetype',b'application/epub+zip',compress_type=ZIP_STORED)
        z.writestr('META-INF/container.xml',CONTAINER)
        z.writestr('EPUB/content.opf',opf)
        z.writestr('EPUB/text/ch001.xhtml',chapter)
        if not order:
            z.writestr('mimetype',b'application/epub+zip',compress_type=ZIP_STORED)
    return p

def test_stage_metadata_only_and_immutable(tmp_path):
    p=fixture(tmp_path)
    result=stage_epub_private(p,source_id='unit_masterbook',private_quarantine=tmp_path/'private')
    assert result['status']=='QUARANTINED_RIGHTS_REVIEW'
    assert result['training_approved'] is False and result['broker_orders'] is False
    assert result['chapter_count']==1 and 'text' not in result['chapters'][0]
    manifest=json.loads(next((tmp_path/'private').glob('*.manifest.json')).read_text())
    assert 'Research ideas' not in json.dumps(manifest)
    assert 'Research ideas' in next((tmp_path/'private').glob('*.chapters.jsonl')).read_text()
    with pytest.raises(GateError,match='already staged'):
        stage_epub_private(p,source_id='unit_masterbook',private_quarantine=tmp_path/'private')

@pytest.mark.parametrize('bad', ['mimetype','traversal','missing','dtd','replacement'])
def test_fail_closed_epub(tmp_path,bad):
    if bad=='mimetype':
        p=fixture(tmp_path,order=False)
    elif bad=='traversal':
        p=fixture(tmp_path,opf=OPF.replace(b'text/ch001.xhtml',b'../../../outside.xhtml'))
    elif bad=='missing':
        p=fixture(tmp_path,opf=OPF.replace(b'idref="ch1"',b'idref="other"'))
    elif bad=='dtd':
        p=fixture(tmp_path,chapter=b'<!DOCTYPE html [<!ENTITY xx "invalid">]>'+CHAPTER)
    else:
        p=fixture(tmp_path,chapter=CHAPTER.replace(b'Learning',b'\xef\xbf\xbd'))
    with pytest.raises(GateError): inspect_epub(p,source_id='unit_masterbook')


def test_benign_html_doctype_is_supported(tmp_path):
    harmless = b'<?xml version="1.0"?>\n<!DOCTYPE html>\n' + CHAPTER
    p=fixture(tmp_path,chapter=harmless)
    result=inspect_epub(p,source_id='test_book')
    assert result['chapter_count']==1
