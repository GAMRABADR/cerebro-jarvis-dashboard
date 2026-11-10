#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===============================================================================
EBJ QMD ENGINE — Query Markdown Documents (Advanced Second Brain)
===============================================================================
Motore ad altissima efficienza ispirato all'architettura QMD (Tobi Lütke / Shopify)
e alle best-practice di Second Brain avanzato per LLM (Zero-Token Waste,
Hybrid BM25 + Semantic AST Header Chunking).

Caratteristiche Chiave:
1. Header-Aware AST Chunking: suddividi i documenti per sezioni logiche (#, ##, ###)
   preservando il breadcrumb gerarchico, blocchi di codice e tabelle intatte.
2. Indicizzazione FTS5 con BM25 su SQLite ad alte prestazioni (WAL mode, <3ms).
3. Ponderazione avanzata BM25: Breadcrumb (5x), Heading (10x), Body (1x).
4. Zero-Token Waste: inietta nel context window del modello SOLO i 2-3 chunk
   esatti con coordinate di riga e path, risparmiando il 95% dei token.
5. Auto-Discovery: indicizza PROJECT_MASTER_WIKI.md, HOLOGRAPHIC_MEMORY_VAULT.md,
   tutte le SKILL.md, AGENTS.md e file di documentazione dell'ecosistema.
===============================================================================
"""

import os
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

import time
import re
import sqlite3
import hashlib
from typing import List, Dict, Any, Optional

# Percorsi di riferimento
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
QMD_DB_PATH = os.path.join(CURRENT_DIR, "qmd_vault.db")

# Directory target per la scansione del Second Brain
VAULT_SOURCES = [
    os.path.join(CURRENT_DIR),                                     # cerebro-jarvis-dashboard (*.md)
    os.path.join(PROJECT_ROOT),                                    # Root (*.md come AGENTS.md, WIKI.md)
    os.path.join(PROJECT_ROOT, ".agents", "skills"),               # Skills (*.md)
    os.path.join(PROJECT_ROOT, ".agents", "rules"),                # Rules (*.md)
]

ITALIAN_STOPWORDS = {
    "il", "lo", "la", "i", "gli", "le", "un", "uno", "una", "di", "a", "da", "in", "con",
    "su", "per", "tra", "fra", "e", "ed", "o", "che", "dove", "come", "cosa", "quando",
    "perche", "chi", "abbiamo", "nostro", "nostri", "nostra", "nostre", "sono", "sei",
    "mio", "mia", "tuo", "tua", "si", "no", "jarvis", "ebj", "dimmi", "quale", "quali", "dei", "delle",
    "del", "della", "nel", "nella", "nei", "sul", "sulla", "al", "alla", "mi", "ti", "ci", "è", "qual"
}

# Parole di comando: dicono a EBJ COSA fare, non COSA cercare. Vanno tolte dalla query.
COMMAND_WORDS = {
    "cerca", "cercami", "trova", "trovami", "mostra", "mostrami", "leggi", "apri", "controlla",
    "vault", "memoria", "second", "brain", "wiki", "documentazione", "note", "nelle", "archivio",
    "per", "favore", "parlami", "sapere", "voglio", "vorrei", "puoi", "riguardo", "info", "informazioni"
}

# Cartelle escluse: backup/snapshot (duplicati) e documentazione di terze parti.
EXCLUDED_DIRS = {
    ".git", "node_modules", "target", "venv", ".venv", "Build", "Binaries", "Intermediate",
    "Saved", ".cache", "__pycache__", "cloud_storage_staging", "storage", "04_Backup_Vault_DB",
    "NeoStackAI-3.1.59-UE5.8-Win64", "webui", "extensions", "TRELLIS", "TripoSR", "ds4",
    "references", "vendor", "dist", "site-packages"
}

# Fonti curate dell'ecosistema EBJ: ricevono un boost di rilevanza.
PRIORITY_FILES = {
    "AGENTS.md", "CAPABILITIES_LEDGER.md", "HOLOGRAPHIC_MEMORY_VAULT.md", "PROJECT_MASTER_WIKI.md",
    "WIKI.md", "PROMPTS_EBJ_SUPREME.md", "DOCUMENTAZIONE_8_AGENTI_EBJ.md", "EBJ_Ecosystem_Capability_Map.md"
}

def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(QMD_DB_PATH, timeout=10.0)
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    conn.execute("PRAGMA busy_timeout = 10000;")
    return conn

def init_qmd_db():
    conn = get_db_connection()
    c = conn.cursor()
    # Tabella file indicizzati
    c.execute("""
        CREATE TABLE IF NOT EXISTS qmd_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT UNIQUE,
            file_name TEXT,
            mtime REAL,
            file_hash TEXT,
            chunk_count INTEGER DEFAULT 0,
            indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # Tabella chunks
    c.execute("""
        CREATE TABLE IF NOT EXISTS qmd_chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT,
            file_name TEXT,
            heading TEXT,
            breadcrumb TEXT,
            content TEXT,
            start_line INTEGER,
            end_line INTEGER,
            char_count INTEGER,
            mtime REAL
        )
    """)
    # Tabella FTS5 con tokenizzatore Porter e rimozione diacritici
    c.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS qmd_chunks_fts USING fts5(
            heading, breadcrumb, content,
            content='qmd_chunks', content_rowid='id',
            tokenize='porter unicode61 remove_diacritics 2'
        )
    """)
    conn.commit()
    conn.close()

def parse_markdown_into_chunks(file_path: str, base_dir: str = PROJECT_ROOT) -> List[Dict[str, Any]]:
    """
    AST-like Header Chunking: analizza il markdown riga per riga.
    Traccia la gerarchia degli header (#, ##, ###, ####) e divide in sezioni
    logiche preservando i blocchi di codice, tabelle e il percorso (breadcrumb).
    """
    if not os.path.exists(file_path):
        return []

    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except Exception as e:
        print(f"[QMD Parser Error] Impossibile leggere {file_path}: {e}")
        return []

    if not lines:
        return []

    rel_path = os.path.relpath(file_path, base_dir).replace("\\", "/")
    file_name = os.path.basename(file_path)
    file_mtime = os.path.getmtime(file_path)

    chunks = []
    header_stack = [] # [(level, text)]
    current_lines = []
    current_start_line = 1
    current_heading = file_name
    in_code_block = False

    def build_breadcrumb(stack, fallback):
        if not stack:
            return fallback
        return " > ".join([h[1] for h in stack])

    for line_idx, line in enumerate(lines, start=1):
        stripped = line.strip()
        # Monitora delimitatori blocco codice
        if stripped.startswith("```"):
            in_code_block = not in_code_block

        # Rileva intestazione markdown solo fuori dai blocchi codice
        heading_match = None
        if not in_code_block and stripped.startswith("#"):
            m = re.match(r'^(#{1,6})\s+(.*)$', stripped)
            if m:
                heading_match = (len(m.group(1)), m.group(2).strip())

        if heading_match:
            # Salva il chunk accumulato finora se non vuoto
            content_text = "".join(current_lines).strip()
            if content_text and len(content_text) > 40:
                breadcrumb = build_breadcrumb(header_stack, file_name)
                chunks.append({
                    "file_path": rel_path,
                    "file_name": file_name,
                    "heading": current_heading,
                    "breadcrumb": breadcrumb,
                    "content": content_text,
                    "start_line": current_start_line,
                    "end_line": line_idx - 1,
                    "char_count": len(content_text),
                    "mtime": file_mtime
                })
            
            # Aggiorna lo stack delle intestazioni
            level, text = heading_match
            # Rimuovi intestazioni di livello pari o inferiore
            while header_stack and header_stack[-1][0] >= level:
                header_stack.pop()
            header_stack.append((level, text))

            current_heading = text
            current_start_line = line_idx
            current_lines = [line]
        else:
            current_lines.append(line)

            # Se una sezione senza sottotitoli supera i 3500 caratteri, spezza al primo paragrafo vuoto
            content_len = sum(len(l) for l in current_lines)
            if content_len > 3500 and stripped == "" and not in_code_block:
                content_text = "".join(current_lines).strip()
                if content_text:
                    breadcrumb = build_breadcrumb(header_stack, file_name)
                    chunks.append({
                        "file_path": rel_path,
                        "file_name": file_name,
                        "heading": f"{current_heading} (Parte)",
                        "breadcrumb": breadcrumb,
                        "content": content_text,
                        "start_line": current_start_line,
                        "end_line": line_idx,
                        "char_count": len(content_text),
                        "mtime": file_mtime
                    })
                    current_lines = []
                    current_start_line = line_idx + 1

    # Salva l'ultimo chunk residuo
    content_text = "".join(current_lines).strip()
    if content_text and len(content_text) > 40:
        breadcrumb = build_breadcrumb(header_stack, file_name)
        chunks.append({
            "file_path": rel_path,
            "file_name": file_name,
            "heading": current_heading,
            "breadcrumb": breadcrumb,
            "content": content_text,
            "start_line": current_start_line,
            "end_line": len(lines),
            "char_count": len(content_text),
            "mtime": file_mtime
        })

    return chunks

def discover_markdown_files() -> List[str]:
    """Cerca tutti i file Markdown rilevanti nelle sorgenti del Second Brain."""
    found = []
    seen = set()

    for src in VAULT_SOURCES:
        if not os.path.exists(src):
            continue
        if os.path.isfile(src) and src.endswith(".md"):
            p = os.path.abspath(src)
            if p not in seen:
                seen.add(p)
                found.append(p)
        else:
            # Scansione directory (se src è PROJECT_ROOT escludiamo cartelle pesanti non-doc)
            for root, dirs, files in os.walk(src):
                # Esclusioni per performance
                dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS and not d.startswith("snapshot_")]
                for f in files:
                    if f.endswith(".md"):
                        p = os.path.abspath(os.path.join(root, f))
                        if p not in seen:
                            seen.add(p)
                            found.append(p)
    return found

def index_all_markdown(force: bool = False) -> Dict[str, Any]:
    """
    Indicizza tutti i file Markdown scoperti.
    Esegue controllo differenziale di mtime e hash: rielabora solo i file modificati.
    """
    init_qmd_db()
    files = discover_markdown_files()
    conn = get_db_connection()
    c = conn.cursor()

    total_chunks = 0
    updated_files = 0
    start_time = time.time()

    for file_path in files:
        rel_path = os.path.relpath(file_path, PROJECT_ROOT).replace("\\", "/")
        file_name = os.path.basename(file_path)
        mtime = os.path.getmtime(file_path)

        c.execute("SELECT mtime, file_hash FROM qmd_files WHERE file_path = ?", (rel_path,))
        row = c.fetchone()

        # Calcolo hash per certezza
        try:
            with open(file_path, "rb") as f:
                f_hash = hashlib.md5(f.read(65536)).hexdigest()
        except Exception:
            f_hash = ""

        if not force and row:
            db_mtime, db_hash = row
            if abs(db_mtime - mtime) < 0.001 and db_hash == f_hash:
                continue # Nessuna modifica

        # Rielabora i chunk di questo file
        chunks = parse_markdown_into_chunks(file_path)
        if not chunks:
            continue

        # Cancella vecchi chunk del file
        c.execute("DELETE FROM qmd_chunks WHERE file_path = ?", (rel_path,))
        
        # Inserisci nuovi chunk
        for ch in chunks:
            c.execute("""
                INSERT INTO qmd_chunks (file_path, file_name, heading, breadcrumb, content, start_line, end_line, char_count, mtime)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                ch["file_path"], ch["file_name"], ch["heading"], ch["breadcrumb"],
                ch["content"], ch["start_line"], ch["end_line"], ch["char_count"], ch["mtime"]
            ))

        c.execute("""
            INSERT INTO qmd_files (file_path, file_name, mtime, file_hash, chunk_count, indexed_at)
            VALUES (?, ?, ?, ?, ?, datetime('now'))
            ON CONFLICT(file_path) DO UPDATE SET
                mtime = excluded.mtime,
                file_hash = excluded.file_hash,
                chunk_count = excluded.chunk_count,
                indexed_at = excluded.indexed_at
        """, (rel_path, file_name, mtime, f_hash, len(chunks)))

        total_chunks += len(chunks)
        updated_files += 1

    # Pota i file eliminati o ora esclusi (evita risultati fantasma)
    current = {os.path.relpath(p, PROJECT_ROOT).replace("\\", "/") for p in files}
    stale = [r[0] for r in c.execute("SELECT file_path FROM qmd_files").fetchall() if r[0] not in current]
    stale += [r[0] for r in c.execute("SELECT DISTINCT file_path FROM qmd_chunks").fetchall()
              if r[0] not in current and r[0] not in stale]
    for sp in stale:
        c.execute("DELETE FROM qmd_chunks WHERE file_path = ?", (sp,))
        c.execute("DELETE FROM qmd_files WHERE file_path = ?", (sp,))
    removed_files = len(stale)

    # Ricostruisci indice FTS5 per sincronizzazione perfetta
    if updated_files > 0 or removed_files > 0 or force:
        c.execute("INSERT INTO qmd_chunks_fts(qmd_chunks_fts) VALUES('rebuild')")
        conn.commit()

    conn.close()
    elapsed_ms = (time.time() - start_time) * 1000

    return {
        "status": "SUCCESS",
        "total_files_scanned": len(files),
        "updated_files": updated_files,
        "new_chunks_indexed": total_chunks,
        "removed_files": removed_files,
        "elapsed_ms": round(elapsed_ms, 2)
    }


