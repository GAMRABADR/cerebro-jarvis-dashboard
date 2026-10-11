"""Hermes Kali: catalogo + docker exec allowlist. Niente playbook d'attacco.

POLICY OPERATIVA (vincolante)
-----------------------------
Questa skill e' uno strumento da OPERATORE difensivo: inventario tool, verifica
presenza binari, lettura di `--help`/`--version`, audit sull'infrastruttura di
proprieta'. Non contiene ne' genera catene d'attacco, payload o exploit.

Perimetro autorizzato (soli host di proprieta' dell'operatore):
  - badrexpress.com  (ed eb.badrexpress.com)
  - pietrotraslochi.com
  - tinoshop.it
  - 127.0.0.1 / localhost e reti private RFC1918
  - VPS Oracle 92.4.233.42

Un target IPv4/CIDR o dominio pubblico fuori da questo perimetro viene
rifiutato (`REJECTED_TARGET_OUT_OF_SCOPE`). `--help` e `--version` restano
sempre consentiti perche' non contengono alcun target.
"""
from __future__ import annotations

import hashlib
import ipaddress
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

# Host di proprieta' dell'operatore: vedi POLICY nel docstring del modulo.
OPERATOR_HOSTS = {
    "badrexpress.com",
    "pietrotraslochi.com",
    "tinoshop.it",
    "localhost",
    "127.0.0.1",
    "92.4.233.42",
}
# Categorie del catalogo che accettano un target di rete: solo qui applichiamo
# il controllo di perimetro. Reverse/forensics/mobile lavorano su file locali.
_NET_CATEGORIES = {"recon", "vuln", "rete", "web", "password", "wireless", "identity"}

_IPV4 = re.compile(r"^\d{1,3}(?:\.\d{1,3}){3}(?:/\d{1,2})?$")
_HOSTNAME = re.compile(r"^(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z]{2,24}\.?$", re.IGNORECASE)
_SAFE_FLAGS = {"--help", "-h", "--version", "-V", "-v", "--usage"}


def _state_path() -> str:
    """File di stato ultima esecuzione (solo nome tool + exit, mai argomenti)."""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "last-exec.json")


def _write_last_exec(tool: str, exit_code, status: str, action: str = "run") -> None:
    try:
        with open(_state_path(), "w", encoding="utf-8") as f:
            json.dump(
                {
                    "tool": str(tool or "")[:80],
                    "exit_code": exit_code,
                    "status": status,
                    "action": action,
                    "ts_unix": int(time.time()),
                    "container": CONTAINER,
                },
                f,
                ensure_ascii=False,
            )
    except Exception:
        pass


