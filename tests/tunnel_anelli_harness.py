#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Harness dei DUE ANELLI del watchdog locale.

    python tests/tunnel_anelli_harness.py

Perche' esiste: il check vecchio (`check_public_tunnel`) chiedeva
`requests.get(PUBLIC_URL, allow_redirects=True)` e si dichiarava verde su
200/301/302/308. Dietro `eb.badrexpress.com` c'e' Cloudflare Access, che
risponde 302 verso il proprio idP SENZA mai toccare il tunnel: la riga
"Tunnel pubblico OK" nel log restava verde anche con cloudflared spento, e
misurava l'esistenza di Cloudflare invece che del servizio. Misurato
2026-10-13: `https://eb.badrexpress.com/` -> 302 ->
`ebgstudio.cloudflareaccess.com/cdn-cgi/access/login/...`, mentre la prova
vera (`http://127.0.0.1:20241/ready`) rispondeva 200.

Qui non si tocca nessuna rete e nessun processo reale: il modulo viene
importato e le sue sonde sostituite.
"""
import importlib.util
import os
import re
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET = os.path.join(BASE, "tunnel_watchdog_supervisor.py")

spec = importlib.util.spec_from_file_location("tw", TARGET)
tw = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tw)

VISTI = {"log": [], "kill": 0, "start": 0, "http": []}

# Le sonde vengono sostituite caso per caso: senza questo salvataggio il setup
# del caso dopo avrebbe chiamato le lambda del caso precedente invece delle
# funzioni vere (e A4/A5/A6 sarebbero passati vuoti).
ORIG = {n: getattr(tw, n) for n in
        ("connector_ready", "edge_answers", "start_cloudflared",
         "is_cloudflared_os_alive", "requests", "subprocess", "log")}


def setup(mod):
    for nome, fn in ORIG.items():
        setattr(mod, nome, fn)
    mod.log = lambda msg, level="INFO": VISTI["log"].append((level, msg))
    mod.is_port_responding = lambda port: True
    mod.time.sleep = lambda s: None

    class FakeSub:
        def run(self, cmd, **kw):
            if "taskkill" in cmd[0]:
                VISTI["kill"] += 1
            return None

        def Popen(self, cmd, **kw):
            VISTI.setdefault("popen", []).append((cmd, kw))
            return None

    mod.subprocess = FakeSub()
    mod.start_cloudflared = lambda: (VISTI.__setitem__("start", VISTI["start"] + 1), "PROC")[1]

    def fake_get(url, **kw):
        VISTI["http"].append((url, kw))

        class R:
            status_code = 200
        return R()

    class FakeReq:
        get = staticmethod(fake_get)

    mod.requests = FakeReq()
    VISTI["log"].clear(); VISTI["kill"] = 0; VISTI["start"] = 0; VISTI["http"].clear()


ok = fail = 0


def check(cond, cosa):
    global ok, fail
    if cond:
        ok += 1
        print("  ok:", cosa)
    else:
        fail += 1
        print("  MANCA:", cosa)


def righe(testo):
    return [m for _, m in VISTI["log"] if testo in m]


print("=== A1: anello CONNETTORE rotto -> cloudflared riavviato ===")
setup(tw)
tw.connector_ready = lambda: False
tw.edge_answers = lambda: True
esito = tw.tunnel_step()
check(esito == "riavviato", "esito 'riavviato'")
check(VISTI["kill"] == 1 and VISTI["start"] == 1, "esattamente 1 kill + 1 avvio")
check(righe("Anello CONNETTORE rotto"), "il log nomina l'anello rotto, non 'tunnel non raggiungibile'")

print("=== A2: connettore OK, edge KO -> NON riavviare (il caso Access) ===")
setup(tw)
tw.connector_ready = lambda: True
tw.edge_answers = lambda: False
esito = tw.tunnel_step()
check(esito == "non-toccare", "esito 'non-toccare'")
check(VISTI["kill"] == 0 and VISTI["start"] == 0, "nessun kill e nessun avvio: un trasporto sano non si ammazza")
check(righe("DNS/Cloudflare"), "il log dice quale anello e' colpevole")

print("=== A3: entrambi verdi -> verde davvero, e dice cosa ha misurato ===")
setup(tw)
tw.connector_ready = lambda: True
tw.edge_answers = lambda: True
esito = tw.tunnel_step()
check(esito == "ok", "esito 'ok'")
check(righe("connettore:agganciato") and righe("edge:rISPONDE"),
      "la riga verde nomina TUTTI e due gli anelli")

print("=== A4: edge_answers non segue i redirect (era il difetto) ===")
setup(tw)
tw.edge_answers()
chiamate = [(u, k.get("allow_redirects")) for u, k in VISTI["http"]]
check(any(u == tw.PUBLIC_URL and r is False for u, r in chiamate),
      "GET su PUBLIC_URL con allow_redirects=False")
check(not any(r is True for _, r in chiamate), "nessuna chiamata con allow_redirects=True")

print("=== A5: connector_ready bussa alla porta di stato di cloudflared ===")
setup(tw)
tw.connector_ready()
check(any(u == tw.CF_READY_URL for u, _ in VISTI["http"]),
      f"GET su {tw.CF_READY_URL}")

class Non200:
    status_code = 503

class Req503:
    @staticmethod
    def get(url, **kw):
        return Non200()

tw.requests = Req503()
check(tw.connector_ready() is False, "503 sulla /ready = connettore NON pronto (solo 200 conta)")

class Esplode:
    @staticmethod
    def get(url, **kw):
        raise RuntimeError("connection refused")

tw.requests = Esplode()
check(tw.connector_ready() is False and tw.edge_answers() is False,
      "sonda che esplode = False, non eccezione che ammutolisce il ciclo")

print("=== A6: senza token il tunnel non parte, e il log dice quale slot riempire ===")
setup(tw)
tw.CF_TOKEN = ""
tw.is_cloudflared_os_alive = lambda: False
VISTI["popen"] = []
proc = ORIG["start_cloudflared"]()   # la funzione vera, con i globale gia' sostituiti
check(proc is None, "nessun processo restituito")
check(not VISTI.get("popen"), "NESSUNA Popen: nessun tentativo a vuoto che innesca il backoff")
check(righe("CF_TUNNEL_TOKEN"), "il log nomina lo slot da popolare")

print("=== A7: guardia anti-regressione sul sorgente ===")
src = open(TARGET, encoding="utf-8").read()
check(not re.search(r'CF_TOKEN\s*=\s*"eyJ', src), "nessun token cloudflared letterale nel sorgente")
check('"--token"' not in src, "il token non viaggia piu' in argv (leggibile da tasklist)")
check("check_public_tunnel" not in src, "il vecchio check a 302 non e' piu' richiamabile")

print()
print(f"verde {ok} / rosso {fail}")
sys.exit(1 if fail else 0)
