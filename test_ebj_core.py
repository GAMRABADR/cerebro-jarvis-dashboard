#!/usr/bin/env python3
"""
EBJ Core Regression Suite
=========================
Test rapidi (< 5 s) sui pezzi che in passato si sono rotti IN SILENZIO:
  - il ponte Rust :9000 della memoria (bug `import requests` mancante, nov 2026)
  - la qualità del Second Brain QMD (duplicati da backup, parole di comando nella query)
  - l'instradamento del motore di riflesso (una corsia che ruba la richiesta a un'altra)
  - gli endpoint HTTP vivi di server.py

Uso:
    python test_ebj_core.py            # tutti i test (gli HTTP si saltano se il server è spento)
    python test_ebj_core.py --offline  # solo test che non richiedono servizi attivi
Exit code 0 = tutto verde, 1 = almeno un fallimento.
"""
import os
import sys
import time
import json
import urllib.request

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
OFFLINE = "--offline" in sys.argv
RESULTS = []


def check(name, fn):
    t0 = time.perf_counter()
    try:
        outcome = fn()
        ms = (time.perf_counter() - t0) * 1000
        if outcome == "SKIP":
            RESULTS.append(("SKIP", name, ms, ""))
        else:
            RESULTS.append(("PASS", name, ms, ""))
    except AssertionError as e:
        RESULTS.append(("FAIL", name, (time.perf_counter() - t0) * 1000, str(e)))
    except Exception as e:
        RESULTS.append(("FAIL", name, (time.perf_counter() - t0) * 1000, f"{type(e).__name__}: {e}"))


