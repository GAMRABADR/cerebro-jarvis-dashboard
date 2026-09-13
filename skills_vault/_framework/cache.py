"""SkillCache — LRU cache con TTL per risultati skill.

Riduce chiamate ridondanti a provider esterni (Groq, Gemini, API varie).
Configurabile per-skill tramite cache_ttl_secs.

Uso:
    cache = SkillCache(max_size=500, default_ttl=300)
    result = cache.get_or_compute(key, compute_fn, ttl=60)
"""
from __future__ import annotations

import hashlib
import json
import threading
import time
from collections import OrderedDict
from typing import Any, Callable, Optional


class _CacheEntry:
    __slots__ = ("value", "expires_at", "created_at", "hit_count")

    def __init__(self, value: Any, ttl_secs: int):
        self.value = value
        self.created_at = time.time()
        self.expires_at = self.created_at + ttl_secs
        self.hit_count = 0

    @property
    def is_expired(self) -> bool:
        return time.time() > self.expires_at


class SkillCache:
    """Cache LRU thread-safe con TTL per skill results.

    Parametri:
        max_size: numero massimo di entry (default 500)
        default_ttl: TTL default in secondi (default 300 = 5 min)
    """

    def __init__(self, max_size: int = 500, default_ttl: int = 300):
        self._store: OrderedDict[str, _CacheEntry] = OrderedDict()
        self._lock = threading.Lock()
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._hits = 0
        self._misses = 0

    @staticmethod
    def make_key(skill_id: str, params: dict) -> str:
        """Genera cache key deterministic da skill_id + params."""
        raw = json.dumps(params, sort_keys=True, default=str)
        h = hashlib.sha256(f"{skill_id}:{raw}".encode()).hexdigest()[:16]
        return f"{skill_id}:{h}"

    def get(self, key: str) -> Optional[Any]:
        """Ottieni valore da cache. None se assente o scaduto."""
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                self._misses += 1
                return None
            if entry.is_expired:
                del self._store[key]
                self._misses += 1
                return None
            self._store.move_to_end(key)
            entry.hit_count += 1
            self._hits += 1
            return entry.value

    def set(self, key: str, value: Any, ttl_secs: int = None) -> None:
        """Inserisci/aggiorna entry in cache."""
        ttl = ttl_secs if ttl_secs is not None else self._default_ttl
        with self._lock:
            if key in self._store:
                del self._store[key]
            self._store[key] = _CacheEntry(value, ttl)
            while len(self._store) > self._max_size:
                self._store.popitem(last=False)

    def get_or_compute(
        self,
        key: str,
        compute_fn: Callable[[], Any],
        ttl_secs: int = None,
    ) -> Any:
        """Get from cache or compute and cache. Atomic under lock."""
        cached = self.get(key)
        if cached is not None:
            return cached
        value = compute_fn()
        self.set(key, value, ttl_secs)
        return value

    def invalidate(self, key: str) -> bool:
        """Rimuovi entry specifica. Ritorna True se esisteva."""
        with self._lock:
            if key in self._store:
                del self._store[key]
                return True
            return False

    def invalidate_prefix(self, prefix: str) -> int:
        """Rimuovi tutte le entry che iniziano con prefix. Ritorna count."""
        removed = 0
        with self._lock:
            keys_to_remove = [k for k in self._store if k.startswith(prefix)]
            for k in keys_to_remove:
                del self._store[k]
                removed += 1
        return removed

    def clear(self) -> None:
        """Svuota tutta la cache."""
        with self._lock:
            self._store.clear()
            self._hits = 0
            self._misses = 0

    def cleanup_expired(self) -> int:
        """Rimuovi entry scadute. Ritorna count."""
        removed = 0
        with self._lock:
            expired_keys = [k for k, v in self._store.items() if v.is_expired]
            for k in expired_keys:
                del self._store[k]
                removed += 1
        return removed

    def stats(self) -> dict:
        """Statistiche cache."""
        total = self._hits + self._misses
        return {
            "size": len(self._store),
            "max_size": self._max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(self._hits / total * 100, 2) if total > 0 else 0.0,
            "expired": sum(1 for v in self._store.values() if v.is_expired),
        }
