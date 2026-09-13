"""SkillRegistry — registrazione, discovery e routing skill.

Il registry mantiene un dizionario skill_id → istanza SkillBase.
Supporta:
  - register() / unregister()
  - get() per skill_id
  - route(intent) per routing da intent a skill corretta
  - list_by_category() per raggruppamento
  - health_check_all() per verifica stato globale
  - stats_all() per metriche aggregate
"""
from __future__ import annotations

import importlib
import json
import os
import threading
from typing import Optional

from .base import SkillBase, SkillResult


class SkillRegistry:
    """Registro centrale per tutte le skill agentiche."""

    def __init__(self):
        self._skills: dict[str, SkillBase] = {}
        self._intent_map: dict[str, str] = {}
        self._lock = threading.Lock()

    def register(self, skill: SkillBase, intents: list[str] = None) -> None:
        """Registra una skill. intents opzionali per routing automatico."""
        with self._lock:
            self._skills[skill.skill_id] = skill
            if intents:
                for intent in intents:
                    self._intent_map[intent.lower()] = skill.skill_id

    def unregister(self, skill_id: str) -> None:
        """Rimuovi una skill dal registry."""
        with self._lock:
            self._skills.pop(skill_id, None)
            self._intent_map = {
                k: v for k, v in self._intent_map.items() if v != skill_id
            }

    def get(self, skill_id: str) -> Optional[SkillBase]:
        """Ottieni skill per ID."""
        return self._skills.get(skill_id)

    def route(self, intent: str) -> Optional[SkillBase]:
        """Routing da intent a skill. Intent matching case-insensitive."""
        skill_id = self._intent_map.get(intent.lower())
        if skill_id:
            return self._skills.get(skill_id)
        for key, sid in self._intent_map.items():
            if key in intent.lower():
                return self._skills.get(sid)
        return None

    def list_all(self) -> list[dict]:
        """Lista tutte le skill registrate con metadati."""
        return [s.stats() for s in self._skills.values()]

    def list_by_category(self, category: str) -> list[dict]:
        """Lista skill per categoria."""
        return [
            s.stats() for s in self._skills.values() if s.category == category
        ]

    def health_check_all(self) -> dict[str, bool]:
        """Health check di tutte le skill. Ritorna {skill_id: healthy}."""
        results = {}
        for skill_id, skill in self._skills.items():
            try:
                results[skill_id] = skill.health_check()
                skill._health_status = results[skill_id]
            except Exception:
                results[skill_id] = False
                skill._health_status = False
        return results

    def stats_all(self) -> dict:
        """Statistiche aggregate di tutte le skill."""
        all_stats = self.list_all()
        total_exec = sum(s["execution_count"] for s in all_stats)
        total_errors = sum(s["error_count"] for s in all_stats)
        return {
            "total_skills": len(all_stats),
            "total_executions": total_exec,
            "total_errors": total_errors,
            "overall_error_rate": (
                round(total_errors / total_exec * 100, 2) if total_exec > 0 else 0.0
            ),
            "healthy_count": sum(1 for s in all_stats if s["healthy"]),
            "skills": all_stats,
        }

    def auto_discover(self, skills_dir: str) -> int:
        """Scansione automatica directory skills_vault/ per skill registrabili.

        Cerca manifest.json in ogni sottodirectory, carica skill.py se esiste.
        Ritorna numero di skill caricate.
        """
        loaded = 0
        if not os.path.isdir(skills_dir):
            return 0

        for entry in os.listdir(skills_dir):
            skill_path = os.path.join(skills_dir, entry)
            manifest_path = os.path.join(skill_path, "manifest.json")
            skill_py = os.path.join(skill_path, "skill.py")

            if not os.path.isfile(manifest_path) or not os.path.isfile(skill_py):
                continue
            if entry.startswith("_"):
                continue

            try:
                with open(manifest_path, "r", encoding="utf-8") as f:
                    manifest = json.load(f)

                module_name = f"skills_vault.{entry}.skill"
                mod = importlib.import_module(module_name)

                for attr_name in dir(mod):
                    attr = getattr(mod, attr_name)
                    if (
                        isinstance(attr, type)
                        and issubclass(attr, SkillBase)
                        and attr is not SkillBase
                    ):
                        instance = attr()
                        instance.name = manifest.get("name", instance.name)
                        instance.skill_id = manifest.get("id", entry)
                        instance.category = manifest.get("category", instance.category)
                        instance.version = manifest.get("version", instance.version)
                        self.register(instance)
                        loaded += 1
                        break
            except Exception:
                continue

        return loaded
