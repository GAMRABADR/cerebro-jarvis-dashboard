import sqlite3
import os
import time
import datetime
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

def get_user_identity_dossier():
    try:
        conn = sqlite3.connect(MEMORY_DB)
        c = conn.cursor()
        c.execute("""
            SELECT full_name, alias, birth_date, birth_place, residence, phone, email, primary_roles, companies, active_projects, personal_preferences 
            FROM user_identity_dossier WHERE id=1
        """)
        row = c.fetchone()
        conn.close()
        if row:
            return {
                "full_name": row[0],
                "alias": row[1],
                "birth_date": row[2],
                "birth_place": row[3],
                "residence": row[4],
                "phone": row[5],
                "email": row[6],
                "primary_roles": row[7],
                "companies": row[8],
                "active_projects": row[9],
                "personal_preferences": row[10]
            }
    except Exception as e:
        print(f"[Dossier Read Err]: {e}")
    return {
        "full_name": "Badr El Ouariti",
        "alias": "Ingegner Badr / EB",
        "birth_date": "07/01/1988",
        "birth_place": "Marocco",
        "fiscal_code": "LRTBDR88A07Z330L",
        "residence": "Via San Vitale 187/189, 40026 Imola (BO)",
        "phone": "+39 388 870 3508",
        "email": "badraudi@gmail.com",
        "primary_roles": "Fondatore BadrExpress.com & EBGStudio (AI & Software Architect, Programmatore PLC Siemens S7-1200 / CNC)",
        "partner": "Pietro (PietroTraslochi.com - Tel: +39 328 426 3554)",
        "companies": "BadrExpress.com, PietroTraslochi.com, EBGStudio",
        "active_projects": "EBGS Survival MMO (Steam AppID: 2886940), B2B Sgomberi Immobiliari Bologna/Imola H24",
        "personal_preferences": "Massima efficienza, risposte dirette, orientamento al business e zero preamboli."
    }

def extract_and_update_biography(prompt):

    p_low = prompt.lower()
    updated_fields = {}
    
    # 1. Detect Birth Date
    m_birth = re.search(r'(?:sono nato il|data di nascita(?:\s+è)?|mio compleanno(?:\s+è)?|nato il)\s+([0-9]{1,2}[/\-.][0-9]{1,2}[/\-.][0-9]{2,4}|[0-9]{1,2}\s+[a-zA-Zàèéìòù]+\s+[0-9]{4}|[0-9]{1,2}\s+[a-zA-Zàèéìòù]+)', prompt, re.IGNORECASE)
    if m_birth:
        b_date = m_birth.group(1).strip()
        updated_fields["birth_date"] = b_date
        store_memory("USER_BIOGRAPHY", "Data di Nascita Proprietario", f"La data di nascita ufficiale dell'Ingegner Badr è {b_date}.", importance=10)

    # 2. Detect Birth Place
    m_place = re.search(r'(?:sono nato a|nato a|luogo di nascita(?:\s+è)?)\s+([A-Za-z\s]+?)(?:,|\.|$|e\s+vivo|il)', prompt, re.IGNORECASE)
    if m_place:
        b_place = m_place.group(1).strip().title()
        if len(b_place) > 2 and b_place.lower() not in ["un", "una", "casa", "ospedale"]:
            updated_fields["birth_place"] = b_place
            store_memory("USER_BIOGRAPHY", "Luogo di Nascita", f"L'Ingegner Badr è nato a {b_place}.", importance=10)

    # 3. Detect Residence
    m_res = re.search(r'(?:abito a|vivo a|risiedo a|residenza a)\s+([A-Za-z\s]+?)(?:,|\.|$)', prompt, re.IGNORECASE)
    if m_res:
        res_city = m_res.group(1).strip().title()
        if len(res_city) > 2:
            updated_fields["residence"] = res_city
            store_memory("USER_BIOGRAPHY", "Residenza", f"L'Ingegner Badr risiede a {res_city}.", importance=9)

    # Apply updates to SQL if any
    if updated_fields:
        for db_p in [MEMORY_DB, os.path.join(os.path.dirname(MEMORY_DB), "mail_vault.db")]:
            if os.path.exists(db_p):
                try:
                    conn = sqlite3.connect(db_p)
                    c = conn.cursor()
                    set_clauses = [f"{k}=?" for k in updated_fields.keys()]
                    vals = list(updated_fields.values()) + [datetime.datetime.now().isoformat()]
                    c.execute(f"UPDATE user_identity_dossier SET {', '.join(set_clauses)}, updated_at=? WHERE id=1", vals)
                    conn.commit()
                    conn.close()
                except Exception as e:
                    print(f"[Bio Update Err in {db_p}]: {e}")
        sync_to_markdown_vault()
        return updated_fields
    return None

