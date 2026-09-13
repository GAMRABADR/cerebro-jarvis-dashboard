import os
import re
import time
import datetime
import urllib.parse
import sqlite3

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
VAULT_DB = os.path.join(BASE_DIR, "mail_vault.db")

def harvest_real_opportunities(zone="Bologna", category="sgombero"):
    clean_zone = zone.strip() if zone else "Bologna"
    cz_low = clean_zone.lower()
    
    leads = []
    try:
        conn = sqlite3.connect(VAULT_DB)
        c = conn.cursor()
        c.execute("""
            SELECT client_name, phone, city, service_type, volume_mq, estimated_budget, source, scraped_date, notes 
            FROM verified_leads_2026 
            ORDER BY id DESC
        """)
        rows = c.fetchall()
        conn.close()
        
        for r in rows:
            c_name, phone, city, service, v_mq, budget, source, s_date, notes = r
            if cz_low not in ["tutte", "tutto", "tutti", "italia", "nazionale"]:
                if cz_low not in city.lower():
                    continue
                    
            clean_p = re.sub(r'[^0-9]', '', phone)
            pitch_txt = (
                f"Salve {c_name}, la contattiamo da BadrExpress.com & PietroTraslochi.com "
                f"in merito alla richiesta di {service} a {city}.\n\n"
                f"Disponiamo di squadra operativa con piattaforma elevatrice e smaltimento certificato. "
                f"Preventivo stimato: circa € {budget:,.2f} con intervento immediato in 24-48 ore.\n\n"
                f"Contatti diretti: Ingegner Badr (+39 388 870 3508) | Pietro (+39 328 426 3554).\n"
                f"Possiamo visionare foto o concordare un sopralluogo su WhatsApp? Cordiali saluti."
            )
            
            p_msg = f"NUOVO LAVORO PIETRO TRASLOCHI\nCliente: {c_name}\nCitta: {city}\nServizio: {service}\nBudget: EUR {budget:,.2f}\nTel: {phone}\nData: {s_date}\nNote: {notes}"
            
            leads.append({
                "client_name": c_name,
                "phone": phone,
                "city": city,
                "service_type": service,
                "volume_mq": v_mq,
                "estimated_budget": budget,
                "source": source,
                "ad_date": s_date,
                "details": notes or f"{service} ({v_mq} mq) a {city}",
                "urgency": "ALTA (Richiesta verificata)",
                "whatsapp_url": f"https://wa.me/{clean_p}?text={urllib.parse.quote(pitch_txt)}",
                "pietro_dispatch_url": f"https://wa.me/393284263554?text={urllib.parse.quote(p_msg)}"
            })
    except Exception as e:
        print(f"[Harvest DB Err]: {e}")
        
    return {
        "status": "SUCCESS",
        "zone_searched": clean_zone,
        "leads_found": len(leads),
        "leads": leads,
        "total_estimated_pipeline": sum(l["estimated_budget"] for l in leads),
        "harvest_timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

def execute(params=None):
    params = params or {}
    z = params.get("zone") or params.get("city") or "Torino"
    cat = params.get("category", "sgombero")
    return harvest_real_opportunities(zone=z, category=cat)

if __name__ == "__main__":
    import sys, json
    tgt = sys.argv[1] if len(sys.argv) > 1 else "Torino"
    print(json.dumps(harvest_real_opportunities(tgt), indent=2))
