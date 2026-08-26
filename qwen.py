import sys
import requests
import json

UNSLOTH_PORT = 61517
MODEL_NAME = "Blackfrost-AI/Qwen3.8-27B-ABLITERATED-GGUF"

def ask_qwen(prompt_text):
    if not prompt_text:
        print("Uso: python qwen.py \"La tua domanda qui\"")
        return
    
    url = f"http://127.0.0.1:{UNSLOTH_PORT}/v1/chat/completions"
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": "Sei l'assistente IA locale di Ingegner Badr. Rispondi con precisione e chiarezza."},
            {"role": "user", "content": prompt_text}
        ],
        "temperature": 0.6,
        "max_tokens": 800
    }
    
    try:
        r = requests.post(url, json=payload, timeout=60)
        if r.status_code == 200:
            res = r.json()["choices"][0]["message"]["content"].strip()
            print(res)
        else:
            print(f"Errore Unsloth HTTP {r.status_code}: {r.text}")
    except Exception as e:
        print(f"Errore connessione a Unsloth porta {UNSLOTH_PORT}: {e}")

if __name__ == "__main__":
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else ""
    ask_qwen(query)
