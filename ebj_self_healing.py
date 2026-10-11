"""
E.B.J. Autonomous Self-Healing & Reflection Engine (PRAR Architecture 2026)
Cycle: Perceive -> Reason -> Act -> Reflect (Critique) -> Heal (Refine)

Features:
  1. Grounded Verification: Evaluates output against objective criteria (exit codes, schemas, data quality).
  2. Infrastructure-as-Context: Feeds raw exceptions and stack traces back into self-healing prompt.
  3. Bounded Reflection Loop: Max 3 self-healing iterations before controlled escalation.
  4. Execution Ledger: Persistent audit trail with time-stamped proof receipts.
"""
from __future__ import annotations

import os
import sys
import time
import json
import traceback
import sqlite3
from typing import Dict, Any, List, Optional, Callable

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ebj_reflection_ledger.db")

def _init_db():
    try:
        with sqlite3.connect(DB_PATH) as con:
            cur = con.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS reflection_ledger (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT,
                    goal TEXT,
                    iteration INTEGER,
                    action_name TEXT,
                    status TEXT, -- PASS, FAIL, HEALED
                    critique TEXT,
                    error_context TEXT,
                    latency_ms REAL,
                    timestamp REAL
                )
            """)
            con.commit()
    except Exception:
        pass

_init_db()


class SelfHealingReflectionEngine:
    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries

    def record_step(self, task_id: str, goal: str, iteration: int, action_name: str, status: str, critique: str, error_context: str, latency_ms: float):
        try:
            with sqlite3.connect(DB_PATH) as con:
                cur = con.cursor()
                cur.execute("""
                    INSERT INTO reflection_ledger (task_id, goal, iteration, action_name, status, critique, error_context, latency_ms, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (task_id, goal, iteration, action_name, status, critique, error_context, latency_ms, time.time()))
                con.commit()
        except Exception:
            pass

    def execute_with_reflection(self, goal: str, action_fn: Callable[[Dict[str, Any]], Dict[str, Any]], initial_params: Optional[Dict[str, Any]] = None, verifier_fn: Optional[Callable[[Dict[str, Any]], Tuple[bool, str]]] = None) -> Dict[str, Any]:
        """
        Executes an action within an autonomous self-healing reflection loop.
        If action_fn fails or verifier_fn returns False, context is gathered and action_fn is re-invoked with corrective hints.
        """
        t0 = time.time()
        task_id = f"REF_{int(time.time()*1000)}"
        params = dict(initial_params or {})
        iteration = 1
        last_error = ""

        while iteration <= self.max_retries:
            iter_t0 = time.time()
            try:
                # 1. ACT
                params["_reflection_iteration"] = iteration
                if last_error:
                    params["_healing_context"] = f"PREVIOUS ATTEMPT FAILED: {last_error}. Adjust strategy accordingly."

                result = action_fn(params)
                
                # 2. REFLECT & CRITIQUE (Grounded verification)
                passed = True
                critique = "All validation checks passed."
                if verifier_fn:
                    passed, critique = verifier_fn(result)
                elif isinstance(result, dict) and result.get("status") in ("ERROR", "FAILED"):
                    passed = False
                    critique = result.get("message") or result.get("error") or "Status returned ERROR"

                iter_lat = round((time.time() - iter_t0) * 1000, 2)

                if passed:
                    self.record_step(task_id, goal, iteration, "EXECUTE", "HEALED" if iteration > 1 else "PASS", critique, "", iter_lat)
                    return {
                        "status": "SUCCESS",
                        "task_id": task_id,
                        "goal": goal,
                        "iterations": iteration,
                        "self_healed": (iteration > 1),
                        "critique": critique,
                        "result": result,
                        "latency_ms": round((time.time() - t0) * 1000, 2)
                    }
                else:
                    last_error = critique
                    self.record_step(task_id, goal, iteration, "CRITIQUE", "FAIL", critique, "", iter_lat)
                    iteration += 1

            except Exception as e:
                # Captures infrastructure-as-context
                err_detail = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
                last_error = err_detail
                iter_lat = round((time.time() - iter_t0) * 1000, 2)
                self.record_step(task_id, goal, iteration, "EXCEPTION", "FAIL", f"Exception raised: {type(e).__name__}", err_detail, iter_lat)
                iteration += 1

        # Max retries exhausted
        return {
            "status": "FAILED",
            "task_id": task_id,
            "goal": goal,
            "iterations": self.max_retries,
            "self_healed": False,
            "error": f"Self-healing reflection exhausted after {self.max_retries} attempts. Last error: {last_error}",
            "latency_ms": round((time.time() - t0) * 1000, 2)
        }


_GLOBAL_REFLECTION_ENGINE = SelfHealingReflectionEngine()

def run_self_healing_action(goal: str, action_fn: Callable[[Dict[str, Any]], Dict[str, Any]], params: Optional[Dict[str, Any]] = None, verifier_fn: Optional[Callable[[Dict[str, Any]], Tuple[bool, str]]] = None) -> Dict[str, Any]:
    return _GLOBAL_REFLECTION_ENGINE.execute_with_reflection(goal, action_fn, params, verifier_fn)
