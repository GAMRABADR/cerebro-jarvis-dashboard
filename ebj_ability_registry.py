"""
==============================================================================
EBJ SUPREME ABILITY REGISTRY (PLUGGABLE SKILLS RUNTIME)
==============================================================================
Modulo di orchestrazione modulare per registrare, abilitare, disabilitare e
richiamare nuove abilità cognitive ed operative per l'agente EBJ senza mai
toccare o sporcare il server monolitico.

Supporta:
  - Dynamic Dispatch con prioritizzazione (Priority Queue)
  - Fast Memory Caching
  - Tracciamento metriche di esecuzione (latenza, success rate, fallback)
  - Abilitazione/Disabilitazione runtime a caldo (Hot Reload)
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
        self.tier = tier  # 0: Sub-1ms native/cache, 1: CLM/Reflex, 2: LLM
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
                "ability_latency_ms": round(lat, 3)
            }

class AbilityRegistry:
    def __init__(self):
        self._abilities: Dict[str, Ability] = {}

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

# Singleton globale
_GLOBAL_REGISTRY = AbilityRegistry()

def get_ability_registry() -> AbilityRegistry:
    return _GLOBAL_REGISTRY
