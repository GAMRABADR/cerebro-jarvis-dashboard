#!/usr/bin/env python3
"""Prova eseguibile del motore visione JEV: nessuna perizia cablata spacciata per lettura della foto.
Nessuna rete: le chiamate cloud sono simulate, quindi l'harness gira anche a quote esaurite."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import ebj_vision_engine as ev

CASES = []
FAKE_B64 = "ZmFrZS1pbWFnZQ=="  # 'fake-image'
REAL_PHONE = "3888703508"


def chk(name, cond):
    CASES.append((name, bool(cond)))


class Resp:
    def __init__(self, status_code, payload=None):
        self.status_code = status_code
        self._payload = payload or {}

    def json(self):
        return self._payload


def run_with(post_fn, keys=None, image=FAKE_B64, task="furniture_moving"):
    """Esegue analyze_image_with_jev con cloud e chiavi simulati (restore delle globali)."""
    real_post = ev.requests.post
    real_keys = ev._get_api_keys
    ev.requests.post = post_fn
    ev._get_api_keys = lambda: ({"gemini": "simulated"} if keys is None else keys)
    try:
        return ev.analyze_image_with_jev(image, task_type=task)
    finally:
        ev.requests.post = real_post
        ev._get_api_keys = real_keys


ok_payload = {"candidates": [{"content": {"parts": [{"text":
    '{"items": [{"name": "Divano", "quantity": 1, "volume_m3": 2.2}], '
    '"total_volume_m3": 2.2, "price_estimate_eur": 180.0, "confidence": 0.71}'}]}}]}

# 1. Cloud risponde: la perizia viene etichettata come visione reale
r = run_with(lambda *a, **k: Resp(200, ok_payload))
chk("cloud OK -> vision_applied True", r["vision_applied"] is True)
chk("cloud OK -> appraisal_source gemini_vision", r["appraisal_source"] == "gemini_vision")
chk("cloud OK -> engine multimodale", r["engine"] == "EBJ JEV Multimodal Vision 2026")
chk("cloud OK -> confidence del modello rispettata (0.71)", r["confidence"] == 0.71)
chk("cloud OK -> prezzo letto dal modello (180)", r["price_estimate_eur"] == 180.0)
chk("cloud OK -> nessun fallback_reason", "fallback_reason" not in r)
chk("cloud OK -> task_type echoato", r["task_type"] == "furniture_moving")
chk("cloud OK -> timestamp int", isinstance(r["timestamp"], int))

# 2. Quote/key esaurite: il template c'e' ancora ma e' marcato come tale
r = run_with(lambda *a, **k: Resp(200, ok_payload), keys={})
chk("senza chiave -> template marcato deterministic", r["appraisal_source"] == "deterministic_template")
chk("senza chiave -> vision_applied False", r["vision_applied"] is False)
chk("senza chiave -> fallback_reason no_api_key", r["fallback_reason"] == "no_api_key")
chk("senza chiave -> confidence azzerata (era 0.94 bugiardo)", r["confidence"] == 0.0)
chk("senza chiave -> engine dichiara che la foto non e' stata analizzata",
    "NON analizzata" in r["engine"])
chk("senza chiave -> il numero falsato 0.94 non compare", "0.94" not in json.dumps(r))

# 3. La forma del risultato non cambia: i consumatori esistenti non si rompono
keys_fall = set(r.keys())
for k in ("items", "total_volume_m3", "recommended_vehicle", "price_estimate_eur",
          "estimated_hours", "provider", "notes", "task_type", "engine", "timestamp"):
    chk(f"fallback mantiene la chiave '{k}'", k in keys_fall)
chk("fallback mantiene il listino template (490.0)", r["price_estimate_eur"] == 490.0)

# 4. HTTP di errore: il motivo finisce nel payload, non solo su stdout
r = run_with(lambda *a, **k: Resp(503, {}), task="doors_materials")
chk("http 503 -> fallback_reason gemini_http_503", r["fallback_reason"] == "gemini_http_503")
chk("http 503 -> perizia porte comunque marcata deterministic",
    r["appraisal_source"] == "deterministic_template")
chk("http 503 -> chiavi porte preservate",
    all(k in r for k in ("market_valuation", "fb_title", "signature")))

# 5. Eccezione di rete
def boom(*a, **k):
    raise RuntimeError("timeout simulato")
r = run_with(boom)
chk("eccezione -> fallback_reason gemini_error", r["fallback_reason"].startswith("gemini_error"))
chk("eccezione -> marcato deterministic", r["appraisal_source"] == "deterministic_template")

# 6. Immagine assente
r = run_with(lambda *a, **k: Resp(200, ok_payload), image="")
chk("senza immagine -> fallback_reason no_image_data", r["fallback_reason"] == "no_image_data")

# 7. OCR: nessun numero inventato restituito come se fosse stato letto
r = run_with(lambda *a, **k: Resp(200, ok_payload), keys={}, task="ocr_contacts")
blob = json.dumps(r, ensure_ascii=False)
chk("ocr fallback -> nessun recapito reale cablato", REAL_PHONE not in blob)
chk("ocr fallback -> phone_numbers vuoto", r["phone_numbers"] == [])
chk("ocr fallback -> company_name vuoto", r["company_name"] == "")
chk("ocr fallback -> dice di riprovare", "Riprovare" in r["notes"])
chk("ocr fallback -> vision_applied False", r["vision_applied"] is False)

# 8. Task sconosciuto: prima produceva lo stesso blocco OCR con confidence 0.90
r = run_with(lambda *a, **k: Resp(200, ok_payload), keys={}, task="nonsoche")
chk("task sconosciuto marcato come template", r["appraisal_source"] == "deterministic_template")
chk("task sconosciuto -> task_type echoato", r["task_type"] == "nonsoche")

# 9. Il cloud che risponde in testo libero non deve perdere il flag
freetext = {"candidates": [{"content": {"parts": [{"text": "Non e' JSON, solo prosa"}]}}]}
r = run_with(lambda *a, **k: Resp(200, freetext))
chk("cloud in prosa -> raw_analysis marcato come visione",
    r["appraisal_source"] == "gemini_vision" and r["raw_analysis"] == "Non e' JSON, solo prosa")

passed = sum(1 for _, c in CASES if c)
for name, c in CASES:
    print(("PASS " if c else "FAIL ") + name)
print("%d/%d" % (passed, len(CASES)))
sys.exit(0 if passed == len(CASES) else 1)
