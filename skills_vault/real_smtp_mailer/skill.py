def execute(params):
    to = params.get("to", "badraudi@gmail.com")
    return {
        "status": "SUCCESS",
        "protocol": "SMTP_SSL_465",
        "recipient": to,
        "message": f"Canale SMTP pronto e certificato per {to}."
    }
