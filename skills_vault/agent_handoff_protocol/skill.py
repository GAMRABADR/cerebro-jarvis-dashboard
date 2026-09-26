import os
import json
import sqlite3
import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, "autonomous_task_queue.db")

def init_handoff_table():
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS agent_handoffs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT,
                from_agent TEXT,
                to_agent TEXT,
                context_payload TEXT,
                status TEXT,
                created_at TEXT
            )
        """)
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[Handoff Init Err]: {e}")

def execute(params=None):
    params = params or {}
    from_agent = params.get("from_agent", "hermes")
    to_agent = params.get("to_agent", "b2b_pitcher")
    task_id = params.get("task_id", f"task_{int(datetime.datetime.now().timestamp())}")
    payload = params.get("payload") or {"task": "Followup preventivo lead", "priority": "HIGH"}
    
    init_handoff_table()
    
    now_str = datetime.datetime.now().isoformat()
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            INSERT INTO agent_handoffs (task_id, from_agent, to_agent, context_payload, status, created_at)
            VALUES (?, ?, ?, ?, 'HANDOFF_COMPLETED', ?)
        """, (task_id, from_agent, to_agent, json.dumps(payload), now_str))
        conn.commit()
        conn.close()
    except Exception as e:
        return {"status": "ERROR", "message": str(e)}

    return {
        "status": "SUCCESS",
        "skill": "agent_handoff_protocol",
        "task_id": task_id,
        "from": from_agent,
        "to": to_agent,
        "payload": payload,
        "transition": f"{from_agent.upper()} ➡️ {to_agent.upper()}",
        "message": f"Passaggio consegne atomico completato: {from_agent} -> {to_agent} per #{task_id}."
    }
