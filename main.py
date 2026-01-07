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

# --- CONFIGURAZIONE ---
FACEBOOK_TOKEN = os.environ.get("FACEBOOK_TOKEN")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
PAGE_ID = "INSERISCI_QUI_ID_PAGINA_FACEBOOK_SE_FISSO" 

CSV_FILE = "Frasichiesa.csv"
LOGO_PATH = "logo.png"
FONT_NAME = "arial.ttf" 

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
    base_style = "bright, divine light, photorealistic, 8k, sun rays, cinematic"
    
    prompts_consolazione = [
        f"peaceful sunset over calm lake, warm golden light, {base_style}",
        f"gentle morning light through trees, forest path, {base_style}",
        f"hands holding light, soft warm background, {base_style}"
    ]
    prompts_esortazione = [
        f"majestic mountain peak, sunrise rays, dramatic sky, {base_style}",
        f"eagle flying in blue sky, sun flare, freedom, {base_style}",
        f"running water stream, clear river, energy, {base_style}"
    ]
    prompts_altro = [
        f"beautiful blue sky with white clouds, heaven light, {base_style}",
        f"field of flowers, spring, colorful, creation beauty, {base_style}"
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

# --- 4. FUNZIONE CARICAMENTO FONT ---
def load_font(size):
    fonts_to_try = [FONT_NAME, "DejaVuSans-Bold.ttf", "arial.ttf"]
    for font_path in fonts_to_try:
        try:
            return ImageFont.truetype(font_path, size)
        except: continue
    return ImageFont.load_default()

# --- 5. CREAZIONE IMMAGINE (SPOSTATA IN ALTO) ---
def create_verse_image(row):
    prompt = get_image_prompt(row['Categoria'])
    base_img = get_ai_image(prompt).resize((1080, 1080))
    
    overlay = Image.new('RGBA', base_img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    W, H = base_img.size
    
    # FONT 110
    font_txt = load_font(110)  
    font_ref = load_font(65)   

    text = f"“{row['Frase']}”"
    lines = textwrap.wrap(text, width=14) 
    
    line_height = 120 
    text_block_height = len(lines) * line_height
    ref_height = 90
    total_content_height = text_block_height + ref_height
    
    # --- CALCOLO POSIZIONE VERTICALE ---
    # Prima era: (H - total_content_height) / 2  -> (Centro perfetto)
    # Ora tolgo 150px per tirarlo su
    start_y = ((H - total_content_height) / 2) - 150
    
    # BOX SFUMATO
    padding = 50
    box_left = 40
    box_top = start_y - padding
    box_right = W - 40
    box_bottom = start_y + total_content_height + padding
    
    draw.rectangle(
        [(box_left, box_top), (box_right, box_bottom)], 
        fill=(0, 0, 0, 140), 
        outline=None
    )
    
    final_img = Image.alpha_composite(base_img, overlay)
    draw_final = ImageDraw.Draw(final_img)
    
    current_y = start_y
    for line in lines:
        bbox = draw_final.textbbox((0, 0), line, font=font_txt)
        w = bbox[2] - bbox[0]
        draw_final.text(((W - w)/2, current_y), line, font=font_txt, fill="white")
        current_y += line_height
        
    ref = str(row['Riferimento'])
    bbox_ref = draw_final.textbbox((0, 0), ref, font=font_ref)
    w_ref = bbox_ref[2] - bbox_ref[0]
    draw_final.text(((W - w_ref)/2, current_y + 30), ref, font=font_ref, fill="#FFD700")

    return final_img

# --- 6. LOGO ---
def add_logo(img):
    if os.path.exists(LOGO_PATH):
        try:
            logo = Image.open(LOGO_PATH).convert("RGBA")
            w = int(img.width * 0.20)
            h = int(w * (logo.height / logo.width))
            logo = logo.resize((w, h))
            # Logo in basso
            img.paste(logo, ((img.width - w)//2, img.height - h - 30), logo)
        except: pass
    return img

# --- 7. MEDITAZIONE ---
def genera_meditazione(row):
    cat = str(row['Categoria']).lower()
    intro = random.choice(["🌿 𝗨𝗻 𝗽𝗲𝗻𝘀𝗶𝗲𝗿𝗼:", "💡 𝗟𝘂𝗰𝗲 𝗱𝗶 𝗼𝗴𝗴𝗶:", "🙏 𝗥𝗶𝗳𝗹𝗲𝘀𝘀𝗶𝗼𝗻𝗲:"])
    
    msg = ""
    if "consolazione" in cat:
        msg = "Non sei solo/a. C'è una pace pronta ad abbracciarti oggi."
    elif "esortazione" in cat:
        msg = "Oggi hai una forza nuova! Guarda alla vittoria che ti aspetta."
    elif "edificazione" in cat:
        msg = "Costruisci la tua giornata su questa verità solida."
    else:
        msg = "Porta questa promessa nel cuore, sarà la tua forza oggi."

    return f"{intro} {msg}"

# --- 8. SOCIAL ---
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
        
        meditazione = genera_meditazione(row)
        caption = (
            f"✨ {str(row['Categoria']).upper()} ✨\n\n"
            f"“{row['Frase']}”\n"
            f"📖 {row['Riferimento']}\n\n"
            f"────────────────\n"
            f"{meditazione}\n"
            f"────────────────\n\n"
            f"📍 Chiesa L'Eterno Nostra Giustizia\n\n"
            f"#fede #vangelodelgiorno #chiesa #gesù #preghiera #bibbia"
        )
        
        send_telegram(buf, caption)
        buf.seek(0)
        post_facebook(buf, caption)
