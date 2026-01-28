import os
import requests
import pandas as pd
import matplotlib
matplotlib.use('Agg') 
import textwrap
import random
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timezone

# --- CONFIGURAZIONE ---
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN") or "INSERISCI_QUI_IL_TUO_TOKEN"
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID") or "INSERISCI_QUI_IL_TUO_ID"

MAKE_WEBHOOK_URL = "https://hook.eu1.make.com/hiunkuvfe8mjvfsgyeg0vck4j8dwx6h2"

CSV_FILE = "Frasichiesa.csv"
LOGO_PATH = "logo.png"
INDIRIZZO_CHIESA = "📍 Chiesa Evangelica Eterno Nostra Giustizia\nPiazza Umberto, Grotte (AG)"

# URL per scaricare il font (Roboto Bold per essere ben leggibile)
FONT_URL = "https://github.com/google/fonts/raw/main/apache/roboto/Roboto-Bold.ttf"
FONT_NAME = "Roboto-Bold.ttf"

# --- 1. LETTURA DATI ---
def get_random_verse(filtro_categoria=None):
    try:
        df = pd.read_csv(CSV_FILE)
        if df.empty: return None
        if filtro_categoria:
            df_filtered = df[df['Categoria'].astype(str).str.contains(filtro_categoria, case=False, na=False)]
            if not df_filtered.empty: return df_filtered.sample(1).iloc[0]
        return df.sample(1).iloc[0]
    except Exception as e:
        print(f"⚠️ Errore lettura CSV: {e}")
        return None

# --- 2. PROMPT AI ---
def get_image_prompt(categoria):
    cat = str(categoria).lower().strip()
    base_style = "bright, divine light, photorealistic, 8k, sun rays, cinematic"
    if "consolazione" in cat:
        return random.choice([f"peaceful sunset, {base_style}", f"forest path light, {base_style}"])
    elif "esortazione" in cat:
        return random.choice([f"majestic mountain, {base_style}", f"eagle sky, {base_style}"])
    else:
        return random.choice([f"blue sky clouds, {base_style}", f"flower field, {base_style}"])

# --- 3. GENERAZIONE IMMAGINE ---
def get_ai_image(prompt_text):
    print(f"🎨 Generazione immagine: {prompt_text}")
    try:
        clean_prompt = prompt_text.replace(" ", "%20")
        url = f"https://image.pollinations.ai/prompt/{clean_prompt}?width=1080&height=1080&nologo=true"
        response = requests.get(url, timeout=60)
        if response.status_code == 200:
            return Image.open(BytesIO(response.content)).convert("RGBA")
    except Exception as e:
        print(f"⚠️ Errore AI: {e}")
    return Image.new('RGBA', (1080, 1080), (50, 50, 70))

# --- 4. FONT ---
def load_font(size):
    if not os.path.exists(FONT_NAME):
        print("⬇️ Font mancante. Download in corso...")
        try:
            r = requests.get(FONT_URL)
            with open(FONT_NAME, 'wb') as f:
                f.write(r.content)
            print("✅ Font scaricato!")
        except Exception as e:
            print(f"⚠️ Impossibile scaricare il font: {e}. Uso default.")
            return ImageFont.load_default()
    try:
        return ImageFont.truetype(FONT_NAME, size)
    except Exception as e:
        return ImageFont.load_default()

