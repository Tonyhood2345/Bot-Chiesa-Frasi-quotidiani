import os
import requests
import pandas as pd
import textwrap
import random
from datetime import datetime
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

# --- CONFIGURAZIONE ---
# ⚠️ IMPORTANTE: Incolla qui sotto il link "Production URL" del nodo Webhook di n8n
N8N_WEBHOOK_URL = "http://localhost:5678/webhook-test/post-chiesa"

# Questi token servono solo se vuoi testare in locale (opzionali se usi n8n)
FACEBOOK_TOKEN = os.environ.get("FACEBOOK_TOKEN", "")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

PAGE_ID = "1479209002311050"
CSV_FILE = "Frasichiesa.csv"
LOGO_PATH = "logo.png"
FONT_NAME = "DejaVuSans-Bold.ttf"

# --- VERIFICA SECRET ALL'AVVIO ---
print("=" * 50)
print("🚀 AVVIO BOT CHIESA -> N8N")
print(f"⏰ UTC: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 50)

# --- 1. GESTIONE DATI ---
def get_random_verse():
    try:
        if not os.path.exists(CSV_FILE):
             print(f"❌ Errore: File {CSV_FILE} non trovato!")
             return None
        df = pd.read_csv(CSV_FILE)
        if df.empty:
            print("CSV vuoto!")
            return None
        # Prende un versetto a caso
        row = df.sample(1).iloc[0]
        print(f"\n📖 Versetto: {row['Riferimento']}")
        print(f"📂 Categoria: {row['Categoria']}")
        return row
    except Exception as e:
        print(f"Errore lettura CSV: {e}")
        return None

# --- 2. GENERATORE PROMPT ---
def get_image_prompt(categoria):
    cat = str(categoria).lower().strip()
    base_style = "bright, divine light, photorealistic, 8k, sun rays, cinematic"

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

# --- 3. GENERAZIONE IMMAGINE AI ---
def get_ai_image(prompt_text):
    print(f"\n🎨 Generazione immagine...")
    try:
        clean_prompt = prompt_text.replace(" ", "%20")
        url = f"https://image.pollinations.ai/prompt/{clean_prompt}?width=1080&height=1080&nologo=true"
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            print("✅ Immagine generata!")
            return Image.open(BytesIO(response.content)).convert("RGBA")
        else:
            print(f"Pollinations errore: {response.status_code}")
    except Exception as e:
        print(f"Errore AI: {e}")
    print("Uso immagine di default (Fallback)")
    return Image.new('RGBA', (1080, 1080), (50, 50, 70))

# --- 4. CARICAMENTO FONT ---
def load_font(size):
    for font_path in [FONT_NAME, "DejaVuSans.ttf", "arial.ttf"]:
        try:
            return ImageFont.truetype(font_path, size)
        except:
            continue
    return ImageFont.load_default()

# --- 5. CREAZIONE IMMAGINE CON TESTO ---
def create_verse_image(row):
    prompt = get_image_prompt(row['Categoria'])
    base_img = get_ai_image(prompt).resize((1080, 1080))

    overlay = Image.new('RGBA', base_img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    W, H = base_img.size

    font_txt = load_font(100)
    font_ref = load_font(60)

    # Virgolette normali per evitare errori di sintassi
    frase = str(row['Frase'])
    text = '"' + frase + '"'
    lines = textwrap.wrap(text, width=16)

    line_height = 110
    text_block_height = len(lines) * line_height
    total_content_height = text_block_height + 80

    start_y = ((H - total_content_height) / 2) - 150

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
        draw_final.text(((W - w) / 2, current_y), line, font=font_txt, fill="white")
        current_y += line_height

    ref = str(row['Riferimento'])
    bbox_ref = draw_final.textbbox((0, 0), ref, font=font_ref)
    w_ref = bbox_ref[2] - bbox_ref[0]
    draw_final.text(((W - w_ref) / 2, current_y + 25), ref, font=font_ref, fill="#FFD700")

    return final_img

# --- 6. LOGO ---
def add_logo(img):
    if os.path.exists(LOGO_PATH):
        try:
            logo = Image.open(LOGO_PATH).convert("RGBA")
            w = int(img.width * 0.20)
            h = int(w * (logo.height / logo.width))
            logo = logo.resize((w, h))
            img.paste(logo, ((img.width - w) // 2, img.height - h - 30), logo)
            print("✅ Logo aggiunto")
        except Exception as e:
            print(f"Errore logo: {e}")
    else:
        print("⚠️ logo.png non trovato, proseguo senza.")
    return img

# --- 7. TESTI DINAMICI ---
def genera_meditazione(row):
    cat = str(row['Categoria']).lower()
    intro = random.choice([
        "🔥 Parola di Vita:",
        "🕊️ Guida dello Spirito:",
        "🙏 Per il tuo Cuore:",
        "🙌 Gloria a Dio:"
    ])

    if "consolazione" in cat:
        msgs = [
            "Fratello, sorella, non temere! Lo Spirito Santo è il Consolatore e oggi asciuga ogni tua lacrima.",
            "Affida ogni peso a Gesù. Lui ha già portato le tue sofferenze sulla croce per darti pace."
        ]
    elif "esortazione" in cat:
        msgs = [
            "Alzati nel nome di Gesù! Dichiara vittoria sulla tua situazione.",
            "Sii forte e coraggioso. Non guardare alle circostanze!"
        ]
    else:
        msgs = [
            "Metti Dio al primo posto e Lui si prenderà cura di tutto il resto. Amen!",
            "Ricorda: se Dio è per noi, chi sarà contro di noi?"
        ]

    return intro + "\n" + random.choice(msgs)


def get_footer_message(row):
    giorno = datetime.utcnow().weekday()
    ora = datetime.utcnow().hour
    is_pomeriggio = ora >= 15

    if giorno == 5 and is_pomeriggio:
        return "🗓️ POMERIGGIO PER DOMANI:\n" + random.choice([
            "Preparati! Domani alle 18:00 ci riuniamo per lodare il Signore. Non mancare!",
            "Domani è il giorno del Signore! Ti aspettiamo alle 18:00.",
            "Un invito speciale: domani ore 18:00 culto di adorazione. Gesù ti aspetta!"
        ])
    elif giorno == 6 and is_pomeriggio:
        return "🚨 AVVISO IMPORTANTE:\n" + random.choice([
            "Vieni in Chiesa stasera alle 18:00! Gesù ti sta aspettando.",
            "Ti ricordo: appuntamento con Gesù alle 18:00. Non mancare!",
            "La Parola di Dio oggi alle 18:00 sarà detta per il tuo bisogno."
        ])
    else:
        cat = str(row['Categoria']).lower()
        if "consolazione" in cat:
            return random.choice([
                "Nutri il tuo spirito. Dio è il tuo rifugio sicuro. Pace a te!",
                "Lascia che la Sua pace custodisca il tuo cuore. Egli è fedele in eterno.",
                "Non sei mai solo: la Sua Parola è balsamo per l'anima. Alleluia!"
            ])
        elif "esortazione" in cat:
            return random.choice([
                "La fede viene dall'udire la Parola di Dio. Risplendi per la Sua gloria!",
                "Sii un operatore della Parola e non soltanto un uditore!",
                "Chi confida nell'Eterno rinnova le forze."
            ])
        else:
            return "Nutri il tuo spirito con la Parola oggi. Alleluia!"


# --- 8. WEBHOOK N8N (Il cuore del sistema) ---
def trigger_n8n_webhook(img_bytes, caption_social, row):
    print("\n🔗 === CONNESSIONE A N8N ===")

    if "INSERISCI_QUI" in N8N_WEBHOOK_URL:
        print("❌ ERRORE: Non hai inserito il link del Webhook di n8n nel codice!")
        return False

    # Dati da mandare a n8n
    data_payload = {
        "categoria": str(row.get('Categoria', 'N/A')),
        "riferimento": str(row.get('Riferimento', 'N/A')),
        "frase": str(row.get('Frase', 'N/A')),
        # Mandiamo il testo completo del post!
        "caption": caption_social 
    }
    
    # Mandiamo l'immagine come file
    # 'upload_file' è il nome del campo che vedrai in n8n
    files_payload = {'upload_file': ('post_chiesa.png', img_bytes, 'image/png')}

    try:
        response = requests.post(N8N_WEBHOOK_URL, data=data_payload, files=files_payload, timeout=45)
        print(f"Risposta Server n8n: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ SUCCESSO: Immagine e Testo inviati a n8n!")
            return True
        else:
            print(f"❌ ERRORE n8n: {response.text}")
            return False
    except Exception as e:
        print(f"❌ ERRORE DI CONNESSIONE: {e}")
        return False


# --- MAIN ---
if __name__ == "__main__":
    row = get_random_verse()
    if row is None:
        print("Nessun versetto disponibile!")
        exit(1)

    # 1. Crea immagine
    img = add_logo(create_verse_image(row))
    buf = BytesIO()
    img.save(buf, format='PNG')
    img_data = buf.getvalue()
    print(f"\n🖼️ Immagine creata: {len(img_data)} bytes")

    # 2. Crea Testi (Meditazione + Footer + Info)
    meditazione = genera_meditazione(row)
    footer = get_footer_message(row)

    # 3. Costruisci il testo FINALE per i Social
    caption_completa = (
        "📖 " + str(row['Riferimento']) + "\n\n"
        + meditazione + "\n\n"
        + "────────────────\n"
        + footer + "\n"
        + "────────────────\n"
        + "⛪ Chiesa L'Eterno Nostra Giustizia\n"
        + "📍 Piazza Umberto I, Grotte (AG)\n"
        + "👤 Pastore Infatino Giuseppe\n\n"
        + "#fede #vangelodelgiorno #chiesa #preghiera #bibbia #paroladidio #pentecostale"
    )

    # 4. INVIO A N8N
    print("\n" + "=" * 50)
    print("📤 INVIO AL CENTRO DI CONTROLLO (N8N)")
    print("=" * 50)

    n8n_ok = trigger_n8n_webhook(img_data, caption_completa, row)

    print("\n" + "=" * 50)
    print(f"📊 ESITO FINALE: {'✅ TUTTO OK' if n8n_ok else '❌ QUALCOSA È ANDATO STORTO'}")
    print("=" * 50)
