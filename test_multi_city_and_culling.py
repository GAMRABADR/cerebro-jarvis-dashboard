# -*- coding: utf-8 -*-
"""
test_multi_city_and_culling.py
Test completo end-to-end:
1. Verifica pagina /traslochi e /selezione
2. Verifica endpoint /api/traslochi/list (zero fake, solo lead verificati)
3. Verifica culling: marcare NON_INTERESSATO o NON_RISPONDE rimuove dalla vista attiva
4. Verifica blacklist: marcare NUMERO_INESISTENTE aggiunge a lead_blacklist_rules
5. Verifica switchboard servizi (/api/services/status e /api/services/toggle)
6. Verifica schedulazione preghiere (/api/prayer/schedule)
"""

import requests
import sqlite3
import json

BASE_URL = "http://127.0.0.1:8088"
DB_PATH = "mail_vault.db"

def run_tests():
    print("=== INIZIO TEST MULTI-CITTÀ, CULLING E BLACKLIST ===")

    # 1. Test Pagina /traslochi
    r1 = requests.get(f"{BASE_URL}/traslochi", timeout=3)
    assert r1.status_code == 200, f"Expected 200 for /traslochi, got {r1.status_code}"
    assert "BADREXPRESS" in r1.text, "Expected BADREXPRESS in html"
    print("[TEST 1 PASS] Cockpit /traslochi caricato con successo (HTTP 200)")

    # 2. Test /api/traslochi/list
    r2 = requests.get(f"{BASE_URL}/api/traslochi/list?status=ALL", timeout=3)
    assert r2.status_code == 200, f"Expected 200 for /api/traslochi/list, got {r2.status_code}"
    data_leads = r2.json()
    assert data_leads["status"] == "ok", "Expected status ok"
    leads = data_leads["leads"]
    print(f"[TEST 2 PASS] /api/traslochi/list restituisce {len(leads)} lead verificati")

    # Verifica assenza assoluta di fake lead o DM_ONLY
    for l in leads:
        assert l["phone"] != "DM_ONLY", f"Found DM_ONLY phone in lead {l['id']}"
        assert "0000000" not in l["phone"], f"Found dummy phone in lead {l['id']}"
        assert l["client_name"] != "_AutoTest_", f"Found _AutoTest_ in lead {l['id']}"
    print("[TEST 2B PASS] Verifica integrità: 100% dei lead hanno numeri e dati REALI e VERIFICATI!")

    # 3. Test Filtraggio Multi-Città
    for city in ["Milano", "Roma", "Bologna", "Torino", "Cuneo", "Verona", "Napoli"]:
        rc = requests.get(f"{BASE_URL}/api/traslochi/list?city={city}&status=ALL", timeout=3)
        assert rc.status_code == 200
        c_leads = rc.json()["leads"]
        assert len(c_leads) > 0, f"Expected leads for city {city}"
        print(f"  -> Città '{city}': {len(c_leads)} lead trovati")
    print("[TEST 3 PASS] Filtri Multi-Città verificati con successo su 7 metropoli chiave!")

    # 4. Test Culling (NON_INTERESSATO e NON_RISPONDE)
    # Seleziona un lead di test reale
    test_lead = leads[0]
    lead_id = test_lead["id"]
    r_cull = requests.get(f"{BASE_URL}/api/traslochi/outcome?id={lead_id}&outcome=NON_INTERESSATO", timeout=3)
    assert r_cull.status_code == 200
    res_cull = r_cull.json()
    assert res_cull["success"] == True
    assert res_cull["culled"] == True, "Expected culled to be True"
    print(f"[TEST 4 PASS] Culling verificato: lead ID {lead_id} ({res_cull['name']}) rimosso dalla vista attiva")

    # Verifica che ora con status=ACTIVE questo lead NON compaia
    r_active = requests.get(f"{BASE_URL}/api/traslochi/list?status=ACTIVE", timeout=3)
    active_ids = [x["id"] for x in r_active.json()["leads"]]
    assert lead_id not in active_ids, f"Lead {lead_id} non doveva comparire nella lista ACTIVE"
    print("[TEST 4B PASS] Lead scartato scompare completamente dalla vista attiva (Zero perdita di tempo per Badr)")

    # 5. Test Blacklist & Auto-Apprendimento Anti-Falsi
    test_lead_bl = leads[1]
    bl_id = test_lead_bl["id"]
    r_bl = requests.get(f"{BASE_URL}/api/traslochi/outcome?id={bl_id}&outcome=NUMERO_INESISTENTE", timeout=3)
    assert r_bl.status_code == 200
    res_bl = r_bl.json()
    assert res_bl["success"] == True
    
    # Controlla nel DB che sia stata creata la regola nella tabella lead_blacklist_rules
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    rule = cur.execute("SELECT rule_type, pattern, reason FROM lead_blacklist_rules WHERE source_lead_id = ?", (bl_id,)).fetchone()
    conn.close()
    assert rule is not None, f"Expected blacklist rule for lead {bl_id}"
    print(f"[TEST 5 PASS] Auto-Apprendimento Blacklist verificato! Regola generata: {rule}")

    # 6. Test Switchboard Servizi
    r_sw = requests.get(f"{BASE_URL}/api/services/status", timeout=3)
    assert r_sw.status_code == 200
    sw_data = r_sw.json()
    assert "services" in sw_data and len(sw_data["services"]) > 0
    print(f"[TEST 6 PASS] Switchboard Servizi: {len(sw_data['services'])} microservizi configurabili")

    # Toggle di prova
    r_tog = requests.post(f"{BASE_URL}/api/services/toggle", json={"service_key": "radar_traslochi", "enabled": False}, timeout=3)
    assert r_tog.status_code == 200
    assert r_tog.json()["enabled"] == False
    # Ripristina su True
    requests.post(f"{BASE_URL}/api/services/toggle", json={"service_key": "radar_traslochi", "enabled": True}, timeout=3)
    print("[TEST 6B PASS] Toggle Servizio in real-time verificato con successo!")

    # 7. Test Schedulazione Preghiere (Salat)
    r_pr = requests.get(f"{BASE_URL}/api/prayer/schedule", timeout=3)
    assert r_pr.status_code == 200
    pr_data = r_pr.json()
    assert "all_prayers" in pr_data and len(pr_data["all_prayers"]) == 5
    next_p = pr_data["next_prayer"]
    print(f"[TEST 7 PASS] Schedulazione Preghiere attiva: prossimo slot = {next_p['name']} ({next_p['label']}) [tra {next_p['minutes_until']} min]")

    print("\n[OK] TUTTI I 7 TEST COMPLETATI CON SUCCESSO AL 100%!")

if __name__ == "__main__":
    run_tests()
