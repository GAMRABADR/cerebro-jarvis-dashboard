import os, time
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors

FATTURE_DIR = r"D:\EBGStudioProgetti\Oracle-VPS and EBGStudio\cerebro-jarvis-dashboard\fatture"
os.makedirs(FATTURE_DIR, exist_ok=True)

def execute(params=None):
    params = params or {}
    codice = params.get("codice", f"INV-{int(time.time())}")
    cliente = params.get("cliente", "Gentile Cliente")
    totale = float(params.get("totale", 720.0))
    mq = params.get("mq", 60)
    
    pdf_path = os.path.join(FATTURE_DIR, f"{codice}.pdf")
    
    # Create PDF vector canvas
    c = canvas.Canvas(pdf_path, pagesize=letter)
    width, height = letter
    
    # Header Banner
    c.setFillColor(colors.HexColor("#061c28"))
    c.rect(0, height - 90, width, 90, fill=1, stroke=0)
    
    c.setFillColor(colors.HexColor("#00f0ff"))
    c.setFont("Helvetica-Bold", 20)
    c.drawString(40, height - 50, "EBGSTUDIO & PIETRO TRASLOCHI")
    
    c.setFillColor(colors.white)
    c.setFont("Helvetica", 10)
    c.drawString(40, height - 70, "Logistica Avanzata, Sgomberi e Servizi Aziendali")
    
    # Pratica Details
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, height - 130, f"DOCUMENTO / PREVENTIVO: #{codice}")
    
    c.setFont("Helvetica", 10)
    c.drawString(40, height - 155, f"Intestatario: {cliente}")
    c.drawString(40, height - 170, f"Data Emissione: {time.strftime('%d/%m/%Y %H:%M')}")
    c.drawString(40, height - 185, f"Metratura Stimata: {mq} mq")
    
    # Pricing Box
    c.setFillColor(colors.HexColor("#f8fafc"))
    c.roundRect(40, height - 290, width - 80, 80, 6, fill=1, stroke=1)
    
    c.setFillColor(colors.HexColor("#0f172a"))
    c.setFont("Helvetica-Bold", 12)
    c.drawString(60, height - 235, "Totale Servizio Trasloco / Sgombero:")
    
    c.setFillColor(colors.HexColor("#10b981"))
    c.setFont("Helvetica-Bold", 18)
    c.drawString(60, height - 265, f"€ {totale:.2f} (IVA inclusa)")
    
    # Footer
    c.setFillColor(colors.HexColor("#94a3b8"))
    c.setFont("Helvetica-Oblique", 9)
    c.drawString(40, 40, "Generato automaticamente dal Sistema CEREBRO JARVIS per EBGStudio.")
    
    c.save()
    
    return {
        "status": "SUCCESS",
        "codice": codice,
        "pdf_path": pdf_path,
        "totale": totale,
        "message": f"Documento PDF #{codice} generato con successo in {pdf_path}."
    }

if __name__ == "__main__":
    print(execute())
