import os
import requests
import pandas as pd
import matplotlib
matplotlib.use('Agg') 
import textwrap
import random
import json
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timezone

# --- CONFIGURAZIONE ---
FACEBOOK_TOKEN = os.environ.get("FACEBOOK_TOKEN")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
PAGE_ID = "1479209002311050"
MAKE_WEBHOOK_URL = "https://hook.eu1.make.com/hiunkuvfe8mjvfsgyeg0vck4j8dwx6h2"

CSV_FILE = "Frasichiesa.csv"
LOGO_PATH = "logo.png"
FONT_NAME = "arial.ttf" 
INDIRIZZO_CHIESA = "📍 Chiesa Evangelica Eterno Nostra Giustizia\nPiazza Umberto, Grotte (AG)"

# --- GESTIONE DATI E IMMAGINI (Invariata) ---
def get_random_verse(filtro_categoria=None):
    try:
        df = pd.read_csv(CSV_FILE)
        if df.empty: return None
        if filtro_categoria:
            df_filtered = df[df['Categoria'].astype(str).str.contains(filtro_categoria, case=False, na=False)]
            if not df_filtered.empty: return df_filtered.sample(1).iloc[0]
        return df.sample(1).iloc[0]
    except Exception as e:
        print(f"⚠️ Errore CSV: {e}")
        return None

def get_image_prompt(categoria):
    cat = str(categoria).lower().strip()
    base = "bright, divine light, photorealistic, 8k, cinematic, biblical atmosphere"
    if "consolazione" in cat: return f"peaceful sunset, warm light, {base}"
    elif "esortazione" in cat: return f"majestic mountain, sun rays, {base}"
    else: return f"blue sky, clouds, heaven light, {base}"

def get_ai_image(prompt):
    try:
        url = f"https://image.pollinations.ai/prompt/{prompt.replace(' ', '%20')}?width=1080&height=1080&nologo=true"
        return Image.open(BytesIO(requests.get(url, timeout=30).content)).convert("RGBA")
    except: return Image.new('RGBA', (1080, 1080), (50, 50, 70))

def load_font(size):
    try: return ImageFont.truetype(FONT_NAME, size)
    except: return ImageFont.load_default()

def create_verse_image(row):
    img = get_ai_image(get_image_prompt(row['Categoria'])).resize((1080, 1080))
    overlay = Image.new('RGBA', img.size, (0,0,0,0))
    draw = ImageDraw.Draw(overlay)
    
    font_txt = load_font(90)
    font_ref = load_font(60)
    
    lines = textwrap.wrap(f"“{row['Frase']}”", width=18)
    h_block = len(lines) * 100 + 80
    start_y = (1080 - h_block) / 2 - 100
    
    draw.rectangle([(40, start_y-40), (1040, start_y + h_block + 40)], fill=(0,0,0,150))
    final = Image.alpha_composite(img, overlay)
    draw_f = ImageDraw.Draw(final)
    
    y = start_y
    for line in lines:
        w = draw_f.textlength(line, font=font_txt)
        draw_f.text(((1080-w)/2, y), line, font=font_txt, fill="white")
        y += 100
    
    ref = str(row['Riferimento'])
    w_ref = draw_f.textlength(ref, font=font_ref)
    draw_f.text(((1080-w_ref)/2, y+20), ref, font=font_ref, fill="#FFD700")
    
    if os.path.exists(LOGO_PATH):
        l = Image.open(LOGO_PATH).convert("RGBA")
        nw = int(1080*0.2)
        nh = int(nw*(l.height/l.width))
        final.paste(l.resize((nw,nh)), ((1080-nw)//2, 1080-nh-30), l.resize((nw,nh)))
    
    return final

# --- INVIO SOCIAL ---
def send_telegram(img, cap):
    requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto", 
                  files={'photo': img}, data={'chat_id': TELEGRAM_CHAT_ID, 'caption': cap})

def post_facebook(img, msg):
    requests.post(f"https://graph.facebook.com/v19.0/{PAGE_ID}/photos?access_token={FACEBOOK_TOKEN}",
                  files={'file': img}, data={'message': msg, 'published': 'true'})

def trigger_make(row, img, cap):
    requests.post(MAKE_WEBHOOK_URL, 
                  data={'categoria': row.get('Categoria'), 'frase': row.get('Frase'), 'caption_completa': cap},
                  files={'upload_file': ('post.png', img, 'image/png')})

# --- LOGICA DI SELEZIONE POST ---
def esegui_bot():
    # Ottieni l'ora attuale in UTC (GitHub usa UTC)
    now = datetime.now(timezone.utc)
    hour = now.hour # 0-23
    weekday = now.weekday() # 0=Lun, 5=Sab, 6=Dom
    
    print(f"🕒 Orario UTC rilevato: {hour}:00 - Giorno: {weekday}")

    row = None
    caption = ""

    # REGOLA 1: MATTINA PRESTO (circa le 07:00-08:00 Italiane -> 06:00-07:00 UTC)
    # Esegue TUTTI I GIORNI, inclusi Sabato e Domenica
    if 5 <= hour <= 8:
        print("☀️ Rilevato slot: MATTINA (Versetto del giorno)")
        row = get_random_verse()
        if row is not None:
            intro = random.choice(["🔥 Parola di Vita:", "🕊️ Guida dello Spirito:", "🙏 Per il tuo Cuore:"])
            frase_extra = random.choice(["Dio ti benedica oggi.", "Sii forte nel Signore.", "Cammina per fede."])
            caption = (
                f"✨ {str(row['Categoria']).upper()} ✨\n\n“{row['Frase']}”\n📖 {row['Riferimento']}\n\n"
                f"────────────────\n{intro}\n{frase_extra}\n────────────────\n\n"
                f"{INDIRIZZO_CHIESA}\n\n#fede #vangelodelgiorno #chiesa #gesù"
            )

    # REGOLA 2: SABATO MATTINA TARDI (circa 11:00 Italiane -> 10:00 UTC)
    elif weekday == 5 and 9 <= hour <= 11:
        print("🚨 Rilevato slot: SABATO (Invito)")
        row = get_random_verse("Esortazione")
        if row is None: row = get_random_verse()
        caption = (
            "🚨 NON MANCARE DOMANI! 🚨\n\nFratello, sorella! Domani è il giorno del Signore! 🙌\n"
            "Ti aspettiamo per lodare Dio insieme.\n\n🗓 **DOMANI DOMENICA**\n🕕 **ORE 18


            # REGOLA 2: SABATO
    # Nota: Ho messo <= 18 per permetterti di testare ora
    elif weekday == 5 and 9 <= hour <= 18:
        print("🚨 Rilevato slot: SABATO (Invito)")
        # ... resto del codice ...
