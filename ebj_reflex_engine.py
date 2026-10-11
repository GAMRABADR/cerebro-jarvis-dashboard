#!/usr/bin/env python3
# ==============================================================================
#  E.B.J. APEX REFLEX & DECISION ENGINE (RUST SIMD ACCELERATED + THE JUDGE)
# ==============================================================================
#  Ispirato all'architettura JEV & Claude Opus 5.5 (Zubair Trabzada / AI Workshop)
#  ma potenziato con RUST SIMD nativo, Zero-Cost Reflex e Armor Anti-Allucinazione.
# ==============================================================================

import os
import sys
import re
import json
import time
import subprocess
import sqlite3
from typing import Dict, Any, List, Optional, Tuple

DIR = os.path.dirname(os.path.abspath(__file__))
VAULT_DB = os.path.join(DIR, "mail_vault.db")
RUST_BIN_REL = os.path.abspath(os.path.join(DIR, "..", "ebj-supreme", "rust-agents", "target", "release", "lead-extractor.exe"))
RUST_BIN_DBG = os.path.abspath(os.path.join(DIR, "..", "ebj-supreme", "rust-agents", "target", "debug", "lead-extractor.exe"))

RUST_BIN = RUST_BIN_REL if os.path.exists(RUST_BIN_REL) else (RUST_BIN_DBG if os.path.exists(RUST_BIN_DBG) else None)

# ── LE LEGGI DEI RIFLESSI (SOGLIE COSTANTI NOMINATE - JEV / REFLEX LAWS) ─────
LANE_ACT_THRESHOLD = 0.70          # Se la corsia è certa >= 70%, esegui senza chiedere
LANE_CLARIFY_THRESHOLD = 0.50      # Se tra 50% e 70%, chiarisci brevemente
COMPLETE_FIRE_THRESHOLD = 0.85     # Frase considerata completa
ADDRESSED_ROOM_THRESHOLD = 0.75    # Rivolto a EBJ (vs narrazione o terzi in stanza)
STAKES_CONFIRM_THRESHOLD = 0.50    # Azioni irreversibili (invio, delete, pagamento) richiedono conferma
CLAIM_THRESHOLD = 0.70             # Il modello afferma che un'azione esterna è stata compiuta
BACKED_THRESHOLD = 0.40            # L'affermazione è supportata da una ricevuta nel turno
GOV_SPEAK_THRESHOLD = 0.55         # Il governor fa parlare l'avviso per il lead
GOV_URGENT_THRESHOLD = 0.75        # Lead ad altissima urgenza (< 1h)
GOV_MONEY_THRESHOLD = 0.70         # Presenza esplicita di budget o transazione monetaria

# ── 1. LAYER 0: ACCELERATORE RUST SIMD (< 1ms, 0€ COST, NON CENSURATO) ──────
def fast_rust_extract(text: str) -> Optional[Dict[str, Any]]:
    """Esegue il binario compilato in Rust Release per estrarre telefoni de-offuscati e score."""
    if RUST_BIN and os.path.exists(RUST_BIN):
        try:
            t0 = time.perf_counter()
            p = subprocess.run([RUST_BIN, "--test", text], capture_output=True, text=True, timeout=2)
            if p.returncode == 0 and p.stdout.strip():
                data = json.loads(p.stdout)
                data["latency_ms"] = round((time.perf_counter() - t0) * 1000, 2)
                data["engine"] = "Rust SIMD Release Binary"
                return data
        except Exception as e:
            pass
    return None

