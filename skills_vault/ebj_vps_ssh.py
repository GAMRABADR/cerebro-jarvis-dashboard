"""Resolver unico chiave SSH VPS Oracle + timeout Kali.

Ordine: env EBJ_VPS_SSH_KEY, poi controllo/keys/vps_ssh_key.key, poi fallback Downloads.
Non stampa il contenuto della chiave.
"""
from __future__ import annotations

import os
import subprocess

TIMEOUT_S = int(os.environ.get("EBJ_KALI_TIMEOUT", "120"))
CONTAINER = "ebj-kali-engine"
VPS_HOST = os.environ.get("EBJ_VPS_HOST", "ubuntu@92.4.233.42")

_SKILLS_DIR = os.path.dirname(os.path.abspath(__file__))
_DASHBOARD_DIR = os.path.dirname(_SKILLS_DIR)
_REPO_ROOT = os.path.dirname(_DASHBOARD_DIR)

_KEY_CANDIDATES = (
    os.environ.get("EBJ_VPS_SSH_KEY") or "",
    os.path.join(_REPO_ROOT, "controllo", "keys", "vps_ssh_key.key"),
    r"C:\Users\Admin\Downloads\ssh-key-2026-08-18.key",
)


def resolve_ssh_key() -> str | None:
    for p in _KEY_CANDIDATES:
        if p and os.path.isfile(p):
            return p
    return None


def ssh_run(remote: str, timeout: int | None = None) -> subprocess.CompletedProcess:
    key = resolve_ssh_key()
    cmd = ["ssh"]
    if key:
        cmd += ["-i", key]
    cmd += [
        "-o", "StrictHostKeyChecking=no",
        "-o", "ConnectTimeout=8",
        VPS_HOST,
        remote,
    ]
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout if timeout is not None else TIMEOUT_S,
    )