def _http(method, path, body=None, timeout=8):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(f"http://127.0.0.1:8088{path}", data=data, method=method,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def _server_up():
    try:
        _http("GET", "/health", timeout=2)
        return True
    except Exception:
        return False


# ── 1. Memoria Hermes ───────────────────────────────────────────────────────
def t_hermes_has_requests():
    import hermes_memory
    assert hasattr(hermes_memory, "requests"), "hermes_memory non importa `requests`: il ponte Rust :9000 è morto in silenzio"

def t_hermes_search_returns():
    import hermes_memory
    res = hermes_memory.search_memory("Badr", limit=3)
    assert res, "search_memory('Badr') vuoto"
    assert any("Badr" in (r.get("fact") or "") for r in res), "nessun fatto su Badr"

def t_hermes_context_has_qmd():
    import hermes_memory
    ctx = hermes_memory.get_holographic_memory_context("Steam AppID di EBGS")
    assert "2886940" in ctx, "il contesto non contiene l'AppID 2886940"


# ── 2. Second Brain QMD ─────────────────────────────────────────────────────
GOLDEN = [
    # (query, stringa attesa nel top-3, file atteso nel top-3 o None)
    ("tariffe sgomberi", "8€ a mq", "HOLOGRAPHIC_MEMORY_VAULT.md"),
    ("Steam AppID EBGS", "2886940", None),
    ("cerca nel vault le tariffe di sgombero", "8€ a mq", None),  # parole di comando da ignorare
]

def t_qmd_golden():
    import ebj_qmd_engine as q
    for query, needle, fname in GOLDEN:
        res = q.qmd_search(query, limit=3)
        assert res, f"nessun risultato per '{query}'"
        blob = " ".join(r["content"] for r in res)
        assert needle in blob, f"'{needle}' assente nel top-3 di '{query}'"
        if fname:
            assert any(r["file_name"] == fname for r in res), f"{fname} assente nel top-3 di '{query}'"

def t_qmd_no_duplicates():
    import ebj_qmd_engine as q
    res = q.qmd_search("tariffe sgomberi", limit=4)
    contents = [r["content"] for r in res]
    assert len(contents) == len(set(contents)), "il top-4 contiene blocchi duplicati"

def t_qmd_no_backup_paths():
    import ebj_qmd_engine as q
    conn = q.get_db_connection()
    paths = [r[0] for r in conn.execute("SELECT DISTINCT file_path FROM qmd_chunks").fetchall()]
    conn.close()
    # Controllo sui segmenti di CARTELLA (in SQL LIKE '_' è un jolly e dà falsi positivi)
    bad = [p for p in paths
           if any(seg in q.EXCLUDED_DIRS or seg.startswith("snapshot_") for seg in p.split("/")[:-1])]
    assert not bad, f"{len(bad)} file da cartelle escluse, es. {bad[:3]}"

def t_qmd_command_words_stripped():
    import ebj_qmd_engine as q
    toks = q.clean_query_tokens("cerca nel vault le tariffe di sgombero")
    assert "cerca" not in toks and "vault" not in toks, f"token di comando rimasti: {toks}"
    assert "tariffe" in toks, f"token utile perso: {toks}"

def t_qmd_latency():
    import ebj_qmd_engine as q
    q.qmd_search("riscaldamento cache", limit=3)
    t0 = time.perf_counter()
    q.qmd_search("tariffe sgomberi traslochi", limit=3)
    ms = (time.perf_counter() - t0) * 1000
    assert ms < 150, f"qmd_search troppo lenta: {ms:.1f} ms"


# ── 3. Motore di riflesso ───────────────────────────────────────────────────
ROUTES = [
    ("cerca nel vault le tariffe di sgombero", "VAULT_SEARCH"),
    ("cerca nella memoria la porta di n8n sulla vps", "VAULT_SEARCH"),  # non deve finire su SYSTEM_VPS_STATUS
    ("controlla la posta in arrivo", "EMAIL_INBOX"),
]

def t_reflex_routing():
    import ebj_reflex_engine as r
    for prompt, intent in ROUTES:
        res = r.jev_reflex_dispatch(prompt)
        assert res and res.get("intent") == intent, f"'{prompt}' -> {res and res.get('intent')} (atteso {intent})"

def t_reflex_spoken_clean():
    import ebj_reflex_engine as r
    ack = r.jev_reflex_dispatch("cerca nel vault le tariffe di sgombero")["ack"]
    assert "8€ a mq" in ack, f"la risposta parlata non contiene la tariffa: {ack}"
    for bad in ["`", "★", "##", "**"]:
        assert bad not in ack, f"la risposta parlata contiene '{bad}' (verrebbe letto dalla voce)"


# ── 4. HTTP live ────────────────────────────────────────────────────────────
def t_http_health():
    if OFFLINE or not _server_up():
        return "SKIP"
    d = _http("GET", "/health")
    assert d.get("status") == "ok", d

def t_http_qmd_search():
    if OFFLINE or not _server_up():
        return "SKIP"
    d = _http("POST", "/api/qmd/search", {"query": "tariffe sgomberi", "limit": 2})
    assert d.get("status") == "SUCCESS" and d.get("count", 0) > 0, d


if __name__ == "__main__":
    for name, fn in [
        ("hermes: import requests (ponte Rust)", t_hermes_has_requests),
        ("hermes: search_memory", t_hermes_search_returns),
        ("hermes: contesto con QMD", t_hermes_context_has_qmd),
        ("qmd: query golden", t_qmd_golden),
        ("qmd: niente duplicati", t_qmd_no_duplicates),
        ("qmd: niente backup indicizzati", t_qmd_no_backup_paths),
        ("qmd: parole di comando rimosse", t_qmd_command_words_stripped),
        ("qmd: latenza < 150 ms", t_qmd_latency),
        ("reflex: instradamento", t_reflex_routing),
        ("reflex: risposta parlata pulita", t_reflex_spoken_clean),
        ("http: /health", t_http_health),
        ("http: /api/qmd/search", t_http_qmd_search),
    ]:
        check(name, fn)

    fails = 0
    for status, name, ms, err in RESULTS:
        icon = {"PASS": "✅", "FAIL": "❌", "SKIP": "⏭️"}[status]
        print(f"{icon} {name:<40} {ms:7.1f} ms {err}")
        fails += status == "FAIL"
    passed = sum(1 for s in RESULTS if s[0] == "PASS")
    print(f"\n{passed} passati, {fails} falliti, {len(RESULTS) - passed - fails} saltati")
    sys.exit(1 if fails else 0)
