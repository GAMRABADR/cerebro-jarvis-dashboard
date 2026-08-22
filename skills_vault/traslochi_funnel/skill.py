def execute(params):
    mq = float(params.get("mq", 60))
    tot = (mq * 8.0) + 80.0
    return {
        "status": "SUCCESS",
        "prezzo_totale": tot,
        "message": f"Preventivo calcolato: €{tot:.2f} per {mq} mq."
    }
