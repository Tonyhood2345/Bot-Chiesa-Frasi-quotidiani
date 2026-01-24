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

# --- GESTIONE DATI E IMMAGINI ---
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
    if not TELEGRAM_TOKEN: return
    try:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto", 
                      files={'photo': img}, data={'chat_id': TELEGRAM_CHAT_ID, 'caption': cap})
    except Exception as e: print(f"Errore Telegram: {e}")

def post_facebook(img, msg):
    if not FACEBOOK_TOKEN: return
    try:
        requests.post(f"https://graph.facebook.com/v19.0/{PAGE_ID}/photos?access_token={FACEBOOK_TOKEN}",
                      files={'file': img}, data={'message': msg, 'published': 'true'})
    except Exception as e: print(f"Errore Facebook: {e}")

def trigger_make(row, img, cap):
    try:
        requests.post(MAKE_WEBHOOK_URL, 
                      data={'categoria': row.get('Categoria'), 'frase': row.get('Frase'), 'caption_completa': cap},
                      files={'upload_file': ('post.png', img, 'image/png')})
    except Exception as e: print(f"Errore Make: {e}")

# --- LOGICA DI SELEZIONE POST ---
def esegui_bot():
    # Ottieni l'ora attuale in UTC (GitHub usa UTC)
    now = datetime.now(timezone.utc)
    hour = now.hour # 0-23
    weekday = now.weekday() # 0=Lun, 5=Sab, 6=Dom
    
    print(f"🕒 Orario UTC rilevato: {hour}:00 - Giorno: {weekday}")

    row = None
    caption = ""

    # REGOLA 1: MATTINA PRESTO (Tutti i giorni)
    if 5 <= hour <= 8:
        print("☀️ Rilevato slot: MATTINA (Versetto del giorno)")
        row = get_random_verse()
        if row is not None:
            intro = random.choice(["🔥 Parola di Vita:", "🕊️ Guida dello Spirito:", "🙏 Per il tuo Cuore:"])
            frase_extra = random.choice(["Dio ti benedica oggi.", "Sii forte nel Signore.", "Cammina per fede."])
            caption = (
                f"✨ {str(row['Categoria']).upper()} ✨\n\n"
                f"“{row['Frase']}”\n"
                f"📖 {row['Riferimento']}\n\n"
                f"────────────────\n{intro}\n{frase_extra}\n────────────────\n\n"
                f"{INDIRIZZO_CHIESA}\n\n#fede #vangelodelgiorno #chiesa #gesù"
            )

    # REGOLA 2: SABATO MATTINA/POMERIGGIO (Invito)
    # NOTA: Ho messo fino alle 20 UTC per permetterti il test ORA
    elif weekday == 5 and 9 <= hour <= 20:
        print("🚨 Rilevato slot: SABATO (Invito)")
        row = get_random_verse("Esortazione")
        if row is None: row = get_random_verse()
        
        # Uso le parentesi per unire le stringhe senza errori di sintassi
        caption = (
            "🚨 NON MANCARE DOMANI! 🚨\n\n"
            "Fratello, sorella! Domani è il giorno del Signore! 🙌\n"
            "Ti aspettiamo per lodare Dio insieme.\n\n"
            "🗓 **DOMANI DOMENICA**\n"
            "🕕 **ORE 18:00**\n"
            f"{INDIRIZZO_CHIESA}\n\n"
            "Non venire da solo, porta un amico! Dio ha una parola per te. 🔥\n\n"
            f"────────────────\n"
            f"📖 *Parola per te:*\n"
            f"“{row['Frase']}”\n"
            f"({row['Riferimento']})\n"
            f"────────────────\n\n"
            "#chiesa #grotte #fede #culto"
        )

    # REGOLA 3: DOMENICA POMERIGGIO (Reminder)
    elif weekday == 6 and 15 <= hour <= 17:
        print("⏳ Rilevato slot: DOMENICA (Reminder)")
        row = get_random_verse()
        caption = (
            "⏳ NON MANCARE, STA PER INIZIARE! ⏳\n\n"
            "Ci siamo quasi! Alle **18:00** iniziamo il culto. ❤️\n"
            f"Lascia tutto e corri alla presenza di Dio!\n\n{INDIRIZZO_CHIESA}\n\n"
            f"Gesù ti sta aspettando!\n\n"
            f"────────────────\n"
            f"📖 *La Parola:*\n"
            f"“{row['Frase']}”\n"
            f"({row['Riferimento']})\n"
            f"────────────────\n\n"
            "#chiesa #grotte #culto #nonmancare"
        )

    else:
        print("❌ Nessuno slot orario corrispondente trovato. Il bot non farà nulla.")
        return

    # ESECUZIONE
    if row is not None and caption:
        print(f"🚀 Invio in corso... (Versetto: {row['Riferimento']})")
        img = create_verse_image(row)
        buf = BytesIO()
        img.save(buf, format='PNG')
        img_data = buf.getvalue()
        
        send_telegram(img_data, caption)
        post_facebook(img_data, caption)
        trigger_make(row, img_data, caption)
        print("✅ Tutto inviato correttamente!")
    else:
        print("❌ Errore: Nessun contenuto generato.")

if __name__ == "__main__":
    esegui_bot()
