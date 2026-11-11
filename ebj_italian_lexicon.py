# -*- coding: utf-8 -*-
"""
==============================================================================
📚 E.B.J. ITALIAN LEXICON, ASR NORMALIZER & BUTLER ELOQUENCE ENGINE
==============================================================================
Dizionario semantico esteso della lingua italiana, normalizzatore per dettatura
vocale (ASR) e generatore di espressioni eleganti in stile J.A.R.V.I.S.
(Nino Prester / Paul Bettany) a zero latenza (< 0.5 ms).
==============================================================================
"""

from __future__ import annotations
import re
from typing import Dict, Any, List, Tuple, Optional

# ── 0. IN-PROCESS RUST TURBO CORE (ctypes FFI, < 10 microsecondi, ZERO IPC) ──
import ctypes as _ctypes
import json as _json
import os as _os
import sys as _sys

_TURBO_DIR = _os.path.dirname(_os.path.abspath(__file__))
_TURBO_LIB_NAME = "ebj_turbo_core.dll" if _sys.platform == "win32" else "libebj_turbo_core.so"
_TURBO_CANDIDATES = [
    _os.path.abspath(_os.path.join(_TURBO_DIR, "..", "ebj-supreme", "rust-agents", "target", "release", _TURBO_LIB_NAME)),
    _os.path.join(_TURBO_DIR, "bin", _TURBO_LIB_NAME),
    _os.path.join(_TURBO_DIR, _TURBO_LIB_NAME),
]

_TURBO_LIB = None
for _cand in _TURBO_CANDIDATES:
    if _os.path.isfile(_cand):
        try:
            _lib = _ctypes.CDLL(_cand)
            _lib.ebj_turbo_normalize_and_tag.argtypes = [_ctypes.c_char_p]
            _lib.ebj_turbo_normalize_and_tag.restype = _ctypes.c_void_p
            _lib.ebj_turbo_clean_tts.argtypes = [_ctypes.c_char_p, _ctypes.c_size_t]
            _lib.ebj_turbo_clean_tts.restype = _ctypes.c_void_p
            _lib.ebj_turbo_free_str.argtypes = [_ctypes.c_void_p]
            _lib.ebj_turbo_free_str.restype = None
            _TURBO_LIB = _lib
            break
        except Exception:
            _TURBO_LIB = None

def is_rust_turbo_loaded() -> bool:
    return _TURBO_LIB is not None

def clean_tts_fast(text: str, max_len: int = 420) -> Optional[str]:
    if not _TURBO_LIB or not text:
        return None
    try:
        ptr = _TURBO_LIB.ebj_turbo_clean_tts(text.encode("utf-8", errors="ignore"), max_len)
        if ptr:
            out = _ctypes.cast(ptr, _ctypes.c_char_p).value.decode("utf-8", errors="replace")
            _TURBO_LIB.ebj_turbo_free_str(ptr)
            return out
    except Exception:
        pass
    return None

def _rust_norm_and_tag(text: str) -> Optional[Dict[str, Any]]:
    if not _TURBO_LIB or not text:
        return None
    try:
        ptr = _TURBO_LIB.ebj_turbo_normalize_and_tag(text.encode("utf-8", errors="ignore"))
        if ptr:
            raw_json = _ctypes.cast(ptr, _ctypes.c_char_p).value.decode("utf-8", errors="replace")
            _TURBO_LIB.ebj_turbo_free_str(ptr)
            return _json.loads(raw_json)
    except Exception:
        pass
    return None


# ── 1. NORMALIZZATORE ASR & ERRORI DI BATTITURA COMUNI IN ITALIANO ───────────
_ASR_REPLACEMENTS: List[Tuple[re.Pattern, str]] = [
    (re.compile(r'\bmilior[aeo]\b', re.I), 'migliora'),
    (re.compile(r'\bparrlare\b', re.I), 'parlare'),
    (re.compile(r'\binerazion[ei]\b', re.I), 'interazione'),
    (re.compile(r'\bcapsce\b', re.I), 'capace'),
    (re.compile(r'\blavoori\b', re.I), 'lavori'),
    (re.compile(r'\bpitturra\b', re.I), 'pittura'),
    (re.compile(r'\bgiardinagio\b', re.I), 'giardinaggio'),
    (re.compile(r'\bcolli di bottilia\b', re.I), 'colli di bottiglia'),
    (re.compile(r'\bqual[\x27\s]?e\b', re.I), 'qual è'),
    (re.compile(r'\bcom[\x27\s]?e\b', re.I), "com'è"),
    (re.compile(r'\bcosati\b', re.I), 'cosa ti'),
    (re.compile(r'\bdeto\b', re.I), 'detto'),
    (re.compile(r'\bunattimo\b', re.I), 'un attimo'),
    (re.compile(r'\bperfavore\b', re.I), 'per favore'),
    (re.compile(r'\bfammivedere\b', re.I), 'fammi vedere'),
    (re.compile(r'\bche\s+ti\s+ho\s+chiesto\b', re.I), 'cosa ti ho chiesto'),
    (re.compile(r'\bche\s+ti\s+ho\s+detto\b', re.I), 'cosa ti ho detto'),
    (re.compile(r'\bdimme\b', re.I), 'dimmi'),
    (re.compile(r'\bfamme\b', re.I), 'fammi'),
    (re.compile(r'\bdammi un\s*occhio\b', re.I), 'controlla'),
    (re.compile(r'\bbuttaci un\s*occhio\b', re.I), 'controlla'),
]

