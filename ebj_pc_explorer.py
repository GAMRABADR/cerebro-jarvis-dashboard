"""
==============================================================================
EBJ PC FILE & FOLDER EXPLORER (NATIVE WORKSTATION AGENT)
==============================================================================
Modulo specialistico ad altissima efficienza per esplorare, navigare,
cercare file e cartelle, aprire Esplora Risorse ed elencare contenuti
del PC per l'Ingegnere Badr.

Supporta:
  - Apertura istantanea di cartelle e percorsi nel Desktop reale (explorer.exe)
  - Scansione e listing veloce di qualsiasi directory su C: e D:
  - Ricerca intelligente di file per nome, estensione o parola chiave (glob fast)
  - Scorciatoie veloci in linguaggio naturale (es. "esplora desktop", "esplora progetti",
    "cosa c'è in download", "cerca file fattura", "mostra cartella immagini")
  - Statistiche immediate: dimensione cartella, numero file, ultimo file modificato
==============================================================================
"""
from __future__ import annotations
import os
import sys
import glob
import time
import subprocess
from typing import Dict, Any, List, Optional

USER_PROFILE = os.environ.get("USERPROFILE", r"C:\Users\Admin")

KNOWN_LOCATIONS = {
    "desktop": os.path.join(USER_PROFILE, "Desktop"),
    "scrivania": os.path.join(USER_PROFILE, "Desktop"),
    "download": os.path.join(USER_PROFILE, "Downloads"),
    "downloads": os.path.join(USER_PROFILE, "Downloads"),
    "scaricati": os.path.join(USER_PROFILE, "Downloads"),
    "documenti": os.path.join(USER_PROFILE, "Documents"),
    "documents": os.path.join(USER_PROFILE, "Documents"),
    "immagini": os.path.join(USER_PROFILE, "Pictures"),
    "pictures": os.path.join(USER_PROFILE, "Pictures"),
    "foto": os.path.join(USER_PROFILE, "Pictures"),
    "musica": os.path.join(USER_PROFILE, "Music"),
    "video": os.path.join(USER_PROFILE, "Videos"),
    "progetti": r"D:\EBGStudioProgetti",
    "ebg": r"D:\EBGStudioProgetti",
    "ebgstudio": r"D:\EBGStudioProgetti",
    "oracle": r"D:\EBGStudioProgetti\Oracle-VPS and EBGStudio",
    "dashboard": r"D:\EBGStudioProgetti\Oracle-VPS and EBGStudio\cerebro-jarvis-dashboard",
    "disco c": r"C:\\",
    "disco d": r"D:\\",
    "disco e": r"E:\\",
    "c:": r"C:\\",
    "d:": r"D:\\",
    "e:": r"E:\\",
    "c": r"C:\\",
    "d": r"D:\\",
    "e": r"E:\\",
    "ylenia": r"E:\Foto_Ylenia",
    "foto ylenia": r"E:\Foto_Ylenia",
    "foto_ylenia": r"E:\Foto_Ylenia",
    "foto di ylenia": r"E:\Foto_Ylenia"
}

def resolve_target_path(query: str) -> str:
    """Risolve un testo o percorso naturale nel percorso assoluto su disco."""
    q_clean = query.lower().strip()
    # Rimuovi prefissi verbali comuni
    for prefix in [
        "esplora la cartella", "esplora cartella", "esplora il", "esplora",
        "apri la cartella", "apri cartella", "apri il percorso", "apri",
        "cosa c'è in", "cosa c'e in", "elenca", "mostra cartella", "mostra i file in"
    ]:
        if q_clean.startswith(prefix):
            q_clean = q_clean[len(prefix):].strip()
            break

    # 1. Match diretto nei percorsi noti
    if q_clean in KNOWN_LOCATIONS:
        return KNOWN_LOCATIONS[q_clean]
        
    for k, p in KNOWN_LOCATIONS.items():
        if k in q_clean:
            return p

    # 2. Se è già un percorso valido
    if os.path.exists(query.strip()):
        return query.strip()

    # 3. Tentativo di percorso parziale
    if ":\\" in query or ":/" in query:
        cleaned_path = query.strip().replace('"', '')
        if os.path.exists(cleaned_path):
            return cleaned_path

    # Fallback predefinito: Desktop
    return KNOWN_LOCATIONS["desktop"]

