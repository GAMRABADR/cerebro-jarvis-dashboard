"""
==============================================================================
EBJ SUPREME ABILITY REGISTRY (PLUGGABLE SKILLS RUNTIME)
==============================================================================
Modulo di orchestrazione modulare per registrare, abilitare, disabilitare e
richiamare nuove abilità cognitive ed operative per l'agente EBJ senza mai
toccare o appesantire il server monolitico.

Supporta:
  - Dynamic Dispatch con prioritizzazione (Priority Queue per Tier)
  - Fast Memory Caching & Auto-Inizializzazione delle Abilità di Produzione:
      * Traduzione Istantanea Rust / Cloud
      * Creazione Account / Gmail con Consegna Credenziali a badraudi@gmail.com
      * Email Outreach ad Agenzie Immobiliari
      * Caselle Email Temporanee Usa-e-Getta (Mail.tm)
      * Operazioni Win32 & App Launch (JEV System Ops)
  - Tracciamento metriche di esecuzione (latenza, success rate, chiamate)
  - Hot Reload a runtime
==============================================================================
"""
from __future__ import annotations
import os
import sys
import time
import json
import logging
from typing import Dict, Any, Callable, Optional, List

logger = logging.getLogger("EBJ_Ability_Registry")

class Ability:
    def __init__(
        self,
        name: str,
        description: str,
        handler: Callable[[Dict[str, Any]], Dict[str, Any]],
        triggers: List[str] = None,
        tier: int = 1,
        enabled: bool = True
    ):
        self.name = name
        self.description = description
        self.handler = handler
        self.triggers = [t.lower() for t in (triggers or [])]
        self.tier = tier  # 0: Sub-1ms native/cache, 1: Fast Reflex, 2: Remote/Automation
        self.enabled = enabled
        self.call_count = 0
        self.total_latency_ms = 0.0

    def match(self, query: str) -> bool:
        if not self.enabled:
            return False
        q = query.lower()
        return any(t in q for t in self.triggers)

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        t0 = time.perf_counter()
        self.call_count += 1
        try:
            res = self.handler(payload)
            lat = (time.perf_counter() - t0) * 1000.0
            self.total_latency_ms += lat
            if isinstance(res, dict):
                res["ability_name"] = self.name
                res["ability_latency_ms"] = round(lat, 3)
            return res
        except Exception as e:
            lat = (time.perf_counter() - t0) * 1000.0
            return {
                "status": "error",
                "ability_name": self.name,
                "error": str(e),
                "spoken_response": f"Errore durante l'esecuzione dell'abilità {self.name}: {str(e)}",
                "ability_latency_ms": round(lat, 3)
            }

