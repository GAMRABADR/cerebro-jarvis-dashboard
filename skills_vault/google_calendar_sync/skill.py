import time, sqlite3, os

KANBAN_DB = r"D:\EBGStudioProgetti\Oracle-VPS and EBGStudio\cerebro-jarvis-dashboard\hermes_kanban.db"

def execute(params=None):
    params = params or {}
    title = params.get("title", "Cantiere Trasloco Milano")
    data_lavoro = params.get("date", time.strftime("%Y-%m-%d"))
    note = params.get("note", "Squadra 2 operatori assegnati")
    
    try:
        conn = sqlite3.connect(KANBAN_DB)
        c = conn.cursor()
        task_id = f"cal_{int(time.time())}"
        c.execute("""
            INSERT INTO kanban_tasks (id, board, lane, title, description, assignee, created_at, updated_at)
            VALUES (?, 'calendar', 'todo', ?, ?, 'Badr', datetime('now'), datetime('now'))
        """, (task_id, f"📅 {title} ({data_lavoro})", note))
        conn.commit()
        conn.close()
        
        return {
            "status": "SUCCESS",
            "event_id": task_id,
            "title": title,
            "date": data_lavoro,
            "message": f"Evento '{title}' salvato in agenda per il {data_lavoro}."
        }
    except Exception as e:
        return {"status": "ERROR", "message": f"Errore calendario: {str(e)}"}

if __name__ == "__main__":
    print(execute())