# ── 2. PREPASS REFLEX EVALUATOR (LANE, COMPLETE, ADDRESSED, STAKES) ─────────
def evaluate_reflex_prepass(utterance: str, history_len: int = 0) -> Dict[str, Any]:
    """Valuta in sub-millisecondi corsia, intenzione, completezza e livello di rischio."""
    t0 = time.perf_counter()
    u_lower = utterance.lower().strip()

    # De-offuscamento e analisi rapida Rust se sembra un messaggio con lead
    rust_lead = None
    if any(k in u_lower for k in ["trasloc", "sgomber", "furgon", "cantin", "autolavagg", "detergent", "schium", "3", "tre", "preventiv"]):
        rust_lead = fast_rust_extract(utterance)

    # 1. Lane Determination
    lane = "chat"
    lane_confidence = 0.60

    if rust_lead and (rust_lead.get("phone") or rust_lead.get("lead_score", 0) >= 60):
        if "autolavaggio" in u_lower or "detergente" in u_lower or "schiuma" in u_lower:
            lane = "selezione_chimica"
            lane_confidence = 0.95
        elif any(k in u_lower for k in ["trasloc", "sgomber", "furgon", "cantin"]):
            lane = "lead_hunter"
            lane_confidence = 0.98
    elif any(k in u_lower for k in ["preventivo", "quanto costa", "costo", "prezzo", "stima", "quotazione"]):
        lane = "quote_engine"
        lane_confidence = 0.92
    elif any(k in u_lower for k in ["autolavaggio", "pista", "portale", "detergente", "nanotech", "cera", "fusto"]):
        lane = "selezione_chimica"
        lane_confidence = 0.94
    elif any(k in u_lower for k in ["mail", "email", "invia", "spedisci", "telegram", "promemoria", "agenda", "calendario"]):
        lane = "desk_action"
        lane_confidence = 0.88
    elif any(k in u_lower for k in ["note", "vault", "cerca nel database", "ricordi", "cosa abbiamo", "elenco"]):
        lane = "vault_search"
        lane_confidence = 0.90
    elif any(k in u_lower for k in ["ciao", "buongiorno", "buonasera", "grazie", "chi sei", "come stai"]):
        lane = "small_talk"
        lane_confidence = 0.95

    # 2. Addressed (Rivolto a EBJ vs ad altre persone in stanza)
    addressed_score = 0.85
    wake_match = bool(re.search(r'\b(ebj|jarvis|e\.b\.j|e bi gi|computer|agente)\b', u_lower))
    if wake_match:
        addressed_score = 0.98
    elif any(u_lower.startswith(w) for w in ["cerca", "trova", "fai", "invia", "dimmi", "scansiona", "estrai", "chiama"]):
        addressed_score = 0.90
    elif any(k in u_lower for k in ["sto dicendo a lui", "parlo con mario", "un attimo al telefono"]):
        addressed_score = 0.15

    # 3. Complete (Frase finita o spezzata su congiunzioni)
    ends_on_connector = bool(re.search(r'\b(e|ed|per|con|di|da|ma|oppure|perché|mentre|il|la|lo|un|una)\s*$', u_lower))
    complete_score = 0.40 if ends_on_connector else (0.95 if len(u_lower) > 8 else 0.70)

    # 4. Stakes (Rischio di operazione esterna irreversibile)
    high_stakes = any(k in u_lower for k in ["cancella", "elimina", "paga", "bonifico", "invia subito a tutti", "pubblica annuncio"])
    stakes_score = 0.85 if high_stakes else (0.45 if "invia" in u_lower else 0.10)

    # 5. Urgent
    urgent = any(k in u_lower for k in ["subito", "urgente", "ora", "emergenza", "entro un'ora", "disperato"])

    elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)

    return {
        "lane": lane,
        "lane_confidence": lane_confidence,
        "addressed": addressed_score,
        "complete": complete_score,
        "stakes": stakes_score,
        "urgent": urgent,
        "rust_lead": rust_lead,
        "latency_ms": elapsed_ms,
        "cost_usd": 0.00,  # 100% Gratis e Locale
        "verdict": "ACT" if lane_confidence >= LANE_ACT_THRESHOLD and addressed_score >= ADDRESSED_ROOM_THRESHOLD else "CLARIFY"
    }

