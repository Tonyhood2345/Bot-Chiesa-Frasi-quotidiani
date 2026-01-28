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
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

MAKE_WEBHOOK_URL = "https://hook.eu1.make.com/hiunkuvfe8mjvfsgyeg0vck4j8dwx6h2"

CSV_FILE = "Frasichiesa.csv"
LOGO_PATH = "logo.png"
# FONT_NAME rimosso perché usiamo il default generico
INDIRIZZO_CHIESA = "📍 Chiesa Evangelica Eterno Nostra Giustizia\nPiazza Umberto, Grotte (AG)"

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

# --- 4. FONT (MODIFICATO PER GENERICO + GRANDE) ---
def load_font(size):
    try:
        # Tenta di caricare il font di default scalabile (Richiede Pillow >= 10.0.0)
        return ImageFont.load_default(size=size)
    except TypeError:
        # Fallback per vecchie versioni di Pillow (o se size non è supportato)
        print("⚠️ Attenzione: Aggiorna Pillow per dimensionare il font di default.")
        return ImageFont.load_default()
    except Exception as e:
        print(f"⚠️ Errore Font: {e}")
        return ImageFont.load_default()

# --- 5. GRAFICA (MODIFICATO PER TESTO PIÙ GRANDE) ---
def create_verse_image(row):
    prompt = get_image_prompt(row['Categoria'])
    base_img = get_ai_image(prompt).resize((1080, 1080))
    overlay = Image.new('RGBA', base_img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    W, H = base_img.size
    
    # --- DIMENSIONI FONT AUMENTATE ---
    font_size_main = 150  # Era 100
    font_size_ref = 70    # Era 60
    
    font_txt = load_font(font_size_main)
    font_ref = load_font(font_size_ref)
    
    text = f"“{row['Frase']}”"
    
    # Riduco la larghezza del wrap perché il font è più grande (12 caratteri invece di 16)
    lines = textwrap.wrap(text, width=12)
    
    # Calcoli dimensioni aumentati
    line_height = font_size_main + 40 # Spazio tra le righe aumentato (circa 190px)
    total_h = (len(lines) * line_height) + 100
    start_y = ((H - total_h) / 2) - 100
    
    # Sfondo scuro adattato
    draw.rectangle([(20, start_y - 40), (W - 20, start_y + total_h + 60)], fill=(0, 0, 0, 150))
    
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
    # Sposto il riferimento un po' più in basso
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

# --- 7. INVIO A MAKE ---
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
    if not TELEGRAM_TOKEN: return
    try:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto", 
                      files={'photo': img}, data={'chat_id': TELEGRAM_CHAT_ID, 'caption': cap})
    except Exception as e: print(f"Errore Telegram: {e}")

# --- 8. LOGICA ---
def esegui_bot():
    now = datetime.now(timezone.utc)
    hour = now.hour
    weekday = now.weekday()
    print(f"🕒 Ore: {hour}, Giorno: {weekday}")

    row = None
    caption = ""

    # Logica Orari
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
        # MODALITA' MANUALE (Test)
        print("⚠️ Fuori orario: Modalità Test Attiva")
        row = get_random_verse()
        caption = f"✨ PAROLA DEL SIGNORE ✨\n\n“{row['Frase']}”\n📖 {row['Riferimento']}\n\n{INDIRIZZO_CHIESA}\n\n#test"

    # ESECUZIONE
    if row is not None:
        print("🚀 Generazione...")
        img = add_logo(create_verse_image(row))
        
        buf = BytesIO()
        img.save(buf, format='PNG')
        img_data = buf.getvalue()

        # 1. Telegram
        send_telegram(img_data, caption)
        
        # 2. MAKE
        trigger_make(row, img_data, caption)

        # 3. Salvataggio locale
        with open("output.txt", "w", encoding="utf-8") as f: f.write(caption)
        img.save("immagine.png", format="PNG")
        
        print("✅ Finito.")
    else:
        print("❌ Errore.")

if __name__ == "__main__":
    esegui_bot()
