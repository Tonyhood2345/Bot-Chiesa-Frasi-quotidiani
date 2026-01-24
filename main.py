import os
import requests
import pandas as pd
import matplotlib
matplotlib.use('Agg') 
import matplotlib.pyplot as plt
import textwrap
import random
import json
import time
import schedule
from io import BytesIO
from PIL import Image, ImageOps, ImageDraw, ImageFont
from datetime import datetime

# --- CONFIGURAZIONE ---
FACEBOOK_TOKEN = os.environ.get("FACEBOOK_TOKEN")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
PAGE_ID = "1479209002311050"
MAKE_WEBHOOK_URL = "https://hook.eu1.make.com/hiunkuvfe8mjvfsgyeg0vck4j8dwx6h2"

CSV_FILE = "Frasichiesa.csv"
LOGO_PATH = "logo.png"
FONT_NAME = "arial.ttf" 

# INDIRIZZO CHIESA
INDIRIZZO_CHIESA = "📍 Chiesa Evangelica Eterno Nostra Giustizia\nPiazza Umberto, Grotte (AG)"

# --- 1. GESTIONE DATI ---
def get_random_verse(filtro_categoria=None):
    try:
        df = pd.read_csv(CSV_FILE)
        if df.empty: return None
        
        if filtro_categoria:
            df_filtered = df[df['Categoria'].astype(str).str.contains(filtro_categoria, case=False, na=False)]
            if not df_filtered.empty:
                return df_filtered.sample(1).iloc[0]
        
        return df.sample(1).iloc[0]
    except Exception as e:
        print(f"⚠️ Errore lettura CSV: {e}")
        return None

# --- 2. GENERATORE PROMPT ---
def get_image_prompt(categoria):
    cat = str(categoria).lower().strip()
    base_style = "bright, divine light, photorealistic, 8k, sun rays, cinematic, biblical atmosphere"
    
    if "consolazione" in cat:
        return random.choice([
            f"peaceful sunset over calm lake, warm golden light, {base_style}",
            f"gentle morning light through trees, forest path, {base_style}",
            f"hands holding light, soft warm background, {base_style}"
        ])
    elif "esortazione" in cat:
        return random.choice([
            f"majestic mountain peak, sunrise rays, dramatic sky, {base_style}",
            f"eagle flying in blue sky, sun flare, freedom, {base_style}",
            f"running water stream, clear river, energy, {base_style}"
        ])
    else:
        return random.choice([
            f"beautiful blue sky with white clouds, heaven light, {base_style}",
            f"field of flowers, spring, colorful, creation beauty, {base_style}"
        ])

# --- 3. AI & IMMAGINI ---
def get_ai_image(prompt_text):
    print(f"🎨 Generazione immagine: {prompt_text}")
    try:
        clean_prompt = prompt_text.replace(" ", "%20")
        url = f"https://image.pollinations.ai/prompt/{clean_prompt}?width=1080&height=1080&nologo=true"
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            return Image.open(BytesIO(response.content)).convert("RGBA")
    except Exception as e:
        print(f"⚠️ Errore AI: {e}")
    return Image.new('RGBA', (1080, 1080), (50, 50, 70))

# --- 4. FUNZIONE CARICAMENTO FONT ---
def load_font(size):
    fonts_to_try = [FONT_NAME, "DejaVuSans-Bold.ttf", "arial.ttf", "segoeui.ttf"]
    for font_path in fonts_to_try:
        try:
            return ImageFont.truetype(font_path, size)
        except: continue
    return ImageFont.load_default()