def extract_and_update_family_tree(prompt):
    """Detects family relations and saves to family_tree_dossier"""
    # Matches patterns like: "El Ouariti Hanane è mia sorella", "Hanane è mia sorella", "Mio fratello è ..."
    m_rel = re.search(r'([A-Za-z\s]+?)\s+(?:è|e)\s+(?:mia|mio)\s+(sorella|fratello|padre|madre|mamma|papà|cugino|cugina|zio|zia|parente|moglie|figlio|figlia)', prompt, re.IGNORECASE)
    if m_rel:
        name = m_rel.group(1).replace("e.b.j.", "").replace("jarvis", "").replace("ricorda che", "").strip().title()
        relation = m_rel.group(2).strip().lower()
        if len(name) > 2 and name.lower() not in ["lui", "lei", "questo", "chi"]:
            for db_p in [MEMORY_DB, os.path.join(os.path.dirname(MEMORY_DB), "mail_vault.db")]:
                if os.path.exists(db_p):
                    try:
                        conn = sqlite3.connect(db_p)
                        c = conn.cursor()
                        c.execute("""
                            INSERT INTO family_tree_dossier (full_name, relation_degree, updated_at)
                            VALUES (?, ?, ?)
                            ON CONFLICT(full_name) DO UPDATE SET relation_degree=excluded.relation_degree, updated_at=excluded.updated_at
                        """, (name, relation.title(), datetime.datetime.now().isoformat()))
                        conn.commit()
                        conn.close()
                    except Exception as e:
                        print(f"[Family Tree Err]: {e}")
            store_memory("FAMILY_TREE", f"Parentela {name}", f"{name} è {relation} dell'Ingegner Badr El Ouariti.", importance=10)
            return {"name": name, "relation": relation}
    return None


def get_master_wiki_snippet(prompt=""):
    """Reads PROJECT_MASTER_WIKI.md and extracts relevant knowledge sections in real-time"""
    wiki_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "PROJECT_MASTER_WIKI.md")
    if not os.path.exists(wiki_file):
        return None
    try:
        with open(wiki_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        # If specific topic asked, extract relevant section
        p_low = prompt.lower()
        if any(k in p_low for k in ["wiki", "regol", "serviz", "catalogo", "hardware", "porte", "docker", "kali", "migliori", "storia", "progetto", "architettur"]):
            # Return high-density wiki summary
            sections = content.split("---")
            relevant_secs = []
            for sec in sections:
                if any(w in sec.lower() for w in p_low.split() if len(w) > 3):
                    relevant_secs.append(sec.strip())
            if relevant_secs:
                return "\n---\n".join(relevant_secs[:2])
            return content[:3000] # First 3000 chars of master wiki
    except Exception as e:
        print(f"[Wiki Snippet Err]: {e}")
    return None

def get_holographic_memory_context(prompt=""):
    # TIER 1: CORE STRUCTURED IDENTITY DOSSIER (Always injected at top)
    dossier = get_user_identity_dossier()
    
    if prompt:
        extract_and_update_biography(prompt)

    lines = [
        "\n==================================================================",
        "[TIER 1: IDENTITÀ UFFICIALE E.B.J. & PROPRIETARIO]",
        "• NOME AGENTE: E.B.J. (El Ouariti Badr Jarvis)",
        f"• PROPRIETARIO & COMANDANTE: {dossier['full_name']} (Alias: {dossier['alias']})",
        f"• DATA DI NASCITA: {dossier['birth_date']} | LUOGO: {dossier['birth_place']}",
        f"• RESIDENZA: {dossier['residence']} | TELEFONO: {dossier['phone']} | EMAIL: {dossier['email']}",
        f"• PARTNER OPERATIVO LOGISTICA: Pietro (PietroTraslochi.com - Tel: +39 328 426 3554)",
        f"• SITI & AZIENDE: BadrExpress.com & PietroTraslochi.com (Reperibilità H24/7)",
        f"• PROGETTI: {dossier['active_projects']}",
        "REGOLA ASSOLUTA: Tu sei E.B.J. (El Ouariti Badr Jarvis). Conosci alla perfezione Badr e Pietro e rispondi sempre con certezza.",
        "==================================================================",
        "\n[TIER 2 & 3: MEMORIE DI ECOSISTEMA RILEVANTI]:"
    ]

    # Dynamic Semantic & Keyword Retrieval for current prompt
    relevant = search_memory(prompt, limit=8) if prompt else []
    if relevant:
        for r in relevant:
            lines.append(f"• [{r['category']} - {r['topic']}]: {r['fact']}")
            
    # TIER 4: LIVE MASTER WIKI INGESTION
    wiki_snip = get_master_wiki_snippet(prompt)
    if wiki_snip:
        lines.append("\n==================================================================")
        lines.append("[TIER 4: ACCESSO DIRETTO ALLA WIKI MASTER PRIVATA (PROJECT_MASTER_WIKI.md)]")
        lines.append(wiki_snip)
        lines.append("==================================================================")
    
    lines.append("[FINE MEMORIA PERSISTENTE OLOGRAFICA]")
    return "\n".join(lines)

def auto_memorize_turn(user_prompt, ai_response):
    p_low = user_prompt.lower()
    # 1. Update biography if present
    extract_and_update_biography(user_prompt)

    # 2. General episodic memory storage
    if len(user_prompt) > 8 and not any(k in p_low for k in ["ciao", "chi sei", "status", "ora", "meteo"]):
        topic = "Interazione Utente"
        cat = "AUTO_CONVERSATION_MEMORY"
        if "trasloc" in p_low or "sgomber" in p_low:
            cat, topic = "BUSINESS_SGOMBERI", "Richiesta/Dettaglio Trasloco"
        elif "ue5" in p_low or "unreal" in p_low or "gioco" in p_low:
            cat, topic = "GAME_DEV", "Sviluppo Unreal Engine 5.8"
        elif "vps" in p_low or "server" in p_low or "n8n" in p_low:
            cat, topic = "INFRASTRUCTURE", "Configurazione Server/VPS"
        
        clean_fact = user_prompt.strip()[:200]
        store_memory(cat, topic, clean_fact, importance=6)



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
