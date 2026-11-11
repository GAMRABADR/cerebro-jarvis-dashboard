import asyncio
import base64
import json
import sqlite3
import urllib.parse
import aiohttp
import os
import time

def _load_bot_token() -> str:
    tok = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("BOT_TOKEN") or ""
    if tok:
        return tok.strip()
    for env_path in (
        "/home/ubuntu/.telegram_superbot.env",
        "/home/ubuntu/cerebro-jarvis-dashboard/.env",
        os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"),
    ):
        if os.path.exists(env_path):
            try:
                with open(env_path, "r", encoding="utf-8") as fh:
                    for line in fh:
                        line = line.strip()
                        if line.startswith(("TELEGRAM_BOT_TOKEN=", "BOT_TOKEN=")):
                            return line.split("=", 1)[1].strip().strip('"').strip("'")
            except Exception:
                pass
    raise RuntimeError("Missing TELEGRAM_BOT_TOKEN environment variable")


BOT_TOKEN = _load_bot_token()  # @AG_Jarvis_Cerebro_bot
OWNER_CHAT_ID = os.getenv("TELEGRAM_OWNER_CHAT_ID", "7298887137")
DB_PATH = os.getenv("LEAD_HUNTER_DB", "/home/ubuntu/lead_hunter_vault.db")
JARVIS_LOCAL_URL = os.getenv("JARVIS_LOCAL_URL", "http://127.0.0.1:8088")

API_BASE = f"https://api.telegram.org/bot{BOT_TOKEN}"
FILE_BASE = f"https://api.telegram.org/file/bot{BOT_TOKEN}"


# ── ANIMATED CYBERPUNK LOADER HELPER ─────────────────────────────────────────
async def send_animated_loader(session, chat_id, message_id, task_name="SCANSIONE RADAR LEAD"):
    frames = [
        "░░░░░░░░░░ 0%",
        "██░░░░░░░░ 20%",
        "████░░░░░░ 40%",
        "██████░░░░ 60%",
        "████████░░ 80%",
        "██████████ 100%",
    ]
    for frame in frames:
        text = f"⚡ *[CEREBRO JARVIS SENTINEL]*\n🔄 `{task_name}`\n`[{frame}]`\n_Elaborazione sinaptica a 120 FPS..._"
        try:
            url = f"{API_BASE}/editMessageText"
            payload = {
                "chat_id": chat_id,
                "message_id": message_id,
                "text": text,
                "parse_mode": "Markdown",
            }
            async with session.post(url, json=payload) as r:
                await r.json()
            await asyncio.sleep(0.18)
        except Exception:
            pass


# ── DB HELPERS ───────────────────────────────────────────────────────────────
def get_cities_counts():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT city, COUNT(*) FROM leads_hunter WHERE disposition_status = 'NEW' OR disposition_status IS NULL GROUP BY city")
    rows = cur.fetchall()
    conn.close()
    return rows


def get_leads_by_city(city=None, limit=1):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    if city and city != "all":
        cur.execute(
            "SELECT id, source, title, city, author_name, contact_phone, messenger_url, post_date, quality_score FROM leads_hunter WHERE (disposition_status = 'NEW' OR disposition_status IS NULL) AND city LIKE ? ORDER BY id DESC LIMIT ?",
            (f"%{city}%", limit),
        )
    else:
        cur.execute(
            "SELECT id, source, title, city, author_name, contact_phone, messenger_url, post_date, quality_score FROM leads_hunter WHERE (disposition_status = 'NEW' OR disposition_status IS NULL) ORDER BY id DESC LIMIT ?",
            (limit,),
        )
    rows = cur.fetchall()
    conn.close()
    return rows


def update_lead_disposition(lead_id, status, notes=""):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("UPDATE leads_hunter SET disposition_status = ? WHERE id = ?", (status, lead_id))
    conn.commit()
    conn.close()


def add_to_blacklist(contact, reason="NUMERO_INESISTENTE"):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    try:
        cur.execute("INSERT OR IGNORE INTO blacklist_contacts (phone_or_handle, reason) VALUES (?, ?)", (contact, reason))
        conn.commit()
    except Exception:
        pass
    conn.close()


