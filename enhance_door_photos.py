#!/usr/bin/env python3
"""
EBJ Supreme — AI Photo Studio & Marketplace Visual Enhancer
Ottimizzazione automatica delle foto di porte usate per Facebook Marketplace:
1. Rimozione dello sfondo disordinato (cantina/garage) dalla foto principale tramite rembg
2. Compositing su sfondo moderno studio architettonico (parete chiara con luce calda e ombra realistica)
3. Ottimizzazione colore, contrasto, saturazione delle venature del legno noce/castagno
4. Creazione copertina quadrata 1080x1080 ottimizzata per l'algoritmo di Facebook Marketplace
5. Batch enhancement di tutte le foto di dettaglio (stipiti, cardini, chiavi in ottone)
"""

import os
import sys
from PIL import Image, ImageEnhance, ImageFilter, ImageDraw, ImageFont
import rembg

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

UPLOAD_DIR = r"C:\Users\Admin\.gemini\antigravity\brain\72dbc376-f271-4e04-8154-7a159d279000\.user_uploaded"
ARTIFACTS_DIR = r"C:\Users\Admin\.gemini\antigravity\brain\72dbc376-f271-4e04-8154-7a159d279000"
PUBLIC_DIR = r"d:\EBGStudioProgetti\Oracle-VPS and EBGStudio\cerebro-jarvis-dashboard\public\marketplace_doors"
os.makedirs(PUBLIC_DIR, exist_ok=True)

IMG_MAP = {
    "hero": "media_1789979406467.jpg",     # Porta singola intera con maniglia
    "frames_1": "media_1789979406468.jpg", # Telai e stipiti con numeri
    "keys": "media_1789979406470.jpg",     # Chiavi in ottone
    "stack": "media_1789979406473.jpg",    # 3 porte impilate con etichette
    "frames_2": "media_1789979406476.jpg"  # Dettaglio giunti telaio
}

def enhance_basic(img, contrast=1.25, brightness=1.10, sharpness=1.35, color=1.20):
    """Migliora nitidezza, brillantezza e colore del legno"""
    img = ImageEnhance.Brightness(img).enhance(brightness)
    img = ImageEnhance.Contrast(img).enhance(contrast)
    img = ImageEnhance.Color(img).enhance(color)
    img = ImageEnhance.Sharpness(img).enhance(sharpness)
    return img

def process_hero_with_rembg(hero_path, output_path, output_cover_path):
    print("[*] Elaborazione Hero Door con AI rembg per eliminazione sfondo...")
    orig = Image.open(hero_path).convert("RGB")
    
    # 1. Rimuovi lo sfondo con rembg
    no_bg = rembg.remove(orig)
    
    # 2. Crea sfondo studio luxury (gradiente grigio chiaro / avorio)
    w, h = orig.size
    bg = Image.new("RGBA", (w, h), (245, 246, 250, 255))
    
    # Aggiungi ombra morbida sotto la porta
    shadow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    door_bbox = no_bg.getbbox()
    if door_bbox:
        left, upper, right, lower = door_bbox
        # Disegna un'ellisse ombra alla base
        shadow_draw.ellipse([left + 20, lower - 25, right - 20, lower + 35], fill=(20, 20, 30, 90))
        shadow = shadow.filter(ImageFilter.GaussianBlur(16))
    
    bg.paste(shadow, (0, 0), shadow)
    
    # Ottimizza la porta isolata
    door_rgb = no_bg.convert("RGB")
    door_rgb = enhance_basic(door_rgb, contrast=1.25, brightness=1.08, color=1.25, sharpness=1.4)
    door_enhanced = Image.new("RGBA", (w, h))
    door_enhanced.paste(door_rgb, (0, 0), mask=no_bg.split()[3])
    
    bg.paste(door_enhanced, (0, 0), door_enhanced)
    final_hero = bg.convert("RGB")
    final_hero.save(output_path, quality=95)
    print(f"[+] Salvata Hero senza sfondo in: {output_path}")
    
    # 3. Creazione Copertina Quadrata Pro 1080x1080 per Facebook Marketplace
    square_size = 1080
    square_bg = Image.new("RGB", (square_size, square_size), (240, 242, 245))
    
    # Ridimensiona l'immagine della porta per centrarla nel quadrato
    scale = (square_size * 0.90) / float(h)
    new_w = int(w * scale)
    new_h = int(h * scale)
    door_resized = final_hero.resize((new_w, new_h), Image.Resampling.LANCZOS)
    
    offset_x = (square_size - new_w) // 2
    offset_y = (square_size - new_h) // 2
    square_bg.paste(door_resized, (offset_x, offset_y))
    
    # Disegna Banner e Badge Professionali per FB Marketplace
    draw = ImageDraw.Draw(square_bg)
    
    # Badge in alto: "OPPORTUNITÀ RISTRUTTURAZIONE"
    draw.rectangle([30, 30, 480, 80], fill=(15, 23, 42)) # Blu scuro
    draw.rectangle([30, 76, 480, 80], fill=(250, 204, 21)) # Riga oro
    
    # Badge Prezzo in evidenza in alto a destra: "75€ CAD. / 200€ TUTTE E 3"
    draw.rectangle([square_size - 440, 30, square_size - 30, 110], fill=(22, 163, 74)) # Verde smeraldo
    draw.rectangle([square_size - 440, 106, square_size - 30, 110], fill=(250, 204, 21)) # Riga oro
    
    # Banner inferiore: "3 PORTE IN LEGNO MASSELLO COMPLETE DI TELAIO, CARDINI E CHIAVI"
    draw.rectangle([0, square_size - 100, square_size, square_size], fill=(15, 23, 42))
    draw.rectangle([0, square_size - 100, square_size, square_size - 96], fill=(2, 132, 199))
    
    try:
        # Testo con font di default
        draw.text((45, 45), "🚪 3 PORTE INTERNE MASSELLO", fill=(255, 255, 255))
        draw.text((square_size - 425, 45), "🔥 75€ CAD. (3x = 200€)", fill=(255, 255, 255))
        draw.text((square_size - 425, 75), "TELAIO + CARDINI + CHIAVI INCLUSE", fill=(250, 204, 21))
        draw.text((30, square_size - 75), "COMPLETO DI STIPITI E CHIAVI · RITIRO IMOLA/BOLOGNA · CONSEGNA BADREXPRESS.COM", fill=(255, 255, 255))
    except Exception:
        pass
        
    square_bg.save(output_cover_path, quality=95)
    print(f"[+] Salvata Copertina Facebook Marketplace Pro in: {output_cover_path}")

