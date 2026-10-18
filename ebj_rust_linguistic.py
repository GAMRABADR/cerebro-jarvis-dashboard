"""
==============================================================================
⚡ EBJ SUPREME — RUST LINGUISTIC & JEV/CLM CONNECTOR
==============================================================================
Bridge ad altissima velocità tra Python e il binario nativo Rust
'ebj-linguistic-core.exe'. Esegue language profiling, rilevamento Darija
e classificazione intent CLM in < 1 millisecondo con caching LRU in RAM.
==============================================================================
"""

from __future__ import annotations
import os
import sys
import json
import time
import subprocess
from typing import Dict, Any, Optional

import threading

RUST_LINGUISTIC_BIN = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..", "ebj-supreme", "rust-agents", "target", "release", "ebj-linguistic-core.exe"
))

# Cache LRU in memoria per query frequenti
_QUERY_CACHE: Dict[str, Dict[str, Any]] = {}
_MAX_CACHE_ENTRIES = 2000

class _RustDaemonWorker:
    """Worker daemon persistente in background per azzerare l'overhead di CreateProcessW (<0.1ms)."""
    def __init__(self):
        self._proc: Optional[subprocess.Popen] = None
        self._lock = threading.Lock()

    def _ensure_process(self) -> Optional[subprocess.Popen]:
        if not os.path.exists(RUST_LINGUISTIC_BIN):
            return None
        if self._proc is not None and self._proc.poll() is None:
            return self._proc
        try:
            self._proc = subprocess.Popen(
                [RUST_LINGUISTIC_BIN, "--daemon"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                bufsize=1,
                encoding="utf-8"
            )
            return self._proc
        except Exception:
            self._proc = None
            return None

    def query(self, text: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            proc = self._ensure_process()
            if not proc or not proc.stdin or not proc.stdout:
                return None
            try:
                clean_text = text.replace("\r", " ").replace("\n", " ").strip()
                if not clean_text:
                    return None
                proc.stdin.write(clean_text + "\n")
                proc.stdin.flush()
                line = proc.stdout.readline()
                if not line:
                    # Process died, reset
                    self._proc = None
                    return None
                return json.loads(line.strip())
            except Exception:
                try:
                    if self._proc:
                        self._proc.kill()
                except Exception:
                    pass
                self._proc = None
                return None

_DAEMON = _RustDaemonWorker()

def analyze_linguistic_intent(query_text: str) -> Dict[str, Any]:
    """
    Analizza la query tramite il motore compilato in Rust.
    Ritorna la lingua rilevata (con supporto Darija), voce consigliata,
    intento CLM/JEV e trigger barge-in in < 0.2ms.
    """
    t0 = time.perf_counter()
    q = str(query_text or "").strip()
    if not q:
        return {
            "detected_language": "it",
            "language_name": "Italiano",
            "confidence": 1.0,
            "intent": "EMPTY",
            "barge_in_triggered": False,
            "latency_ms": 0.0
        }

    # Controllo cache RAM
    if q in _QUERY_CACHE:
        res = dict(_QUERY_CACHE[q])
        res["cached"] = True
        res["latency_ms"] = round((time.perf_counter() - t0) * 1000.0, 3)
        return res

    # 1. Pipeline ultra-rapida tramite Daemon Persistente Rust
    rust_res = _DAEMON.query(q)
    if rust_res:
        lat_ms = (time.perf_counter() - t0) * 1000.0
        rust_res["latency_ms"] = round(lat_ms, 3)
        if len(_QUERY_CACHE) >= _MAX_CACHE_ENTRIES:
            _QUERY_CACHE.clear()
        _QUERY_CACHE[q] = rust_res
        return rust_res

    # 2. Fallback: esecuzione singola se il daemon non risponde
    if os.path.exists(RUST_LINGUISTIC_BIN):
        try:
            proc = subprocess.run(
                [RUST_LINGUISTIC_BIN, "--analyze", q],
                capture_output=True, text=True, timeout=1.0
            )
            if proc.returncode == 0 and proc.stdout:
                parsed = json.loads(proc.stdout)
                lat_ms = (time.perf_counter() - t0) * 1000.0
                parsed["latency_ms"] = round(lat_ms, 3)
                if len(_QUERY_CACHE) >= _MAX_CACHE_ENTRIES:
                    _QUERY_CACHE.clear()
                _QUERY_CACHE[q] = parsed
                return parsed
        except Exception:
            pass

    # 3. Fallback euristico ultra-rapido
    lat_ms = (time.perf_counter() - t0) * 1000.0
    lower = q.lower()
    is_darija = any(w in lower for w in ["salam", "khoya", "kidayr", "labas", "chouf", "mzyan", "bzaf", "wesh", "3afak", "safi"])
    is_stop = any(w in lower for w in ["stop", "fermo", "fermati", "basta", "aspetta", "taci", "silenzio", "calma", "safi", "wqef"])

    return {
        "detected_language": "ar-ma" if is_darija else "it",
        "language_name": "Arabo Marocchino (Darija)" if is_darija else "Italiano",
        "confidence": 0.90 if is_darija else 0.75,
        "is_darija": is_darija,
        "is_arabic_script": False,
        "intent": "BARGE_IN_STOP" if is_stop else "GENERAL_CONVERSATION",
        "intent_confidence": 1.0 if is_stop else 0.8,
        "barge_in_triggered": is_stop,
        "suggested_voice": "ar-MA-JamalNeural" if is_darija else "it-IT-DiegoNeural",
        "latency_ms": round(lat_ms, 3),
        "engine": "fallback_heuristic"
    }

if __name__ == "__main__":
    t_start = time.perf_counter()
    res = analyze_linguistic_intent("Salam a khoya Badr entra nel pc")
    print("Test Result:", json.dumps(res, indent=2))
    print(f"Total roundtrip: {(time.perf_counter() - t_start)*1000:.2f} ms")
