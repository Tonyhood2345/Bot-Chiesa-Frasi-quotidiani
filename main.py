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

# --- 2. GENERATORE PROMPT (SOLO IMMAGINI LUMINOSE) ---
def get_image_prompt(categoria):
    cat = str(categoria).lower().strip()
    # Aggiungo keyword "bright, sunny, divine light" per forzare la luminosità
    base_style = "bright, sunny, divine light, photorealistic, 8k, uplifting"
    
    prompts_consolazione = [
        f"peaceful sunset with sun rays breaking through clouds, {base_style}",
        f"calm lake reflection morning sun, {base_style}",
        f"hands reaching for light in sky, {base_style}"
    ]
    prompts_esortazione = [
        f"majestic mountain peak in full daylight, {base_style}",
        f"eagle flying in bright blue sky with sun flare, {base_style}",
        f"pathway in green forest with sunbeams, {base_style}"
    ]
    prompts_altro = [
        f"beautiful blue sky with white fluffy clouds, {base_style}",
        f"field of flowers in spring sunshine, {base_style}"
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
    return Image.new('RGBA', (1080, 1080), (200, 200, 200)) # Fallback chiaro

# --- 4. FUNZIONE TESTO "LUMINOSO & LEGGIBILE" (Drop Shadow) ---
def create_verse_image(row):
    prompt = get_image_prompt(row['Categoria'])
    base_img = get_ai_image(prompt).resize((1080, 1080))
    
    # Velo leggerissimo (solo 40 su 255) per mantenere la luce
    overlay = Image.new('RGBA', base_img.size, (0, 0, 0, 40))
    final_img = Image.alpha_composite(base_img, overlay)
    draw = ImageDraw.Draw(final_img)
    W, H = final_img.size
    
    try:
        font_txt = ImageFont.truetype(FONT_PATH, 110)
        font_ref = ImageFont.truetype(FONT_PATH, 70)
    except:
        font_txt = ImageFont.load_default()
        font_ref = ImageFont.load_default()

    text = f"“{row['Frase']}”"
    lines = textwrap.wrap(text, width=16)
    
    line_height = 125
    total_height = len(lines) * line_height
    y = (H - total_height) / 2 - 60
    
    # Parametri Ombra (Spostamento)
    shadow_offset = 6 
    
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font_txt)
        w = bbox[2] - bbox[0]
        
        # 1. Disegna l'OMBRA (Nero semi-trasparente) spostata
        # Simula un'ombra morbida disegnandola più volte o con colore meno intenso se necessario
        # Qui usiamo un nero netto spostato per massima leggibilità pulita
        draw.text(((W - w)/2 + shadow_offset, y + shadow_offset), line, font=font_txt, fill="black")
        
        # 2. Disegna il TESTO (Bianco Puro) sopra
        draw.text(((W - w)/2, y), line, font=font_txt, fill="white")
        
        y += line_height
        
    # Riferimento (Oro con Ombra Nera)
    ref = str(row['Riferimento'])
    bbox_ref = draw.textbbox((0, 0), ref, font=font_ref)
    w_ref = bbox_ref[2] - bbox_ref[0]
    
    # Ombra riferimento
    draw.text(((W - w_ref)/2 + 4, y + 50 + 4), ref, font=font_ref, fill="black")
    # Testo riferimento
    draw.text(((W - w_ref)/2, y + 50), ref, font=font_ref, fill="#FFD700") # Oro

    return final_img

# --- 5. LOGO ---
def add_logo(img):
    if os.path.exists(LOGO_PATH):
        try:
            logo = Image.open(LOGO_PATH).convert("RGBA")
            w = int(img.width * 0.20)
            h = int(w * (logo.height / logo.width))
            logo = logo.resize((w, h))
            img.paste(logo, ((img.width - w)//2, img.height - h - 40), logo)
        except: pass
    return img

# --- 6. MEDITAZIONE ---
def genera_meditazione(row):
    cat = str(row['Categoria']).lower()
    
    intro = random.choice([
        "🌿 𝗨𝗻 𝗽𝗲𝗻𝘀𝗶𝗲𝗿𝗼 𝗽𝗲𝗿 𝘁𝗲:",
        "💡 𝗟𝗮 𝗹𝘂𝗰𝗲 𝗱𝗶 𝗼𝗴𝗴𝗶:",
        "🙏 𝗠𝗲𝗱𝗶𝘁𝗶𝗮𝗺𝗼 𝗶𝗻𝘀𝗶𝗲𝗺𝗲:",
        "❤️ 𝗣𝗲𝗿 𝗶𝗹 𝘁𝘂𝗼 𝗰𝘂𝗼𝗿𝗲:"
    ])
    
    msg = ""
    if "consolazione" in cat:
        msg = "Non sei solo/a nelle tue sfide. C'è una pace pronta ad abbracciarti oggi. Respira e affidati."
    elif "esortazione" in cat:
        msg = "Oggi hai una forza nuova! Non guardare l'ostacolo, ma guarda alla vittoria che ti aspetta."
    elif "edificazione" in cat:
        msg = "Costruisci la tua giornata su questa verità. Sei prezioso/a e amato/a."
    else:
        msg = "Porta questa promessa nel cuore, sarà la tua forza e il tuo sorriso oggi."

    return f"{intro}\n{msg}"

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
            f"📍 Chiesa L'Eterno nostra Giustizia\n\n"
            f"#fede #vangelodelgiorno #chiesa #gesù #preghiera #bibbia #speranza #dioèamore #versettodelgiorno #amen"
        )
        
        send_telegram(buf, caption)
        buf.seek(0)
        post_facebook(buf, caption)
