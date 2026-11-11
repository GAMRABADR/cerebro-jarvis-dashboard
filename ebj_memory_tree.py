# -*- coding: utf-8 -*-
"""
==============================================================================
🌳 E.B.J. HIERARCHICAL MEMORY TREE & 20-MIN AUTO-INGEST BRIDGE
==============================================================================
Ponte ad altissima velocità tra Python e il motore nativo Rust `ebj-memory-tree`.
Compila e mantiene aggiornato un albero gerarchico in Markdown compatibile con
Obsidian (`memory_tree/`) unificando ogni 20 minuti:
  - Email (`mail_vault.db -> emails`)
  - Lead Verificati (`mail_vault.db -> verified_leads_2026`)
  - Turni Conversazionali (`mail_vault.db -> chat_session_history`)
  - Memoria LTM & Dossier Identità (`hermes_ltm_memory.db`)
==============================================================================
"""

from __future__ import annotations

import os
import sys
import json
import time
import sqlite3
import subprocess
import threading
from typing import Dict, Any, List, Optional

DIR = os.path.dirname(os.path.abspath(__file__))
MEMORY_TREE_DIR = os.path.join(DIR, "memory_tree")
VAULT_DB = os.path.join(DIR, "mail_vault.db")
LTM_DB = os.path.join(DIR, "hermes_ltm_memory.db")

_BIN_NAME = "ebj-memory-tree.exe" if sys.platform == "win32" else "ebj-memory-tree"
_CANDIDATE_BINS = [
    os.path.abspath(os.path.join(DIR, "..", "ebj-supreme", "rust-agents", "target", "release", _BIN_NAME)),
    os.path.join(DIR, "bin", _BIN_NAME),
    os.path.join(DIR, _BIN_NAME),
]

RUST_TREE_BIN: Optional[str] = next((p for p in _CANDIDATE_BINS if os.path.isfile(p)), None)

_SCHEDULER_STARTED = False


