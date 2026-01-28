import os
import sys
import subprocess
import time

# --- 0. GESTIONE DIPENDENZE ---
def setup_dependencies():
    print("🔧 Controllo librerie...")
    packages = [("moviepy", "1.0.3"), ("decorator", "4.4.2"), ("imageio", "2.4.1")]
    for package, version in packages:
        try:
            mod = __import__(package)
            if package == "moviepy" and mod.__version__.startswith("2"): raise ImportError
        except ImportError:
            print(f"⬇️ Installazione {package}=={version}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", f"{package}=={version}"])

setup_dependencies()

import requests
import pandas as pd
import matplotlib
matplotlib.use('Agg') 
import textwrap
import random
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timezone

try:
    from moviepy.editor import ImageClip, AudioFileClip
except ImportError:
    print("⚠️ Riavvio script per caricare librerie...")
    sys.exit(1)

# --- CONFIGURAZIONE ---
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN") or "INSERISCI_QUI_IL_TUO_TOKEN"
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID") or "INSERISCI_QUI_IL_TUO_ID"
MAKE_WEBHOOK_URL = "https://hook.eu1.make.com/hiunkuvfe8mjvfsgyeg0vck4j8dwx6h2"

CSV_FILE = "Frasichiesa.csv"
LOGO_PATH = "logo.png"
INDIRIZZO_CHIESA = "📍 Chiesa Evangelica Eterno Nostra Giustizia\nPiazza Umberto, Grotte (AG)"

# FILE AUDIO SICURO (Link GitHub raw solitamente non blocca i bot)
AUDIO_FILENAME = "musica.mp3"
AUDIO_URL = "https://github.com/rafaelgss/sample-file/raw/master/sample.mp3" 
# Alternativa se serve più lungo: "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3"

FONT_FILENAME = "Roboto-Bold.ttf"
FONT_URL = "https://github.com/google/fonts/raw/main/apache/roboto/Roboto-Bold.ttf"

# --- 1. DATI ---
def get_random_verse(filtro_categoria=None):
    try:
        df = pd.read_csv(CSV_FILE)
        if df.empty: return None
        if filtro_categoria:
            df_filtered = df[df['Categoria'].astype(str).str.contains(filtro_categoria, case=False, na=False)]
            if not df_filtered.empty: return df_filtered.sample(1).iloc[0]
        return df.sample(1).iloc[0]
    except Exception as e:
        print(f"⚠️ Errore CSV: {e}")
        return None

# --- 2. PROMPT ---
def get_image_prompt(categoria):
    cat = str(categoria).lower().strip()
    base_style = "bright, divine light, photorealistic, 8k, sun rays, cinematic"
    if "consolazione" in cat: return f"peaceful sunset, {base_style}"
    elif "esortazione" in cat: return f"majestic mountain, {base_style}"
    else: return f"blue sky clouds, {base_style}"

# --- 3. IMMAGINE ---
def get_ai_image(prompt_text):
    print(f"🎨 Generazione immagine: {prompt_text}")
    try:
        url = f"https://image.pollinations.ai/prompt/{prompt_text.replace(' ', '%20')}?width=1080&height=1080&nologo=true"
        return Image.open(BytesIO(requests.get(url, timeout=60).content)).convert("RGBA")
    except: return Image.new('RGBA', (1080, 1080), (50, 50, 70))

# --- 4. RISORSE (FIX AUDIO CORROTTO) ---
def check_resources():
    # 1. CANCELLA I FILE VECCHI/CORROTTI PER FORZARE IL RISCARICAMENTO
    if os.path.exists(AUDIO_FILENAME):
        # Se il file è troppo piccolo (meno di 10KB), è sicuramente rotto -> cancellalo
        if os.path.getsize(AUDIO_FILENAME) < 10000:
            print("🗑️ Trovato audio corrotto. Cancellazione...")
            os.remove(AUDIO_FILENAME)

    # 2. SCARICA FONT
    if not os.path.exists(FONT_FILENAME):
        try:
            with open(FONT_FILENAME, 'wb') as f: f.write(requests.get(FONT_URL).content)
        except: pass

    # 3. SCARICA AUDIO (CON HEADER FALSI PER NON ESSERE BLOCCATI)
    if not os.path.exists(AUDIO_FILENAME):
        print("⬇️ Scarico audio sicuro...")
        try:
            # FINGIAMO DI ESSERE UN BROWSER REALE
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
            r = requests.get(AUDIO_URL, headers=headers, stream=True)
            if r.status_code == 200:
                with open(AUDIO_FILENAME, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=1024):
                        if chunk: f.write(chunk)
                print("✅ Audio scaricato correttamente.")
            else:
                print(f"⚠️ Errore download audio: Stato {r.status_code}")
        except Exception as e: 
            print(f"⚠️ Errore download: {e}")

def load_font(size):
    try: return ImageFont.truetype(FONT_FILENAME, size)
    except: return ImageFont.load_default()

