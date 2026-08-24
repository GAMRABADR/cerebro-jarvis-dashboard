import sqlite3
import os
import time
import re
import json

MEMORY_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hermes_ltm_memory.db")
VAULT_MD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "HOLOGRAPHIC_MEMORY_VAULT.md")

def init_memory():
    conn = sqlite3.connect(MEMORY_DB)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT,
            topic TEXT,
            fact TEXT UNIQUE,
            importance INTEGER DEFAULT 5,
            created_at INTEGER,
            last_accessed INTEGER,
            access_count INTEGER DEFAULT 1
        )
    """)
    c.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
            topic, fact, category, content='memories', content_rowid='id'
        )
    """)
    conn.commit()
    
    # Sync FTS
    c.execute("INSERT INTO memories_fts(memories_fts) VALUES('rebuild')")
    conn.commit()
    conn.close()

    # Seed essential ecosystem memories if empty
    seed_ecosystem_memories()
    sync_to_markdown_vault()

def seed_ecosystem_memories():
    essential_memories = [
        ("ECOSYSTEM_IDENTITY", "Direttore & Proprietario", "Il proprietario e comandante supremo dell'ecosistema è Badr (EBGStudio), chat ID Telegram: 7298887137.", 10),
        ("GAME_DEV", "EBGS Survival MMO Steamworks", "Il gioco principale in sviluppo è EBGS Survival MMO su Unreal Engine 5.8 con Lumen, shader personalizzati e Steam AppID: 2886940.", 10),
        ("BUSINESS_SGOMBERI", "Tariffe Sgomberi & Traslochi", "I preventivi di sgombero/trasloco si calcolano stimando ~8€ a mq per manodopera base, volume m3, supplemento piano scale se senza ascensore e discarica ecocentro.", 9),
        ("MARKETPLACE_RULES", "Regole di Vendita Subito/Facebook", "Gli annunci per il marketplace richiedono titolo persuasivo ad alto CTR, stima del prezzo ottimale e tag SEO per Subito.it e Facebook.", 8),
        ("INFRASTRUCTURE", "VPS Oracle & Ports Topology", "La VPS Oracle è all'IP 92.4.233.42 con n8n su porta 5678, Agente Zero su porta 50080 e JARVIS su porta 8088 con tunnel Cloudflare automatico.", 9),
        ("VOICE_SETTINGS", "Tasto Vocale Push-To-Talk", "Il tasto rapido vocale predefinito di JARVIS è Ctrl + Spazio.", 7),
        ("AI_MODELS", "Motori Neurale Predefiniti", "La modalità Auto Intelligence usa Groq Qwen 27B / GPT-OSS per sub-second e Gemini 3.7 Flash per compiti complessi.", 8)
    ]
    
    conn = sqlite3.connect(MEMORY_DB)
    c = conn.cursor()
    now = int(time.time())
    for cat, topic, fact, imp in essential_memories:
        try:
            c.execute("INSERT OR IGNORE INTO memories (category, topic, fact, importance, created_at, last_accessed) VALUES (?,?,?,?,?,?)",
                      (cat, topic, fact, imp, now, now))
        except Exception:
            pass
    c.execute("INSERT INTO memories_fts(memories_fts) VALUES('rebuild')")
    conn.commit()
    conn.close()

def store_memory(category, topic, fact, importance=5):
    now = int(time.time())
    conn = sqlite3.connect(MEMORY_DB)
    c = conn.cursor()
    try:
        c.execute("""
            INSERT INTO memories (category, topic, fact, importance, created_at, last_accessed)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(fact) DO UPDATE SET
                access_count = access_count + 1,
                last_accessed = ?,
                importance = MAX(importance, ?)
        """, (category, topic, fact, importance, now, now, now, importance))
        c.execute("INSERT INTO memories_fts(memories_fts) VALUES('rebuild')")
        conn.commit()
        sync_to_markdown_vault()
        return True
    except Exception as e:
        print(f"[Memory Store Error]: {e}")
        return False
    finally:
        conn.close()

ITALIAN_STOPWORDS = {
    "il", "lo", "la", "i", "gli", "le", "un", "uno", "una", "di", "a", "da", "in", "con",
    "su", "per", "tra", "fra", "e", "ed", "o", "che", "dove", "come", "cosa", "quando",
    "perche", "chi", "abbiamo", "nostro", "nostri", "nostra", "nostre", "sono", "sei",
    "mio", "mia", "tuo", "tua", "si", "no", "jarvis", "agente", "dimmi", "quale", "quali"
}

