"""Security-only fixtures. Never call invented observations market data."""
import json
from pathlib import Path

import pytest
from src.self_learning.pipeline import GateError
from scripts.run_ecb_reference_research import reproduce, _git_blob_sha, _locked_output_dir, MODEL_CODE_BLOB, REPO_ROOT


def test_model_code_blob_pinned():
    source = (REPO_ROOT / 'src/self_learning/reference_model.py').read_bytes()
    assert _git_blob_sha(source) == MODEL_CODE_BLOB


def test_reject_public_repository_artifact_location():
    with pytest.raises(GateError, match='repository'):
        _locked_output_dir(REPO_ROOT / 'public_artifacts')


def test_reject_unverified_source_before_any_output(tmp_path):
    source = tmp_path / 'unverified.json'
    source.write_text(json.dumps({'series': 'EXR.D.USD.EUR.SP00.A', 'observations': []}))
    output = tmp_path / 'private'
    with pytest.raises(GateError, match='snapshot bytes'):
        reproduce(source, output)
    assert not output.exists()


def test_reject_private_output_symlink(tmp_path):
    safe = tmp_path / 'safe'
    safe.mkdir()
    link = tmp_path / 'redirect'
    try:
        link.symlink_to(safe, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip('filesystem symlinks unavailable')
    with pytest.raises(GateError, match='symlink'):
        _locked_output_dir(link)