# --- 5. GRAFICA ---
def create_verse_image(row):
    base_img = get_ai_image(get_image_prompt(row['Categoria'])).resize((1080, 1080))
    overlay = Image.new('RGBA', base_img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    W, H = base_img.size
    
    font_main = load_font(130)
    font_ref = load_font(65)
    
    text = f"“{row['Frase']}”"
    lines = textwrap.wrap(text, width=15) 
    line_height = 140
    total_h = (len(lines) * line_height) + 100
    start_y = ((H - total_h) / 2) - 80
    
    draw.rectangle([(30, start_y - 40), (W - 30, start_y + total_h + 50)], fill=(0, 0, 0, 160))
    final = Image.alpha_composite(base_img, overlay)
    d = ImageDraw.Draw(final)
    
    curr_y = start_y
    for line in lines:
        w = d.textbbox((0, 0), line, font=font_main)[2]
        d.text(((W - w)/2, curr_y), line, font=font_main, fill="white")
        curr_y += line_height
        
    w_ref = d.textbbox((0, 0), str(row['Riferimento']), font=font_ref)[2]
    d.text(((W - w_ref)/2, curr_y + 30), str(row['Riferimento']), font=font_ref, fill="#FFD700")
    
    # LOGO
    if os.path.exists(LOGO_PATH):
        try:
            logo = Image.open(LOGO_PATH).convert("RGBA")
            w_l = int(W * 0.2)
            h_l = int(w_l * (logo.height / logo.width))
            final.paste(logo.resize((w_l, h_l)), ((W - w_l)//2, H - h_l - 30), logo.resize((w_l, h_l)))
        except: pass
        
    return final

# --- 6. VIDEO ---
def create_video(img_obj):
    print("🎬 Creazione video...")
    img_obj.save("temp.png")
    try:
        # Se l'audio non c'è o è rotto, creiamo video muto per non bloccare tutto
        if not os.path.exists(AUDIO_FILENAME) or os.path.getsize(AUDIO_FILENAME) < 1000:
            print("⚠️ Audio non valido. Creo video muto.")
            audio = None
        else:
            audio = AudioFileClip(AUDIO_FILENAME)
            
        # Durata fissa 15s (o meno se l'audio è corto)
        dur = 15
        if audio and audio.duration < 15: dur = audio.duration
        
        clip = ImageClip("temp.png").set_duration(dur)
        if audio: clip = clip.set_audio(audio.subclip(0, dur).audio_fadeout(2))
        
        clip.write_videofile("post.mp4", fps=1, codec="libx264", audio_codec="aac")
        return "post.mp4"
    except Exception as e:
        print(f"❌ Errore critico video: {e}")
        return None

# --- 7. INVIO ---
def send(row, vid, cap):
    if not vid: return
    print("📡 Invio Telegram...")
    try:
        with open(vid, 'rb') as f:
            requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo", 
                          files={'video': f}, data={'chat_id': TELEGRAM_CHAT_ID, 'caption': cap})
        print("✅ Telegram OK")
    except Exception as e: print(f"❌ Telegram: {e}")
    
    print("📡 Invio Make...")
    try:
        with open(vid, 'rb') as f:
            requests.post(MAKE_WEBHOOK_URL, 
                          files={'upload_file': ('p.mp4', f, 'video/mp4')},
                          data={'categoria': row['Categoria'], 'frase': row['Frase'], 'caption_completa': cap})
        print("✅ Make OK")
    except: pass

# --- MAIN ---
def run():
    check_resources()
    now = datetime.now(timezone.utc)
    hour = now.hour
    
    # LOGICA ORARI SEMPLIFICATA
    row, cap = None, ""
    if 5 <= hour <= 8:
        row = get_random_verse()
        cap = f"✨ {row['Categoria']} ✨\n\n“{row['Frase']}”\n📖 {row['Riferimento']}\n\n{INDIRIZZO_CHIESA}\n\n#fede"
    elif now.weekday() == 5 and 9 <= hour <= 22:
        row = get_random_verse("Esortazione") or get_random_verse()
        cap = f"🚨 DOMANI CULTO!\n\n{INDIRIZZO_CHIESA}\n\n📖 “{row['Frase']}”"
    elif now.weekday() == 6 and 15 <= hour <= 17:
        row = get_random_verse()
        cap = f"⏳ TRA POCO CULTO!\n\n{INDIRIZZO_CHIESA}\n\n📖 “{row['Frase']}”"
    else:
        print("⚠️ Test Mode")
        row = get_random_verse()
        cap = f"✨ TEST ✨\n\n“{row['Frase']}”\n📖 {row['Riferimento']}\n\n#test"

    if row is not None:
        img = create_verse_image(row)
        vid = create_video(img)
        send(row, vid, cap)
        print("✅ FINE.")
    else: print("❌ Nessun dato.")

if __name__ == "__main__":
    run()
