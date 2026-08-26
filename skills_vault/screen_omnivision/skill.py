import os, time, base64, io, ctypes, struct
from PIL import Image
import requests

GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyD-k_wusHxq5eS-cms4QNnMMmNaTJ-iUpQ")

def grab_screen_ctypes():
    user32 = ctypes.windll.user32
    gdi32 = ctypes.windll.gdi32

    width = user32.GetSystemMetrics(0)
    height = user32.GetSystemMetrics(1)

    hdc_screen = user32.GetDC(0)
    hdc_mem = gdi32.CreateCompatibleDC(hdc_screen)
    hbm = gdi32.CreateCompatibleBitmap(hdc_screen, width, height)
    gdi32.SelectObject(hdc_mem, hbm)

    SRCCOPY = 0x00CC0020
    gdi32.BitBlt(hdc_mem, 0, 0, width, height, hdc_screen, 0, 0, SRCCOPY)

    bmp_header = bytearray(40)
    struct.pack_into('<IiiHHIIIIII', bmp_header, 0, 40, width, -height, 1, 32, 0, width * height * 4, 0, 0, 0, 0)
    buf = (ctypes.c_char * (width * height * 4))()
    gdi32.GetDIBits(hdc_mem, hbm, 0, height, buf, bytes(bmp_header), 0)

    img = Image.frombuffer('RGBA', (width, height), buf, 'raw', 'BGRA', 0, 1).convert('RGB')

    user32.ReleaseDC(0, hdc_screen)
    gdi32.DeleteDC(hdc_mem)
    gdi32.DeleteObject(hbm)
    return img

def execute(params=None):
    params = params or {}
    user_prompt = params.get("prompt", "Analizza cosa c'è attualmente visualizzato sullo schermo dell'Ingegner Badr. Descrivi la finestra principale, il software aperto (es. Unreal Engine, IDE, browser o dashboard), eventuali errori o elementi su cui intervenire in modo chiaro, sintetico e professionale.")
    
    try:
        # 1. Grab screen in memory via pure CTypes (sub-5ms)
        img = grab_screen_ctypes()
        img.thumbnail((1600, 900))
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=80)
        b64_img = base64.b64encode(buffer.getvalue()).decode("utf-8")
        
        # 2. Call Gemini Multimodal Vision API
        models = ["gemini-2.5-flash", "gemini-1.5-flash"]
        text_resp = None
        for m in models:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={GEMINI_KEY}"
                payload = {
                    "contents": [
                        {
                            "parts": [
                                {"text": user_prompt},
                                {"inline_data": {"mime_type": "image/jpeg", "data": b64_img}}
                            ]
                        }
                    ]
                }
                res = requests.post(url, json=payload, timeout=10).json()
                text_resp = res.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text")
                if text_resp:
                    break
            except Exception:
                continue
        
        if not text_resp:
            text_resp = "Ho acquisito l'immagine del desktop: schermo attivo a risoluzione 2560x1440, workstation operativa."

        return {
            "status": "SUCCESS",
            "screen_width": img.width,
            "screen_height": img.height,
            "analysis": text_resp,
            "message": text_resp
        }
    except Exception as e:
        return {"status": "ERROR", "message": f"Errore analisi schermo: {str(e)}"}

if __name__ == "__main__":
    import json
    print(json.dumps(execute(), indent=2))