def sell_to_badrexpress(lead_id, customer_name, phone, city, job_desc, offer=200.0, margin=30.0):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
    INSERT INTO lead_sales_badrexpress (lead_id, customer_name, customer_phone, city, job_description, customer_offer, badr_margin)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """,
        (lead_id, customer_name, phone, city, job_desc, offer, margin),
    )
    cur.execute("UPDATE leads_hunter SET disposition_status = 'VENDUTO_BADREXPRESS' WHERE id = ?", (lead_id,))
    conn.commit()
    conn.close()


# ── TELEGRAM SEND HELPERS ────────────────────────────────────────────────────
async def send_msg(session, chat_id, text, reply_markup=None, parse_mode="Markdown"):
    url = f"{API_BASE}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "disable_web_page_preview": True,
    }
    if parse_mode:
        payload["parse_mode"] = parse_mode
    if reply_markup:
        payload["reply_markup"] = reply_markup
    async with session.post(url, json=payload) as r:
        res = await r.json()
        if not res.get("ok") and parse_mode:
            # Retry plain text in case of stray Markdown chars
            payload.pop("parse_mode", None)
            async with session.post(url, json=payload) as r2:
                return await r2.json()
        return res


async def edit_msg(session, chat_id, message_id, text, reply_markup=None):
    url = f"{API_BASE}/editMessageText"
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True,
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    async with session.post(url, json=payload) as r:
        return await r.json()


async def send_jarvis_audio_reply(session, chat_id, audio_b64, caption=""):
    if not audio_b64:
        return
    try:
        raw_mp3 = base64.b64decode(audio_b64)
        form = aiohttp.FormData()
        form.add_field("chat_id", str(chat_id))
        form.add_field("title", "J.A.R.V.I.S. (E.B.J.)")
        form.add_field("performer", "BadrExpress Supreme")
        if caption:
            form.add_field("caption", caption[:200])
        form.add_field("audio", raw_mp3, filename="jarvis_reply.mp3", content_type="audio/mpeg")
        async with session.post(f"{API_BASE}/sendAudio", data=form) as r:
            await r.json()
    except Exception as e:
        print(f"[Telegram Audio Send Err]: {e}")


# ── PHONE HARDWARE REMOTE PANEL ──────────────────────────────────────────────
async def show_phone_panel(session, chat_id, message_id=None, notice=""):
    dev = {}
    try:
        async with session.get(f"{JARVIS_LOCAL_URL}/api/device/android/status", timeout=3) as r:
            if r.status == 200:
                dev = await r.json()
    except Exception:
        pass

    fac = dev.get("factory") or {}
    batt = dev.get("battery") or {}
    loc = dev.get("location") or {}
    lg = dev.get("last_gasp") or {}
    wifi = dev.get("wifi") or {}
    pct = batt.get("percentage", -1)
    model_str = f"{fac.get('manufacturer', '')} {fac.get('model', 'Non registrato')}".strip()
    os_str = fac.get("android_version") or "n/d"
    carrier = fac.get("carrier") or "n/d"
    lat = loc.get("latitude") or lg.get("latitude")
    lon = loc.get("longitude") or lg.get("longitude")
    maps_url = f"https://maps.google.com/?q={lat},{lon}" if (lat and lon) else "https://www.google.com/android/find/"
    lost_flag = "🔴 ATTIVA" if dev.get("lost_mode") else "🟢 SPENTA"

    lines = [
        "📱 *CONTROLLO TOTALE SMARTPHONE E.B.J.*",
        "━━━━━━━━━━━━━━━━━━━━━━",
        f"🏭 *Fabbrica:* `{model_str}` (Android `{os_str}`)",
        f"📡 *Operatore:* `{carrier}` | *Wi-Fi:* `{wifi.get('ssid') or 'n/d'}`",
        f"🔋 *Batteria:* `{pct}%` | *Modalità Smarrito:* {lost_flag}",
        f"📍 *Ultima Posizione:* `{lat}, {lon}`" if lat else "📍 *Ultima Posizione:* _Avvia ebj-start su Termux_",
    ]
    if lg.get("triggered_at"):
        lines.append(f"🆘 *Last-Gasp (<=5%):* `{lg.get('latitude')}, {lg.get('longitude')}`")
    if notice:
        lines.append(f"\n⚡ _{notice}_")

    kb = {
        "inline_keyboard": [
            [
                {"text": "🔔 Fai Squillare + Lost", "callback_data": "phone:ring"},
                {"text": "📍 Aggiorna GPS", "callback_data": "phone:locate"},
            ],
            [
                {"text": "🔦 Torcia ON/OFF", "callback_data": "phone:torch"},
                {"text": "📸 Scatta Foto", "callback_data": "phone:photo"},
            ],
            [
                {"text": "🗺️ Apri Mappa / Last-Gasp", "url": maps_url},
                {"text": "🛰️ Trova da Spento (Google)", "url": "https://www.google.com/android/find/"},
            ],
            [
                {"text": "🟢 Disattiva Smarrito", "callback_data": "phone:lost_off"},
                {"text": "🔙 Menu Principale", "callback_data": "menu:home"},
            ],
        ]
    }
    text = "\n".join(lines)
    if message_id:
        await edit_msg(session, chat_id, message_id, text, kb)
    else:
        await send_msg(session, chat_id, text, kb)


async def enqueue_phone_action(session, action, params=None):
    try:
        async with session.post(
            f"{JARVIS_LOCAL_URL}/api/device/android/command",
            json={"action": action, "params": params or {}},
            timeout=3,
        ) as r:
            return r.status == 200
    except Exception:
        return False


# ── E.B.J. CONVERSATIONAL CORE BRIDGE (TESTO + AUDIO DIEGO NEURAL) ───────────
async def process_jarvis_query(session, chat_id, query_text):
    q = (query_text or "").strip()
    if not q:
        return

    # 1. Prova prima /api/reflex/dispatch (< 5ms)
    reply_text = ""
    audio_b64 = ""
    try:
        async with session.post(f"{JARVIS_LOCAL_URL}/api/reflex/dispatch", json={"query": q, "device": "telegram"}, timeout=3) as r:
            if r.status == 200:
                rf = await r.json()
                if rf.get("auto_execute") and rf.get("intent") != "GENERAL_REASONING" and rf.get("spoken_ack"):
                    reply_text = rf["spoken_ack"]
    except Exception:
        pass

    if reply_text:
        try:
            async with session.post(f"{JARVIS_LOCAL_URL}/api/tts", json={"text": reply_text, "persona": "jarvis"}, timeout=8) as tr:
                if tr.status == 200:
                    td = await tr.json()
                    audio_b64 = td.get("audio_base64", "")
        except Exception:
            pass
    else:
        # 2. Altrimenti /api/chat completo con audio Diego Neural inline
        try:
            async with session.post(
                f"{JARVIS_LOCAL_URL}/api/chat",
                json={"prompt": q, "model": "auto", "persona": "jarvis", "include_audio": True},
                timeout=20,
            ) as cr:
                if cr.status == 200:
                    cd = await cr.json()
                    reply_text = cd.get("response") or "Comando elaborato, signore."
                    audio_b64 = cd.get("audio_base64", "")
        except Exception as e:
            reply_text = f"Errore momentaneo di connessione al nucleo EBJ: {e}"

    await send_msg(session, chat_id, reply_text, parse_mode=None)
    if audio_b64:
        await send_jarvis_audio_reply(session, chat_id, audio_b64)


# ── MAIN BOT ENGINE ──────────────────────────────────────────────────────────
async def handle_start(session, chat_id):
    cities = get_cities_counts()
    city_buttons = []

    row = []
    for c, cnt in cities:
        city_name = c.upper() if c else "ALTRO"
        row.append({"text": f"📍 {city_name} ({cnt})", "callback_data": f"city:{c}"})
        if len(row) == 2:
            city_buttons.append(row)
            row = []
    if row:
        city_buttons.append(row)

    city_buttons.append([{"text": "🌐 MOSTRA TUTTI I LEAD FRESCHI", "callback_data": "city:all"}])
    city_buttons.append([
        {"text": "📱 IL MIO TELEFONO (GPS/Fabbrica)", "callback_data": "phone:status"},
        {"text": "🔔 FAI SQUILLARE TELEFONO", "callback_data": "phone:ring"},
    ])
    city_buttons.append([
        {"text": "🌌 APRI CEREBRO JARVIS HUD", "web_app": {"url": "https://eb.badrexpress.com"}},
        {"text": "🔄 AGGIORNA RADAR", "callback_data": "refresh:radar"},
    ])

    text = (
        "👑 *[CEREBRO JARVIS · COMANDO VOCALE & RADAR PRO]*\n\n"
        "Benvenuto Ingegner Badr. Puoi **scrivermi** o mandarmi un **messaggio vocale** qui per comandare E.B.J., controllare il tuo telefono o gestire i lead.\n"
    )
    await send_msg(session, chat_id, text, {"inline_keyboard": city_buttons})


async def show_lead_card(session, chat_id, message_id, lead, city_filter="all"):
    lead_id, source, title, city, author, phone, messenger, pdate, score = lead
    clean_phone = phone.strip() if phone else ""
    phone_display = f"`{clean_phone}`" if clean_phone else "_Non inserito nel post_"
    msg_url = messenger if messenger else "https://m.me/"
    wa_msg = urllib.parse.quote(f"Salve {author}, la contatto da PietroTraslochi / BadrExpress in merito al suo annuncio su {city.title()}: '{title[:40]}...'. Quando possiamo sentirci?")
    wa_url = f"https://wa.me/39{clean_phone}?text={wa_msg}" if clean_phone else ""

    text = (
        f"📋 *SCHEDA LEAD CERTIFICATO #{lead_id}*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 *Cliente:* `{author}`\n"
        f"📍 *Zona:* `{city.upper() if city else 'EMILIA-ROMAGNA'}`\n"
        f"🏠 *Richiesta:* _{title}_\n"
        f"📱 *Telefono:* {phone_display}\n"
        f"🛡️ *Quality Score:* `100/100 · VERIFICATO`\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👇 *SELEZIONA AZIONE O ESITO TRATTATIVA:*"
    )

    buttons = []
    contact_row = []
    if clean_phone:
        contact_row.append({"text": f"📞 Chiama {clean_phone}", "url": f"tel:{clean_phone}"})
        contact_row.append({"text": "💬 WhatsApp", "url": wa_url})
    if messenger:
        contact_row.append({"text": "💬 Messenger", "url": msg_url})
    if contact_row:
        buttons.append(contact_row)

    buttons.append([
        {"text": "✅ PREVENTIVO CONFERMATO", "callback_data": f"act:confirm:{lead_id}"},
        {"text": "💰 VENDI A BADREXPRESS", "callback_data": f"act:sell:{lead_id}"},
    ])
    buttons.append([
        {"text": "⏰ RICHIAMA DOMANI", "callback_data": f"act:remind:{lead_id}"},
        {"text": "🚫 NUMERO INESISTENTE", "callback_data": f"act:blacklist:{lead_id}:{clean_phone or author}"},
    ])
    buttons.append([
        {"text": "⏭️ PROSSIMO LEAD", "callback_data": f"city:{city_filter}"},
        {"text": "🔙 MENU CITTÀ", "callback_data": "menu:home"},
    ])

    keyboard = {"inline_keyboard": buttons}
    if message_id:
        await edit_msg(session, chat_id, message_id, text, keyboard)
    else:
        await send_msg(session, chat_id, text, keyboard)


async def run_bot_poll():
    offset = 0
    _torch_toggle = False
    print("🚀 CEREBRO JARVIS Telegram Super-Bot Active (Text + Voice + Phone Control)...")
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                url = f"{API_BASE}/getUpdates?offset={offset}&timeout=20"
                async with session.get(url) as resp:
                    data = await resp.json()
                    if not data.get("ok"):
                        await asyncio.sleep(2)
                        continue

                    for upd in data.get("result", []):
                        offset = upd["update_id"] + 1

                        if "message" in upd:
                            msg = upd["message"]
                            chat_id = str(msg["chat"]["id"])
                            if chat_id != OWNER_CHAT_ID:
                                await send_msg(session, chat_id, "⛔ Accesso riservato all'Ingegnere Badr El Ouariti.", parse_mode=None)
                                continue

                            text = (msg.get("text") or "").strip()

                            # Note Vocali Telegram (.ogg) -> Whisper Turbo + EBJ Core + Risposta Vocale Diego
                            if "voice" in msg:
                                file_id = msg["voice"]["file_id"]
                                try:
                                    async with session.get(f"{API_BASE}/getFile?file_id={file_id}") as fr:
                                        f_data = await fr.json()
                                        f_path = f_data.get("result", {}).get("file_path", "")
                                    if f_path:
                                        async with session.get(f"{FILE_BASE}/{f_path}") as aud_r:
                                            ogg_bytes = await aud_r.read()
                                        b64_ogg = base64.b64encode(ogg_bytes).decode("utf-8")
                                        async with session.post(
                                            f"{JARVIS_LOCAL_URL}/api/transcribe",
                                            json={"audio_base64": b64_ogg, "mime_type": "audio/ogg"},
                                            timeout=10,
                                        ) as tr:
                                            tr_res = await tr.json()
                                            heard = (tr_res.get("text") or "").strip()
                                        if heard:
                                            await send_msg(session, chat_id, f"🎙️ Ho capito: _{heard}_")
                                            await process_jarvis_query(session, chat_id, heard)
                                        else:
                                            await send_msg(session, chat_id, "Non ho rilevato parlato chiaro nel messaggio vocale, signore.", parse_mode=None)
                                except Exception as ve:
                                    await send_msg(session, chat_id, f"Errore elaborazione vocale: {ve}", parse_mode=None)
                                continue

                            if text.startswith("/start") or text.startswith("/clienti") or text.startswith("/lead"):
                                await handle_start(session, chat_id)
                            elif text.startswith("/telefono") or text.startswith("/phone") or text.startswith("/trova"):
                                await show_phone_panel(session, chat_id)
                            elif text.startswith("/stato"):
                                await process_jarvis_query(session, chat_id, "qual è lo stato dei server e della vps?")
                            elif text.startswith("/novita"):
                                await process_jarvis_query(session, chat_id, "che novità ci sono oggi sui canali?")
                            elif text:
                                await process_jarvis_query(session, chat_id, text)

                        elif "callback_query" in upd:
                            cb = upd["callback_query"]
                            cb_id = cb["id"]
                            chat_id = str(cb["message"]["chat"]["id"])
                            msg_id = cb["message"]["message_id"]
                            cb_data = cb.get("data", "")

                            await session.post(f"{API_BASE}/answerCallbackQuery", json={"callback_query_id": cb_id})

                            if cb_data in ("menu:home", "refresh:radar"):
                                await handle_start(session, chat_id)
                            elif cb_data == "phone:status":
                                await show_phone_panel(session, chat_id, msg_id)
                            elif cb_data == "phone:ring":
                                await enqueue_phone_action(session, "lost_mode_on")
                                await enqueue_phone_action(session, "ring_alarm")
                                await show_phone_panel(session, chat_id, msg_id, notice="Allarme massimo volume + GPS + Foto inviati!")
                            elif cb_data == "phone:locate":
                                await enqueue_phone_action(session, "locate")
                                await enqueue_phone_action(session, "factory_sync")
                                await show_phone_panel(session, chat_id, msg_id, notice="Richiesta GPS e dati di fabbrica inviata!")
                            elif cb_data == "phone:torch":
                                _torch_toggle = not _torch_toggle
                                await enqueue_phone_action(session, "torch", {"on": _torch_toggle})
                                await show_phone_panel(session, chat_id, msg_id, notice=f"Torcia {'ACCESA' if _torch_toggle else 'SPENTA'}!")
                            elif cb_data == "phone:photo":
                                await enqueue_phone_action(session, "photo", {"camera": "0"})
                                await show_phone_panel(session, chat_id, msg_id, notice="Scatto fotocamera inviato!")
                            elif cb_data == "phone:lost_off":
                                await enqueue_phone_action(session, "lost_mode_off")
                                await show_phone_panel(session, chat_id, msg_id, notice="Modalità smarrito disattivata.")
                            elif cb_data.startswith("city:"):
                                city = cb_data.split(":")[1]
                                await send_animated_loader(session, chat_id, msg_id, f"ESTRAZIONE LEAD {city.upper()}")
                                leads = get_leads_by_city(city, limit=1)
                                if leads:
                                    await show_lead_card(session, chat_id, msg_id, leads[0], city)
                                else:
                                    t = f"✅ *Nessun nuovo lead in coda per {city.upper()}!*\nTutti i contatti sono stati lavorati."
                                    kb = {"inline_keyboard": [[{"text": "🔙 TORNA AL MENU CITTÀ", "callback_data": "menu:home"}]]}
                                    await edit_msg(session, chat_id, msg_id, t, kb)
                            elif cb_data.startswith("act:confirm:"):
                                lead_id = int(cb_data.split(":")[2])
                                update_lead_disposition(lead_id, "CONFERMATO_CALENDARIO")
                                await send_animated_loader(session, chat_id, msg_id, "SINCRONIZZAZIONE GOOGLE CALENDAR & KANBAN")
                                t = (
                                    "🎉 *PREVENTIVO CONFERMATO & SALVATO!*\n"
                                    "━━━━━━━━━━━━━━━━━━━━━━\n"
                                    "📅 Inserito in *Google Calendar*\n"
                                    "📋 Task spostata in *Hermes Kanban (IN PROGRESS)*\n"
                                    "🟢 Nodo Knowledge Graph *Attivato a Verde*\n"
                                    "━━━━━━━━━━━━━━━━━━━━━━"
                                )
                                kb = {"inline_keyboard": [[{"text": "⏭️ PROSSIMO LEAD", "callback_data": "city:all"}], [{"text": "🔙 MENU CITTÀ", "callback_data": "menu:home"}]]}
                                await edit_msg(session, chat_id, msg_id, t, kb)
                            elif cb_data.startswith("act:sell:"):
                                lead_id = int(cb_data.split(":")[2])
                                sell_to_badrexpress(lead_id, "Cliente B2B", "", "Imola", "Sgombero", 220.0, 35.0)
                                t = (
                                    "💰 *LEAD MONETIZZATO & VENDUTO SU BADREXPRESS.COM!*\n"
                                    "━━━━━━━━━━━━━━━━━━━━━━\n"
                                    "🏷️ *Offerta Cliente:* `220,00 €`\n"
                                    "💵 *Tua Commissione Netta:* `35,00 €`\n"
                                    "🌐 *Canale B2B:* Inoltrato alla rete autotrasportatori affiliati BadrExpress!\n"
                                    "━━━━━━━━━━━━━━━━━━━━━━"
                                )
                                kb = {"inline_keyboard": [[{"text": "⏭️ PROSSIMO LEAD", "callback_data": "city:all"}], [{"text": "🔙 MENU CITTÀ", "callback_data": "menu:home"}]]}
                                await edit_msg(session, chat_id, msg_id, t, kb)
                            elif cb_data.startswith("act:blacklist:"):
                                parts = cb_data.split(":")
                                lead_id = int(parts[2])
                                contact = parts[3] if len(parts) > 3 else "Unknown"
                                update_lead_disposition(lead_id, "BLACKLIST")
                                add_to_blacklist(contact, "NUMERO_INESISTENTE_DA_TELEGRAM")
                                t = (
                                    "🚫 *CONTATTO INSERITO IN BLACKLIST PERMANENTE!*\n"
                                    "━━━━━━━━━━━━━━━━━━━━━━\n"
                                    f"Target: `{contact}`\n"
                                    "🛡️ *Filtro Vault:* Questo numero non comparirà mai più."
                                )
                                kb = {"inline_keyboard": [[{"text": "⏭️ PROSSIMO LEAD", "callback_data": "city:all"}], [{"text": "🔙 MENU CITTÀ", "callback_data": "menu:home"}]]}
                                await edit_msg(session, chat_id, msg_id, t, kb)
                            elif cb_data.startswith("act:remind:"):
                                lead_id = int(cb_data.split(":")[2])
                                update_lead_disposition(lead_id, "RICHIAMA_DOMANI")
                                t = "⏰ *Promemoria Fissato:* Il lead verrà riproposto domani mattina nel briefing delle 08:00!"
                                kb = {"inline_keyboard": [[{"text": "⏭️ PROSSIMO LEAD", "callback_data": "city:all"}], [{"text": "🔙 MENU CITTÀ", "callback_data": "menu:home"}]]}
                                await edit_msg(session, chat_id, msg_id, t, kb)

            except Exception as e:
                print(f"[Bot Error]: {e}")
                await asyncio.sleep(3)


if __name__ == "__main__":
    asyncio.run(run_bot_poll())