# ── 3. THE JUDGE: LEGGE INVIOLABILE ANTI-ALLUCINAZIONE CON RICEVUTE ──────────
def judge_response(user_question: str, proposed_answer: str, receipts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Ispeziona la risposta prima che venga pronunciata. Se afferma un'azione senza ricevuta, la blocca."""
    t0 = time.perf_counter()
    ans_lower = proposed_answer.lower()

    # Riconosce verbi di azione compiuta (claim)
    claims_action = any(k in ans_lower for k in [
        "ho inviato", "ho spedito", "è stato inviato", "ho cancellato", "ho rimosso",
        "ho salvato nel database", "ho pubblicato l'annuncio", "ho prenotato", "ho chiamato"
    ])
    claim_score = 0.85 if claims_action else 0.15

    # Verifica se c'è almeno una ricevuta valida registrata in questo turno
    has_receipt = len(receipts) > 0 and any(r.get("status") in ("SUCCESS", "CONFIRMED", "OK") for r in receipts)
    backed_score = 0.95 if has_receipt else 0.10

    blocked = False
    corrected_answer = proposed_answer

    if claim_score >= CLAIM_THRESHOLD and backed_score < BACKED_THRESHOLD and len(receipts) == 0:
        # VIOLAZIONE RILEVATA: il modello dichiara di aver fatto qualcosa che non è avvenuto
        blocked = True
        corrected_answer = (
            "Badr, stavo per confermarti l'operazione, ma il sistema di controllo ha verificato "
            "che non è ancora stata emessa una ricevuta ufficiale per questa azione. "
            "Nessun dato o messaggio è stato inviato all'esterno. Vuoi che proceda realmente adesso?"
        )

    elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)

    return {
        "blocked": blocked,
        "claim_score": claim_score,
        "backed_score": backed_score,
        "receipts_count": len(receipts),
        "final_text": corrected_answer,
        "original_text": proposed_answer if blocked else None,
        "latency_ms": elapsed_ms
    }

# ── 4. THE SHADOW GOVERNOR: TRIAGE SOCIAL LEADS (FACEBOOK, SUBITO, MERCATINO) 
def governor_triage_card(card_text: str, author: str = "", city: str = "") -> Dict[str, Any]:
    """Punteggia e categorizza ogni commento/post social scartando lo spam ed elevando i clienti veri."""
    t0 = time.perf_counter()
    text_lower = card_text.lower()

    # Passaggio Rust SIMD
    rust_res = fast_rust_extract(card_text)

    # Rilevamento rumore / spam (noise question)
    is_noise = any(k in text_lower for k in [
        "guadagna da casa", "lavoro online", "crypto", "investimento", "seguimi",
        "clicca sul link", "sub for sub", "sexy", "whatsapp per dettagli gratis"
    ])

    has_money = bool(re.search(r'\b(\d{2,5}\s*€|\d{2,5}\s*euro|budget|pago|compro|tariffa)\b', text_lower))
    has_waiting_person = any(k in text_lower for k in ["urgente", "aiuto", "cerco qualcuno", "chi è disponibile", "subito"])
    has_phone = bool(rust_res and rust_res.get("phone"))

    # Punteggio di priorità 0.0 - 1.0
    score = 0.20
    if is_noise:
        score = 0.05
    else:
        if has_phone: score += 0.40
        if has_money: score += 0.20
        if has_waiting_person: score += 0.15
        if rust_res and rust_res.get("lead_score", 0) >= 70: score += 0.15

    score = min(round(score, 2), 1.0)
    should_interrupt = score >= GOV_SPEAK_THRESHOLD and not is_noise

    category = "LEAD_TRASLOCO" if "trasloc" in text_lower or "furgon" in text_lower else (
        "LEAD_CHIMICA_LAVAGGI" if "autolavagg" in text_lower or "detergent" in text_lower else (
            "LEAD_SGOMBERO" if "sgomber" in text_lower or "cantin" in text_lower else (
                "SPAM_NOISE" if is_noise else "GENERIC_INQUIRY"
            )
        )
    )

    elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)

    return {
        "category": category,
        "situational_score": score,
        "should_speak": should_interrupt,
        "is_noise": is_noise,
        "has_phone": has_phone,
        "phone": rust_res.get("phone") if rust_res else None,
        "author": author or "Utente Social",
        "city": city or (rust_res.get("route_from") if rust_res else "Bologna"),
        "rust_data": rust_res,
        "latency_ms": elapsed_ms
    }

