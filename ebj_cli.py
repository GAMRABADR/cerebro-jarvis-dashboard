# ==============================================================================
#  EBJ UNIFIED CLI DISPATCHER — J.A.R.V.I.S. Command Line Interface
#  Fast access to all Rust & Python OS Engines
# ==============================================================================

import sys
import json
import argparse
import requests

try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

RUST_URL = "http://127.0.0.1:9000"
PYTHON_URL = "http://127.0.0.1:8088"

def cmd_status(args):
    try:
        r = requests.get(f"{RUST_URL}/api/status", timeout=2)
        if r.status_code == 200:
            d = r.json()
            print("╔══════════════════════════════════════════════════════════════╗")
            print("║  E.B.J. AI-OS SUPERPOWER SYSTEM STATUS                       ║")
            print("╚══════════════════════════════════════════════════════════════╝")
            print(f" Status       : {d.get('status')} ({d.get('version')})")
            print(f" Platform     : {d.get('platform')}")
            print(f" Uptime       : {d.get('uptime_secs')}s")
            print(f" Latency Grade: {d.get('latency_grade')}")
            print(f" Gate         : {d.get('gate')}")
            print(f" Moduli Attivi: {len(d.get('modules', []))} moduli nativi Rust:")
            for m in d.get("modules", []):
                print(f"   [+] {m}")
        else:
            print(f"Errore HTTP: {r.status_code}")
    except Exception as e:
        print(f"Errore connessione a J.A.R.V.I.S. Core: {e}")

def cmd_fuzzy(args):
    query = " ".join(args.query)
    try:
        r = requests.post(f"{RUST_URL}/api/fuzzy/match-command", json={"query": query}, timeout=2)
        if r.status_code == 200:
            d = r.json()
            print(f"Query Input   : '{d.get('query')}'")
            print(f"Best Match    : '{d.get('best_match')}' (Confidenza Score: {d.get('best_score')})")
            print(f"Latenza Match : {d.get('latency_us')}µs")
            print("Top Candidati :")
            for m in d.get("matches", []):
                print(f"   * {m.get('candidate')} -> Score: {m.get('score')}")
        else:
            print(f"Errore: {r.status_code} - {r.text}")
    except Exception as e:
        print(f"Errore richiesta fuzzy: {e}")

def cmd_quote(args):
    payload = {
        "mq": args.mq,
        "piano_partenza": args.piano_p,
        "piano_arrivo": args.piano_a,
        "ascensore_partenza": not args.no_asc,
        "ascensore_arrivo": not args.no_asc,
        "km_trasferta": args.km
    }
    try:
        r = requests.post(f"{RUST_URL}/api/math/quote-estimate", json=payload, timeout=2)
        if r.status_code == 200:
            d = r.json()
            print("╔══════════════════════════════════════════════════════════════╗")
            print("║  PREVENTIVO ISTANTANEO RUST FAST MATH                        ║")
            print("╚══════════════════════════════════════════════════════════════╝")
            print(f" Totale Stimato : €{d.get('total_price')}")
            print(f" Volume Merci   : {d.get('volume_m3')} m³")
            print(f" Codice Pratica : {d.get('pratica_id')}")
            print(f" Latenza Calcolo: {d.get('execution_time_us')}µs")
        else:
            print(f"Errore: {r.status_code}")
    except Exception as e:
        print(f"Errore calcolo preventivo: {e}")

def cmd_excel(args):
    title = args.title or "Report Operativo EBJ"
    payload = {
        "title": title,
        "sheet_name": "Riepilogo",
        "headers": ["Modulo", "Tempo Esecuzione", "Affidabilita"],
        "rows": [
            ["Fuzzy Matcher", 0.00013, 0.999],
            ["Fast Math Pricing", 0.00002, 1.0],
            ["Vector PDF Forge", 0.00082, 1.0],
            ["Resilience Circuit", 0.00010, 1.0]
        ],
        "include_totals": False
    }
    try:
        r = requests.post(f"{RUST_URL}/api/office/generate-xlsx", json=payload, timeout=3)
        if r.status_code == 200:
            d = r.json()
            filename = d.get("filename")
            import base64
            with open(filename, "wb") as f:
                f.write(base64.b64decode(d.get("base64_content")))
            print(f" Foglio Excel generato con successo: {filename} ({d.get('bytes_size')} bytes in {d.get('latency_us')}µs)")
        else:
            print(f"Errore: {r.status_code}")
    except Exception as e:
        print(f"Errore generazione Excel: {e}")