# --- 5. CREAZIONE IMMAGINE ---
def create_verse_image(row):
    prompt = get_image_prompt(row['Categoria'])
    base_img = get_ai_image(prompt).resize((1080, 1080))
    
    overlay = Image.new('RGBA', base_img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    W, H = base_img.size
    
    font_txt = load_font(90)
    font_ref = load_font(60)   

    text = f"“{row['Frase']}”"
    lines = textwrap.wrap(text, width=18) 
    
    line_height = 100
    text_block_height = len(lines) * line_height
    ref_height = 80
    total_content_height = text_block_height + ref_height
    
    start_y = ((H - total_content_height) / 2) - 100
    padding = 40
    
    draw.rectangle(
        [(40, start_y - padding), (W - 40, start_y + total_content_height + padding)], 
        fill=(0, 0, 0, 150), outline=None
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
    draw_final.text(((W - w_ref)/2, current_y + 20), ref, font=font_ref, fill="#FFD700")

    return final_img

# --- 6. LOGO ---
def add_logo(img):
    if os.path.exists(LOGO_PATH):
        try:
            logo = Image.open(LOGO_PATH).convert("RGBA")
            w = int(img.width * 0.20)
            h = int(w * (logo.height / logo.width))
            logo = logo.resize((w, h))
            img.paste(logo, ((img.width - w)//2, img.height - h - 30), logo)
        except: pass
    return img

# --- 7. MEDITAZIONE (PER I GIORNI SETTIMANALI) ---
def genera_meditazione(row):
    intro = random.choice(["🔥 Parola di Vita:", "🕊️ Guida dello Spirito:", "🙏 Per il tuo Cuore:", "🙌 Gloria a Dio:"])
    msgs = [
        "Fratello, sorella, non temere! Lo Spirito Santo è il Consolatore.",
        "Affida ogni peso a Gesù. Lui ha già portato le tue sofferenze.",
        "Anche se attraversi la valle oscura, il Buon Pastore è con te.",
        "Metti Dio al primo posto e Lui si prenderà cura di tutto.",
        "La fede sposta le montagne. Oggi ordina alla tua montagna di spostarsi!"
    ]
    return f"{intro}\n{random.choice(msgs)}"

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

def trigger_make_webhook(row, img_bytes, caption_completa):
    print("📡 Inviando dati a Make.com...")
    data_payload = {
        "categoria": row.get('Categoria', 'N/A'),
        "riferimento": row.get('Riferimento', 'N/A'),
        "frase": row.get('Frase', 'N/A'),
        "caption_completa": caption_completa,
        "evento": "Post Chiesa"
    }
    files_payload = {'upload_file': ('post_chiesa.png', img_bytes, 'image/png')}
    try:
        requests.post(MAKE_WEBHOOK_URL, data=data_payload, files=files_payload)
        print("✅ Webhook Make attivato!")
    except Exception as e: print(f"❌ Errore Make: {e}")

# --- 9. CORE PUBBLICAZIONE ---
def pubblica_post(tipo_post):
    print(f"🚀 Avvio procedura pubblicazione: {tipo_post}")
    
    row = None
    caption = ""
    
    # --- A. CASO QUOTIDIANO (TUTTI I GIORNI ORE 08:00) ---
    if tipo_post == "QUOTIDIANO":
        row = get_random_verse() # Pesca a caso
        if row is not None:
            meditazione = genera_meditazione(row)
            caption = (
                f"✨ {str(row['Categoria']).upper()} ✨\n\n"
                f"“{row['Frase']}”\n"
                f"📖 {row['Riferimento']}\n\n"
                f"────────────────\n"
                f"{meditazione}\n"
                f"────────────────\n\n"
                f"{INDIRIZZO_CHIESA}\n\n"
                f"#fede #vangelodelgiorno #chiesa #gesù #preghiera #bibbia"
            )

    # --- B. CASO SABATO MATTINA (INVITO ORE 11:00) ---
    elif tipo_post == "SABATO":
        row = get_random_verse(filtro_categoria="Esortazione")
        if row is None: row = get_random_verse()
        
        caption = (
            "🚨 NON MANCARE DOMANI! 🚨\n\n"
            "Fratello, sorella! Domani è il giorno del Signore! 🙌\n"
            "Ti aspettiamo per lodare Dio insieme.\n\n"
            "🗓 **DOMANI DOMENICA**\n"
            "🕕 **ORE 18:00**\n"
            f"{INDIRIZZO_CHIESA}\n\n"
            "Non venire da solo, porta un amico! Dio ha una parola per te. 🔥\n\n"
            f"────────────────\n"
            f"📖 *Versetto di incoraggiamento:*\n"
            f"“{row['Frase']}”\n"
            f"({row['Riferimento']})\n"
            f"────────────────\n\n"
            "#chiesa #grotte #fede #culto #domenica"
        )

    # --- C. CASO DOMENICA POMERIGGIO (REMINDER ORE 17:00) ---
    elif tipo_post == "DOMENICA":
        row = get_random_verse()
        caption = (
            "⏳ NON MANCARE, STA PER INIZIARE! ⏳\n\n"
            "Ci siamo quasi! Alle **18:00** iniziamo il culto. ❤️\n"
            "Lascia tutto e corri alla presenza di Dio!\n\n"
            f"{INDIRIZZO_CHIESA}\n\n"
            "Gesù ti sta aspettando!\n\n"
            f"────────────────\n"
            f"📖 *La Parola di oggi:*\n"
            f"“{row['Frase']}”\n"
            f"({row['Riferimento']})\n"
            f"────────────────\n\n"
            "#chiesa #grotte #fede #culto #vangelodelgiorno #nonmancare"
        )

    # --- GENERAZIONE E INVIO ---
    if row is not None and caption:
        print(f"📖 Versetto scelto: {row['Riferimento']}")
        img = add_logo(create_verse_image(row))
        buf = BytesIO()
        img.save(buf, format='PNG')
        img_data = buf.getvalue()
        
        send_telegram(img_data, caption)
        post_facebook(img_data, caption)
        trigger_make_webhook(row, img_data, caption)
    else:
        print("❌ Nessun versetto trovato o tipo post non valido.")

# --- 10. SCHEDULATORE ---
def job_mattina():
    pubblica_post("QUOTIDIANO")

def job_sabato():
    pubblica_post("SABATO")

def job_domenica():
    pubblica_post("DOMENICA")

if __name__ == "__main__":
    print("🤖 Bot Chiesa avviato!")
    print(f"📍 Indirizzo impostato: {INDIRIZZO_CHIESA}")
    print("📅 Orari programmati:")
    print("   - TUTTI I GIORNI: 08:00 (Versetto Quotidiano)")
    print("   - Sabato EXTRA:   17:08 (Invito Culto)")
    print("   - Domenica EXTRA: 17:00 (Reminder Urgente)")

    # 1. TUTTI I GIORNI (inclusi Sabato e Domenica) - Versetto Quotidiano
    schedule.every().day.at("08:00").do(job_mattina)

    # 2. Sabato - Invito Extra
    schedule.every().saturday.at("17:08").do(job_sabato)

    # 3. Domenica - Reminder Extra Urgente
    schedule.every().sunday.at("17:00").do(job_domenica)

    # Loop Infinito
    while True:
        schedule.run_pending()
        time.sleep(60)