# ── 5. JEV REFLEX DOMAIN ROUTERS (ISPIRATO AL VIDEO JARVIS UPGRADE) ────────
def route_email_action(prompt: str) -> Optional[Dict[str, Any]]:
    p_lower = prompt.lower()
    if any(k in p_lower for k in ["leggi email", "nuove email", "controlla posta", "inbox", "posta in arrivo"]):
        return {
            "domain": "EMAIL",
            "action": "READ_INBOX",
            "handler": "mail_vault_sync",
            "ack": "Controllo la posta in arrivo e sincronizzo il Vault, Badr."
        }
    if any(k in p_lower for k in ["invia email", "manda email", "scrivi email", "spedisci email"]):
        return {
            "domain": "EMAIL",
            "action": "COMPOSE_SEND",
            "handler": "instant_surprise_mailer",
            "ack": "Apro il modulo di composizione e preparo l'invio prioritario, Badr."
        }
    return None

def route_calendar_action(prompt: str) -> Optional[Dict[str, Any]]:
    p_lower = prompt.lower()
    if any(k in p_lower for k in ["agenda", "calendario", "impegni", "appuntamenti di oggi", "cosa ho da fare"]):
        return {
            "domain": "CALENDAR",
            "action": "LIST_EVENTS",
            "handler": "calendar_agenda_view",
            "ack": "Apro la tua agenda e verifico gli impegni in programma, Badr."
        }
    if any(k in p_lower for k in ["fissa appuntamento", "aggiungi in agenda", "segna per domani", "promemoria"]):
        return {
            "domain": "CALENDAR",
            "action": "ADD_EVENT",
            "handler": "calendar_event_creator",
            "ack": "Registro il promemoria in agenda con notifica prioritaria, Badr."
        }
    return None

def route_vault_query(prompt: str) -> Optional[Dict[str, Any]]:
    p_lower = prompt.lower()
    if any(k in p_lower for k in ["cerca nel vault", "memoria", "cosa ricordi", "dati salvati", "database", "ricordi di"]):
        return {
            "domain": "VAULT",
            "action": "FTS_QUERY",
            "handler": "holographic_memory_vault",
            "ack": "Interrogo il Memory Vault neurale e recupero i record pertinenti, Badr."
        }
    return None

def route_invoice_handling(prompt: str) -> Optional[Dict[str, Any]]:
    p_lower = prompt.lower()
    if any(k in p_lower for k in ["fattura", "fatture", "emetti fattura", "ricevuta", "calcola totale", "preventivo da pagare"]):
        return {
            "domain": "INVOICE",
            "action": "INVOICE_PROCESSING",
            "handler": "instant_invoice_generator",
            "ack": "Modulo fatturazione e preventivi agganciato, calcolo il documento fiscale, Badr."
        }
    return None

def route_agent_task(prompt: str) -> Optional[Dict[str, Any]]:
    p_lower = prompt.lower()
    if any(k in p_lower for k in ["assegna alla flotta", "subagente", "task in background", "manda all'agente", "delega"]):
        return {
            "domain": "AGENT_FLEET",
            "action": "DISPATCH_TASK",
            "handler": "autonomous_employee_fleet",
            "ack": "Assegno il task al worker autonomo della flotta, Badr."
        }
    return None

def jev_reflex_dispatch(prompt: str) -> Optional[Dict[str, Any]]:
    """
    Jev Reflex Master Dispatcher:
    Valuta l'intento in sub-millisecondi e restituisce il routing immediato (System One).
    """
    for router in [route_email_action, route_calendar_action, route_vault_query, route_invoice_handling, route_agent_task]:
        match = router(prompt)
        if match:
            return match
    return None

if __name__ == "__main__":
    print("--- TEST E.B.J. REFLEX & JEV ROUTING ---")
    print("Email test:", jev_reflex_dispatch("invia email urgente al cliente"))
    print("Calendar test:", jev_reflex_dispatch("quali appuntamenti ho in agenda per oggi?"))
    print("Vault test:", jev_reflex_dispatch("cosa ricordi nel vault riguardo alle 3 porte?"))
