"""SkillBase — interfaccia astratta per tutte le skill agentiche EBJ.

Ogni skill deve ereditare da SkillBase e implementare:
  - execute(params) → SkillResult
  - health_check() → bool
  - metadata() → dict

Esempio minimo:
    class MySkill(SkillBase):
        def execute(self, params):
            return SkillResult(success=True, data={"result": "ok"})
"""
from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class SkillResult:
    """Risultato standardizzato di una skill."""
    success: bool
    data: Any = None
    error: Optional[str] = None
    latency_ms: float = 0.0
    provider: Optional[str] = None
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "latency_ms": round(self.latency_ms, 2),
            "provider": self.provider,
            "metadata": self.metadata,
        }


class SkillError(Exception):
    """Errore specifico skill — include codice e contesto."""
    def __init__(self, message: str, code: str = "SKILL_ERROR", context: dict = None):
        super().__init__(message)
        self.code = code
        self.context = context or {}


class SkillBase(ABC):
    """Classe base astratta per tutte le skill.

    Attributi:
        name: nome umano della skill
        skill_id: identificativo univoco (snake_case)
        category: categoria (communication, data_processing, automation, business)
        version: versione semver
        timeout_secs: timeout massimo esecuzione
        cache_ttl_secs: TTL cache risultati (0 = no cache)
    """

    name: str = "Unnamed Skill"
    skill_id: str = "unnamed"
    category: str = "general"
    version: str = "1.0.0"
    timeout_secs: int = 30
    cache_ttl_secs: int = 0

    def __init__(self):
        self._last_health_check = 0
        self._health_status = True
        self._execution_count = 0
        self._error_count = 0

    @abstractmethod
    def execute(self, params: dict) -> SkillResult:
        """Esegui la skill con i parametri dati. Ritorna SkillResult."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Verifica che la skill sia operativa. Ritorna True/False."""
        pass

    @abstractmethod
    def metadata(self) -> dict:
        """Ritorna metadati della skill (inputs, outputs, description, ecc)."""
        pass

    def run(self, params: dict) -> SkillResult:
        """Wrapper con timing, conteggio errori, gestione eccezioni."""
        self._execution_count += 1
        start = time.time()
        try:
            result = self.execute(params)
            result.latency_ms = (time.time() - start) * 1000
            if not result.success:
                self._error_count += 1
            return result
        except SkillError as e:
            self._error_count += 1
            return SkillResult(
                success=False,
                error=str(e),
                latency_ms=(time.time() - start) * 1000,
                metadata={"error_code": e.code, "context": e.context},
            )
        except Exception as e:
            self._error_count += 1
            return SkillResult(
                success=False,
                error=f"{type(e).__name__}: {e}",
                latency_ms=(time.time() - start) * 1000,
                metadata={"error_code": "UNHANDLED"},
            )

    def stats(self) -> dict:
        """Statistiche esecuzione skill."""
        return {
            "skill_id": self.skill_id,
            "name": self.name,
            "category": self.category,
            "version": self.version,
            "execution_count": self._execution_count,
            "error_count": self._error_count,
            "error_rate": (
                round(self._error_count / self._execution_count * 100, 2)
                if self._execution_count > 0
                else 0.0
            ),
            "healthy": self._health_status,
        }

    def __repr__(self) -> str:
        return f"<Skill:{self.skill_id} v{self.version} cat={self.category}>"
