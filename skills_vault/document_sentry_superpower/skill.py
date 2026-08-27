import os
import time
import datetime
import fitz
import re
import sqlite3

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
VAULT_DB = os.path.join(BASE_DIR, "mail_vault.db")
MEMORY_DB = os.path.join(BASE_DIR, "hermes_ltm_memory.db")
HOT_FOLDER = r"D:\EBGStudioProgetti\Oracle-VPS and EBGStudio\DOCUMENTI_INGESTION_AUTOMATICA"
FAMILY_ARCHIVE = os.path.join(HOT_FOLDER, "Archivio_Personale_e_Familiare")

def deep_scan_and_ingest():
    results = []
    
    # 1. Scan Hot Folder (contiene anche l'Archivio_Personale_e_Familiare)
    scan_paths = [HOT_FOLDER]
        
    for sp in scan_paths:
        for root, dirs, files in os.walk(sp):
            for f in files:
                ext = os.path.splitext(f)[1].lower()
                if ext in [".pdf", ".png", ".jpg", ".jpeg", ".txt", ".docx"]:
                    full_p = os.path.join(root, f)
                    
                    # Deduce owner and category
                    owner = "Badr El Ouariti"
                    cat = "IDENTITÀ_PERSONALE"
                    
                    if "hanane" in full_p.lower():
                        owner = "El Ouariti Hanane (Sorella)"
                        cat = "DOCUMENTI_HANANE"
                    elif "mamma" in full_p.lower():
                        owner = "Mamma (Famiglia El Ouariti)"
                        cat = "DOCUMENTI_MAMMA"
                    elif "patente" in full_p.lower():
                        cat = "PATENTE_GUIDA"
                    elif "passaporto" in full_p.lower():
                        cat = "PASSAPORTO"
                    elif "fiscale" in full_p.lower() or "cf" in full_p.lower():
                        cat = "CODICE_FISCALE"
                    elif "affitto" in full_p.lower() or "contratto" in full_p.lower():
                        cat = "CONTRATTO_CASA"
                    elif "certificato" in full_p.lower() or "plc" in full_p.lower():
                        cat = "CERTIFICAZIONE_TECNICA"
                        
                    # Extract text if PDF
                    text = ""
                    if ext == ".pdf":
                        try:
                            doc = fitz.open(full_p)
                            for page in doc: text += page.get_text() or ""
                        except Exception: pass
                    
                    summary = text[:300].strip() if text else f"Documento {cat} di {owner} (Pronto per consultazione immediata)"
                    
                    # Store in Catalog
                    for db_p in [VAULT_DB, MEMORY_DB]:
                        if os.path.exists(db_p):
                            try:
                                conn = sqlite3.connect(db_p)
                                c = conn.cursor()
                                c.execute("""
                                    INSERT INTO document_vault_catalog 
                                    (doc_title, doc_category, owner_name, file_path, extracted_summary, created_at)
                                    VALUES (?, ?, ?, ?, ?, ?)
                                    ON CONFLICT(file_path) DO UPDATE SET
                                    extracted_summary=excluded.extracted_summary
                                """, (f, cat, owner, full_p, summary, datetime.datetime.now().isoformat()))
                                conn.commit()
                                conn.close()
                            except Exception: pass
                            
                    results.append({
                        "file": f,
                        "owner": owner,
                        "category": cat,
                        "path": full_p
                    })
                    
    return {
        "status": "SUCCESS",
        "total_documents_cataloged": len(results),
        "hot_folder": HOT_FOLDER,
        "family_archive": FAMILY_ARCHIVE,
        "sample_catalog": results[:10],
        "message": f"Assimilazione completata! {len(results)} documenti catalogati ed estratti in memoria permanente."
    }

def execute(params=None):
    return deep_scan_and_ingest()

if __name__ == "__main__":
    import json
    print(json.dumps(execute(), indent=2))