# ── 2. REPERTORIO VASTO DI SINONIMI & ESPRESSIONI COLLOQUIALI ITALIANE ───────
ITALIAN_SYNONYM_GROUPS: Dict[str, List[str]] = {
    "RECALL_MEMORY": [
        "cosa ti ho detto", "che ti ho detto", "cosa ho detto", "cosa ti ho chiesto",
        "cosa ci siamo detti", "di cosa stavamo parlando", "di che stavamo parlando",
        "ripeti quello che ho detto", "ripeti cosa ho detto", "ricordi cosa ho detto",
        "qual era la mia ultima richiesta", "cosa ti avevo chiesto", "ultimo messaggio",
        "cosa ho appena detto", "che avevo detto", "cosa abbiamo detto", "riassumi la chat",
        "ricordi cosa abbiamo detto", "quale comando ti ho dato", "che ordine ti ho dato"
    ],
    "SYSTEM_STATUS": [
        "vps", "server", "container", "tunnel", "stato sistema", "stato dei server",
        "tutto online", "sistemi vitali", "come vanno i server", "controlla i server",
        "diagnostica rete", "ping", "tutto a posto", "funziona tutto", "stato infrastruttura",
        "verifica porte", "salute sistema", "check vps", "monitoraggio", "cloud attivo"
    ],
    "PAINTING": [
        "pittura", "imbiancare", "imbiancatura", "imbianchino", "tinteggiatura",
        "tinteggiare", "pitturare", "dare il bianco", "dare una mano di bianco",
        "rinfrescare le pareti", "dipingere casa", "verniciare muri", "pareti bianche",
        "idropittura", "traspirante", "lavabile", "stuccatura", "rasatura", "soffitti",
        "muri sporchi", "tinteggio", "rimettere a nuovo i muri"
    ],
    "GARDENING": [
        "giardinaggio", "giardiniere", "giardino", "potatura", "potare",
        "taglio erba", "tagliare l'erba", "tagliare erba", "sfalcio", "sfalci",
        "prato", "siepe", "siepi", "cespugli", "decespugliatore", "tosaerba",
        "cura del verde", "pulizia giardino", "ramaglie", "foglie secche",
        "disboscamento", "aiuole", "alberi da potare", "sistemare il verde",
        "area verde", "ecocentro sfalci", "manutenzione parco"
    ],
    "MOVING_CLEARING": [
        "trasloco", "traslochi", "traslocare", "sgombero", "sgomberi", "sgomberare",
        "svuotare", "svuota casa", "svuota cantina", "svuota solaio", "facchinaggio",
        "furgone", "autoscala", "scatole", "imballaggio", "mobili", "deposito",
        "custodia mobili", "smaltimento ingombranti", "pre-rogito", "fine locazione"
    ],
    "QUOTES_PRICING": [
        "preventivo", "preventivare", "quanto costa", "quanto viene", "che prezzo ha",
        "stima", "quotazione", "tariffa", "prezzo", "budget", "spesa prevista",
        "conto economico", "calcola il costo", "fammi un prezzo", "dammi una cifra"
    ],
    "ACTION_SEARCH_HUNT": [
        "trova", "cerca", "scova", "scansiona", "individua", "recupera", "estrai",
        "mostrami", "elenca", "lista", "radar", "lead", "clienti", "commesse",
        "richieste", "opportunita", "opportunità", "contatti", "lavori"
    ],
    "FABLE_3D_ROBOT": [
        "robot 3d", "chassis", "corpo robotico", "stage 3d", "fable 3d",
        "modello 3d robot", "crea robot", "fable 5.2", "ologramma robot", "armatura 3d"
    ],
    "FABLE_3D_EXPLODE": [
        "esplodi vista", "vista esplosa", "exploded view", "scomponi modello",
        "esploso 3d", "esplodi il modello", "apri i componenti", "esplodi"
    ],
    "FABLE_3D_FLOORPLAN": [
        "planimetria in 3d", "planimetria 3d", "da 2d a 3d", "piantina in 3d",
        "piantina 3d", "ambiente 3d", "blueprint 3d", "trasforma planimetria",
        "ricostruisci stanza 3d", "mappa 3d"
    ],
    "FABLE_3D_LANDSCAPE": [
        "landscaping", "cura del verde 3d", "alberi e prato 3d", "giardino 3d",
        "ai landscaping", "verde 3d", "piante in 3d"
    ],
    "VAULT_MEMORY": [
        "second brain", "cerca nel vault", "cerca nella memoria", "cerca nella documentazione",
        "cerca nella wiki", "cosa dice la wiki", "trova nelle note", "archivio conoscenza",
        "documenti salvati", "regole di sistema", "regolamento", "database personale"
    ],
}

