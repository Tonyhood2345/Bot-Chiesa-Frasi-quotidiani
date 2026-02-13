import os
import requests
import pandas as pd
import textwrap
import random
from datetime import datetime
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

# ==========================================
# 🔥 CONFIGURAZIONE CREDENZIALI (DA SECRET)
# ==========================================

# Recupero automatico dai Secret del tuo ambiente
FB_PAGE_ID = os.environ.get('PAGE_ID')
FB_ACCESS_TOKEN = os.environ.get('FACEBOOK_TOKEN')
TG_TOKEN = os.environ.get('TELEGRAM_TOKEN')
TG_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

# --- FILE LOCALI ---
CSV_FILE = "Frasichiesa.csv"
LOGO_PATH = "logo.png"
FONT_NAME = "DejaVuSans-Bold.ttf" 

# ==========================================
# 1. GESTIONE DATI E IMMAGINI
# ==========================================

def get_random_verse():
    try:
        if not os.path.exists(CSV_FILE):
            print(f"❌ Errore: File {CSV_FILE} non trovato!")
            return None
        df = pd.read_csv(CSV_FILE)
        if df.empty: return None
        return df.sample(1).iloc[0]
    except Exception as e:
        print(f"Errore lettura CSV: {e}")
        return None

def get_ai_image(categoria):
    cat = str(categoria).lower().strip()
    prompts = {
        "consolazione": "peaceful sunset over calm lake, warm golden light, photorealistic, 8k",
        "esortazione": "majestic mountain peak, sunrise rays, dramatic sky, photorealistic, 8k",
        "default": "beautiful blue sky with white clouds, divine heaven light, photorealistic, 8k"
    }
    p = prompts.get(cat, prompts["default"]).replace(" ", "%20")
    url = f"https://image.pollinations.ai/prompt/{p}?width=1080&height=1080&nologo=true"
    try:
        response = requests.get(url, timeout=30)
        return Image.open(BytesIO(response.content)).convert("RGBA")
    except:
        return Image.new('RGBA', (1080, 1080), (50, 50, 70))

def create_verse_image(row):
    base_img = get_ai_image(row['Categoria']).resize((1080, 1080))
    overlay = Image.new('RGBA', base_img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    # Caricamento Font
    try:
        font_txt = ImageFont.truetype(FONT_NAME, 80)
        font_ref = ImageFont.truetype(FONT_NAME, 50)
    except:
        font_txt = font_ref = ImageFont.load_default()

    # Testo e rettangolo semi-trasparente
    text = f"\"{row['Frase']}\""
    lines = textwrap.wrap(text, width=20)
    
    # Disegna box centrato
    draw.rectangle([(50, 300), (1030, 800)], fill=(0, 0, 0, 130))
    
    y_text = 350
    for line in lines:
        draw.text((540, y_text), line, font=font_txt, fill="white", anchor="mm")
        y_text += 90
    
    draw.text((540, 750), str(row['Riferimento']), font=font_ref, fill="#FFD700", anchor="mm")
    
    final_img = Image.alpha_composite(base_img, overlay)
    
    # Aggiunta Logo
    if os.path.exists(LOGO_PATH):
        try:
            logo = Image.open(LOGO_PATH).convert("RGBA")
            logo.thumbnail((200, 200))
            final_img.paste(logo, (440, 850), logo)
        except: pass
        
    return final_img

# ==========================================
# 2. FUNZIONI DI PUBBLICAZIONE
# ==========================================

def publish_to_facebook(img_bytes, caption):
    if not FB_ACCESS_TOKEN or not FB_PAGE_ID:
        print("⚠️ Facebook Secret mancanti!")
        return
    
    print("📡 Pubblicazione su Facebook...")
    url = f"https://graph.facebook.com/v18.0/{FB_PAGE_ID}/photos"
    payload = {'message': caption, 'access_token': FB_ACCESS_TOKEN}
    files = {'source': ('post.png', img_bytes, 'image/png')}
    
    try:
        r = requests.post(url, data=payload, files=files)
        if r.status_code == 200:
            print("✅ Facebook: Post pubblicato!")
        else:
            print(f"❌ Facebook Errore: {r.text}")
    except Exception as e:
        print(f"❌ Errore connessione Facebook: {e}")

def send_to_telegram(img_bytes, caption):
    if not TG_TOKEN or not TG_CHAT_ID:
        print("⚠️ Telegram Secret mancanti!")
        return

    print("📡 Invio a Telegram...")
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto"
    data = {'chat_id': TG_CHAT_ID, 'caption': caption}
    files = {'photo': ('post.png', img_bytes, 'image/png')}
    
    try:
        r = requests.post(url, data=data, files=files)
        if r.status_code == 200:
            print("✅ Telegram: Messaggio inviato!")
        else:
            print(f"❌ Telegram Errore: {r.text}")
    except Exception as e:
        print(f"❌ Errore connessione Telegram: {e}")

# ==========================================
# 3. MAIN EXECUTION
# ==========================================

if __name__ == "__main__":
    print(f"🚀 Avvio Bot Chiesa - {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    
    row = get_random_verse()
    if row is not None:
        # Generazione immagine
        img = create_verse_image(row)
        buf = BytesIO()
        img.save(buf, format='PNG')
        img_data = buf.getvalue()
        
        # Testo del post
        caption = (
            f"📖 {row['Riferimento']}\n\n"
            f"\"{row['Frase']}\"\n\n"
            "────────────────\n"
            "⛪ Chiesa L'Eterno Nostra Giustizia\n"
            "📍 Piazza Umberto I, Grotte (AG)\n"
            "#fede #bibbia #cristo #chiesa #grotte #evangelo"
        )
        
        # Esecuzione parallela
        publish_to_facebook(img_data, caption)
        send_to_telegram(img_data, caption)
        
        print("\n🎉 Operazione conclusa!")
    else:
        print("❌ Errore: Dati non caricati correttamente.")
