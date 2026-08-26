import time

FURNITURE_VOLUME_MAP = {
    "armadio": 2.5,
    "armadio_6_ante": 4.0,
    "letto_matrimoniale": 2.0,
    "letto_singolo": 1.0,
    "divano_2_posti": 1.5,
    "divano_3_posti": 2.2,
    "divano_angolare": 3.5,
    "tavolo_sedie": 1.8,
    "cucina_completa": 6.0,
    "frigorifero": 1.0,
    "lavatrice": 0.5,
    "scatoloni_10": 1.0,
    "parete_attrezzata": 3.0,
    "cassettiera": 0.8
}

def estimate_volume(furniture_list=None, estimated_mq=None):
    total_m3 = 0.0
    items_detected = []
    
    if furniture_list and isinstance(furniture_list, list):
        for item in furniture_list:
            key = str(item).lower().strip().replace(" ", "_")
            vol = 1.0
            for k, v in FURNITURE_VOLUME_MAP.items():
                if k in key:
                    vol = v
                    break
            total_m3 += vol
            items_detected.append({"item": item, "volume_m3": vol})
    elif estimated_mq:
        total_m3 = round(float(estimated_mq) * 0.35, 1)
        items_detected.append({"item": f"Stima volumetrica su {estimated_mq} mq", "volume_m3": total_m3})
    else:
        total_m3 = 18.0
        items_detected.append({"item": "Arredo appartamento standard", "volume_m3": 18.0})

    if total_m3 <= 14.0:
        furgone = "1x Fiat Ducato Maxi (14 m³)"
        prezzo_base = 350.0
    elif total_m3 <= 22.0:
        furgone = "1x Iveco Daily Gran Volume (20-22 m³)"
        prezzo_base = 550.0
    elif total_m3 <= 40.0:
        furgone = "2x Iveco Daily oppure 1x Camion Medio (40 m³)"
        prezzo_base = 950.0
    else:
        furgone = "Camion Pesante 60 m³ o 2 viaggi combinati"
        prezzo_base = 1450.0

    return {
        "status": "SUCCESS",
        "skill": "vision_furniture_volume_estimator",
        "total_volume_m3": total_m3,
        "items_detected": items_detected,
        "recommended_vehicle": furgone,
        "base_price_estimate_eur": prezzo_base,
        "estimated_hours": max(3, int(total_m3 / 4.5)),
        "timestamp": int(time.time())
    }

def execute(params=None):
    params = params or {}
    items = params.get("furniture_list") or params.get("items")
    mq = params.get("mq") or params.get("estimated_mq")
    return estimate_volume(items, mq)