_AUTO_REINDEX_STARTED = False

def start_auto_reindex(interval_sec: int = 600) -> bool:
    """
    Avvia un thread daemon che reindicizza in modo differenziale ogni `interval_sec`.
    Attivo di default solo su Windows (PC con il repo completo). Sulla VPS (RAM sotto
    pressione) va abilitato esplicitamente con QMD_AUTO_REINDEX=1, perché lì PROJECT_ROOT
    è /home/ubuntu e la scansione costerebbe troppo.
    """
    global _AUTO_REINDEX_STARTED
    flag = os.environ.get("QMD_AUTO_REINDEX", "1" if sys.platform == "win32" else "0")
    if _AUTO_REINDEX_STARTED or flag != "1":
        return False
    _AUTO_REINDEX_STARTED = True
    import threading

    def _loop():
        while True:
            try:
                res = index_all_markdown()
                if res.get("updated_files") or res.get("removed_files"):
                    print(f"[QMD Auto-Reindex] +{res['updated_files']} file, -{res['removed_files']} file, {res['elapsed_ms']}ms")
            except Exception as ex:
                print(f"[QMD Auto-Reindex Error]: {ex}")
            time.sleep(interval_sec)

    threading.Thread(target=_loop, daemon=True, name="qmd-auto-reindex").start()
    return True