# --- 5. GRAFICA (MODIFICATA: TESTO MOLTO PIÙ GRANDE) ---
def create_verse_image(row):
    prompt = get_image_prompt(row['Categoria'])
    base_img = get_ai_image(prompt).resize((1080, 1080))
    overlay = Image.new('RGBA', base_img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    W, H = base_img.size
    
    # --- NUOVE DIMENSIONI MAXI ---
    font_size_main = 200  # Aumentato drasticamente per leggibilità
    font_size_ref = 100    
    
    font_txt = load_font(font_size_main)
    font_ref = load_font(font_size_ref)
    
    text = f"“{row['Frase']}”"
    
    # Riduco i caratteri per riga così le parole sono più grosse e vanno a capo prima
    lines = textwrap.wrap(text, width=15) 
    
    # Calcoli dimensioni
    line_height = font_size_main + 10 # Spazio interlinea stretto
    total_h = (len(lines) * line_height) + 100
    start_y = ((H - total_h) / 2) - 80
    
    # Sfondo scuro
    draw.rectangle([(30, start_y - 40), (W - 30, start_y + total_h + 50)], fill=(0, 0, 0, 160))
    
    final_img = Image.alpha_composite(base_img, overlay)
    draw_final = ImageDraw.Draw(final_img)
    
    curr_y = start_y
    for line in lines:
        bbox = draw_final.textbbox((0, 0), line, font=font_txt)
        w = bbox[2] - bbox[0]
        draw_final.text(((W - w)/2, curr_y), line, font=font_txt, fill="white")
        curr_y += line_height
        
    ref = str(row['Riferimento'])
    bbox_ref = draw_final.textbbox((0, 0), ref, font=font_ref)
    w_ref = bbox_ref[2] - bbox_ref[0]
    draw_final.text(((W - w_ref)/2, curr_y + 30), ref, font=font_ref, fill="#FFD700")
    
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

# --- 7. INVIO ---
def trigger_make(row, img_bytes, cap):
    print("📡 Tentativo invio a Make...")
    try:
        files = {'upload_file': ('post.png', img_bytes, 'image/png')}
        data = {
            'categoria': row.get('Categoria'),
            'frase': row.get('Frase'), 
            'caption_completa': cap
        }
        res = requests.post(MAKE_WEBHOOK_URL, data=data, files=files)
        print(f"✅ Make risponde: {res.status_code}")
    except Exception as e: 
        print(f"❌ Errore Make: {e}")

def send_telegram(img, cap):
    if not TELEGRAM_TOKEN or "INSERISCI" in TELEGRAM_TOKEN:
        print("⚠️ Token Telegram mancante.")
        return
    try:
        print("📡 Invio a Telegram...")
        res = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto", 
            files={'photo': img}, 
            data={'chat_id': TELEGRAM_CHAT_ID, 'caption': cap}
        )
        print(f"Telegram status: {res.status_code}")
    except Exception as e: 
        print(f"❌ Errore Telegram: {e}")

# --- 8. ESECUZIONE ---
def esegui_bot():
    now = datetime.now(timezone.utc)
    hour = now.hour
    weekday = now.weekday()
    print(f"🕒 Ore: {hour}, Giorno: {weekday}")

    row = None
    caption = ""

    if 5 <= hour <= 8:
        row = get_random_verse()
        caption = f"✨ {str(row['Categoria']).upper()} ✨\n\n“{row['Frase']}”\n📖 {row['Riferimento']}\n\n{INDIRIZZO_CHIESA}\n\n#fede #vangelo"
    elif weekday == 5 and 9 <= hour <= 22:
        row = get_random_verse("Esortazione") or get_random_verse()
        caption = f"🚨 DOMANI CULTO! 🚨\n\nVi aspettiamo alle 18:00!\n{INDIRIZZO_CHIESA}\n\n📖 “{row['Frase']}”\n\n#culto #chiesa"
    elif weekday == 6 and 15 <= hour <= 17:
        row = get_random_verse()
        caption = f"⏳ TRA POCO CULTO! ⏳\n\nIniziamo alle 18:00.\n{INDIRIZZO_CHIESA}\n\n📖 “{row['Frase']}”\n\n#domenica"
    else:
        print("⚠️ Fuori orario: Modalità Test Attiva")
        row = get_random_verse()
        caption = f"✨ PAROLA DEL SIGNORE ✨\n\n“{row['Frase']}”\n📖 {row['Riferimento']}\n\n{INDIRIZZO_CHIESA}\n\n#test"

    if row is not None:
        print("🚀 Generazione...")
        img = add_logo(create_verse_image(row))
        
        buf = BytesIO()
        img.save(buf, format='PNG')
        img_data = buf.getvalue()

        send_telegram(img_data, caption)
        trigger_make(row, img_data, caption)

        with open("output.txt", "w", encoding="utf-8") as f: f.write(caption)
        img.save("immagine.png", format="PNG")
        print("✅ Finito.")
    else:
        print("❌ Errore.")

if __name__ == "__main__":
    esegui_bot()