class AbilityRegistry:
    def __init__(self):
        self._abilities: Dict[str, Ability] = {}
        self._init_default_abilities()

    def register(self, ability: Ability) -> None:
        self._abilities[ability.name] = ability

    def get(self, name: str) -> Optional[Ability]:
        return self._abilities.get(name)

    def list_abilities(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": a.name,
                "description": a.description,
                "triggers_count": len(a.triggers),
                "tier": a.tier,
                "enabled": a.enabled,
                "calls": a.call_count,
                "avg_latency_ms": round(a.total_latency_ms / max(1, a.call_count), 2)
            }
            for a in self._abilities.values()
        ]

    def dispatch(self, query: str, payload: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        payload = payload or {}
        payload["query"] = query
        # Ordina per priorità di tier (Tier 0 prima di Tier 1, ecc.)
        sorted_abilities = sorted(self._abilities.values(), key=lambda a: a.tier)
        for ab in sorted_abilities:
            if ab.match(query):
                return ab.execute(payload)
        return None

    def _init_default_abilities(self) -> None:
        """Inizializza il catalogo delle abilità standard operative per l'agente EBJ."""
        # 1. Traduzione Multilingue Istantanea (Rust Apex / Cloud)
        try:
            from ebj_translation_gateway import ebj_translate
            def _handle_translate(payload: Dict[str, Any]) -> Dict[str, Any]:
                q = payload.get("query", "")
                text = payload.get("text") or q
                target = payload.get("target_lang") or payload.get("lang") or "en"
                res = ebj_translate(text=text, target_lang=target)
                spoken = f"Traduzione in {target.upper()}: {res.get('translated_text', '')}"
                res["spoken_response"] = spoken
                return res

            self.register(Ability(
                name="realtime_translation",
                description="Traduzione istantanea multilingue a bassa latenza con Rust Apex Cache e Google GTX / MyMemory",
                handler=_handle_translate,
                triggers=["traduci", "traduzione", "translate", "come si dice in"],
                tier=0
            ))
        except Exception as e:
            logger.warning(f"Abilità realtime_translation non caricata: {e}")

        # 2. Casella Email Temporanea Usa-e-Getta (Mail.tm)
        try:
            from ebj_temp_email_manager import execute_temp_email
            def _handle_temp_email(payload: Dict[str, Any]) -> Dict[str, Any]:
                res = execute_temp_email(payload)
                if res.get("status") == "success" and "email" in res:
                    res["spoken_response"] = f"Ho generato una casella email temporanea usa e getta: {res['email']}. Ricezione codici e OTP attiva."
                return res

            self.register(Ability(
                name="temp_email_generator",
                description="Creazione e consultazione istantanea di caselle email usa-e-getta senza Captcha (Mail.tm)",
                handler=_handle_temp_email,
                triggers=["email temporanea", "mail temporanea", "temp mail", "crea email usa e getta", "casella usa e getta", "temp email"],
                tier=1
            ))
        except Exception as e:
            logger.warning(f"Abilità temp_email_generator non caricata: {e}")

        # 3. Creazione Account / Gmail con Consegna a badraudi@gmail.com
        try:
            from ebj_gmail_account_creator import execute_gmail_creator
            def _handle_gmail_creator(payload: Dict[str, Any]) -> Dict[str, Any]:
                res = execute_gmail_creator(payload)
                if res.get("status") == "success":
                    person = res.get("person", "l'utente richiesto")
                    email = res.get("email", "")
                    res["spoken_response"] = f"Ho predisposto l'account per {person}: indirizzo {email}. Le credenziali complete sono state inviate alla tua email badraudi@gmail.com, Badr."
                return res

            self.register(Ability(
                name="gmail_account_creator",
                description="Generazione credenziali email/Google con recapito immediato e sicuro alla casella badraudi@gmail.com",
                handler=_handle_gmail_creator,
                triggers=["crea una gmail", "crea gmail", "crea account per", "crea una mail per", "registra gmail", "creami una gmail"],
                tier=1
            ))
        except Exception as e:
            logger.warning(f"Abilità gmail_account_creator non caricata: {e}")

        # 4. Email Outreach per Agenzie Immobiliari
        try:
            from ebj_real_estate_mailer import execute_real_estate_mailer
            def _handle_real_estate(payload: Dict[str, Any]) -> Dict[str, Any]:
                res = execute_real_estate_mailer(payload)
                if res.get("status") == "success":
                    res["spoken_response"] = "Proposta di partnership e collaborazione inviata con successo all'agenzia immobiliare. Ti ho recapitato il riepilogo su badraudi@gmail.com, Badr."
                elif res.get("status") == "need_recipient":
                    res["spoken_response"] = "Dimmi l'indirizzo email o il nome dell'agenzia immobiliare a cui vuoi che invii la proposta di collaborazione."
                return res

            self.register(Ability(
                name="real_estate_outreach",
                description="Invio email commerciali di convenzione traslochi/sgomberi ad agenzie immobiliari con notifica a Badr",
                handler=_handle_real_estate,
                triggers=["manda email a immobiliari", "invia mail immobiliare", "email agenzia immobiliare", "contatta immobiliari", "invia alle agenzie"],
                tier=1
            ))
        except Exception as e:
            logger.warning(f"Abilità real_estate_outreach non caricata: {e}")

        # 5. Esplorazione Cartelle e File PC (Explorer & File Scanner)
        try:
            from ebj_pc_explorer import execute_pc_explorer
            def _handle_pc_explorer(payload: Dict[str, Any]) -> Dict[str, Any]:
                return execute_pc_explorer(payload)

            self.register(Ability(
                name="pc_folder_explorer",
                description="Esplorazione, apertura cartelle in Windows Explorer e ricerca rapida di file su disco",
                handler=_handle_pc_explorer,
                triggers=[
                    "esplora cartelle", "esplora cartella", "esplora il pc", "esplora pc",
                    "apri cartella", "apri la cartella", "esplora desktop", "esplora download",
                    "cosa c'è in", "cosa c'e in", "cerca file", "trova file", "mostra cartella", "esplora"
                ],
                tier=0
            ))
        except Exception as e:
            logger.warning(f"Abilità pc_folder_explorer non caricata: {e}")

# Singleton globale
_GLOBAL_REGISTRY = AbilityRegistry()

def get_ability_registry() -> AbilityRegistry:
    return _GLOBAL_REGISTRY