def process_all_photos():
    print("=" * 65)
    print("   EBJ SUPREME — AI PHOTO STUDIO PER FACEBOOK MARKETPLACE   ")
    print("=" * 65)
    
    enhanced_files = []
    
    # 1. Hero Door con rembg
    hero_in = os.path.join(UPLOAD_DIR, IMG_MAP["hero"])
    hero_clean = os.path.join(PUBLIC_DIR, "porta_1_hero_studio.jpg")
    hero_cover = os.path.join(PUBLIC_DIR, "porta_cover_fb_marketplace.jpg")
    
    process_hero_with_rembg(hero_in, hero_clean, hero_cover)
    enhanced_files.append(hero_cover)
    enhanced_files.append(hero_clean)
    
    # 2. Elaborazione di tutte le altre 4 foto di dettaglio
    details = [
        ("porta_2_telai_stipiti.jpg", IMG_MAP["frames_1"], 1.25, 1.15),
        ("porta_3_chiavi_ottone.jpg", IMG_MAP["keys"], 1.30, 1.20),
        ("porta_4_blocco_3_porte.jpg", IMG_MAP["stack"], 1.25, 1.12),
        ("porta_5_dettaglio_giunti.jpg", IMG_MAP["frames_2"], 1.25, 1.15)
    ]
    
    for out_name, in_name, cont, bright in details:
        in_p = os.path.join(UPLOAD_DIR, in_name)
        out_p = os.path.join(PUBLIC_DIR, out_name)
        if os.path.exists(in_p):
            im = Image.open(in_p).convert("RGB")
            im_enh = enhance_basic(im, contrast=cont, brightness=bright, sharpness=1.35, color=1.20)
            im_enh.save(out_p, quality=92)
            enhanced_files.append(out_p)
            print(f"[+] Ottimizzata foto di dettaglio: {out_name}")
            
    # Copia anche nella cartella artifacts per visualizzazione diretta nel browser
    for f in enhanced_files:
        fn = os.path.basename(f)
        art_p = os.path.join(ARTIFACTS_DIR, fn)
        try:
            with open(f, "rb") as src, open(art_p, "wb") as dst:
                dst.write(src.read())
        except Exception:
            pass
            
    print(f"\n[SUCCESS] Tutte le foto ottimizzate con successo in: {PUBLIC_DIR}")
    return enhanced_files

if __name__ == "__main__":
    process_all_photos()
