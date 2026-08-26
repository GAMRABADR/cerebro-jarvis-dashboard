import tkinter as tk
from tkinter import ttk, messagebox
import requests
import threading

UNSLOTH_PORT = 61517
MODEL_NAME = "Blackfrost-AI/Qwen3.8-27B-ABLITERATED-GGUF"

def send_query():
    prompt = text_input.get("1.0", tk.END).strip()
    if not prompt: return
    
    btn_send.config(state=tk.DISABLED, text="Generazione GPU in corso...")
    lbl_status.config(text="⚡ Elaborazione su GPU NVIDIA (Unsloth Qwen 3.8)...", foreground="#00ff9f")
    
    def _run():
        try:
            url = f"http://127.0.0.1:{UNSLOTH_PORT}/v1/chat/completions"
            payload = {
                "model": MODEL_NAME,
                "messages": [
                    {"role": "system", "content": "Sei l'assistente IA di Ingegner Badr. Rispondi con precisione e stile chiaro."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.6,
                "max_tokens": 800
            }
            r = requests.post(url, json=payload, timeout=60)
            if r.status_code == 200:
                ans = r.json()["choices"][0]["message"]["content"].strip()
                root.after(0, lambda: show_result(ans))
            else:
                root.after(0, lambda: show_error(f"Errore HTTP {r.status_code}: {r.text}"))
        except Exception as e:
            root.after(0, lambda: show_error(f"Errore connessione Unsloth: {e}"))
            
    threading.Thread(target=_run, daemon=True).start()

def show_result(text):
    text_output.config(state=tk.NORMAL)
    text_output.delete("1.0", tk.END)
    text_output.insert(tk.END, text)
    text_output.config(state=tk.DISABLED)
    btn_send.config(state=tk.NORMAL, text="⚡ Esegui su Qwen 3.8")
    lbl_status.config(text="✅ Risposta generata con successo!", foreground="#00f0ff")

def show_error(err):
    lbl_status.config(text=f"❌ {err}", foreground="#ff4444")
    btn_send.config(state=tk.NORMAL, text="⚡ Esegui su Qwen 3.8")

root = tk.Tk()
root.title("E.B.J. - Azione Rapida Qwen 3.8 Locale (Unsloth GPU)")
root.geometry("680x520")
root.configure(bg="#0a0e17")

lbl_title = tk.Label(root, text="⚡ E.B.J. QUICK ACTION · QWEN 3.8 LOCALE (UNSLOTH)", font=("Segoe UI", 12, "bold"), fg="#00ff9f", bg="#0a0e17")
lbl_title.pack(pady=10)

text_input = tk.Text(root, height=4, font=("Segoe UI", 10), bg="#111928", fg="#ffffff", insertbackground="#00ff9f", relief=tk.FLAT, padx=8, pady=8)
text_input.pack(fill=tk.X, padx=15, pady=5)
text_input.insert(tk.END, "Scrivi qui la tua richiesta per Qwen 3.8...")

btn_send = tk.Button(root, text="⚡ Esegui su Qwen 3.8", font=("Segoe UI", 11, "bold"), bg="#00ff9f", fg="#0a0e17", activebackground="#00f0ff", cursor="hand2", relief=tk.FLAT, command=send_query)
btn_send.pack(pady=8)

lbl_status = tk.Label(root, text="Pronto. Connesso a Unsloth porta 61517.", font=("Segoe UI", 9), fg="#8892b0", bg="#0a0e17")
lbl_status.pack()

text_output = tk.Text(root, height=12, font=("Segoe UI", 10), bg="#050811", fg="#00f0ff", relief=tk.FLAT, padx=8, pady=8, state=tk.DISABLED)
text_output.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

root.mainloop()
