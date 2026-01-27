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
FONT_NAME = "arial.ttf" 
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

# --- 3. GENERAZIONE IMMAGINE AI ---
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
    fonts_to_try = [FONT_NAME, "DejaVuSans-Bold.ttf", "arial.ttf"]
    for font_path in fonts_to_try:
        try:
            return ImageFont.truetype(font_path, size)
        except: continue
    return ImageFont.load_default()

# --- 5. COMPOSIZIONE GRAFICA ---
def create_verse_image(row):
    prompt = get_image_prompt(row['Categoria'])
    base_img = get_ai_image(prompt).resize((1080, 1080))
    
    overlay = Image.new('RGBA', base_img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    W, H = base_img.size
    
    font_txt = load_font(100)  
    font_ref = load_font(60)   

    text = f"“{row['Frase']}”"
    lines = textwrap.wrap(text, width=16) 
    
    line_height = 110
    text_block_height = len(lines) * line_height
    ref_height = 80
    total_content_height = text_block_height + ref_height
    
    start_y = ((H - total_content_height) / 2) - 150
    
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
    draw_final.text(((W - w_ref)/2, current_y + 25), ref, font=font_ref, fill="#FFD700")

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

# --- 7. INVIO TELEGRAM & MAKE ---
def send_telegram(img, cap):
    if not TELEGRAM_TOKEN: return
    try:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto", 
                      files={'photo': img}, data={'chat_id': TELEGRAM_CHAT_ID, 'caption': cap})
    except Exception as e: print(f"Errore Telegram: {e}")

def trigger_make(row, img, cap):
    try:
        requests.post(MAKE_WEBHOOK_URL, 
                      data={'categoria': row.get('Categoria'), 'frase': row.get('Frase'), 'caption_completa': cap},
                      files={'upload_file': ('post.png', img, 'image/png')})
    except Exception as e: print(f"Errore Make: {e}")

# --- 8. LOGICA PRINCIPALE (MODIFICATA) ---
def esegui_bot():
    now = datetime.now(timezone.utc)
    hour = now.hour
    weekday = now.weekday()
    
    print(f"🕒 Orario UTC: {hour}:00 - Giorno: {weekday}")

    row = None
    caption = ""

    # REGOLA 1: MATTINA (05-08 UTC)
    if 5 <= hour <= 8:
        print("☀️ Slot: MATTINA")
        row = get_random_verse()
        if row is not None:
            intro = random.choice(["🔥 Parola di Vita:", "🕊️ Guida dello Spirito:", "🙏 Per il tuo Cuore:"])
            frase_extra = random.choice(["Dio ti benedica oggi.", "Sii forte nel Signore.", "Cammina per fede."])
            caption = f"""✨ {str(row['Categoria']).upper()} ✨

“{row['Frase']}”
📖 {row['Riferimento']}

────────────────
{intro}
{frase_extra}
────────────────

{INDIRIZZO_CHIESA}

#fede #vangelodelgiorno #chiesa #gesù"""

    # REGOLA 2: SABATO (09-22 UTC)
    elif weekday == 5 and 9 <= hour <= 22:
        print("🚨 Slot: SABATO")
        row = get_random_verse("Esortazione")
        if row is None: row = get_random_verse()
        caption = f"""🚨 NON MANCARE DOMANI! 🚨

Fratello, sorella! Domani è il giorno del Signore! 🙌
Ti aspettiamo per lodare Dio insieme.

🗓 **DOMANI DOMENICA**
🕕 **ORE 18:00**
{INDIRIZZO_CHIESA}

Non venire da solo, porta un amico! Dio ha una parola per te. 🔥

────────────────
📖 *Parola per te:*
“{row['Frase']}”
({row['Riferimento']})
────────────────

#chiesa #grotte #fede #culto"""

    # REGOLA 3: DOMENICA (15-17 UTC)
    elif weekday == 6 and 15 <= hour <= 17:
        print("⏳ Slot: DOMENICA")
        row = get_random_verse()
        caption = f"""⏳ NON MANCARE, STA PER INIZIARE! ⏳

Ci siamo quasi! Alle **18:00** iniziamo il culto. ❤️
Lascia tutto e corri alla presenza di Dio!

{INDIRIZZO_CHIESA}

Gesù ti sta aspettando!

────────────────
📖 *La Parola:*
“{row['Frase']}”
({row['Riferimento']})
────────────────

#chiesa #grotte #culto #nonmancare"""

    # --- MODIFICA FONDAMENTALE ---
    # Se non siamo in nessuno degli orari sopra, significa che l'hai lanciato a mano!
    # Invece di fermarsi, ora genera un post "generico".
    else:
        print("⚠️ Nessun orario schedulato rilevato. Eseguo in MODALITÀ MANUALE!")
        row = get_random_verse()
        if row is not None:
            # Crea una caption standard che va bene sempre
            caption = f"""✨ PAROLA DEL SIGNORE ✨

“{row['Frase']}”
📖 {row['Riferimento']}

Dio ti benedica grandemente!

────────────────
{INDIRIZZO_CHIESA}

#fede #bibbia #gesù #chiesa"""

    # ESECUZIONE (Valida per tutti i casi sopra)
    if row is not None and caption:
        print(f"🚀 Generazione contenuto...")
        img_final = add_logo(create_verse_image(row))
        
        # Buffer per invio immediato Telegram/Make
        buf = BytesIO()
        img_final.save(buf, format='PNG')
        img_data = buf.getvalue()
        
        # 1. Invia a Telegram e Make
        send_telegram(img_data, caption)
        trigger_make(row, img_data, caption)
        
        # 2. SALVATAGGIO SU DISCO PER GITHUB/N8N
        with open("output.txt", "w", encoding="utf-8") as f:
            f.write(caption)
        
        img_final.save("immagine.png", format="PNG")
        
        print("✅ Immagine e Testo salvati su disco per n8n.")
    else:
        print("❌ Errore: Nessun contenuto generato (Forse CSV vuoto?).")

if __name__ == "__main__":
    esegui_bot()

