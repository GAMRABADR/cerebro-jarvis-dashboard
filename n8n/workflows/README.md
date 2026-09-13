# EBJ_H — Commander + Famiglie (n8n + Rust)

Architettura **1 Commander + 7 Famiglie** al posto di 123 workflow separati.
Un solo punto d'ingresso, allowlist unica in RAM (Rust Actix :9000), esecuzione
difensiva via Hermes nel container Kali. Un tool per job, `--help` come default.

## Componenti

- **Rust hot-path** (`jarvis-bridge` Actix, porta `9000`)
  - `GET  /api/ebj-h/catalog`  → catalogo tool + sha256 (caricato UNA volta all'avvio)
  - `GET  /api/ebj-h/families` → mappa Famiglia → categorie → tool + webhook
  - `POST /api/ebj-h/dispatch` → valida allowlist + metacaratteri + coerenza famiglia
    in **microsecondi**, poi inoltra a Hermes (`http://127.0.0.1:8088/api/kali/exec`).
    Override: `EBJ_H_EXEC_URL`, `EBJ_H_CATALOG`.
- **n8n workflows** (questa cartella)
  - `EBJ_H_COMMANDER.json`  → webhook `ebj-h-commander` (accetta anche `family`)
  - `EBJ_H_RECON.json`      → webhook `ebj-h-recon`
  - `EBJ_H_WEB.json`        → webhook `ebj-h-web`
  - `EBJ_H_PASSWORD.json`   → webhook `ebj-h-password`
  - `EBJ_H_WIRELESS.json`   → webhook `ebj-h-wireless`
  - `EBJ_H_RETE.json`       → webhook `ebj-h-rete`   (rete + identity)
  - `EBJ_H_VULN.json`       → webhook `ebj-h-vuln`   (vuln + hardening + forensics + reverse + utilita)
  - `EBJ_H_MOBILE.json`     → webhook `ebj-h-mobile`

Ogni famiglia forza il proprio `family`, così il bridge Rust rifiuta i tool fuori
categoria (`FAMILY_MISMATCH`). Se il bridge Rust è irraggiungibile, ogni workflow
ha un **fallback** diretto su Hermes `:8088`.

## Flusso

```
n8n Webhook (POST) → Rust :9000/api/ebj-h/dispatch → Hermes :8088/api/kali/exec
                          │ (allowlist µs)                  │ (SSH → docker exec Kali)
                          └── fallback ─────────────────────┘
```

## Payload

```json
{ "tool": "nmap", "args": ["--help"], "action": "run" }
```

- `tool`   obbligatorio, deve stare nell'allowlist del catalogo.
- `args`   opzionale (lista o stringa). Assente ⇒ `["--help"]`.
- `family` opzionale sul Commander; imposto d'ufficio nelle famiglie.
- `action` `run` (default) | `which`.

## Trigger

```bash
# Commander (qualsiasi tool)
curl -X POST http://127.0.0.1:5678/webhook/ebj-h-commander \
  -H "Content-Type: application/json" \
  -d '{"tool":"nmap","args":["--version"]}'

# Famiglia dedicata
curl -X POST http://127.0.0.1:5678/webhook/ebj-h-recon \
  -H "Content-Type: application/json" \
  -d '{"tool":"whatweb"}'

# Diretto sul bridge Rust (bypass n8n)
curl -X POST http://127.0.0.1:9000/api/ebj-h/dispatch \
  -H "Content-Type: application/json" \
  -d '{"tool":"nuclei","family":"web","args":["--help"]}'
```

## Import in n8n

Locale `http://127.0.0.1:5678` oppure VPS `http://92.4.233.42:5678`.

- **UI**: *Workflows → Import from File* per ognuno degli 8 JSON, poi *Activate*.
- **API** (senza stampare credenziali):
  ```bash
  for f in EBJ_H_*.json; do
    curl -s -X POST "$N8N_URL/api/v1/workflows" \
      -H "X-N8N-API-KEY: $N8N_API_KEY" \
      -H "Content-Type: application/json" \
      --data-binary "@$f" >/dev/null && echo "imported $f"
  done
  ```
  Attiva i workflow dalla UI dopo l'import (i webhook diventano live).

## Policy difensiva

Solo host di proprietà dell'operatore (Hermes applica lo scope). Nessun exploit,
nessun cracker, nessun attacco WiFi/4G: il bridge Rust fa solo validazione+inoltro.