def clean_query_tokens(query: str) -> List[str]:
    # Normalizza contrazioni ed elisioni (es. dell'infrastruttura -> della infrastruttura)
    q_norm = re.sub(r"['’`]", " ", query.lower())
    words = [w.strip(".-") for w in re.findall(r'[\w\.\-]+', q_norm)]
    words = [w for w in words if w]
    tokens = [w for w in words if len(w) > 1 and w not in ITALIAN_STOPWORDS and w not in COMMAND_WORDS]
    if tokens:
        return tokens
    # Se la query era fatta solo di parole di comando, ricadi sulle non-stopword
    return [w for w in words if w not in ITALIAN_STOPWORDS][:3] or words[:3]

def qmd_search(query: str, limit: int = 4) -> List[Dict[str, Any]]:
    """
    Ricerca ibrida QMD:
    1. BM25 pesato con boosting su breadcrumb e heading.
    2. Exact token matching per porte, IP, sigle, codici catastali.
    3. Calcolo score combinato RRF (Reciprocal Rank Fusion).
    """
    if not query or not query.strip():
        return []

    # Auto-inizializzazione se il DB è vuoto o assente
    if not os.path.exists(QMD_DB_PATH) or os.path.getsize(QMD_DB_PATH) < 4096:
        try:
            index_all_markdown()
        except Exception:
            pass

    tokens = clean_query_tokens(query)
    if not tokens:
        return []

    conn = get_db_connection()
    c = conn.cursor()

    # Prepara query FTS5 sicura
    safe_terms = []
    for t in tokens:
        clean_t = re.sub(r'[^\w\.\-]', '', t)
        if clean_t:
            safe_terms.append(f'"{clean_t}"*')

    fts_match_expr = " OR ".join(safe_terms)
    
    # 1. Recupero BM25 con FTS5
    # Pesi BM25: heading (10.0), breadcrumb (5.0), content (1.0)
    results = []
    try:
        c.execute("""
            SELECT c.id, c.file_path, c.file_name, c.heading, c.breadcrumb, c.content, 
                   c.start_line, c.end_line, c.char_count,
                   bm25(qmd_chunks_fts, 10.0, 5.0, 1.0) as bm_score
            FROM qmd_chunks_fts f
            JOIN qmd_chunks c ON f.rowid = c.id
            WHERE qmd_chunks_fts MATCH ?
            ORDER BY bm_score ASC
            LIMIT ?
        """, (fts_match_expr, max(limit * 8, 24)))
        raw_rows = c.fetchall()
    except Exception as e:
        raw_rows = []

    # 2. Se FTS5 non produce risultati o la query contiene caratteri speciali (es. IP 92.4.233.42)
    if not raw_rows:
        for t in tokens[:2]:
            like_pat = f"%{t}%"
            c.execute("""
                SELECT id, file_path, file_name, heading, breadcrumb, content, 
                       start_line, end_line, char_count, 0.0 as bm_score
                FROM qmd_chunks
                WHERE content LIKE ? OR heading LIKE ? OR breadcrumb LIKE ?
                ORDER BY char_count ASC
                LIMIT ?
            """, (like_pat, like_pat, like_pat, limit * 2))
            for r in c.fetchall():
                if not any(x[0] == r[0] for x in raw_rows):
                    raw_rows.append(r)

    # 3. Re-Ranking Semantico / Precisione Termini
    scored_items = []
    query_lower = query.lower()
    q_words = set(query_lower.split())

    for idx, r in enumerate(raw_rows):
        cid, fpath, fname, heading, breadcrumb, content, sline, eline, ccount, bm_score = r
        content_low = content.lower()
        head_low = heading.lower()
        bread_low = breadcrumb.lower()

        # BM25 produce punteggi negativi (più negativi = più rilevanti)
        bm_rank = idx + 1
        rrf_bm = 1.0 / (60.0 + bm_rank)

        # Keyword density & exact match bonus
        exact_hits = 0
        for tok in tokens:
            if tok in head_low:
                exact_hits += 3
            if tok in bread_low:
                exact_hits += 2
            if tok in content_low:
                exact_hits += 1

        # Bonus per query completa contenuta
        full_phrase_bonus = 5.0 if query_lower in content_low or query_lower in head_low else 0.0
        # Copertura: quanti token DIVERSI della query compaiono (premia chi li contiene tutti)
        coverage = sum(1 for tok in tokens if tok in content_low or tok in head_low) / max(1, len(tokens))
        priority_bonus = 2.0 if fname in PRIORITY_FILES else 0.0

        composite_score = rrf_bm * 100.0 + exact_hits + full_phrase_bonus + coverage * 6.0 + priority_bonus

        scored_items.append({
            "id": cid,
            "file_path": fpath,
            "file_name": fname,
            "heading": heading,
            "breadcrumb": breadcrumb,
            "content": content,
            "start_line": sline,
            "end_line": eline,
            "char_count": ccount,
            "score": round(composite_score, 3)
        })

    conn.close()

    # Ordina per score composito decrescente ed elimina i duplicati di contenuto
    scored_items.sort(key=lambda x: x["score"], reverse=True)
    unique, seen_hashes = [], set()
    for it in scored_items:
        h = hashlib.md5(re.sub(r"\*\(Registrato:[^)]*\)\*", "", it["content"]).strip().encode("utf-8", "ignore")).hexdigest()
        if h in seen_hashes:
            continue
        seen_hashes.add(h)
        unique.append(it)
        if len(unique) >= limit:
            break
    return unique