# ── 3. REPERTORIO AUDIO PRE-CARICABILE "ATTENDI UN ATTIMO" (STESSA VOCE JARVIS) ──
ITALIAN_WAIT_ACKS: List[str] = [
    "Attendi un attimo, signore, procedo subito.",
    "Un istante soltanto, signore: verifico ed eseguo immediatamente.",
    "Agli ordini, signore: elaboro subito la tua richiesta.",
    "Un secondo, Badr: consulto i sistemi e torno da te.",
    "Subito, signore: ci lavoro immediatamente.",
    "Certamente, signore: un breve istante per completare l'analisi.",
]

UK_WAIT_ACKS: List[str] = [
    "One moment, sir. Processing your directive immediately.",
    "Right away, sir. Running diagnostics now.",
    "At your service, sir. Analyzing the data for you.",
]

# ── 4. LESSICO RICCO PER SYSTEM PROMPT (PADRONANZA LINGUA ITALIANA) ───────────
ITALIAN_MASTERY_DIRECTIVE = (
    "\n[PADRONANZA LESSICALE & ELOQUIO J.A.R.V.I.S. (NINO PRESTER)]:\n"
    "- Possiedi un vocabolario della lingua italiana vastissimo, colto, elegante e preciso.\n"
    "- Comprendi perfettamente sinonimi, espressioni colloquiali, dialettismi leggeri ed errori di dettatura vocale.\n"
    "- Esprimiti con scioltezza naturale, variando verbi e connettivi (es. 'provvedo', 'dispongo', 'rilevo', 'eseguo', 'certifico') senza mai suonare ripetitivo o tradotto letteralmente dall'inglese.\n"
    "- Nelle interazioni vocali inizia con naturalezza ('Attendi un attimo, signore...', 'Agli ordini, signore...', 'Subito, Badr...') quando esegui azioni, oppure vai dritto al risultato in 1-3 frasi nitide, prive di asterischi, cancelletti, elenchi puntati o codice.\n"
)


def normalize_italian_asr(text: str) -> str:
    """Normalizza errori di trascrizione vocale e fuzzy-correct in Rust FFI (< 10µs) con fallback Python."""
    if not text:
        return ""
    r = _rust_norm_and_tag(text)
    if r and r.get("normalized"):
        return r["normalized"]
    out = text.strip()
    for pat, repl in _ASR_REPLACEMENTS:
        out = pat.sub(repl, out)
    out = re.sub(r'\s+', ' ', out).strip()
    return out


def extract_italian_semantic_tags(text: str) -> List[str]:
    """Restituisce i tag semantici italiani riconosciuti tramite Rust Aho-Corasick SIMD (< 10µs)."""
    if not text:
        return []
    r = _rust_norm_and_tag(text)
    if r and isinstance(r.get("tags"), list):
        return r["tags"]
    norm = normalize_italian_asr(text).lower()
    tags: List[str] = []
    for tag, keywords in ITALIAN_SYNONYM_GROUPS.items():
        if any(kw in norm for kw in keywords):
            tags.append(tag)
    return tags


def is_recall_question(text: str) -> bool:
    """Verifica se l'utente sta chiedendo cosa ha detto/chiesto nei turni precedenti."""
    norm = normalize_italian_asr(text).lower()
    return any(kw in norm for kw in ITALIAN_SYNONYM_GROUPS["RECALL_MEMORY"])
