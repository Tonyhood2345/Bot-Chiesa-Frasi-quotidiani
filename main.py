import os
import requests
import pandas as pd
import random
import textwrap
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

# --- CONFIGURAZIONE ---
# Se usi le variabili d'ambiente (Secrets) lascialo così.
# Altrimenti metti i tuoi dati tra virgolette qui sotto.
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN") or "INSERISCI_TOKEN_QUI"
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID") or "INSERISCI_CHAT_ID_QUI"
FACEBOOK_TOKEN = os.environ.get("FACEBOOK_TOKEN")
PAGE_ID = "1479209002311050"

MAKE_WEBHOOK_URL = "https://hook.eu1.make.com/hiunkuvfe8mjvfsgyeg0vck4j8dwx6h2"

CSV_FILE = "Frasichiesa.csv"
LOGO_PATH = "logo.png"
INDIRIZZO_CHIESA = "📍 Chiesa Evangelica Eterno Nostra Giustizia\nPiazza Umberto, Grotte (AG)"

# Configurazione Font (Download Automatico per evitare errori)
FONT_URL = "https://github.com/google/fonts/raw/main/apache/roboto/Roboto-Bold.ttf"
FONT_NAME = "Roboto-Bold.ttf"

# --- 1. GESTIONE RISORSE (FONT) ---
def check_resources():
    if not os.path.exists(FONT_NAME):
        print("⬇️ Scarico il Font per i testi...")
        try:
            r = requests.get(FONT_URL)
            with open(FONT_NAME, 'wb') as f:
                f.write(r.content)
        except: pass

def load_font(size):
    try:
        return ImageFont.truetype(FONT_NAME, size)
    except:
        return ImageFont.load_default()

# --- 2. GESTIONE DATI ---
def get_random_verse():
    try:
        df = pd.read_csv(CSV_FILE)
        if df.empty: return None
        return df.sample(1).iloc[0]
    except Exception as e:
        print(f"⚠️ Errore lettura CSV: {e}")
        return None

# --- 3. PROMPT AI ---
def get_image_prompt(categoria):
    cat = str(categoria).lower().strip()
    base_style = "bright, divine light, photorealistic, 8k, sun rays, cinematic"
    
    if "consolazione" in cat:
        return random.choice([
            f"peaceful sunset over calm lake, warm golden light, {base_style}",
            f"gentle morning light through trees, forest path, {base_style}"
        ])
    elif "esortazione" in cat:
        return random.choice([
            f"majestic mountain peak, sunrise rays, dramatic sky, {base_style}",
            f"eagle flying in blue sky, sun flare, freedom, {base_style}"
        ])
    else:
        return random.choice([
            f"beautiful blue sky with white clouds, heaven light, {base_style}",
            f"field of flowers, spring, colorful, {base_style}"
        ])

# --- 4. GENERAZIONE IMMAGINE ---
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

