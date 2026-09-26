import os
import json
import sqlite3
import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, "hermes_ltm_memory.db")

def init_blackboard_table():
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS agent_blackboard (
                key TEXT PRIMARY KEY,
                val TEXT,
                locked_by TEXT,
                updated_at TEXT
            )
        """)
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[Blackboard Init Err]: {e}")

def execute(params=None):
    params = params or {}
    action = params.get("action", "read") # read, write, claim, release
    key = params.get("key", "active_lead_channel")
    val = params.get("val")
    agent_id = params.get("agent_id", "hermes")
    
    init_blackboard_table()
    now_str = datetime.datetime.now().isoformat()
    
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        if action == "write":
            val_str = json.dumps(val) if isinstance(val, (dict, list)) else str(val)
            c.execute("""
                INSERT INTO agent_blackboard (key, val, locked_by, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET val=excluded.val, updated_at=excluded.updated_at
            """, (key, val_str, agent_id, now_str))
            conn.commit()
            conn.close()
            return {"status": "SUCCESS", "action": "write", "key": key, "agent_id": agent_id, "message": f"Dato scritto sulla lavagna: {key}"}

        elif action == "claim":
            # Atomically lock resource if not locked by someone else
            c.execute("SELECT locked_by FROM agent_blackboard WHERE key=?", (key,))
            row = c.fetchone()
            if row and row[0] and row[0] != agent_id:
                conn.close()
                return {"status": "LOCKED", "key": key, "locked_by": row[0], "message": f"Risorsa '{key}' già sotto lock da {row[0]}."}
            
            c.execute("""
                INSERT INTO agent_blackboard (key, val, locked_by, updated_at)
                VALUES (?, 'LOCKED', ?, ?)
                ON CONFLICT(key) DO UPDATE SET locked_by=?, updated_at=?
            """, (key, agent_id, now_str, agent_id, now_str))
            conn.commit()
            conn.close()
            return {"status": "SUCCESS", "action": "claim", "key": key, "locked_by": agent_id, "message": f"Lock acquisito con successo da {agent_id}."}

        else: # read
            c.execute("SELECT key, val, locked_by, updated_at FROM agent_blackboard ORDER BY updated_at DESC LIMIT 20")
            rows = c.fetchall()
            items = [{"key": r[0], "val": r[1], "locked_by": r[2], "updated_at": r[3]} for r in rows]
            conn.close()
            return {"status": "SUCCESS", "action": "read", "total_items": len(items), "blackboard": items}

    except Exception as e:
        return {"status": "ERROR", "message": str(e)}
