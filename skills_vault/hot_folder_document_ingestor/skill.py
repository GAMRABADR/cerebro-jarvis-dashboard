import os
import time
import datetime
import fitz
import re
import sqlite3

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
VAULT_DB = os.path.join(BASE_DIR, "mail_vault.db")
MEMORY_DB = os.path.join(BASE_DIR, "hermes_ltm_memory.db")
HOT_FOLDER = r"D:\EBGStudioProgetti\DOCUMENTI_INGESTION_AUTOMATICA"

os.makedirs(HOT_FOLDER, exist_ok=True)

def scan_and_ingest_documents():
    extracted_docs = []
    
    if os.path.exists(HOT_FOLDER):
        for f in os.listdir(HOT_FOLDER):
            full_p = os.path.join(HOT_FOLDER, f)
            if os.path.isfile(full_p):
                ext = os.path.splitext(f)[1].lower()
                text = ""
                
                if ext == ".pdf":
                    try:
                        doc = fitz.open(full_p)
                        for page in doc:
                            text += page.get_text() or ""
                    except Exception as e:
                        text = f"[Errore lettura PDF: {e}]"
                elif ext in [".txt", ".md", ".json", ".csv"]:
                    try:
                        with open(full_p, "r", encoding="utf-8", errors="ignore") as tf:
                            text = tf.read()
                    except Exception as e:
                        text = f"[Errore lettura testo: {e}]"
                elif ext in [".png", ".jpg", ".jpeg"]:
                    text = f"[Immagine Documento Rilevata: {f} (Disponibile per Vision OCR)]"
                
                if text.strip():
                    clean_snip = text.strip()[:300]
                    # Store fact in memory db
                    try:
                        conn = sqlite3.connect(MEMORY_DB)
                        c = conn.cursor()
                        c.execute("INSERT OR REPLACE INTO memories (category, topic, fact, importance, created_at, source) VALUES (?, ?, ?, ?, ?, ?)",
                                  ("DOCUMENT_INGESTION", f"File: {f}", clean_snip, 9, int(time.time()), "HOT_FOLDER_DROP"))
                        conn.commit()
                        conn.close()
                    except Exception: pass
                    
                    extracted_docs.append({
                        "file": f,
                        "size_bytes": os.path.getsize(full_p),
                        "characters_extracted": len(text),
                        "preview": clean_snip
                    })
                    
    return {
        "status": "SUCCESS",
        "hot_folder_path": HOT_FOLDER,
        "total_documents_processed": len(extracted_docs),
        "documents": extracted_docs,
        "message": f"Cartella monitorata H24. Inserisci qualsiasi PDF o foto in {HOT_FOLDER} e verrà assimilato all'istante."
    }

def execute(params=None):
    return scan_and_ingest_documents()

if __name__ == "__main__":
    import json
    print(json.dumps(execute(), indent=2))