def cmd_audio(args):
    sound = args.sound or "reactor_hum"
    try:
        r = requests.get(f"{RUST_URL}/api/audio/sample/{sound}", timeout=3)
        if r.status_code == 200:
            filename = f"{sound}.wav"
            with open(filename, "wb") as f:
                f.write(r.content)
            print(f" Audio sintetizzato scaricato: {filename} ({len(r.content)} bytes)")
        else:
            print(f"Errore: {r.status_code}")
    except Exception as e:
        print(f"Errore audio: {e}")

def main():
    parser = argparse.ArgumentParser(description="E.B.J. AI-OS Unified Command Line Interface")
    subparsers = parser.add_subparsers(dest="command", help="Comando disponibile")

    # status
    subparsers.add_parser("status", help="Mostra lo stato del microkernel Rust e dei moduli attivi")

    # fuzzy
    p_fuzzy = subparsers.add_parser("fuzzy", help="Valuta comandi imperfetti con l'algoritmo Skim V2 in microsecondi")
    p_fuzzy.add_argument("query", nargs="+", help="Testo o comando imperfetto da valutare")

    # quote
    p_quote = subparsers.add_parser("quote", help="Calcola un preventivo istantaneo con Fast Math Rust")
    p_quote.add_argument("--mq", type=int, default=50, help="Metri quadri")
    p_quote.add_argument("--piano-p", type=int, default=1, help="Piano partenza")
    p_quote.add_argument("--piano-a", type=int, default=1, help="Piano arrivo")
    p_quote.add_argument("--km", type=int, default=5, help="Chilometri trasferta")
    p_quote.add_argument("--no-asc", action="store_true", help="Senza ascensore")

    # excel
    p_excel = subparsers.add_parser("excel", help="Genera un foglio di calcolo XLSX nativo")
    p_excel.add_argument("--title", type=str, default="Report Operativo EBJ", help="Titolo report")

    # audio
    p_audio = subparsers.add_parser("audio", help="Genera e scarica un file audio WAV sintetizzato nativamente")
    p_audio.add_argument("--sound", type=str, choices=["reactor_hum", "lock_beep", "access_granted", "stark_chime"], default="reactor_hum")

    # clean (Garbage Collector & Vacuum)
    subparsers.add_parser("clean", help="Esegue la pulizia dei file temporanei, cache e ottimizza il database SQLite")

    # upgrade (Continuous Upgrade & Health Validation)
    subparsers.add_parser("upgrade", help="Verifica l'integrita del sistema ed esegue la suite completa di test")

    # notify (Windows Native Toast Notification)
    p_notify = subparsers.add_parser("notify", help="Emette una notifica desktop nativa Windows con banner J.A.R.V.I.S.")
    p_notify.add_argument("--title", type=str, default="J.A.R.V.I.S. AI-OS", help="Titolo della notifica")
    p_notify.add_argument("--msg", type=str, default="Tutti i sistemi sono a pieno regime.", help="Messaggio del toast")

    # hardware (Hardware Vitals Telemetry)
    subparsers.add_parser("hardware", help="Mostra i parametri vitali di sistema (CPU, RAM, Threads)")

    # build (High-Speed Compiler)
    p_build = subparsers.add_parser("build", help="Compila l'ecosistema in Rust con ottimizzazioni native AVX2")
    p_build.add_argument("--release", action="store_true", help="Compila in modalita Release (massima velocita)")

    args = parser.parse_args()

    if args.command == "status":
        cmd_status(args)
    elif args.command == "fuzzy":
        cmd_fuzzy(args)
    elif args.command == "quote":
        cmd_quote(args)
    elif args.command == "excel":
        cmd_excel(args)
    elif args.command == "audio":
        cmd_audio(args)
    elif args.command == "clean":
        import ebj_maintenance
        ebj_maintenance.clean_workspace()
    elif args.command == "upgrade":
        import ebj_maintenance
        ebj_maintenance.upgrade_system()
    elif args.command == "notify":
        import ebj_maintenance
        ebj_maintenance.send_windows_toast(args.title, args.msg)
    elif args.command == "hardware":
        import ebj_maintenance
        ebj_maintenance.get_hardware_telemetry()
    elif args.command == "build":
        import ebj_maintenance
        ebj_maintenance.build_ecosystem(release=args.release)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
