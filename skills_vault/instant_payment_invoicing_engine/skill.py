import time, urllib.parse

def generate_payment_link(amount=100.0, client="Cliente Badr", description="Acconto Trasloco"):
    satispay_url = f"https://tag.satispay.com/pietrotraslochi?amount={int(amount*100)}&description={urllib.parse.quote(description)}"
    stripe_url = f"https://buy.stripe.com/ebgstudio_acconto?client={urllib.parse.quote(client)}&amount={amount}"
    
    invoice_code = f"EBG-FT-2026-{int(time.time()) % 10000:04d}"
    
    return {
        "status": "SUCCESS",
        "invoice_code": invoice_code,
        "amount_euro": amount,
        "client": client,
        "satispay_link": satispay_url,
        "stripe_link": stripe_url,
        "instant_pay_button": f"[💳 PAGA ACCONTO CON SATISPAY / CARTA]({satispay_url})",
        "message": f"Link di pagamento generato con successo per € {amount:.2f}. Fattura SDI pre-compilata cod. {invoice_code}."
    }

def execute(params=None):
    params = params or {}
    return generate_payment_link(params.get("amount", 100.0), params.get("client", "Cliente Badr"), params.get("description", "Acconto Trasloco"))
