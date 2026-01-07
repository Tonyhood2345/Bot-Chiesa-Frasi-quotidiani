import os
import requests
import pandas as pd
import matplotlib
matplotlib.use('Agg') 
import matplotlib.pyplot as plt
import textwrap
import random
from io import BytesIO
from PIL import Image, ImageOps, ImageDraw, ImageFont

# --- CONFIGURAZIONE CHIESA ---
FACEBOOK_TOKEN = os.environ.get("FACEBOOK_TOKEN")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
PAGE_ID = "INSERISCI_QUI_ID_PAGINA_FACEBOOK_SE_FISSO" 

CSV_FILE = "Frasichiesa.csv"
LOGO_PATH = "logo.png"
FONT_PATH = "arial.ttf" 

# --- 1. GESTIONE DATI ---
def get_random_verse():
    try:
        df = pd.read_csv(CSV_FILE)
        if df.empty: return None
        return df.sample(1).iloc[0]
    except Exception as e:
        print(f"⚠️ Errore lettura CSV: {e}")
        return None

# --- 2. GENERATORE PROMPT ---
def get_image_prompt(categoria):
    cat = str(categoria).lower().strip()
    prompts_consolazione = [
        "peaceful sunset over calm lake, warm golden light, nature, photorealistic, 8k",
        "gentle morning light through trees, forest path, peaceful atmosphere"
    ]
    prompts_esortazione = [
        "majestic mountain peak, sunrise rays, dramatic sky, epic view, 8k",
        "eagle flying in blue sky, sun flare, freedom, strength"
    ]
    prompts_altro = [
        "beautiful blue sky with white clouds, heaven light, spiritual background",
        "field of flowers, spring, colorful, creation beauty"
    ]

    if "consolazione" in cat: return random.choice(prompts_consolazione)
    elif "esortazione" in cat: return random.choice(prompts_esortazione)
    else: return random.choice(prompts_altro)

# --- 3. AI & IMMAGINI ---
def get_ai_image(prompt_text):
    print(f"🎨 Generazione immagine: {prompt_text}")
    try:
        clean_prompt = prompt_text.replace(" ", "%20")
        url = f"https://image.pollinations.ai/prompt/{clean_prompt}?width=1080&height=1080&nologo=true"
        response = requests.get(url, timeout=20)
        if response.status_code == 200:
            return Image.open(BytesIO(response.content)).convert("RGBA")
    except Exception as e:
        print(f"⚠️ Errore AI: {e}")
    return Image.new('RGBA', (1080, 1080), (50, 50, 70))

# --- FUNZIONE TESTO GIGANTE MODIFICATA ---
def create_verse_image(row):
    prompt = get_image_prompt(row['Categoria'])
    base_img = get_ai_image(prompt).resize((1080, 1080))
    
    # Velo scuro (leggermente più scuro per contrasto)
    overlay = Image.new('RGBA', base_img.size, (0, 0, 0, 100))
    final_img = Image.alpha_composite(base_img, overlay)
    draw = ImageDraw.Draw(final_img)
    W, H = final_img.size
    
    try:
        # FONT GIGANTE (Dimensione 120)
        font_txt = ImageFont.truetype(FONT_PATH, 110) 
        # RIFERIMENTO GRANDE (Dimensione 70)
        font_ref = ImageFont.truetype(FONT_PATH, 70)
    except:
        font_txt = ImageFont.load_default()
        font_ref = ImageFont.load_default()

    # Testo Versetto
    text = f"“{row['Frase']}”"
    # Wrap a 15 caratteri per farlo andare a capo spesso e riempire il centro
    lines = textwrap.wrap(text, width=15)
    
    # Calcolo altezza blocco testo
    line_height = 130 # Spazio tra le righe
    total_height = len(lines) * line_height
    y = (H - total_height) / 2 - 50 # Centrato verticalmente
    
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font_txt)
        w = bbox[2] - bbox[0]
        
        # BORDO NERO (STROKE) PER LEGGIBILITÀ TOTALE
        # stroke_width=6 crea un contorno nero spesso intorno alle lettere bianche
        draw.text(((W - w)/2, y), line, font=font_txt, fill="white", stroke_width=6, stroke_fill="black")
        y += line_height
        
    # Riferimento Biblico (Sotto, Giallo Oro con bordo nero)
    ref = str(row['Riferimento'])
    bbox_ref = draw.textbbox((0, 0), ref, font=font_ref)
    w_ref = bbox_ref[2] - bbox_ref[0]
    
    draw.text(((W - w_ref)/2, y + 40), ref, font=font_ref, fill="#FFD700", stroke_width=4, stroke_fill="black")

    return final_img

# --- 4. LOGO ---
def add_logo(img):
    if os.path.exists(LOGO_PATH):
        try:
            logo = Image.open(LOGO_PATH).convert("RGBA")
            w = int(img.width * 0.20) # Logo un po' più grande (20%)
            h = int(w * (logo.height / logo.width))
            logo = logo.resize((w, h))
            img.paste(logo, ((img.width - w)//2, img.height - h - 40), logo)
        except: pass
    return img

# --- 5. SOCIAL ---
def send_telegram(img_bytes, caption):
    if not TELEGRAM_TOKEN: return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
        files = {'photo': ('img.png', img_bytes, 'image/png')}
        data = {'chat_id': TELEGRAM_CHAT_ID, 'caption': caption}
        requests.post(url, files=files, data=data)
        print("✅ Telegram OK")
    except Exception as e: print(f"❌ Telegram Error: {e}")

def post_facebook(img_bytes, message):
    if not FACEBOOK_TOKEN: return
    url = f"https://graph.facebook.com/v19.0/{PAGE_ID}/photos?access_token={FACEBOOK_TOKEN}"
    files = {'file': ('img.png', img_bytes, 'image/png')}
    data = {'message': message, 'published': 'true'}
    try:
        requests.post(url, files=files, data=data)
        print("✅ Facebook OK")
    except Exception as e: print(f"❌ Facebook Error: {e}")

# --- MAIN ---
if __name__ == "__main__":
    row = get_random_verse()
    if row is not None:
        print(f"📖 Versetto: {row['Riferimento']}")
        img = add_logo(create_verse_image(row))
        
        buf = BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)
        
        caption = f"✨ {row['Categoria']} ✨\n\n“{row['Frase']}”\n({row['Riferimento']})\n\n📍 Chiesa L'Eterno nostra Giustizia"
        
        send_telegram(buf, caption)
        buf.seek(0)
        post_facebook(buf, caption)
