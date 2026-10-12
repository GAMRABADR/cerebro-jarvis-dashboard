"""
==============================================================================
EBJ TEMP EMAIL MANAGER (DISPOSABLE INBOX & AUTOMATION)
==============================================================================
Modulo autonomo per la creazione e consultazione istantanea di caselle email
temporanee e usa-e-getta (Disposable Mailboxes) per test, bypass registrazioni,
ricezione di codici OTP / token di verifica e inoltro automatico.

Provider: Mail.tm REST API (affidabile, HTTPS senza Captcha, instant token)
Fallback: Mail.gw
==============================================================================
"""
from __future__ import annotations
import os
import sys
import time
import uuid
import random
import string
import requests
from typing import Dict, Any, List, Optional

BASE_URL = "https://api.mail.tm"
TIMEOUT = 10

class TempEmailManager:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self._current_account: Optional[Dict[str, Any]] = None

    def get_domains(self) -> List[str]:
        """Recupera la lista dei domini attualmente disponibili."""
        try:
            r = requests.get(f"{self.base_url}/domains", timeout=TIMEOUT)
            if r.status_code == 200:
                data = r.json()
                members = data.get("hydra:member", [])
                return [m["domain"] for m in members if m.get("isActive", True)]
        except Exception as e:
            print(f"[TempMail] Errore fetch domini: {e}")
        return ["maxxspace.com"]

    def create_account(self, username_prefix: Optional[str] = None, password: Optional[str] = None) -> Dict[str, Any]:
        """
        Crea un account email temporaneo usa-e-getta.
        Restituisce l'indirizzo email, la password generata e il token di autenticazione JWT.
        """
        domains = self.get_domains()
        if not domains:
            return {"status": "error", "message": "Nessun dominio temporaneo disponibile al momento."}

        domain = domains[0]
        rand_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        
        prefix = username_prefix or "ebj_temp"
        prefix = "".join(c for c in prefix.lower() if c.isalnum() or c in "_-")
        if not prefix:
            prefix = "ebj"
            
        address = f"{prefix}_{rand_suffix}@{domain}"
        pwd = password or (''.join(random.choices(string.ascii_letters + string.digits + "!#$", k=12)))

        try:
            # 1. Registrazione account
            reg_resp = requests.post(
                f"{self.base_url}/accounts",
                json={"address": address, "password": pwd},
                timeout=TIMEOUT
            )
            if reg_resp.status_code not in (200, 201):
                return {
                    "status": "error",
                    "code": reg_resp.status_code,
                    "message": f"Errore creazione account: {reg_resp.text}"
                }
            acc_data = reg_resp.json()

            # 2. Ottieni JWT token
            token_resp = requests.post(
                f"{self.base_url}/token",
                json={"address": address, "password": pwd},
                timeout=TIMEOUT
            )
            token = token_resp.json().get("token") if token_resp.status_code == 200 else None

            account_info = {
                "status": "success",
                "email": address,
                "password": pwd,
                "account_id": acc_data.get("id"),
                "token": token,
                "created_at": time.time(),
                "expires_info": "Valido fino a chiusura sessione / 7 giorni di inattività"
            }
            self._current_account = account_info
            return account_info

        except Exception as e:
            return {"status": "error", "error": str(e)}

    def check_messages(self, token: Optional[str] = None) -> Dict[str, Any]:
        """
        Controlla i messaggi ricevuti nella casella temporanea.
        """
        jwt_token = token or (self._current_account.get("token") if self._current_account else None)
        if not jwt_token:
            return {"status": "error", "message": "Token mancante o nessuna casella temporanea attiva."}

        headers = {"Authorization": f"Bearer {jwt_token}"}
        try:
            r = requests.get(f"{self.base_url}/messages", headers=headers, timeout=TIMEOUT)
            if r.status_code != 200:
                return {"status": "error", "code": r.status_code, "message": r.text}

            data = r.json()
            messages = data.get("hydra:member", [])
            
            clean_msgs = []
            for m in messages:
                clean_msgs.append({
                    "id": m.get("id"),
                    "from": m.get("from", {}).get("address"),
                    "from_name": m.get("from", {}).get("name"),
                    "subject": m.get("subject"),
                    "intro": m.get("intro"),
                    "created_at": m.get("createdAt"),
                    "has_attachments": m.get("hasAttachments", False)
                })

            return {
                "status": "success",
                "count": len(clean_msgs),
                "messages": clean_msgs
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def get_message_content(self, message_id: str, token: Optional[str] = None) -> Dict[str, Any]:
        """Recupera il testo completo / HTML di un messaggio specifico."""
        jwt_token = token or (self._current_account.get("token") if self._current_account else None)
        if not jwt_token:
            return {"status": "error", "message": "Token mancante."}

        headers = {"Authorization": f"Bearer {jwt_token}"}
        try:
            r = requests.get(f"{self.base_url}/messages/{message_id}", headers=headers, timeout=TIMEOUT)
            if r.status_code == 200:
                m = r.json()
                return {
                    "status": "success",
                    "id": m.get("id"),
                    "from": m.get("from", {}).get("address"),
                    "subject": m.get("subject"),
                    "text": m.get("text"),
                    "html": m.get("html"),
                    "created_at": m.get("createdAt")
                }
            return {"status": "error", "code": r.status_code, "message": r.text}
        except Exception as e:
            return {"status": "error", "error": str(e)}

# Singleton
temp_email_manager = TempEmailManager()

def execute_temp_email(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Handler universale compatibile con EBJ Ability Registry."""
    action = payload.get("action", "create")
    if action == "create":
        prefix = payload.get("prefix")
        return temp_email_manager.create_account(username_prefix=prefix)
    elif action in ("check", "list_messages"):
        token = payload.get("token")
        return temp_email_manager.check_messages(token=token)
    elif action == "read":
        msg_id = payload.get("message_id")
        token = payload.get("token")
        if not msg_id:
            return {"status": "error", "message": "message_id obbligatorio per l'azione 'read'."}
        return temp_email_manager.get_message_content(msg_id, token=token)
    else:
        return {"status": "error", "message": f"Azione '{action}' non supportata."}
