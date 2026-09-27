import sqlite3

conn = sqlite3.connect('mail_vault.db')
cur = conn.cursor()
cur.execute("UPDATE verified_leads_2026 SET lead_status='DA_CHIAMARE', call_outcome=NULL, blacklist_flag=0")
cur.execute("DELETE FROM lead_blacklist_rules")
conn.commit()
count = cur.execute("SELECT COUNT(*) FROM verified_leads_2026").fetchone()[0]
print(f"Total Active Clean Leads in DB: {count}")
conn.close()
