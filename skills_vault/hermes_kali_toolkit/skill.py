"""Hermes Kali: catalogo + docker exec allowlist. Niente playbook d'attacco."""
from __future__ import annotations

import hashlib
import json
import os
import re
import shlex
import time

try:
    from skills_vault.ebj_vps_ssh import (
        CONTAINER,
        TIMEOUT_S,
        VPS_HOST,
        resolve_ssh_key,
        ssh_run,
    )
except ImportError:
    import importlib.util
    _ssh_path = os.path.join(os.path.dirname(__file__), "..", "ebj_vps_ssh.py")
    _spec = importlib.util.spec_from_file_location("ebj_vps_ssh", os.path.normpath(_ssh_path))
    _ssh_mod = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_ssh_mod)
    CONTAINER = _ssh_mod.CONTAINER
    TIMEOUT_S = _ssh_mod.TIMEOUT_S
    VPS_HOST = _ssh_mod.VPS_HOST
    resolve_ssh_key = _ssh_mod.resolve_ssh_key
    ssh_run = _ssh_mod.ssh_run

READ_ONLY_BASH = {"uname", "which"}
_SHELL_META = re.compile(r"[;&|`$]")


def _catalog_paths():
    here = os.path.join(os.path.dirname(__file__), "tool-catalog.json")
    supreme = os.path.normpath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "..",
            "ebj-supreme",
            "kali",
            "tool-catalog.json",
        )
    )
    return supreme, here


def _resolve_binary(tool: str) -> str:
    t = str(tool or "").strip()
    for item in _catalog_local():
        name = str(item.get("name") or "").strip()
        binary = str(item.get("binary") or name).strip()
        if t in {name, binary} and binary:
            return binary
    return t


def _catalog_local() -> list:
    for p in _catalog_paths():
        if os.path.isfile(p):
            with open(p, encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                return data
    return []


def catalog_sha256() -> str:
    for p in _catalog_paths():
        if os.path.isfile(p):
            h = hashlib.sha256()
            with open(p, "rb") as f:
                h.update(f.read())
            return h.hexdigest()
    return ""


def allowlist() -> set[str]:
    names: set[str] = set()
    for item in _catalog_local():
        for key in ("name", "binary"):
            val = str(item.get(key) or "").strip()
            if val:
                names.add(val)
    names.update(READ_ONLY_BASH)
    names.add("cat")
    return names


def parse_kali_cli(rest: str) -> dict:
    """Traduce `/kali …` in params per execute()."""
    text = re.sub(r"^/kali\s*:?\s*", "", str(rest or ""), flags=re.IGNORECASE).strip()
    low = text.lower()
    if not text or low in ("tools", "list", "catalogo", "help"):
        return {"action": "list"}
    if low == "update":
        return {"action": "update"}
    try:
        parts = shlex.split(text)
    except ValueError:
        return {"action": "error", "message": "Argomenti non analizzabili."}
    if not parts:
        return {"action": "list"}
    if parts[0].lower() == "which" and len(parts) >= 2:
        return {"action": "which", "tool": parts[1]}
    return {"action": "run", "tool": parts[0], "args": parts[1:]}


def _ssh(remote: str, timeout: int = TIMEOUT_S):
    return ssh_run(remote, timeout=timeout)


def execute(params=None):
    params = params or {}
    action = str(params.get("action") or "list").lower()
    t0 = time.time()
    allowed = allowlist()

    if action == "error":
        return {
            "status": "ERROR",
            "message": params.get("message") or "Richiesta non valida.",
            "latency_ms": round((time.time() - t0) * 1000, 2),
        }

    if action == "list":
        return {
            "status": "SUCCESS",
            "catalog": _catalog_local(),
            "container": CONTAINER,
            "timeout_s": TIMEOUT_S,
            "catalog_sha256": catalog_sha256(),
            "ssh_key_ready": bool(resolve_ssh_key()),
            "latency_ms": round((time.time() - t0) * 1000, 2),
        }

    if action == "which":
        tool = str(params.get("tool") or "").strip()
        if tool not in allowed:
            return {"status": "ERROR", "message": f"Tool non in allowlist: {tool}"}
        r = _ssh(f"docker exec {CONTAINER} command -v {shlex.quote(tool)}")
        return {
            "status": "SUCCESS" if r.returncode == 0 else "ERROR",
            "stdout": (r.stdout or r.stderr or "").strip(),
            "exit_code": r.returncode,
            "latency_ms": round((time.time() - t0) * 1000, 2),
        }

    if action == "update":
        r = _ssh(f"docker exec {CONTAINER} /opt/ebj/update-tools.sh", timeout=600)
        return {
            "status": "SUCCESS" if r.returncode == 0 else "ERROR",
            "stdout": (r.stdout or r.stderr or "").strip(),
            "exit_code": r.returncode,
            "latency_ms": round((time.time() - t0) * 1000, 2),
        }

    if action == "run":
        tool = str(params.get("tool") or "").strip()
        args = params.get("args") or []
        if isinstance(args, str):
            args = shlex.split(args)
        if tool not in allowed:
            return {"status": "ERROR", "message": f"Tool non in allowlist: {tool}"}
        joined = " ".join(str(a) for a in args)
        if _SHELL_META.search(tool) or _SHELL_META.search(joined):
            return {"status": "ERROR", "message": "Caratteri shell rifiutati."}
        binary = _resolve_binary(tool)
        argv = [binary, *[str(a) for a in args]]
        if tool == "cat" or binary == "cat":
            if args != ["/opt/ebj/tool-catalog.json"]:
                return {
                    "status": "ERROR",
                    "message": "cat consentito solo su /opt/ebj/tool-catalog.json",
                }
        remote = "docker exec " + CONTAINER + " " + " ".join(shlex.quote(a) for a in argv)
        r = _ssh(remote)
        out = (r.stdout or "").strip()
        if r.stderr:
            out = (out + "\n" + r.stderr.strip()).strip()
        return {
            "status": "SUCCESS" if r.returncode == 0 else "ERROR",
            "tool": tool,
            "stdout": out or "(nessun output)",
            "exit_code": r.returncode,
            "timeout_s": TIMEOUT_S,
            "latency_ms": round((time.time() - t0) * 1000, 2),
        }

    return {"status": "ERROR", "message": "action deve essere list|run|which|update"}
