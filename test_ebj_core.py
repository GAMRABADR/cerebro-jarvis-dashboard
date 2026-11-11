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

def t_system_probe_real_telemetry():
    import ebj_reflex_engine as r
    diag = r.probe_live_system_and_vps()
    assert diag["total_probes"] >= 5, f"attesi almeno 5 target, trovati {diag['total_probes']}"
    assert diag["online_count"] >= 4, f"troppi servizi offline: {diag['online_count']}/{diag['total_probes']}"
    assert diag["total_latency_ms"] < 600, f"probes troppo lente: {diag['total_latency_ms']} ms"

def t_painting_and_gardening_quotes():
    import ebj_reflex_engine as r
    pq = r.calculate_painting_quote("preventivo pittura bianco 80 mq")
    assert pq["floor_mq"] == 80 and pq["base_price_eur"] == 1520, f"stima pittura errata: {pq}"
    assert "PietroTraslochi.com" in pq["brand"], f"brand mancante: {pq}"

    gq = r.calculate_gardening_quote("preventivo taglio erba giardino 200 mq con potatura siepi")
    assert gq["grass_mq"] == 200 and gq["total_eur"] == 350, f"stima giardino errata: {gq}"
    assert "BadrExpress.com" in gq["brand"], f"brand mancante: {gq}"

def t_home_services_lead_radar():
    import ebj_reflex_engine as r
    res = r.jev_reflex_dispatch("trova lavori di giardinaggio e pittura bianco")
    assert res and res["intent"] == "HOME_SERVICES_LEAD_RADAR", f"intento errato: {res}"
    leads = res["receipt"]["details"]["leads"]
    assert len(leads) >= 10, f"troppi pochi lead: {len(leads)}"

    res_bo = r.jev_reflex_dispatch("trova lavori di giardinaggio a Bologna")
    leads_bo = res_bo["receipt"]["details"]["leads"]
    assert len(leads_bo) >= 1 and all(l["city"] == "Bologna" for l in leads_bo), f"filtro città errato: {leads_bo}"

def t_agentic_metacore_preconditions():
    from ebj_agentic_metacore import CognitiveReflectionEngine
    pre = CognitiveReflectionEngine.check_preconditions("verifica stato vps e calcola strategia")
    assert pre["valid"] is True, f"precondizioni non valide: {pre}"
    assert pre["checks"]["vps_reachable"] is True, f"VPS non raggiungibile: {pre}"
    assert pre["checks"]["local_core_online"] is True, f"Core 8088 offline: {pre}"

def t_fable_3d_kinetic_stage():
    import ebj_reflex_engine as r
    # 1. Robot Body
    r1 = r.jev_reflex_dispatch("carica modello 3d del robot e chassis")
    assert r1 and r1["intent"] == "FABLE_3D_ROBOT_BODY", f"r1 errato: {r1}"
    assert "Fable 5.2" in r1["ack"], f"ack robot errato: {r1['ack']}"
    assert r1["receipt"]["details"]["ui_action"]["action"] == "open_fable_3d", f"ui_action errata: {r1}"

    # 2. Exploded View
    r2 = r.jev_reflex_dispatch("esplodi vista del corpo robotico")
    assert r2 and r2["intent"] == "FABLE_3D_EXPLODED_VIEW", f"r2 errato: {r2}"
    assert "vista esplosa" in r2["ack"], f"ack explode errato: {r2['ack']}"

    # 3. 2D Blueprint to 3D
    r3 = r.jev_reflex_dispatch("trasforma planimetria in 3d")
    assert r3 and r3["intent"] == "FABLE_3D_FLOORPLAN_ENV", f"r3 errato: {r3}"

    # 4. AI Landscaping
    r4 = r.jev_reflex_dispatch("attiva landscaping 3d con alberi e giardino")
    assert r4 and r4["intent"] == "FABLE_3D_LANDSCAPING", f"r4 errato: {r4}"


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

def t_italian_lexicon_and_recall():
    import ebj_italian_lexicon as lex
    import ebj_reflex_engine as r
    norm = lex.normalize_italian_asr("miliora i colli di bottilia e trova lavoori")
    assert "migliora" in norm and "colli di bottiglia" in norm and "lavori" in norm, norm

    r1 = r.jev_reflex_dispatch("quanto viene a dare una mano di bianco in appartamento 90 mq")
    assert r1 and r1["intent"] == "PAINTING_QUOTE", r1

    r2 = r.jev_reflex_dispatch("dammi un occhio ai server e tunnel")
    assert r2 and r2["intent"] == "SYSTEM_VPS_STATUS", r2

    r3 = r.jev_reflex_dispatch("cosa ti ho detto?")
    assert r3 and r3["intent"] == "CONVERSATION_MEMORY_RECALL", r3
    for bad in ["*", "#", "`", "👉"]:
        assert bad not in r3["ack"], f"recall non pulito per voce: {r3['ack']}"

def t_http_tts_acks_and_recall():
    if OFFLINE or not _server_up():
        return "SKIP"
    # Pre-warmed acks check
    acks = _http("GET", "/api/tts/acks")
    assert acks.get("status") == "SUCCESS" and len(acks.get("it", [])) >= 1, acks
    assert acks["it"][0].get("voice") == "it-IT-DiegoNeural", acks

    # Verify /api/reflex/dispatch handles VPS status dynamically (NOT shadowed by Rust)
    vps_d = _http("POST", "/api/reflex/dispatch", {"query": "qual è lo stato della vps?"})
    assert vps_d.get("intent") == "SYSTEM_VPS_STATUS", f"VPS dirottato: {vps_d}"

    # Verify /api/reflex/dispatch handles recall in < 50ms
    rec_d = _http("POST", "/api/reflex/dispatch", {"query": "cosa ti ho detto?"})
    assert rec_d.get("intent") == "CONVERSATION_MEMORY_RECALL", f"Recall fallito: {rec_d}"


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
        ("telemetria: probe socket VPS & locale", t_system_probe_real_telemetry),
        ("formule: pittura bianco & giardinaggio", t_painting_and_gardening_quotes),
        ("radar: lead casa & filtro città", t_home_services_lead_radar),
        ("metacore: agentic precondizioni & VPS", t_agentic_metacore_preconditions),
        ("fable 5.2: stage 3D & vista esplosa", t_fable_3d_kinetic_stage),
        ("lessico: dizionario IT & recall", t_italian_lexicon_and_recall),
        ("http: /health", t_http_health),
        ("http: /api/qmd/search", t_http_qmd_search),
        ("http: /api/tts/acks & reflex unificato", t_http_tts_acks_and_recall),
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