RUST_BRIDGE_URL = "http://127.0.0.1:9000"

def search_memory(query, limit=5, category=None):
    if not query or not query.strip():
        return []
    
    # 1. Ultra-fast Rust Tokio In-Memory Retrieval (< 50 microseconds)
    try:
        payload = {"query": query, "limit": limit}
        if category:
            payload["category"] = category
        r = requests.post(f"{RUST_BRIDGE_URL}/api/memory/search", json=payload, timeout=0.15)
        if r.status_code == 200:
            res_json = r.json()
            if res_json.get("status") == "SUCCESS" and res_json.get("results"):
                return res_json["results"]
    except Exception:
        pass

    # 2. Local SQLite FTS5 fallback
    clean_words = re.findall(r'\w+', query.lower())
    keywords = [w for w in clean_words if w not in ITALIAN_STOPWORDS and len(w) > 2]
    
    if not keywords:
        keywords = clean_words[:3]
    if not keywords:
        return []
    
    conn = sqlite3.connect(MEMORY_DB)
    c = conn.cursor()
    
    fts_query = " OR ".join(keywords)
    try:
        c.execute("""
            SELECT m.category, m.topic, m.fact, m.importance, f.rank
            FROM memories_fts f
            JOIN memories m ON f.rowid = m.id
            WHERE f.memories_fts MATCH ?
            ORDER BY f.rank
            LIMIT ?
        """, (fts_query, limit))
        results = [{"category": r[0], "topic": r[1], "fact": r[2], "importance": r[3]} for r in c.fetchall()]
    except Exception as e:
        print(f"[FTS Query Err]: {e}")
        # Fallback LIKE search
        for kw in keywords[:3]:
            like_term = f"%{kw}%"
            c.execute("""
                SELECT category, topic, fact, importance
                FROM memories
                WHERE fact LIKE ? OR topic LIKE ? OR category LIKE ?
                ORDER BY last_accessed DESC, importance DESC LIMIT ?
            """, (like_term, like_term, like_term, limit))
            for r in c.fetchall():
                item = {"category": r[0], "topic": r[1], "fact": r[2], "importance": r[3]}
                if item not in results:
                    results.append(item)
    finally:
        conn.close()
    
    return results[:limit]

def get_holographic_memory_context(prompt):
    relevant = search_memory(prompt, limit=5)
    if not relevant:
        return ""
    
    lines = ["\n[HERMES INFINITE HOLOGRAPHIC LONG-TERM MEMORY (LTM)]:"]
    for r in relevant:
        lines.append(f"• [{r['category']} - {r['topic']}]: {r['fact']}")
    lines.append("[FINE MEMORIA PERSISTENTE - Usa queste informazioni per rispondere accuratamente]")
    return "\n".join(lines)

def sync_to_markdown_vault():
    conn = sqlite3.connect(MEMORY_DB)
    c = conn.cursor()
    c.execute("SELECT category, topic, fact, importance, datetime(created_at, 'unixepoch') FROM memories ORDER BY category, importance DESC")
    rows = c.fetchall()
    conn.close()

    md = [
        "# 🌌 HERMES AGENT & JARVIS · HOLOGRAPHIC LONG-TERM MEMORY VAULT",
        f"*Ultima sincronizzazione automatica: {time.strftime('%Y-%m-%d %H:%M:%S')}*\n",
        "Questo file mantiene la memoria persistente infinita di Hermes Agent e JARVIS, sincronizzata con SQLite Vector/FTS.\n"
    ]

    current_cat = ""
    for cat, topic, fact, imp, dt in rows:
        if cat != current_cat:
            current_cat = cat
            md.append(f"\n## 📂 Categoria: `{cat}`\n")
        stars = "★" * min(5, imp)
        md.append(f"- **{topic}** `{stars}`: {fact} *(Registrato: {dt})*")

    with open(VAULT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(md))

# Initialize on module load
init_memory()

if __name__ == "__main__":
    print(f"✓ Hermes LTM Engine initialized! Memory DB: {MEMORY_DB}")
    print(f"✓ Holographic Vault: {VAULT_MD}")
    test_res = get_holographic_memory_context("Parlami del gioco EBGS e delle tariffe sgomberi")
    print(test_res)
