import os
import sys
import subprocess

# --- 0. INSTALLAZIONE FORZATA DELLA VERSIONE VECCHIA (1.0.3) ---
# Questo blocco serve a correggere l'errore "No module named moviepy.editor"
def install_package(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

def uninstall_package(package):
    subprocess.call([sys.executable, "-m", "pip", "uninstall", "-y", package])

try:
    # Proviamo a vedere che versione c'è
    import moviepy
    version = moviepy.__version__
    print(f"ℹ️ Versione MoviePy trovata: {version}")
    
    # Se la versione inizia con "2", è quella sbagliata. La cancelliamo.
    if version.startswith("2"):
        print("⚠️ Versione 2.x incompatibile trovata. Disinstallazione in corso...")
        uninstall_package("moviepy")
        raise ImportError # Forziamo la reinstallazione
except (ImportError, AttributeError, ModuleNotFoundError):
    print("⬇️ Installazione MoviePy 1.0.3 (Versione Stabile)...")
    install_package("moviepy==1.0.3")
    install_package("decorator==4.4.2")
    install_package("imageio==2.4.1")
    # Trucco per ricaricare le librerie appena installate senza riavviare
    if "moviepy" in sys.modules: del sys.modules["moviepy"]
    if "moviepy.editor" in sys.modules: del sys.modules["moviepy.editor"]

# ORA che abbiamo la versione giusta, possiamo importare
try:
    from moviepy.editor import ImageClip, AudioFileClip
except ImportError:
    # Se fallisce ancora, riprova l'installazione brute-force
    install_package("moviepy==1.0.3")
    from moviepy.editor import ImageClip, AudioFileClip

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

# Nomi file
AUDIO_FILENAME = "musica.mp3"
AUDIO_URL = "https://cdn.pixabay.com/download/audio/2022/03/09/audio_c8c8a73467.mp3" 

FONT_FILENAME = "Roboto-Bold.ttf"
FONT_URL = "https://github.com/google/fonts/raw/main/apache/roboto/Roboto-Bold.ttf"

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
    print(f"🎨 Generazione immagine base: {prompt_text}")
    try:
        clean_prompt = prompt_text.replace(" ", "%20")
        url = f"https://image.pollinations.ai/prompt/{clean_prompt}?width=1080&height=1080&nologo=true"
        response = requests.get(url, timeout=60)
        if response.status_code == 200:
            return Image.open(BytesIO(response.content)).convert("RGBA")
    except Exception as e:
        print(f"⚠️ Errore AI: {e}")
    return Image.new('RGBA', (1080, 1080), (50, 50, 70))

# --- 4. GESTIONE RISORSE (Audio e Font) ---
def check_resources():
    # Font
    if not os.path.exists(FONT_FILENAME):
        print("⬇️ Scarico il Font...")
        try:
            r = requests.get(FONT_URL)
            with open(FONT_FILENAME, 'wb') as f: f.write(r.content)
        except: pass
        
    # Audio
    if not os.path.exists(AUDIO_FILENAME):
        print("⬇️ Scarico la Musica di sottofondo...")
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            r = requests.get(AUDIO_URL, headers=headers)
            with open(AUDIO_FILENAME, 'wb') as f: f.write(r.content)
            print("✅ Musica scaricata!")
        except Exception as e: 
            print(f"⚠️ Errore scaricamento musica: {e}")

def load_font(size):
    try: return ImageFont.truetype(FONT_FILENAME, size)
    except: return ImageFont.load_default()

# --- 5. GRAFICA (Testo Grande) ---
def create_verse_image(row):
    prompt = get_image_prompt(row['Categoria'])
    base_img = get_ai_image(prompt).resize((1080, 1080))
    overlay = Image.new('RGBA', base_img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    W, H = base_img.size
    
    font_size_main = 130
    font_size_ref = 65    
    font_txt = load_font(font_size_main)
    font_ref = load_font(font_size_ref)
    
    text = f"“{row['Frase']}”"
    lines = textwrap.wrap(text, width=15) 
    
    line_height = font_size_main + 10
    total_h = (len(lines) * line_height) + 100
    start_y = ((H - total_h) / 2) - 80
    
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

# --- 7. CREAZIONE VIDEO ---
def create_video_with_audio(image_obj, output_filename="post_video.mp4"):
    print("🎬 Creazione video in corso... (potrebbe volerci 1 minuto)")
    
    temp_img_path = "temp_image.png"
    image_obj.save(temp_img_path)
    
    try:
        # Usa il file scaricato o esistente
        if os.path.exists(AUDIO_FILENAME):
            audio = AudioFileClip(AUDIO_FILENAME)
        else:
            audio = None
            print("⚠️ Nessun audio trovato, video muto.")

        duration = 15
        # Se l'audio dura meno di 15s, usa la durata dell'audio
        if audio and audio.duration < 15:
            duration = audio.duration

        clip = ImageClip(temp_img_path).set_duration(duration)
        
        if audio:
            audio = audio.subclip(0, duration)
            audio = audio.audio_fadeout(2)
            clip = clip.set_audio(audio)
        
        # Scrittura Video (fps=1 per velocità massima)
        clip.write_videofile(output_filename, fps=1, codec="libx264", audio_codec="aac")
        print("✅ Video creato!")
        return output_filename
        
    except Exception as e:
        print(f"❌ Errore video: {e}")
        return None

# --- 8. INVIO ---
def trigger_make_video(row, video_path, cap):
    print("📡 Invio a Make...")
    try:
        with open(video_path, 'rb') as f:
            files = {'upload_file': ('post.mp4', f, 'video/mp4')}
            data = {'categoria': row.get('Categoria'), 'frase': row.get('Frase'), 'caption_completa': cap}
            requests.post(MAKE_WEBHOOK_URL, data=data, files=files)
        print("✅ Make OK")
    except Exception as e: print(f"❌ Make Errore: {e}")

def send_telegram_video(video_path, cap):
    if not TELEGRAM_TOKEN or "INSERISCI" in TELEGRAM_TOKEN: return
    print("📡 Invio a Telegram...")
    try:
        with open(video_path, 'rb') as f:
            requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo", 
                files={'video': f}, 
                data={'chat_id': TELEGRAM_CHAT_ID, 'caption': cap}
            )
        print("✅ Telegram OK")
    except Exception as e: print(f"❌ Telegram Errore: {e}")

# --- 9. ESECUZIONE ---
def esegui_bot():
    check_resources() # Scarica font e musica se mancano
    
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
        print("🚀 Generazione Immagine...")
        img = add_logo(create_verse_image(row))
        img.save("immagine_base.png")

        video_filename = create_video_with_audio(img, "video_finale.mp4")

        if video_filename:
            send_telegram_video(video_filename, caption)
            trigger_make_video(row, video_filename, caption)
            print("✅ TUTTO COMPLETATO.")
        else:
            print("❌ Errore creazione video.")
    else:
        print("❌ Nessuna frase trovata.")

if __name__ == "__main__":
    esegui_bot()