def read_last_exec() -> dict:
    try:
        p = _state_path()
        if os.path.isfile(p):
            with open(p, encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                return data
    except Exception:
        pass
    return {}


def _tool_category(tool: str) -> str:
    t = str(tool or "").strip()
    for item in _catalog_local():
        name = str(item.get("name") or "").strip()
        binary = str(item.get("binary") or name).strip()
        if t in {name, binary}:
            return str(item.get("category") or "")
    return ""


def _host_in_scope(host: str) -> bool:
    h = str(host or "").strip().rstrip(".").lower()
    if not h:
        return False
    if h in OPERATOR_HOSTS:
        return True
    return any(h.endswith("." + d) for d in OPERATOR_HOSTS if not _IPV4.match(d))


def _ip_out_of_scope(token: str) -> bool:
    """True se il token e' un IPv4/CIDR pubblico fuori perimetro operatore."""
    try:
        net = ipaddress.ip_network(token, strict=False)
    except ValueError:
        return False
    if net.is_private or net.is_loopback or net.is_link_local or net.is_multicast:
        return False
    if net.num_addresses == 1 and _host_in_scope(str(net.network_address)):
        return False
    return True


def check_target_scope(tool: str, args) -> str | None:
    """Ritorna un messaggio in italiano se il target e' fuori perimetro, altrimenti None."""
    if _tool_category(tool) not in _NET_CATEGORIES:
        return None
    for raw in args or []:
        token = str(raw).strip()
        if not token or token.startswith("-") or token in _SAFE_FLAGS:
            continue
        bare = token.split("://", 1)[-1].split("/", 1)[0].split("@")[-1].split(":")[0]
        if _IPV4.match(token) or _IPV4.match(bare):
            if _ip_out_of_scope(token) or _ip_out_of_scope(bare):
                return (
                    f"REJECTED_TARGET_OUT_OF_SCOPE: «{token}» e' un indirizzo pubblico "
                    "fuori dal perimetro autorizzato. Consentiti solo gli host di "
                    "proprieta' (badrexpress.com, pietrotraslochi.com, tinoshop.it, "
                    "VPS Oracle, 127.0.0.1 e reti private). `--help` e `--version` "
                    "restano sempre disponibili."
                )
            continue
        if _HOSTNAME.match(bare) and not _host_in_scope(bare):
            return (
                f"REJECTED_TARGET_OUT_OF_SCOPE: il dominio «{bare}» non e' tra gli host "
                "di proprieta'. Usa badrexpress.com, pietrotraslochi.com, tinoshop.it, "
                "la VPS Oracle o 127.0.0.1."
            )
    return None


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
    if low in ("status", "stato", "diagnostica"):
        return {"action": "status"}
    try:
        parts = shlex.split(text)
    except ValueError:
        return {
            "action": "error",
            "message": "Argomenti non analizzabili: controlla apici e virgolette.",
        }
    if not parts:
        return {"action": "list"}
    if parts[0].lower() in ("which", "dove", "percorso"):
        if len(parts) >= 2:
            return {"action": "which", "tool": parts[1]}
        return {
            "action": "error",
            "message": "Sintassi: `/kali which <tool>` (es. `/kali which nmap`).",
        }
    args = parts[1:]
    if not args:
        args = ["--help"]
    return {"action": "run", "tool": parts[0], "args": args}


def parse_user_kali(prompt: str) -> dict | None:
    """Riconosce /kali, «ebj lancia nmap …» o un binario del catalogo come prima parola."""
    raw = str(prompt or "").strip()
    if not raw:
        return None
    low = raw.lower()
    if low.startswith("/kali"):
        return parse_kali_cli(raw)
    m = re.match(
        r"^(?:ebj|e\.b\.j\.|hermes|jarvis)\s+(?:lancia|esegui|run|avvia|:)\s+(.+)$",
        raw,
        flags=re.IGNORECASE,
    )
    if m:
        return parse_kali_cli(m.group(1))
    m2 = re.match(r"^(?:lancia|esegui|avvia)\s+(\S+)(.*)$", raw, flags=re.IGNORECASE)
    if m2:
        return parse_kali_cli((m2.group(1) + " " + m2.group(2)).strip())
    try:
        parts = shlex.split(raw)
    except ValueError:
        return None
    if not parts:
        return None
    allowed = allowlist()
    if parts[0] in allowed or parts[0].lower() in {x.lower() for x in allowed}:
        real = parts[0]
        for name in allowed:
            if name.lower() == parts[0].lower():
                real = name
                break
        args = parts[1:] or ["--help"]
        return {"action": "run", "tool": real, "args": args}
    return None


def _notify_n8n_kali(tool: str, exit_code, status: str):
    """Evento n8n: solo nome tool ed exit, niente payload d'attacco."""
    try:
        import requests
        payload = {
            "event": "KALI_EXEC",
            "tool": str(tool or "")[:80],
            "exit_code": exit_code,
            "status": status,
        }
        for url in (
            "http://127.0.0.1:5678/webhook/kali-exec",
            "http://92.4.233.42:5678/webhook/kali-exec",
        ):
            try:
                requests.post(url, json=payload, timeout=1.5)
                break
            except Exception:
                continue
    except Exception:
        pass


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
        if not tool:
            return {
                "status": "ERROR",
                "message": "Specifica il tool da cercare, es. `/kali which nmap`.",
                "latency_ms": round((time.time() - t0) * 1000, 2),
            }
        if tool not in allowed:
            return {
                "status": "ERROR",
                "message": f"Tool non in allowlist: {tool}",
                "latency_ms": round((time.time() - t0) * 1000, 2),
            }
        # `command -v` e' una builtin di shell: `docker exec <c> command -v x`
        # cercherebbe un eseguibile chiamato "command" e fallisce sempre. Usiamo
        # argv esplicito con il binario reale `which` risolto dal catalogo.
        binary = _resolve_binary(tool)
        argv = ["which", "--", binary]
        remote = "docker exec " + CONTAINER + " " + " ".join(shlex.quote(a) for a in argv)
        r = _ssh(remote)
        path = (r.stdout or "").strip().splitlines()
        path = path[0].strip() if path else ""
        found = r.returncode == 0 and bool(path)
        _write_last_exec(tool, r.returncode, "SUCCESS" if found else "ERROR", action="which")
        return {
            "status": "SUCCESS" if found else "ERROR",
            "tool": tool,
            "binary": binary,
            "path": path,
            "found": found,
            "stdout": path
            or (r.stderr or "").strip()
            or f"Binario «{binary}» non presente nel container {CONTAINER}.",
            "message": (
                f"«{binary}» disponibile in {path}."
                if found
                else f"«{binary}» non installato in {CONTAINER}: usa l'azione update."
            ),
            "exit_code": r.returncode,
            "latency_ms": round((time.time() - t0) * 1000, 2),
        }

    if action == "status":
        cat = _catalog_local()
        by_cat: dict[str, int] = {}
        for item in cat:
            key = str(item.get("category") or "n/d")
            by_cat[key] = by_cat.get(key, 0) + 1
        return {
            "status": "SUCCESS",
            "container": CONTAINER,
            "vps_host": VPS_HOST,
            "catalog_count": len(cat),
            "categories": dict(sorted(by_cat.items())),
            "catalog_sha256": catalog_sha256(),
            "ssh_key_ready": bool(resolve_ssh_key()),
            "timeout_s": TIMEOUT_S,
            "last_exec": read_last_exec(),
            "latency_ms": round((time.time() - t0) * 1000, 2),
        }

    if action == "update":
        r = _ssh(f"docker exec {CONTAINER} /opt/ebj/update-tools.sh", timeout=600)
        st = "SUCCESS" if r.returncode == 0 else "ERROR"
        _write_last_exec("update-tools.sh", r.returncode, st, action="update")
        return {
            "status": st,
            "stdout": (r.stdout or r.stderr or "").strip()
            or "Aggiornamento tool completato senza output.",
            "exit_code": r.returncode,
            "latency_ms": round((time.time() - t0) * 1000, 2),
        }

    if action == "run":
        tool = str(params.get("tool") or "").strip()
        args = params.get("args") or []
        if isinstance(args, str):
            args = shlex.split(args)
        if not args:
            args = ["--help"]
        if tool not in allowed:
            return {
                "status": "ERROR",
                "message": f"Tool non in allowlist: {tool}",
                "latency_ms": round((time.time() - t0) * 1000, 2),
            }
        joined = " ".join(str(a) for a in args)
        if _SHELL_META.search(tool) or _SHELL_META.search(joined):
            return {
                "status": "ERROR",
                "message": "Caratteri shell rifiutati (; & | ` $).",
                "latency_ms": round((time.time() - t0) * 1000, 2),
            }
        scope_err = check_target_scope(tool, args)
        if scope_err:
            return {
                "status": "ERROR",
                "tool": tool,
                "message": scope_err,
                "stdout": scope_err,
                "exit_code": 126,
                "latency_ms": round((time.time() - t0) * 1000, 2),
            }
        binary = _resolve_binary(tool)
        argv = [binary, *[str(a) for a in args]]
        if tool == "cat" or binary == "cat":
            if args != ["/opt/ebj/tool-catalog.json"]:
                return {
                    "status": "ERROR",
                    "message": "cat consentito solo su /opt/ebj/tool-catalog.json",
                    "latency_ms": round((time.time() - t0) * 1000, 2),
                }
        remote = "docker exec " + CONTAINER + " " + " ".join(shlex.quote(a) for a in argv)
        r = _ssh(remote)
        out = (r.stdout or "").strip()
        if r.stderr:
            out = (out + "\n" + r.stderr.strip()).strip()
        status = "SUCCESS" if r.returncode == 0 else "ERROR"
        _notify_n8n_kali(tool, r.returncode, status)
        _write_last_exec(tool, r.returncode, status, action="run")
        return {
            "status": status,
            "tool": tool,
            "stdout": out or "(nessun output)",
            "exit_code": r.returncode,
            "timeout_s": TIMEOUT_S,
            "latency_ms": round((time.time() - t0) * 1000, 2),
        }

    if act in ("pipeline", "autonomous_pipeline", "autonomous_audit"):
        try:
            from skills_vault.hermes_kali_toolkit.hermes_autonomous_pipeline import run_hermes_autonomous_audit
            tgt = str(payload.get("target") or "127.0.0.1").strip()
            quick = bool(payload.get("quick", True))
            return run_hermes_autonomous_audit(target=tgt, quick_mode=quick)
        except Exception as pe:
            return {
                "status": "ERROR",
                "message": f"Errore pipeline autonoma Hermes: {pe}",
                "latency_ms": round((time.time() - t0) * 1000, 2),
            }

    return {
        "status": "ERROR",
        "message": "action deve essere list|status|run|which|update|pipeline",
        "latency_ms": round((time.time() - t0) * 1000, 2),
    }
