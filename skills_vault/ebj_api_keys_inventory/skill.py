"""Inventario NOMI credenziali. Mai valori, mai log di secret."""
from __future__ import annotations

import os
import re
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
_DASHBOARD = os.path.dirname(os.path.dirname(_HERE))
_REPO_ROOT = os.path.dirname(_DASHBOARD)

_NAME_TOKEN = r"[A-Z][A-Z0-9_]{2,80}"
_CRED_HINT = re.compile(
    r"(?:API[_-]?KEY|ACCESS[_-]?KEY|SECRET|TOKEN|PASSWORD|PASSWD|CREDENTIAL|"
    r"ENCRYPTION[_-]?KEY|AUTH[_-]?TOKEN|PRIVATE[_-]?KEY|_PASS$|_TOKEN$)",
    re.I,
)
_CRED_ALIASES = {
    "GEMINI_KEY",
    "GROQ_KEY",
    "FISH_AUDIO_KEY",
    "NVIDIA_KEY",
    "OPENROUTER_KEY",
    "ELEVEN_KEY",
    "INDEXNOW_KEY",
    "AGENT0_KEY",
    "EBJ_VPS_SSH_KEY",
    "SECRET_KEY",
    "FLASK_SECRET_KEY",
}
_ENV_LINE = re.compile(rf"^\s*(?:export\s+)?({_NAME_TOKEN})\s*=")
_COMPOSE_KV = re.compile(rf"^\s*-\s*({_NAME_TOKEN})\s*=")
_COMPOSE_MAP = re.compile(rf"^\s*({_NAME_TOKEN})\s*:")
_ENV_GET = re.compile(
    rf"""(?:os\.environ(?:\.get|\[[\"']|)|os\.getenv\(|getenv\()\s*[\"']({_NAME_TOKEN})[\"']"""
)
_PY_ASSIGN = re.compile(rf"^\s*({_NAME_TOKEN})\s*=\s*([\"'])")
_SECRETS_GET = re.compile(
    r"""SECRETS(?:\.get)?\(\s*[\"']([a-zA-Z0-9_]+)[\"']"""
)
_INTERPOL = re.compile(r"\$\{[A-Z0-9_]+")

_PLACEHOLDER = re.compile(
    r"(?i)^(cambia|your[-_]|inserisci|todo|xxx+|example|placeholder|changeme|"
    r"change[-_ ]?this|set\s|<|none$|null$|n/?a$)"
)

_SKIP_DIRS = {
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    "dist",
    "build",
    ".next",
    "Binaries",
    "Intermediate",
    "Saved",
    "DerivedData",
}
_SKIP_FILES = {".env", "secrets.json"}
_SKIP_EXT = {".key", ".pem", ".p12", ".pfx", ".der", ".sqlite", ".db", ".exe", ".dll"}
_TEXT_EXT = {
    ".py",
    ".md",
    ".json",
    ".yml",
    ".yaml",
    ".example",
    ".env.example",
    ".txt",
    ".ini",
    ".toml",
    ".cfg",
    ".sh",
    ".ps1",
}

_GROUP_ORDER = ("AI", "cloud/infra", "messaging", "payments", "other")

_AI = (
    "GROQ",
    "GEMINI",
    "OPENAI",
    "OPENROUTER",
    "HUGGINGFACE",
    "HF_",
    "DASHSCOPE",
    "QWEN",
    "ANTHROPIC",
    "CLAUDE",
    "XAI",
    "NVIDIA",
    "ELEVEN",
    "FISH",
    "CHUTES",
    "MODELSCOPE",
    "GOOGLE_API",
    "API_KEY_GOOGLE",
    "API_KEY_GEMINI",
    "API_KEY_OPENROUTER",
    "API_KEY_GROQ",
    "API_KEY_HUGGINGFACE",
    "API_KEY_XAI",
    "API_KEY_CURSOR",
)
_CLOUD = (
    "POSTGRES",
    "N8N",
    "SSH",
    "VPS",
    "ORACLE",
    "HETZNER",
    "AWS",
    "DOCKER",
    "CLOUDFLARE",
    "TURSO",
    "DATABASE",
    "BLOB",
    "GITHUB",
    "STEAM",
    "NEXTAUTH",
    "SECRET_KEY",
    "ENCRYPTION",
    "RFC_PASSWORD",
    "A0_SET",
    "AGENT0",
    "OCI_",
)
_MSG = (
    "TELEGRAM",
    "WHATSAPP",
    "GMAIL",
    "SMTP",
    "DISCORD",
    "FACEBOOK",
    "MAIL",
    "EMAIL",
    "SLACK",
)
_PAY = (
    "STRIPE",
    "SATISPAY",
    "PAYPAL",
    "SUMUP",
    "FATTURE",
    "IBAN",
    "PAYMENT",
    "CHECKOUT",
)


def _is_cred_name(name: str) -> bool:
    u = (name or "").upper()
    if not u or u in ("PORT", "HOST", "DEBUG", "PATH", "HOME", "USER"):
        return False
    if u in _CRED_ALIASES:
        return True
    return bool(_CRED_HINT.search(u))


def _group_for(name: str) -> str:
    u = name.upper()
    for p in _AI:
        if u.startswith(p) or p in u:
            return "AI"
    for p in _PAY:
        if p in u:
            return "payments"
    for p in _MSG:
        if p in u:
            return "messaging"
    for p in _CLOUD:
        if p in u:
            return "cloud/infra"
    return "other"


def _rel(root: str, path: str) -> str:
    try:
        return os.path.relpath(path, root).replace("\\", "/")
    except ValueError:
        return path.replace("\\", "/")


