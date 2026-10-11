#!/usr/bin/env bash
# ==============================================================================
# E.B.J. SUPREME · DEPLOY NOUS RESEARCH HERMES AGENT SU KALI / VPS ORACLE
# Ispirato a HackNovers & Nous Research (Video -1qf4Sxk7gw)
# ==============================================================================
set -e

echo "=== [1/4] Aggiornamento Dipendenze Kali / Debian ==="
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq && apt-get install -y -qq curl git python3 python3-pip ripgrep ffmpeg jq

echo "=== [2/4] Installazione Hermes Agent di Nous Research ==="
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash

echo "=== [3/4] Configurazione Provider Gratuito NVIDIA NIM (build.nvidia.com) ==="
mkdir -p ~/.hermes
cat << 'EOF' > ~/.hermes/config.json
{
  "provider": "nvidia",
  "base_url": "https://integrate.api.nvidia.com/v1",
  "default_model": "meta/llama-3.1-70b-instruct",
  "temperature": 0.4,
  "max_tokens": 4096,
  "auto_approval_mode": true,
  "guardrails": {
    "scope_enforcement": true,
    "authorized_domains": [
      "badrexpress.com",
      "eb.badrexpress.com",
      "pietrotraslochi.com",
      "tinoshop.it",
      "localhost",
      "127.0.0.1",
      "92.4.233.42"
    ]
  }
}
EOF

echo "=== [4/4] Creazione Bridge CLI Hermes per EBJ Studio ==="
cat << 'EOF' > /usr/local/bin/ebj-hermes
#!/usr/bin/env bash
# Wrapper per invocare Hermes Agent con le guardrail di Badr
exec hermes "$@"
EOF
chmod +x /usr/local/bin/ebj-hermes

echo "✅ Hermes Agent installato e pronto all'uso!"
echo "👉 Per avviare la chat interattiva: 'hermes'"
echo "👉 Per eseguire un task autonomo: 'hermes --task \"Scansiona le porte e audit di 92.4.233.42\"'"
