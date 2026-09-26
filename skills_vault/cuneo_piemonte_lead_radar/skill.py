import os
import json
import sqlite3
import datetime
import urllib.parse
from skills_vault.EB_lead_quality_guard.skill import execute as guard_lead

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
VAULT_DB = os.path.join(BASE_DIR, "mail_vault.db")

CUNEO_CITIES = [
    "Cuneo", "Alba", "Bra", "Mondovì", "Fossano", "Savigliano", 
    "Saluzzo", "Borgo San Dalmazzo", "Busca", "Boves"
]

def get_verified_cuneo_leads(limit=15):
    leads = []
    if os.path.exists(VAULT_DB):
        try:
            conn = sqlite3.connect(VAULT_DB)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            query = """
                SELECT * FROM verified_leads_2026 
                WHERE city IN ('Cuneo', 'Alba', 'Bra', 'Mondovì', 'Fossano', 'Savigliano', 'Saluzzo', 'Piemonte')
                   OR phone LIKE '0171%' OR phone LIKE '0172%' OR phone LIKE '0173%' OR phone LIKE '0174%' OR phone LIKE '0175%'
                ORDER BY id DESC LIMIT ?
            """
            rows = c.execute(query, (limit,)).fetchall()
            leads = [dict(r) for r in rows]
            conn.close()
        except Exception as e:
            print(f"[Cuneo Lead DB Err]: {e}")
    return leads

def execute(params=None):
    params = params or {}
    target_city = params.get("city", "Cuneo")
    action = params.get("action", "scan")
    
    # 1. Fetch from Database Vault
    existing_leads = get_verified_cuneo_leads(20)
    
    # 2. If specific lead audit requested
    if "phone" in params:
        lead_audit = guard_lead({
            "name": params.get("name", "Cliente Cuneo"),
            "phone": params.get("phone", ""),
            "partenza": target_city,
            "email": params.get("email", ""),
            "date": datetime.datetime.now().strftime("%Y-%m-%d")
        })
        return {
            "status": "SUCCESS",
            "action": "audit_single",
            "audit": lead_audit,
            "city": target_city
        }

    # 3. Territory Scan Report
    return {
        "status": "SUCCESS",
        "action": "territory_radar",
        "territory": "Cuneo e Provincia (Granda)",
        "monitored_nodes": CUNEO_CITIES,
        "total_active_leads": len(existing_leads),
        "recent_leads": existing_leads[:5],
        "message": f"Radar Cuneo attivo: {len(existing_leads)} lead registrati su Cuneo, Alba, Bra e provincia."
    }
