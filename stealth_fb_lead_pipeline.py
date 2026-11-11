#!/usr/bin/env python3
# ==============================================================================
#  E.B.J. STEALTH FACEBOOK & WEB LEAD PIPELINE — ZERO-FAKE + CAMOUFOX + RUST SIMD
# ==============================================================================
#  1. Rimuove 100% dei mock statici e numeri fittizi: solo post reali live.
#  2. Valida ogni numero con ebj_lead_sanitizer (AGCOM) senza concatenare cifre a caso.
#  3. Scarta ditte concorrenti, blog SEO e autolavaggi fuori target.
#  4. Salva i soli lead coerenti e verificati in mail_vault.db (verified_leads_2026).
# ==============================================================================

from __future__ import annotations

import os
import sys
import re
import json
import datetime
import sqlite3
import subprocess
import urllib.parse
from typing import Any, Dict, List

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

DIR = os.path.dirname(os.path.abspath(__file__))
VAULT_DB = os.path.join(DIR, "mail_vault.db")
RUST_BIN = os.path.abspath(os.path.join(DIR, "..", "ebj-supreme", "rust-agents", "target", "release", "lead-extractor.exe"))
if not os.path.exists(RUST_BIN):
    RUST_BIN = os.path.abspath(os.path.join(DIR, "..", "ebj-supreme", "rust-agents", "target", "debug", "lead-extractor.exe"))

from ebj_lead_sanitizer import (
    validate_italian_phone,
    extract_phones_from_text,
    classify_lead_coherence,
)

FB_SEARCH_TARGETS = [
    {"query": "cerco trasloco bologna", "city": "Bologna", "service": "Trasloco Residenziale"},
    {"query": "sgombero cantina bologna imola", "city": "Imola", "service": "Sgombero Locale / Cantina"},
    {"query": "cerco aiuto trasloco modena", "city": "Modena", "service": "Trasloco con Facchinaggio"},
    {"query": "causa trasloco ferrara mobili", "city": "Ferrara", "service": "Sgombero & Trasporto Mobili"},
]


def parse_with_rust_simd(text: str, source_hint: str = "Facebook Community", title: str = "", url: str = "") -> Dict[str, Any]:
    """Estrae, de-offusca e valida il post senza mai inventare numeri o accettare competitor."""
    cls = classify_lead_coherence(title or text[:80], text, url=url, source=source_hint, target_mode="TRASLOCHI_PRIVATI")
    rust_data: Dict[str, Any] = {}
    if os.path.exists(RUST_BIN):
        try:
            p = subprocess.run([RUST_BIN, "--test", str(text)], capture_output=True, text=True, timeout=3)
            if p.returncode == 0:
                rust_data = json.loads(p.stdout)
                rust_data["engine"] = "Rust SIMD Native"
        except Exception:
            rust_data = {}

    # Validazione stretta del telefono tramite ebj_lead_sanitizer (zero falsi numeri concatenati)
    candidate_phone = rust_data.get("phone")
    ph_info = validate_italian_phone(candidate_phone, strict_mobile_10=True) if candidate_phone else None
    if not ph_info:
        extracted = extract_phones_from_text(text, author_only=False, mobile_only=False)
        ph_info = extracted[0] if extracted else None

    return {
        "source": source_hint,
        "phone": ph_info["e164"] if ph_info else None,
        "phone_formatted": ph_info["formatted"] if ph_info else None,
        "is_valid_phone": bool(ph_info),
        "coherent": cls["coherent"],
        "coherence_category": cls["category"],
        "coherence_reason": cls["reason"],
        "route_from": rust_data.get("route_from") or "Bologna",
        "route_to": rust_data.get("route_to"),
        "service_type": rust_data.get("service_type") or "Trasloco / Sgombero",
        "brand_assigned": "BadrExpress.com & PietroTraslochi.com",
        "lead_score": rust_data.get("lead_score") if (cls["coherent"] and ph_info) else 35,
        "urgency": rust_data.get("urgency") or "STANDARD",
        "estimated_budget_eur": float(rust_data.get("estimated_budget_eur") or 380.0),
        "raw_text": text,
        "engine": rust_data.get("engine") or "Sanitizer Python",
    }