def open_in_explorer(target_path: str) -> Dict[str, Any]:
    """Apre la cartella specificata nella sessione grafica di Windows."""
    t0 = time.perf_counter()
    if not os.path.exists(target_path):
        return {
            "status": "not_found",
            "message": f"Il percorso '{target_path}' non esiste sul sistema."
        }

    try:
        subprocess.Popen(["explorer.exe", target_path])
        lat = (time.perf_counter() - t0) * 1000.0
        return {
            "status": "success",
            "action": "open_explorer",
            "path": target_path,
            "latency_ms": round(lat, 2),
            "message": f"Cartella '{os.path.basename(target_path) or target_path}' aperta in Esplora Risorse."
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

def list_folder_contents(target_path: str, max_items: int = 25) -> Dict[str, Any]:
    """Elenca i file e le sottocartelle di un percorso con dimensioni e date."""
    t0 = time.perf_counter()
    if not os.path.exists(target_path):
        return {
            "status": "not_found",
            "message": f"Percorso non trovato: {target_path}"
        }

    items = []
    total_files = 0
    total_dirs = 0

    try:
        with os.scandir(target_path) as it:
            for entry in it:
                try:
                    is_d = entry.is_dir(follow_symlinks=False)
                    if is_d:
                        total_dirs += 1
                    else:
                        total_files += 1

                    if len(items) < max_items:
                        st = entry.stat(follow_symlinks=False)
                        items.append({
                            "name": entry.name,
                            "is_dir": is_d,
                            "size_kb": 0 if is_d else round(st.st_size / 1024, 1),
                            "modified": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(st.st_mtime))
                        })
                except Exception:
                    continue

        # Ordina: prima le cartelle, poi i file
        items.sort(key=lambda x: (not x["is_dir"], x["name"].lower()))
        lat = (time.perf_counter() - t0) * 1000.0

        return {
            "status": "success",
            "path": target_path,
            "folder_name": os.path.basename(target_path) or target_path,
            "total_directories": total_dirs,
            "total_files": total_files,
            "items": items,
            "latency_ms": round(lat, 2)
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

def search_files_on_pc(query_term: str, search_root: Optional[str] = None, max_results: int = 15) -> Dict[str, Any]:
    """Cerca file o cartelle contenenti la parola chiave a partire da un percorso chiave."""
    t0 = time.perf_counter()
    root = search_root or KNOWN_LOCATIONS["progetti"]
    if not os.path.exists(root):
        root = KNOWN_LOCATIONS["desktop"]

    q_term = query_term.lower().strip()
    found = []

    # Scansione controllata con profondità limitata per non rallentare
    for dirpath, dirnames, filenames in os.walk(root):
        # Salta cartelle pesanti
        dirnames[:] = [d for d in dirnames if d not in [".git", "node_modules", "target", "Intermediate", "Saved", ".cache"]]
        
        for fn in filenames:
            if q_term in fn.lower():
                full = os.path.join(dirpath, fn)
                try:
                    st = os.stat(full)
                    found.append({
                        "filename": fn,
                        "path": full,
                        "size_kb": round(st.st_size / 1024, 1),
                        "modified": time.strftime("%Y-%m-%d %H:%M", time.localtime(st.st_mtime))
                    })
                    if len(found) >= max_results:
                        break
                except Exception:
                    pass
        if len(found) >= max_results:
            break

    lat = (time.perf_counter() - t0) * 1000.0
    return {
        "status": "success",
        "search_term": query_term,
        "search_root": root,
        "count": len(found),
        "results": found,
        "latency_ms": round(lat, 2)
    }

def execute_pc_explorer(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Handler principale compatibile con Ability Registry & Voice Router."""
    query = payload.get("query") or payload.get("path") or ""
    action = payload.get("action", "explore")

    target = resolve_target_path(query)

    # 1. Se l'intento è cercare file
    if any(k in query.lower() for k in ["cerca file", "trova file", "dove si trova"]):
        # Estrai termine di ricerca
        words = query.lower().split()
        term = words[-1] if words else "file"
        for idx, w in enumerate(words):
            if w in ["file", "trova", "cerca"] and idx + 1 < len(words):
                term = words[idx + 1]
                break
        res = search_files_on_pc(query_term=term)
        count = res.get("count", 0)
        res["spoken_response"] = f"Ho trovato {count} file corrispondenti a '{term}', Badr."
        return res

    # 2. Se l'intento è aprire la finestra Esplora Risorse
    open_win = any(k in query.lower() for k in ["apri", "apri cartella", "mostrami", "esplora"]) or action == "open"
    if open_win:
        open_res = open_in_explorer(target)

    # 3. Listing del contenuto per la risposta parlata e visiva
    list_res = list_folder_contents(target)
    
    folder_name = os.path.basename(target) or target
    f_count = list_res.get("total_files", 0)
    d_count = list_res.get("total_directories", 0)
    
    spoken = f"Ho aperto la cartella {folder_name} su schermo. Contiene {f_count} file e {d_count} sottocartelle, Badr."
    list_res["spoken_response"] = spoken
    list_res["opened_in_explorer"] = True
    return list_res