# --- 5. COMPOSIZIONE GRAFICA ---
def create_verse_image(row):
    prompt = get_image_prompt(row['Categoria'])
    base_img = get_ai_image(prompt).resize((1080, 1080))
    
    overlay = Image.new('RGBA', base_img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    W, H = base_img.size
    
    # Carichiamo il font scaricato
    font_txt = load_font(100)  
    font_ref = load_font(60)   

    text = f"“{row['Frase']}”"
    # Wrap del testo a 16 caratteri per ordine
    lines = textwrap.wrap(text, width=16) 
    
    line_height = 110
    text_block_height = len(lines) * line_height
    ref_height = 80
    total_content_height = text_block_height + ref_height
    
    start_y = ((H - total_content_height) / 2) - 100 # Centraggio
    
    # Sfondo scuro semitrasparente dietro al testo
    padding = 50
    draw.rectangle(
        [(40, start_y - padding), (W - 40, start_y + total_content_height + padding)], 
        fill=(0, 0, 0, 140)
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

# --- 6. AGGIUNTA LOGO ---
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

# --- 7. MEDITAZIONE ---
def genera_meditazione(row):
    cat = str(row['Categoria']).lower()
    intro = random.choice(["🔥 𝗣𝗮𝗿𝗼𝗹𝗮 𝗱𝗶 𝗩𝗶𝘁𝗮:", "🕊️ 𝗚𝘂𝗶𝗱𝗮 𝗱𝗲𝗹𝗹𝗼 𝗦𝗽𝗶𝗿𝗶𝘁𝗼:", "🙏 𝗣𝗲𝗿 𝗶𝗹 𝘁𝘂𝗼 𝗖𝘂𝗼𝗿𝗲:"])
    
    msgs = [
        "Metti Dio al primo posto e Lui si prenderà cura di tutto il resto.",
        "La fede sposta le montagne. Credici oggi!",
        "Non temere, Dio è con te in ogni passo.",
        "Affida a Gesù ogni tua preoccupazione."
    ]
    
    if "consolazione" in cat:
        msgs = ["Dio asciuga ogni lacrima.", "Non sei solo, il Consolatore è qui.", "La Sua pace custodisca il tuo cuore."]
    elif "esortazione" in cat:
        msgs = ["Alzati e risplendi!", "Sii forte e coraggioso.", "La vittoria è tua nel nome di Gesù."]

    return f"{intro}\n{random.choice(msgs)}"

# --- 8. INVIO TELEGRAM ---
def send_telegram(img_bytes, caption):
    if not TELEGRAM_TOKEN or "INSERISCI" in TELEGRAM_TOKEN:
        print("⚠️ Token Telegram mancante.")
        return
    
    print("📡 Invio a Telegram...")
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
        files = {'photo': ('img.png', img_bytes, 'image/png')}
        data = {'chat_id': TELEGRAM_CHAT_ID, 'caption': caption}
        
        response = requests.post(url, files=files, data=data)
        
        if response.status_code == 200:
            print("✅ Telegram OK: Messaggio inviato!")
        else:
            print(f"❌ Errore Telegram: {response.text}")
    except Exception as e:
        print(f"❌ Errore Connessione Telegram: {e}")

# --- 9. ALTRI SENDER (FB / MAKE) ---
def post_facebook(img_bytes, message):
    if not FACEBOOK_TOKEN: return
    try:
        url = f"https://graph.facebook.com/v19.0/{PAGE_ID}/photos?access_token={FACEBOOK_TOKEN}"
        files = {'file': ('img.png', img_bytes, 'image/png')}
        data = {'message': message, 'published': 'true'}
        requests.post(url, files=files, data=data)
        print("✅ Facebook OK")
    except: pass

def trigger_make_webhook(row, img_bytes, meditazione_text):
    print("📡 Invio a Make...")
    try:
        files = {'upload_file': ('post_chiesa.png', img_bytes, 'image/png')}
        data = {
            "categoria": row.get('Categoria'),
            "frase": row.get('Frase'),
            "meditazione": meditazione_text
        }
        requests.post(MAKE_WEBHOOK_URL, data=data, files=files)
        print("✅ Make OK")
    except: pass

# --- MAIN ---
if __name__ == "__main__":
    check_resources() # Scarica il font se manca
    row = get_random_verse()
    
    if row is not None:
        print(f"📖 Versetto selezionato: {row['Riferimento']}")
        
        # 1. Crea Immagine
        img = add_logo(create_verse_image(row))
        
        # 2. Converti in Bytes
        buf = BytesIO()
        img.save(buf, format='PNG')
        img_data = buf.getvalue()
        
        # 3. Testi
        meditazione = genera_meditazione(row)
        caption = (
            f"✨ {str(row['Categoria']).upper()} ✨\n\n"
            f"“{row['Frase']}”\n"
            f"📖 {row['Riferimento']}\n\n"
            f"────────────────\n{meditazione}\n────────────────\n\n"
            f"{INDIRIZZO_CHIESA}\n\n#fede #vangelodelgiorno #chiesa"
        )
        
        # 4. Invio
        send_telegram(img_data, caption)
        post_facebook(img_data, caption)
        trigger_make_webhook(row, img_data, meditazione)
        
    else:
        print("❌ Nessun contenuto trovato nel CSV.")
