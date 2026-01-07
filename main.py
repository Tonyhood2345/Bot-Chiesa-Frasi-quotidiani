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
# I token vengono presi dai Segreti di GitHub
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

# --- 2. GENERATORE PROMPT ---
def get_image_prompt(categoria):
    cat = str(categoria).lower().strip()
    prompts_consolazione = [
        "peaceful sunset over calm lake, warm golden light, nature, photorealistic, 8k, rays of light",
        "gentle morning light through trees, forest path, peaceful atmosphere, cinematic lighting"
    ]
    prompts_esortazione = [
        "majestic mountain peak, sunrise rays, dramatic sky, epic view, 8k, powerful nature",
        "eagle flying in blue sky, sun flare, freedom, strength, glorious light"
    ]
    prompts_altro = [
        "beautiful blue sky with white clouds, heaven light, spiritual background, ethereal",
        "field of flowers, spring, colorful, creation beauty, macro shot"
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

# --- FUNZIONE TESTO GIGANTE & BORDO NERO ---
def create_verse_image(row):
    prompt = get_image_prompt(row['Categoria'])
    base_img = get_ai_image(prompt).resize((1080, 1080))
    
    # Velo scuro leggero (per aiutare il contrasto)
    overlay = Image.new('RGBA', base_img.size, (0, 0, 0, 90))
    final_img = Image.alpha_composite(base_img, overlay)
    draw = ImageDraw.Draw(final_img)
    W, H = final_img.size
    
    try:
        # FONT GIGANTE (110)
        font_txt = ImageFont.truetype(FONT_PATH, 110)
        font_ref = ImageFont.truetype(FONT_PATH, 70)
    except:
        font_txt = ImageFont.load_default()
        font_ref = ImageFont.load_default()

    # Testo Versetto
    text = f"“{row['Frase']}”"
    # Wrap stretto per riempire il centro
    lines = textwrap.wrap(text, width=16)
    
    # Calcolo altezza blocco testo
    line_height = 125 
    total_height = len(lines) * line_height
    y = (H - total_height) / 2 - 60 
    
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font_txt)
        w = bbox[2] - bbox[0]
        # Bordo nero spesso (Stroke)
        draw.text(((W - w)/2, y), line, font=font_txt, fill="white", stroke_width=6, stroke_fill="black")
        y += line_height
        
    # Riferimento (Giallo con bordo nero)
    ref = str(row['Riferimento'])
    bbox_ref = draw.textbbox((0, 0), ref, font=font_ref)
    w_ref = bbox_ref[2] - bbox_ref[0]
    draw.text(((W - w_ref)/2, y + 50), ref, font=font_ref, fill="#FFD700", stroke_width=4, stroke_fill="black")

    return final_img

# --- 4. LOGO ---
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

# --- 5. MEDITAZIONE POSITIVA (NUOVA FUNZIONE) ---
def genera_meditazione(row):
    """
    Crea un breve pensiero positivo basato sulla categoria del versetto.
    """
    cat = str(row['Categoria']).lower()
    
    # Frasi di apertura random
    intro = random.choice([
        "🌿 𝗨𝗻 𝗽𝗲𝗻𝘀𝗶𝗲𝗿𝗼 𝗽𝗲𝗿 𝘁𝗲:",
        "💡 𝗟𝗮 𝗹𝘂𝗰𝗲 𝗱𝗶 𝗼𝗴𝗴𝗶:",
        "🙏 𝗠𝗲𝗱𝗶𝘁𝗶𝗮𝗺𝗼 𝗶𝗻𝘀𝗶𝗲𝗺𝗲:",
        "❤️ 𝗣𝗲𝗿 𝗶𝗹 𝘁𝘂𝗼 𝗰𝘂𝗼𝗿𝗲:"
    ])
    
    msg = ""

    # Logica in base alla categoria
    if "consolazione" in cat:
        msg = (
            "Non importa quanto sia grande la sfida che stai affrontando oggi, ricorda che non sei solo/a. "
            "C'è una pace che supera ogni comprensione pronta ad abbracciarti. "
            "Respira profondamente e lascia andare l'ansia: sei custodito/a nelle Sue mani sicure."
        )
    elif "esortazione" in cat:
        msg = (
            "Oggi hai la forza per superare qualsiasi ostacolo! "
            "Non guardare alle tue limitazioni, ma alla grandezza di Colui che ti fortifica. "
            "Alzati con coraggio: c'è un piano meraviglioso che si sta compiendo proprio per te."
        )
    elif "edificazione" in cat:
        msg = (
            "Ogni giorno è un'opportunità per costruire fondamenta solide nella tua vita. "
            "Fai tesoro di questa verità e lascia che guidi le tue decisioni. "
            "Cresci nella consapevolezza che sei amato/a e prezioso/a."
        )
    else: # Generico/Altro
        msg = (
            "Porta questa promessa nel tuo cuore per tutta la giornata. "
            "Lascia che sia la tua forza e il tuo sorriso. "
            "Le cose migliori devono ancora arrivare, credici con tutto te stesso/a!"
        )

    return f"{intro}\n{msg}"

# --- 6. SOCIAL ---
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
        
        # Creazione Immagine
        img = add_logo(create_verse_image(row))
        buf = BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)
        
        # Generazione Testo Meditazione
        meditazione = genera_meditazione(row)
        
        # Creazione Testo Post Completo
        caption = (
            f"✨ {str(row['Categoria']).upper()} ✨\n\n"
            f"“{row['Frase']}”\n"
            f"📖 {row['Riferimento']}\n\n"
            f"────────────────\n"
            f"{meditazione}\n"
            f"────────────────\n\n"
            f"📍 Chiesa L'Eterno Nostra Giustizia\n\n"
            f"#fede #vangelodelgiorno #chiesa #gesù #preghiera #bibbia #speranza #dioèamore #versettodelgiorno #amen"
        )
        
        # Invio
        send_telegram(buf, caption)
        buf.seek(0)
        post_facebook(buf, caption)
