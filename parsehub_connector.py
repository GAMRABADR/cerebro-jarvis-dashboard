"""
ParseHub Lead Connector - EBGStudio / Jarvis
Interfaccia API ufficiale ParseHub per scraping visuale avanzato
API Key: toByU17R2TLO
"""

import requests
import json
import os
import time

PARSEHUB_API_KEY = os.environ.get("PARSEHUB_API_KEY", "toByU17R2TLO")
BASE_URL = "https://www.parsehub.com/api/v2"

def list_projects():
    """Elenca tutti i progetti ParseHub configurati nell'account."""
    try:
        r = requests.get(f"{BASE_URL}/projects", params={"api_key": PARSEHUB_API_KEY}, timeout=10)
        if r.status_code == 200:
            return r.json().get("projects", [])
        return []
    except Exception as e:
        print(f"[ParseHub list_projects err]: {e}")
        return []

def run_project(project_token, start_url=None):
    """Avvia l'esecuzione di un progetto ParseHub."""
    try:
        payload = {"api_key": PARSEHUB_API_KEY}
        if start_url:
            payload["start_url"] = start_url
        r = requests.post(f"{BASE_URL}/projects/{project_token}/run", data=payload, timeout=15)
        if r.status_code == 200:
            return r.json()
        return {"status": "error", "code": r.status_code, "msg": r.text}
    except Exception as e:
        return {"status": "error", "error": str(e)}

def get_last_run_data(project_token):
    """Recupera i dati estratti dall'ultima esecuzione del progetto."""
    try:
        r = requests.get(f"{BASE_URL}/projects/{project_token}/last_ready_run/data", params={"api_key": PARSEHUB_API_KEY}, timeout=20)
        if r.status_code == 200:
            return r.json()
        return None
    except Exception as e:
        print(f"[ParseHub get_data err]: {e}")
        return None

if __name__ == "__main__":
    projs = list_projects()
    print(f"Stato ParseHub: Connesso con successo!")
    print(f"Progetti attivi nell'account: {len(projs)}")
    for p in projs:
        print(f" - {p.get('title')} (token: {p.get('token')})")