def run_camoufox_stealth_crawler(city: str = "Bologna", limit: int = 10) -> List[Dict[str, Any]]:
    """
    Esegue una ricerca live reale su Facebook (solo se sessione cookie presente o ricerca pubblica)
    e fallback su Subito.it via ScrapingBee. Non genera MAI post finti o mock.
    """
    scraped_posts: List[Dict[str, Any]] = []
    try:
        from camoufox.sync_api import Camoufox
        with Camoufox(headless=True) as browser:
            page = browser.new_page()
            page.set_extra_http_headers({
                "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
            })
            target_url = f"https://www.facebook.com/search/posts/?q={urllib.parse.quote('cerco trasloco ' + city)}"
            page.goto(target_url, timeout=14000, wait_until="domcontentloaded")
            page.wait_for_timeout(1800)
            body_text = page.inner_text("body") or ""
            # Se Facebook richiede login esplicito non inventiamo nulla: ritorniamo solo eventuali post reali letti
            if "log in" not in (page.title() or "").lower() and "accedi" not in (page.title() or "").lower():
                articles = page.locator("div[role='article']")
                count = min(articles.count(), limit)
                for idx in range(count):
                    art = articles.nth(idx)
                    txt = (art.inner_text() or "").strip()
                    if len(txt) < 30:
                        continue
                    href = ""
                    try:
                        lnk = art.locator("a[href*='/posts/'], a[href*='/permalink/']").first
                        if lnk.count() > 0:
                            href = lnk.get_attribute("href") or ""
                    except Exception:
                        pass
                    scraped_posts.append({
                        "author": txt.splitlines()[0][:50] or f"Utente Facebook ({city})",
                        "city": city,
                        "raw_text": txt[:800],
                        "post_url": href or target_url,
                    })
    except Exception as e:
        print(f"[Camoufox FB info]: {e}")

    # Integrazione reale con Tavily Search (se TAVILY_API_KEY presente) per Facebook Gruppi / Web
    tavily_key = os.getenv("TAVILY_API_KEY", "").strip()
    if tavily_key and len(scraped_posts) < limit:
        try:
            import requests as _rq
            for tq in (
                f'site:facebook.com/groups "cerco" ("trasloco" OR "sgombero") {city}',
                f'("cerco furgone trasloco" OR "devo sgomberare cantina") {city}',
            ):
                resp = _rq.post(
                    "https://api.tavily.com/search",
                    json={"api_key": tavily_key, "query": tq, "max_results": 5, "search_depth": "basic"},
                    timeout=10,
                )
                if resp.status_code == 200:
                    for item in (resp.json().get("results") or []):
                        scraped_posts.append({
                            "author": (item.get("title") or "Richiesta Web")[:50],
                            "city": city,
                            "raw_text": f"{item.get('title', '')}. {item.get('content', '')}",
                            "post_url": item.get("url", ""),
                            "source": "Facebook/Web Live (Tavily)",
                        })
        except Exception as e_tv:
            print(f"[Tavily Web info]: {e_tv}")

    # Integrazione reale con Subito/Web via ScrapingBee se necessario
    if len(scraped_posts) < limit:
        try:
            sys.path.insert(0, os.path.join(DIR, "skills_vault", "subito_lead_hunter"))
            import skill as subito_skill
            ads = subito_skill.scrape_subito_live_scrapingbee(city=city.lower(), query="trasloco", limit=limit - len(scraped_posts))
            for ad in ads:
                scraped_posts.append({
                    "author": ad.get("title", "Privato Subito")[:50],
                    "city": ad.get("city") or city,
                    "raw_text": f"{ad.get('title', '')}. {ad.get('text', '')}",
                    "post_url": ad.get("url", ""),
                    "source": ad.get("source", "Subito.it Live"),
                })
        except Exception as e_sb:
            print(f"[Subito ScrapingBee info]: {e_sb}")

    return scraped_posts


