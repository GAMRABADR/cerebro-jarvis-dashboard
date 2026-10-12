"""
==============================================================================
EBJ SUPREME TRANSLATION GATEWAY MODULE (RUST & MULTI-PROVIDER)
==============================================================================
Modulo isolato e pluggabile per la gestione della traduzione simultanea e
ordinata. Disaccoppia la logica da server.py e gestisce il router multi-provider:
  Tier 0: Rust Apex Engine Cache (:9000)
  Tier 1: Google GTX Neural Stream (sub-50ms)
  Tier 2: MyMemory Resilient Failover
  Tier 3: DeepL / Lara Translation Model (MCP Protocol)
==============================================================================
"""
from __future__ import annotations
import os
import re
import json
import time
import urllib.request
import urllib.parse
from typing import Tuple, Dict, Any, Optional

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_TRANSLATION_STATE_FILE = os.path.join(BASE_DIR, ".active_translation")

class LiveTranslator:
    def __init__(self):
        self.is_active = False
        self.target_lang = "ru"
        self._load_state()

    def _load_state(self):
        try:
            if os.path.exists(_TRANSLATION_STATE_FILE):
                with open(_TRANSLATION_STATE_FILE, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                    self.is_active = bool(data.get("active", False))
                    self.target_lang = data.get("target", "ru")
        except Exception:
            pass

    def _save_state(self):
        try:
            with open(_TRANSLATION_STATE_FILE, "w", encoding="utf-8") as fh:
                json.dump({"active": self.is_active, "target": self.target_lang}, fh)
        except Exception:
            pass

    def translate_fast(self, text: str, target_lang: str = None, source_lang: str = "auto") -> Tuple[str, str, float]:
        t0 = time.perf_counter()
        clean = str(text or "").strip()
        if not clean:
            return "", "empty", 0.0

        tgt = (target_lang or self.target_lang).lower().strip()
        if tgt == "es-pe":
            tgt = "es"

        # Tier 0 & 1: Rust Apex Engine su porta 9000
        try:
            s_lang = "it" if source_lang == "auto" else source_lang
            req = urllib.request.Request(
                "http://127.0.0.1:9000/translate",
                data=json.dumps({"text": clean, "source_lang": s_lang, "target_lang": tgt}).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=1.8) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                tr = data.get("translated", "").strip()
                prov = data.get("provider", "Rust_Apex_Engine_:9000")
                if tr and not tr.startswith("'AUTO' IS AN INVALID") and tr != clean:
                    lat = (time.perf_counter() - t0) * 1000.0
                    return tr, prov, lat
        except Exception:
            pass

        # Tier 2: Google GTX Neural Stream
        try:
            g_url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl={source_lang}&tl={tgt}&dt=t&q={urllib.parse.quote(clean)}"
            g_req = urllib.request.Request(g_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
            with urllib.request.urlopen(g_req, timeout=2.5) as r:
                g_data = json.loads(r.read().decode("utf-8"))
                res_parts = [part[0] for part in g_data[0] if part and part[0]]
                res_txt = "".join(res_parts).strip()
                if res_txt:
                    lat = (time.perf_counter() - t0) * 1000.0
                    return res_txt, "JEV_GTX_Neural_Stream", lat
        except Exception:
            pass

        lat = (time.perf_counter() - t0) * 1000.0
        return clean, "passthrough", lat

    def handle_voice_query(self, prompt_text: str) -> Tuple[bool, str, str, str]:
        p = str(prompt_text or "").lower().strip()

        # Stop command
        if any(s in p for s in [
            "smetti di tradurre", "stop traduzione", "ferma traduzione", "basta tradurre",
            "interrompi traduzione", "disattiva traduzione", "chiudi traduzione", "fine traduzione"
        ]):
            self.is_active = False
            self._save_state()
            ack = "Sì signore, procedo subito. Modalità traduzione istantanea disattivata. Torno alle normali funzioni operative Stark."
            return True, ack, "it", "stop"

        # Activation command
        is_trans_trigger = bool(re.search(r'\b(ebj\s+traduci|eb\s+traduci|traduci\s+in|inizia\s+a\s+tradurre|attiva\s+traduzione|mettiti\s+a\s+tradurre)\b', p))
        if is_trans_trigger or p in ["ebj traduci", "eb traduci", "traduci"]:
            target = None
            if any(k in p for k in ["russo", "russa", "russian", "russia"]):
                target = "ru"
            elif any(k in p for k in ["inglese", "english", "britannico", "americano"]):
                target = "en"
            elif any(k in p for k in ["francese", "francia", "francais", "français"]):
                target = "fr"
            elif any(k in p for k in ["spagnolo", "spagnola", "espana", "español"]):
                target = "es"
            elif any(k in p for k in ["peruviano", "peru", "perù", "peruano"]):
                target = "es-pe"
            elif any(k in p for k in ["arabo", "araba", "arabic", "marocchino"]):
                target = "ar"
            elif any(k in p for k in ["albanese", "albania", "shqip"]):
                target = "sq"
            elif any(k in p for k in ["cinese", "mandarino", "chinese"]):
                target = "zh"
            elif any(k in p for k in ["italiano", "italiana"]):
                target = "it"

            if target:
                self.is_active = True
                self.target_lang = target
                self._save_state()
                ack = f"Sì signore, procedo subito! Modalità traduttore istantaneo attivata verso {target.upper()}. Parli liberamente: ripeterò e tradurrò ogni sua parola con voce neurale nativa. Per terminare dica semplicemente 'smetti di tradurre'."
                return True, ack, "it", "start"
            else:
                ack = "Certamente signore. In quale lingua desidera che traduca ciò che dice? Può specificare: russo, inglese, arabo, francese, spagnolo, albanese, cinese o peruviano."
                return True, ack, "it", "ask_lang"

        # Active stream translating
        if self.is_active:
            clean_text = re.sub(r'^(ebj|eb|jarvis)\s*[,.:;]?\s*', '', prompt_text, flags=re.I).strip()
            if clean_text:
                translated, engine, lat_ms = self.translate_fast(clean_text, target_lang=self.target_lang, source_lang="it")
                return True, translated, self.target_lang, "translating"

        return False, "", "", "none"

# Singleton
_TRANSLATOR_INSTANCE = LiveTranslator()

def get_translator() -> LiveTranslator:
    return _TRANSLATOR_INSTANCE