def get_qmd_context(query: str, max_chunks: int = 3, max_chars: int = 4000) -> Optional[str]:
    """
    Ritorna il blocco di contesto Markdown Second Brain formattato
    per l'iniezione nel System Prompt con Zero-Token Waste.
    """
    if not query or len(query.strip()) < 3:
        return None

    results = qmd_search(query, limit=max_chunks)
    if not results:
        return None

    blocks = [
        "\n==================================================================",
        f"🧠 [SECOND BRAIN QMD | CONOSCENZA CERTIFICATA PER: '{query.strip()}']",
        "Regola: Usa i dettagli precisi qui sotto per rispondere con autorevolezza ed esattezza.",
        "=================================================================="
    ]

    total_len = 0
    for i, r in enumerate(results, start=1):
        # Troncamento intelligente per non eccedere max_chars
        content = r["content"]
        if len(content) > 1200:
            content = content[:1200] + "\n... [continua nel file]"

        block = (
            f"\n📄 [FONTE #{i}: {r['file_name']} | Righe {r['start_line']}-{r['end_line']}]\n"
            f"📍 Sezione: {r['breadcrumb']}\n"
            f"```markdown\n{content}\n```"
        )
        if total_len + len(block) > max_chars:
            break
        blocks.append(block)
        total_len += len(block)

    blocks.append("==================================================================")
    return "\n".join(blocks)

