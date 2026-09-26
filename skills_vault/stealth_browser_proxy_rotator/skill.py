import random
import os

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:130.0) Gecko/20100101 Firefox/130.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_6_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.6 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
]

VIEWPORTS = [
    {"width": 1920, "height": 1080},
    {"width": 1536, "height": 864},
    {"width": 1440, "height": 900},
    {"width": 1366, "height": 768},
    {"width": 390, "height": 844} # iPhone 14
]

PLATFORMS = ["Win32", "MacIntel", "Linux x86_64"]

def get_stealth_profile(device_type="desktop"):
    if device_type == "mobile":
        ua = USER_AGENTS[3]
        vp = VIEWPORTS[4]
        plat = "iPhone"
    else:
        ua = random.choice([u for u in USER_AGENTS if "iPhone" not in u])
        vp = random.choice(VIEWPORTS[:4])
        plat = "Win32" if "Windows" in ua else ("MacIntel" if "Mac" in ua else "Linux x86_64")

    profile = {
        "user_agent": ua,
        "viewport": vp,
        "platform": plat,
        "locale": "it-IT",
        "timezone": "Europe/Rome",
        "webgl_vendor": "Google Inc. (NVIDIA)",
        "webgl_renderer": "ANGLE (NVIDIA, NVIDIA GeForce RTX 4070 Direct3D11 vs_5_0 ps_5_0, D3D11)",
        "stealth_args": [
            "--disable-blink-features=AutomationControlled",
            "--disable-infobars",
            "--no-sandbox",
            "--disable-dev-shm-usage"
        ]
    }
    return profile

def execute(params=None):
    params = params or {}
    device = params.get("device", "desktop")
    target_url = params.get("url", "https://www.subito.it")
    profile = get_stealth_profile(device)

    return {
        "status": "SUCCESS",
        "skill": "stealth_browser_proxy_rotator",
        "target_url": target_url,
        "profile": profile,
        "message": f"Profilo Stealth configurato per {profile['platform']} (Viewport: {profile['viewport']['width']}x{profile['viewport']['height']}). Pronto per scraping evasivo."
    }