class _MemoryTreeDaemon:
    """Worker persistente in Rust (--daemon) per query < 0.2ms e zero overhead CreateProcess."""

    def __init__(self):
        self._proc: Optional[subprocess.Popen] = None
        self._lock = threading.Lock()

    def _bin(self) -> Optional[str]:
        global RUST_TREE_BIN
        if RUST_TREE_BIN and os.path.isfile(RUST_TREE_BIN):
            return RUST_TREE_BIN
        for p in _CANDIDATE_BINS:
            if os.path.isfile(p):
                RUST_TREE_BIN = p
                return p
        return None

    def _ensure(self) -> Optional[subprocess.Popen]:
        b = self._bin()
        if not b:
            return None
        if self._proc is not None and self._proc.poll() is None:
            return self._proc
        try:
            os.makedirs(MEMORY_TREE_DIR, exist_ok=True)
            self._proc = subprocess.Popen(
                [b, "--vault-dir", MEMORY_TREE_DIR, "--daemon"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                bufsize=1,
                encoding="utf-8",
            )
            return self._proc
        except Exception:
            self._proc = None
            return None

    def call(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        with self._lock:
            proc = self._ensure()
            if not proc or not proc.stdin or not proc.stdout:
                return None
            try:
                proc.stdin.write(json.dumps(payload, ensure_ascii=False) + "\n")
                proc.stdin.flush()
                line = proc.stdout.readline()
                if not line:
                    self._proc = None
                    return None
                return json.loads(line)
            except Exception:
                self._proc = None
                return None


_DAEMON = _MemoryTreeDaemon()


def collect_multichannel_events() -> List[Dict[str, Any]]:
    """Raccoglie gli eventi più recenti dai database locali in formato uniforme."""
    events: List[Dict[str, Any]] = []

    if os.path.exists(VAULT_DB):
        try:
            conn = sqlite3.connect(VAULT_DB, timeout=2.0)
            cur = conn.cursor()

            # 1. Email recenti
            try:
                cur.execute("SELECT sender, subject, body, date FROM emails ORDER BY rowid DESC LIMIT 60")
                for sender, subj, body, dt in cur.fetchall():
                    s_str = (sender or "Mittente").strip()
                    sb_str = (subj or "Comunicazione").strip()
                    bd_str = (body or "").strip()[:300]
                    events.append({
                        "source": "email",
                        "title": f"{sb_str} ({s_str})",
                        "content": bd_str or sb_str,
                        "timestamp": str(dt or ""),
                        "importance": 2.0,
                        "city": "",
                        "phone": "",
                    })
            except Exception:
                pass

            # 2. Lead verificati (Giardinaggio, Pittura, Traslochi, SELEZIONE)
            try:
                cur.execute(
                    """SELECT client_name, phone, city, service_type, estimated_budget, scraped_date, notes
                       FROM verified_leads_2026 ORDER BY id DESC LIMIT 80"""
                )
                for name, phone, city, svc, budget, dt, notes in cur.fetchall():
                    events.append({
                        "source": "lead",
                        "title": f"{name} — {svc}",
                        "content": f"Budget stimato {budget or 0:.0f} euro. {notes or ''}".strip(),
                        "timestamp": str(dt or ""),
                        "importance": 2.4,
                        "city": str(city or ""),
                        "phone": str(phone or ""),
                    })
            except Exception:
                pass

            # 3. Turni conversazionali recenti (esclude domande meta di recall)
            try:
                cur.execute("SELECT role, content, created_at FROM chat_session_history ORDER BY id DESC LIMIT 30")
                for role, txt, dt in cur.fetchall():
                    if role == "user" and txt and len(txt.strip()) >= 12:
                        t_low = txt.strip().lower()
                        if any(k in t_low for k in ("cosa ti ho detto", "che ti ho detto", "cosa ho chiesto", "cosa ti ho chiesto")):
                            continue
                        events.append({
                            "source": "chat",
                            "title": f"Richiesta Badr: {txt.strip()[:70]}",
                            "content": txt.strip(),
                            "timestamp": str(dt or ""),
                            "importance": 1.1,
                            "city": "",
                            "phone": "",
                        })
            except Exception:
                pass

            conn.close()
        except Exception:
            pass

    if os.path.exists(LTM_DB):
        try:
            conn = sqlite3.connect(LTM_DB, timeout=2.0)
            cur = conn.cursor()

            # 4. Memorie LTM
            try:
                cur.execute("SELECT topic, fact, updated_at FROM memories ORDER BY id DESC LIMIT 60")
                for topic, fact, dt in cur.fetchall():
                    events.append({
                        "source": "ltm",
                        "title": str(topic or "Memoria LTM"),
                        "content": str(fact or ""),
                        "timestamp": str(dt or ""),
                        "importance": 2.6,
                        "city": "",
                        "phone": "",
                    })
            except Exception:
                pass

            # 5. Identità / Dossier
            try:
                cur.execute("SELECT entity_name, role, details, updated_at FROM user_identity_dossier LIMIT 20")
                for ent, role, details, dt in cur.fetchall():
                    events.append({
                        "source": "ltm",
                        "title": f"Dossier {ent} ({role})",
                        "content": str(details or ""),
                        "timestamp": str(dt or ""),
                        "importance": 3.0,
                        "city": "Imola",
                        "phone": "",
                    })
            except Exception:
                pass

            conn.close()
        except Exception:
            pass

    return events


def sync_memory_tree() -> Dict[str, Any]:
    """Esegue la sincronizzazione completa sull'albero gerarchico Rust."""
    events = collect_multichannel_events()
    res = _DAEMON.call({"cmd": "ingest", "events": events})
    if res:
        return res
    return {"status": "FALLBACK", "added": 0, "total_nodes": len(events), "engine": "python:fallback"}


def search_memory_tree(query: str, limit: int = 5) -> Dict[str, Any]:
    """Ricerca ultra-rapida (< 0.5ms) nei nodi gerarchici del Memory Tree in Rust."""
    res = _DAEMON.call({"cmd": "search", "query": query, "limit": limit})
    if res:
        return res
    return {"status": "FALLBACK", "count": 0, "results": [], "engine": "python:fallback"}


def get_memory_tree_briefing() -> Dict[str, Any]:
    """Restituisce il briefing sintetico multi-canale dal Memory Tree."""
    res = _DAEMON.call({"cmd": "briefing"})
    if res and res.get("total_nodes", 0) > 0:
        return res
    # Se vuoto al primo avvio, sincronizza subito al volo
    sync_memory_tree()
    res2 = _DAEMON.call({"cmd": "briefing"})
    return res2 or {"status": "EMPTY", "total_nodes": 0, "highlights": []}


def get_tree_context_for_prompt(query: str, max_hits: int = 3) -> str:
    """Formatta i rami più rilevanti del Memory Tree per iniettarli nei prompt LLM."""
    res = search_memory_tree(query, limit=max_hits)
    hits = res.get("results") or []
    if not hits:
        return ""
    lines = ["[MEMORY TREE RUST — CONTESTO GERARCHICO]:"]
    for h in hits:
        lines.append(f"- [{h.get('domain', '')}] {h.get('title', '')}: {h.get('summary', '')}")
    return "\n".join(lines)


def start_memory_tree_scheduler(interval_sec: int = 1200) -> None:
    """Avvia il loop automatico di auto-ingest ogni 20 minuti (1200s)."""
    global _SCHEDULER_STARTED
    if _SCHEDULER_STARTED:
        return
    _SCHEDULER_STARTED = True

    def _worker():
        time.sleep(2.5)
        while True:
            try:
                sync_memory_tree()
            except Exception:
                pass
            time.sleep(interval_sec)

    threading.Thread(target=_worker, daemon=True, name="ebj-memory-tree-sync").start()
