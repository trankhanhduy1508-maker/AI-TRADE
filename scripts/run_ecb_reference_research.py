"""Reproduce one frozen, internally scoped ECB research experiment offline.

The original official ECB rates must already be validated/staged privately.
No network, GPT dependency, database privilege, or broker execution path.
"""
from __future__ import annotations

import argparse
from hashlib import sha1, sha256
import json
import os
from pathlib import Path

from src.self_learning.pipeline import GateError
from src.self_learning.reference_model import build_reference_dataset, train_reference_candidate

MODEL_CODE_BLOB = '5e6fcd0eaf1fbd01e66cd7671379e5df03a4cdd7'
MODEL_CODE_COMMIT = '0a6e111c1bbfb68912d8b1e495a7d5c9e7ad9581'
OFFICIAL_OBSERVATIONS_SHA256 = 'cdc2ece1252e551dd84fc69a43fd4bce17a60e744e898f44abe914f11ea06474'
SOURCE_LOCAL_SHA256 = '45f866d1358d7b23fe5e4fafaffd661a83d4ced2f61380c5dbc7a9b89de076f8'
EXPECTED_DATASET_VERSION = 'ecb-dv1-a6ffe614dbd4715197d7'
EXPECTED_MODEL_VERSION = 'ecb-mc1-ad0855fea6fb17fd7e62'
REPO_ROOT = Path(__file__).resolve().parents[1]


def _git_blob_sha(data: bytes) -> str:
    return sha1(b'blob ' + str(len(data)).encode('ascii') + b'\0' + data).hexdigest()


def _locked_output_dir(path: Path) -> Path:
    requested = path.absolute()
    if requested != requested.resolve():
        raise GateError('private output path must not contain a symlink')
    out = requested.resolve()
    if out == REPO_ROOT or out.is_relative_to(REPO_ROOT):
        raise GateError('never write private model artifacts inside the repository')
    out.mkdir(parents=True, exist_ok=True, mode=0o700)
    out.chmod(0o700)
    return out


def _private_write(path: Path, data: dict) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0)
    try:
        fd = os.open(path, flags, 0o600)
    except FileExistsError as exc:
        raise GateError('immutable experiment output exists; no overwrite') from exc
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            json.dump(data, stream, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)
            stream.write('\n')
    except Exception:
        path.unlink(missing_ok=True)
        raise


def reproduce(snapshot: Path, private_output: Path) -> dict:
    script = REPO_ROOT / 'src/self_learning/reference_model.py'
    if _git_blob_sha(script.read_bytes()) != MODEL_CODE_BLOB:
        raise GateError('model source no longer matches the preregistered Git blob')
    raw_bytes = snapshot.read_bytes()
    if sha256(raw_bytes).hexdigest() != SOURCE_LOCAL_SHA256:
        raise GateError('original privately staged snapshot bytes differ from independently verified source')
    payload = json.loads(raw_bytes)
    if payload.get('series') != 'EXR.D.USD.EUR.SP00.A' or payload.get('attribution') != 'Source: ECB statistics.':
        raise GateError('unverified official series or missing source attribution')
    observations = payload.get('observations')
    if not isinstance(observations, list):
        raise GateError('missing original official observations')
    canonical = json.dumps(observations, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode('utf-8')
    if sha256(canonical).hexdigest() != OFFICIAL_OBSERVATIONS_SHA256:
        raise GateError('original official observations differ from the frozen independent source hash')
    dataset = build_reference_dataset(observations)
    if dataset['dataset_version'] != EXPECTED_DATASET_VERSION:
        raise GateError('normalized dataset version mismatch')
    artifact = train_reference_candidate(dataset, code_sha=MODEL_CODE_COMMIT)
    if artifact['model_version'] != EXPECTED_MODEL_VERSION or artifact['status'] != 'REJECTED':
        raise GateError('model/evaluation differs from frozen reference experiment')
    if artifact['public_inference'] or artifact['broker_orders'] or not artifact['live_money_locked']:
        raise GateError('research runner must never grant a trading permission')
    output = _locked_output_dir(private_output)
    record = {'source_sha256': SOURCE_LOCAL_SHA256,
              'official_observations_sha256': OFFICIAL_OBSERVATIONS_SHA256,
              'model_source_git_blob': MODEL_CODE_BLOB,
              'model_code_commit': MODEL_CODE_COMMIT,
              'dataset_version': dataset['dataset_version'],
              'model_version': artifact['model_version'],
              'status': artifact['status'], 'rights_scope': 'INTERNAL_RESEARCH_ONLY',
              'public_inference': False, 'broker_orders': False, 'live_money_locked': True,
              'model_artifact': artifact}
    _private_write(output / 'ecb_reference_v1_immutable_reproduction.json', record)
    return {k: v for k, v in record.items() if k != 'model_artifact'}


def main() -> None:
    parser = argparse.ArgumentParser(description='Offline, pinned, private ECB model reproduction; no broker integration')
    parser.add_argument('--snapshot', type=Path, required=True)
    parser.add_argument('--private-output', type=Path, required=True)
    options = parser.parse_args()
    print(json.dumps(reproduce(options.snapshot, options.private_output), ensure_ascii=False, sort_keys=True))


if __name__ == '__main__':
    main()