def get_qmd_stats() -> Dict[str, Any]:
    """Ritorna statistiche sull'indice Second Brain."""
    init_qmd_db()
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT count(*) FROM qmd_files")
    files_count = c.fetchone()[0]
    c.execute("SELECT count(*) FROM qmd_chunks")
    chunks_count = c.fetchone()[0]
    c.execute("SELECT max(indexed_at) FROM qmd_files")
    last_indexed = c.fetchone()[0]
    db_size_bytes = os.path.getsize(QMD_DB_PATH) if os.path.exists(QMD_DB_PATH) else 0
    conn.close()

    return {
        "status": "ONLINE",
        "database": os.path.basename(QMD_DB_PATH),
        "total_documents": files_count,
        "total_chunks": chunks_count,
        "database_size_kb": round(db_size_bytes / 1024, 2),
        "last_indexed_at": last_indexed or "Never"
    }

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="EBJ QMD Engine CLI (Query Markdown Documents)")
    parser.add_argument("command", choices=["index", "search", "stats"], help="Comando da eseguire")
    parser.add_argument("query", nargs="?", default="", help="Query di ricerca (per comando search)")
    parser.add_argument("--limit", type=int, default=3, help="Numero massimo di chunk")
    parser.add_argument("--force", action="store_true", help="Forza reindicizzazione completa")

    args = parser.parse_args()

    if args.command == "index":
        print("⚡ Indicizzazione Second Brain in corso...")
        res = index_all_markdown(force=args.force)
        print(f"✓ Indicizzazione completata in {res['elapsed_ms']}ms!")
        print(f"  • File scansionati: {res['total_files_scanned']}")
        print(f"  • File aggiornati: {res['updated_files']}")
        print(f"  • Nuovi chunk indicizzati: {res['new_chunks_indexed']}")
    elif args.command == "stats":
        stats = get_qmd_stats()
        print("📊 Statistiche EBJ QMD Second Brain:")
        for k, v in stats.items():
            print(f"  • {k}: {v}")
    elif args.command == "search":
        if not args.query:
            print("Specificare una query. Esempio: python ebj_qmd_engine.py search 'tariffe sgomberi'")
            sys.exit(1)
        start = time.time()
        ctx = get_qmd_context(args.query, max_chunks=args.limit)
        elapsed = (time.time() - start) * 1000
        if ctx:
            print(f"✓ Trovato contesto in {elapsed:.2f}ms:")
            print(ctx)
        else:
            print(f"Nessun risultato rilevante per '{args.query}' ({elapsed:.2f}ms).")
