import os, time, base64, io
from PIL import ImageGrab
import requests

GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyD-k_wusHxq5eS-cms4QNnMMmNaTJ-iUpQ")

def execute(params=None):
    params = params or {}
    user_prompt = params.get("prompt", "Descrivi cosa vedi sullo schermo, evidenziando eventuali errori o elementi chiave.")
    
    try:
        # 1. Grab screen in memory
        img = ImageGrab.grab()
        # Resize to max 1600px width to keep payload lightning fast (<0.5s)
        img.thumbnail((1600, 1000))
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=82)
        b64_img = base64.b64encode(buffer.getvalue()).decode("utf-8")
        
        # 2. Call Gemini Vision API
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_KEY}"
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
        res = requests.post(url, json=payload, timeout=12).json()
        text_resp = res.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "Analisi visiva completata.")
        
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