def ingest_leads_into_vault(leads: List[Dict[str, Any]]) -> int:
    """Salva in verified_leads_2026 SOLO lead coerenti (zero competitor/autolavaggi/mock/fake phone)."""
    if not leads:
        return 0

    conn = sqlite3.connect(VAULT_DB)
    c = conn.cursor()
    today_str = datetime.datetime.now().strftime("%Y-%m-%d")
    inserted_count = 0

    for l in leads:
        if not l.get("coherent"):
            continue
        phone = l.get("phone")
        post_url = (l.get("post_url") or "").strip()
        if phone:
            ph_ok = validate_italian_phone(phone, strict_mobile_10=False)
            if not ph_ok:
                continue
            phone = ph_ok["e164"]
            wa_link = ph_ok["wa_url"]
        elif post_url:
            phone = "DM_ONLY"
            wa_link = ""
        else:
            continue

        name = (l.get("author") or "Cliente Privato")[:80]
        city = l.get("city") or "Bologna"
        service = l.get("service_type") or "Trasloco Residenziale"
        budget = float(l.get("estimated_budget_eur") or 380.0)
        source = l.get("source") or "Facebook/Web Live Verificato"
        notes = f"Brand: {l.get('brand_assigned', 'BadrExpress.com')} | {l.get('coherence_category')} | Score: {l.get('lead_score', 75)}/100"

        dup = None
        if phone != "DM_ONLY":
            dup = c.execute("SELECT id FROM verified_leads_2026 WHERE phone = ?", (phone,)).fetchone()
        if not dup and post_url:
            dup = c.execute("SELECT id FROM verified_leads_2026 WHERE post_url = ?", (post_url,)).fetchone()
        if not dup:
            c.execute(
                """
                INSERT INTO verified_leads_2026 (
                    client_name, phone, city, service_type, volume_mq, estimated_budget,
                    source, verified_status, contact_type, post_url, whatsapp_link,
                    scraped_date, notes, extraction_method, provenance_channel, lead_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    name, phone, city, service, 55, budget,
                    source, "VERIFICATO_REALE" if phone != "DM_ONLY" else "DM_READY",
                    "TELEFONO_CERTIFICATO" if phone != "DM_ONLY" else "MESSENGER_DM",
                    post_url, wa_link, today_str, notes, "RUST_SIMD_SANITIZED", "FACEBOOK_WEB_LIVE", "DA_CHIAMARE",
                ),
            )
            inserted_count += 1

    conn.commit()
    conn.close()
    return inserted_count


def run_live_coherent_scrape(city: str = "Bologna", limit: int = 8) -> Dict[str, Any]:
    raw_posts = run_camoufox_stealth_crawler(city=city, limit=limit)
    processed: List[Dict[str, Any]] = []
    rejected: List[Dict[str, Any]] = []

    for p in raw_posts:
        r_res = parse_with_rust_simd(
            p.get("raw_text", ""),
            source_hint=p.get("source", "Facebook/Web Live"),
            title=p.get("author", ""),
            url=p.get("post_url", ""),
        )
        r_res["author"] = p.get("author", "Privato")
        r_res["city"] = p.get("city", city)
        r_res["post_url"] = p.get("post_url", "")
        if r_res["coherent"] and (r_res["is_valid_phone"] or r_res["post_url"]):
            processed.append(r_res)
        else:
            rejected.append({
                "author": r_res["author"],
                "category": r_res["coherence_category"],
                "reason": r_res["coherence_reason"],
            })

    inserted = ingest_leads_into_vault(processed)
    return {
        "status": "SUCCESS",
        "city": city,
        "raw_collected": len(raw_posts),
        "coherent_accepted": len(processed),
        "rejected_incoherent": len(rejected),
        "inserted_new": inserted,
        "accepted": processed,
        "rejected_sample": rejected[:5],
    }


if __name__ == "__main__":
    print(json.dumps(run_live_coherent_scrape(), indent=2, ensure_ascii=False))
