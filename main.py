import os
import requests
import pandas as pd
import random
import json
import pytz
import textwrap
from datetime import datetime
from io import BytesIO
from PIL import Image, ImageOps, ImageDraw, ImageFont
from dotenv import load_dotenv

# Carica le variabili da .env se il file esiste (test locale)
load_dotenv()

# --- CONFIGURAZIONE (Prende i dati dai Secrets di GitHub) ---
FACEBOOK_TOKEN = os.getenv("FACEBOOK_TOKEN")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
PAGE_ID = os.getenv("PAGE_ID", "1479209002311050")
MAKE_WEBHOOK_URL = os.getenv("MAKE_WEBHOOK_URL")

CSV_FILE = "Frasichiesa.csv"
LOGO_PATH = "logo.png"
FONT_NAME = "arial.ttf" 

# --- GESTIONE DATE E ORARI ---
def get_italian_time():
    utc_now = datetime.now(pytz.utc)
    rome_tz = pytz.timezone('Europe/Rome')
    return utc_now.astimezone(rome_tz)

# --- 1. GESTIONE DATI ---
def get_random_verse():
    try:
        if not os.path.exists(CSV_FILE):
            print(f"⚠️ Errore: Il file {CSV_FILE} non esiste.")
            return None
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
    
    if "sabato_invito" in cat:
        return f"welcoming church entrance, open doors, warm golden hour light, crowd gathering happily, {base_style}"
    elif "domenica_avviso" in cat:
        return f"inside a modern church, worship atmosphere, hands raised, glowing light, spiritual energy, {base_style}"
    
    prompts_consolazione = [
        f"peaceful sunset over calm lake, warm golden light, {base_style}",
        f"gentle morning light through trees, forest path, {base_style}"
    ]
    prompts_esortazione = [
        f"majestic mountain peak, sunrise rays, dramatic sky, {base_style}",
        f"eagle flying in blue sky, sun flare, freedom, {base_style}"
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
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            return Image.open(BytesIO(response.content)).convert("RGBA")
    except Exception as e:
        print(f"⚠️ Errore AI: {e}")
    return Image.new('RGBA', (1080, 1080), (50, 50, 70))

# --- 4. FUNZIONE CARICAMENTO FONT ---
def load_font(size):
    fonts_to_try = [FONT_NAME, "DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "arial.ttf"]
    for font_path in fonts_to_try:
        try:
            return ImageFont.truetype(font_path, size)
        except: continue
    return ImageFont.load_default()

# --- 5. CREAZIONE IMMAGINE ---
def create_image_overlay(base_img, main_text, sub_text, is_special=False):
    base_img = base_img.resize((1080, 1080))
    overlay = Image.new('RGBA', base_img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    W, H = base_img.size
    
    title_size = 80 if is_special else 100
    sub_size = 50 if is_special else 60
    
    font_txt = load_font(title_size)  
    font_ref = load_font(sub_size)    

    lines = textwrap.wrap(main_text, width=20 if is_special else 16) 
    
    line_height = title_size + 10
    text_block_height = len(lines) * line_height
    ref_height = 80
    total_content_height = text_block_height + ref_height
    
    start_y = ((H - total_content_height) / 2) - 100
    
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
        
    bbox_ref = draw_final.textbbox((0, 0), sub_text, font=font_ref)
    w_ref = bbox_ref[2] - bbox_ref[0]
    draw_final.text(((W - w_ref)/2, current_y + 25), sub_text, font=font_ref, fill="#FFD700")

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

# --- 7. SOCIAL ---
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
    if not FACEBOOK_TOKEN: 
        print("❌ Nessun FACEBOOK_TOKEN trovato.")
        return
    url = f"https://graph.facebook.com/v19.0/{PAGE_ID}/photos?access_token={FACEBOOK_TOKEN}"
    files = {'file': ('img.png', img_bytes, 'image/png')}
    data = {'message': message, 'published': 'true'}
    try:
        resp = requests.post(url, files=files, data=data)
        if resp.status_code == 200:
            print("✅ Facebook OK")
        else:
            print(f"❌ Facebook Error: {resp.text}")
    except Exception as e: print(f"❌ Facebook Exception: {e}")

def trigger_make_webhook(categoria, frase, riferimento, img_bytes, meditazione_text):
    if not MAKE_WEBHOOK_URL: return
    print("📡 Inviando a Make.com...")
    data_payload = {
        "categoria": categoria,
        "riferimento": riferimento,
        "frase": frase,
        "meditazione": meditazione_text
    }
    files_payload = {'upload_file': ('post_chiesa.png', img_bytes, 'image/png')}
    try:
        requests.post(MAKE_WEBHOOK_URL, data=data_payload, files=files_payload)
        print("✅ Webhook Make attivato!")
    except Exception as e: print(f"❌ Errore Make: {e}")

# --- 8. MEDITAZIONE ---
def genera_meditazione(row):
    cat = str(row['Categoria']).lower()
    intro = random.choice(["🔥 𝗣𝗮𝗿𝗼𝗹𝗮 𝗱𝗶 𝗩𝗶𝘁𝗮:", "🕊️ 𝗚𝘂𝗶𝗱𝗮 𝗱𝗲𝗹𝗹𝗼 𝗦𝗽𝗶𝗿𝗶𝘁𝗼:", "🙏 𝗣𝗲𝗿 𝗶𝗹 𝘁𝘂𝗼 𝗖𝘂𝗼𝗿𝗲:"])
    msgs = ["Metti Dio al primo posto e Lui si prenderà cura di tutto. Amen!"]
    if "consolazione" in cat:
        msgs = ["Non temere! Lo Spirito Santo è il Consolatore.", "Affida ogni peso a Gesù."]
    elif "esortazione" in cat:
        msgs = ["Alzati nel nome di Gesù!", "Sii forte e coraggioso. Dio è con te."]
    return f"{intro}\n{random.choice(msgs)}"

# --- MAIN ---
def main():
    ita_time = get_italian_time()
    weekday = ita_time.weekday() # 0=Lun, 5=Sab, 6=Dom
    hour = ita_time.hour
    print(f"🕒 Orario rilevato: {ita_time.strftime('%A %H:%M')}")

    img_data = None
    caption = ""
    tipo_post = ""

    if weekday == 5 and hour >= 16:
        tipo_post = "Invito Sabato"
        testo_img, sotto_testo = "Sei invitato alla riunione di domani!", "Ore 18:00 - Ti aspettiamo"
        caption = "📣 𝗜𝗡𝗩𝗜𝗧𝗢 𝗦𝗣𝗘𝗖𝗜𝗔𝗟𝗘\n\nDomani ore 18:00! 🙌\n#chiesa #culto"
        prompt = get_image_prompt("sabato_invito")
        base_img = get_ai_image(prompt)
        final_img = add_logo(create_image_overlay(base_img, testo_img, sotto_testo, is_special=True))
    
    elif weekday == 6 and hour >= 16:
        tipo_post = "Reminder Domenica"
        testo_img, sotto_testo = "Ehi, non tardare!", "Iniziamo alle 18:00!"
        caption = "⏰ 𝗠𝗔𝗡𝗖𝗔 𝗣𝗢𝗖𝗢!\nTi stiamo aspettando! ❤️"
        prompt = get_image_prompt("domenica_avviso")
        base_img = get_ai_image(prompt)
        final_img = add_logo(create_image_overlay(base_img, testo_img, sotto_testo, is_special=True))

    else:
        tipo_post = "Versetto"
        row = get_random_verse()
        if row is not None:
            prompt = get_image_prompt(row['Categoria'])
            base_img = get_ai_image(prompt)
            final_img = add_logo(create_image_overlay(base_img, f"“{row['Frase']}”", str(row['Riferimento'])))
            meditazione = genera_meditazione(row)
            caption = f"✨ {str(row['Categoria']).upper()} ✨\n\n“{row['Frase']}”\n📖 {row['Riferimento']}\n\n{meditazione}"
        else: return

    # Conversione finale per invio
    buf = BytesIO()
    final_img.save(buf, format='PNG')
    img_bytes = buf.getvalue()

    # Invio globale
    send_telegram(img_bytes, caption)
    post_facebook(img_bytes, caption)
    trigger_make_webhook(tipo_post, caption, "Social Post", img_bytes, caption)

if __name__ == "__main__":
    main()