def _looks_hardcoded_rhs(rhs: str) -> bool:
    raw = (rhs or "").strip().strip("\"'").strip()
    if not raw or raw in ("None", "null", "''", '""'):
        return False
    if _INTERPOL.search(raw):
        return False
    if _PLACEHOLDER.match(raw):
        return False
    if raw.lower() in ("true", "false", "0", "1"):
        return False
    if raw.startswith("http://") or raw.startswith("https://"):
        return False
    if len(raw) < 8:
        return False
    return True


def _record(bucket: dict, name: str, path: str, hardcoded: bool) -> None:
    key = name.strip()
    if not key or not _is_cred_name(key):
        return
    ent = bucket.setdefault(
        key,
        {"name": key, "group": _group_for(key), "sources": [], "hardcoded": False},
    )
    if path and path not in ent["sources"]:
        ent["sources"].append(path)
    if hardcoded:
        ent["hardcoded"] = True


def _scan_text(bucket: dict, rel: str, text: str, kind: str) -> None:
    for i, line in enumerate(text.splitlines(), 1):
        loc = f"{rel}:{i}"
        stripped = line.strip()
        if stripped.startswith("#"):
            continue

        if kind in ("env", "compose"):
            m = _ENV_LINE.match(line) or _COMPOSE_KV.match(line)
            if m:
                name = m.group(1)
                rhs = line.split("=", 1)[1] if "=" in line else ""
                _record(bucket, name, loc, _looks_hardcoded_rhs(rhs))
                continue
            if kind == "compose":
                m2 = _COMPOSE_MAP.match(line)
                if m2 and _is_cred_name(m2.group(1)):
                    rhs = line.split(":", 1)[1] if ":" in line else ""
                    _record(bucket, m2.group(1), loc, _looks_hardcoded_rhs(rhs))

        for m in _ENV_GET.finditer(line):
            name = m.group(1)
            default_hard = False
            # os.environ.get("X", "literal") — default non vuoto = HARDCODED
            get_def = re.search(
                rf"""[\"']{re.escape(name)}[\"']\s*,\s*([\"'])(.*?)(\1)""",
                line,
            )
            if get_def:
                default_hard = _looks_hardcoded_rhs(get_def.group(2))
            _record(bucket, name, loc, default_hard)

        m_as = _PY_ASSIGN.match(line)
        if m_as and _is_cred_name(m_as.group(1)):
            quote = m_as.group(2)
            rest = line.split("=", 1)[1].strip()
            if rest.startswith(quote):
                _record(bucket, m_as.group(1), loc, _looks_hardcoded_rhs(rest))

        for m in _SECRETS_GET.finditer(line):
            _record(bucket, m.group(1).upper(), loc, False)


def _iter_targets(root: str, max_files: int):
    count = 0
    rel_globs = []

    def add(path: str, kind: str):
        nonlocal count
        if count >= max_files:
            return
        if os.path.isfile(path):
            rel_globs.append((path, kind))
            count += 1

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS and not d.startswith(".")]
        base = os.path.basename(dirpath).lower()
        for fn in filenames:
            full = os.path.join(dirpath, fn)
            low = fn.lower()
            ext = os.path.splitext(fn)[1].lower()
            if low in _SKIP_FILES or ext in _SKIP_EXT:
                continue
            kind = None
            if low in ("env.example", ".env.example") or low.endswith(".env.example"):
                kind = "env"
            elif "compose" in low and ext in (".yml", ".yaml"):
                kind = "compose"
            elif fn == "server.py" and "cerebro-jarvis-dashboard" in full.replace("\\", "/"):
                kind = "py"
            elif ext == ".py" and (
                "skills_vault" in full.replace("\\", "/")
                or ".agents" + os.sep + "skills" in full
                or os.sep + "Agente-0" + os.sep in full
                or "/Agente-0/" in full.replace("\\", "/")
            ):
                kind = "py"
            elif ext in (".yml", ".yaml") and (
                os.sep + "Agente-0" + os.sep in full or "/Agente-0/" in full.replace("\\", "/")
            ):
                kind = "compose"
            if kind:
                add(full, kind)
            if count >= max_files:
                return rel_globs
        if count >= max_files:
            break
    return rel_globs


def execute(params=None):
    params = params or {}
    t0 = time.time()
    root = os.path.abspath(params.get("root") or _REPO_ROOT)
    max_files = int(params.get("max_files") or 2500)
    bucket: dict = {}
    scanned = 0
    errors = 0

    for path, kind in _iter_targets(root, max_files):
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                text = fh.read(2_000_000)
        except OSError:
            errors += 1
            continue
        scanned += 1
        _scan_text(bucket, _rel(root, path), text, kind)

    groups = {g: [] for g in _GROUP_ORDER}
    hardcoded = []
    for name in sorted(bucket):
        ent = bucket[name]
        item = {
            "name": ent["name"],
            "sources": ent["sources"][:12],
            "status": "HARDCODED" if ent["hardcoded"] else "ENV",
        }
        if ent["hardcoded"]:
            item["flag"] = "HARDCODED"
            hardcoded.append({"name": name, "paths": ent["sources"][:8]})
        groups[ent["group"]].append(item)

    return {
        "status": "SUCCESS",
        "rule": "NAMES_ONLY_NEVER_VALUES",
        "groups": groups,
        "hardcoded_count": len(hardcoded),
        "hardcoded": hardcoded,
        "scanned_files": scanned,
        "errors": errors,
        "latency_ms": round((time.time() - t0) * 1000, 2),
    }


if __name__ == "__main__":
    import json

    out = execute()
    # Serializza senza alcun campo valore.
    print(json.dumps(out, indent=2, ensure_ascii=False))
