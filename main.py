import os
import requests
import pandas as pd
import textwrap
import random
from datetime import datetime
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

# --- NUOVA CONFIGURAZIONE FACEBOOK ---
# Sostituisci queste stringhe con i tuoi dati reali
FB_PAGE_ID = "1479209002311050"
FB_ACCESS_TOKEN = "EAAZAH7q8wRZAEBQu6mJ7RkZBgTempnMVZAZCwYehoAmuLS5fZA1KI4JOCiqoC1ToFsyswtp6ApbIpLRmMPiPIhiyZAOBYBlAiyRXzwnDr3s0ZAUjZBZBs2SlZCSo5QP59nZCERt8oFO1w9ZClboT4O9LvBm77JWrCawdzL8nZCn3lyab1mLuBH4btMRANyzU1Rli4tSgUmrp7ZAZCA8ETM9SZA3G8dIIY8kmDRydFNhZCMCCUl8eOp93D0miZA3bO2El4GZB"

# Configurazione File
CSV_FILE = "Frasichiesa.csv"
LOGO_PATH = "logo.png"
FONT_NAME = "DejaVuSans-Bold.ttf"

# ... [Le funzioni get_random_verse, get_image_prompt, get_ai_image, load_font, create_verse_image, add_logo rimangono uguali] ...

# --- 8. PUBBLICAZIONE DIRETTA SU FACEBOOK ---
def publish_to_facebook(img_bytes, caption):
    print("\n🌐 === CONNESSIONE A FACEBOOK GRAPH API ===")
    
    # URL per pubblicare foto sulla bacheca della pagina
    url = f"https://graph.facebook.com/v18.0/{FB_PAGE_ID}/photos"
    
    payload = {
        'message': caption,
        'access_token': FB_ACCESS_TOKEN
    }
    
    files = {
        'source': ('post.png', img_bytes, 'image/png')
    }

    try:
        response = requests.post(url, data=payload, files=files)
        result = response.json()
        
        if response.status_code == 200 and "id" in result:
            print(f"✅ SUCCESSO: Post pubblicato con ID: {result['id']}")
            return True
        else:
            print(f"❌ ERRORE FACEBOOK: {result.get('error', {}).get('message', 'Errore sconosciuto')}")
            return False
    except Exception as e:
        print(f"❌ ERRORE DI CONNESSIONE: {e}")
        return False

# --- MAIN AGGIORNATO ---
if __name__ == "__main__":
    print("\n🙏 Bot Chiesa - Pubblicazione Diretta Facebook")
    
    # 1. Selezione versetto
    row = get_random_verse()
    if row is None: exit(1)

    # 2. Crea immagine
    img = add_logo(create_verse_image(row))
    buf = BytesIO()
    img.save(buf, format='PNG')
    img_data = buf.getvalue()

    # 3. Crea Testi
    meditazione = genera_meditazione(row)
    footer = get_footer_message(row)
    caption_completa = (
        "📖 " + str(row['Riferimento']) + "\n\n"
        + meditazione + "\n\n"
        + "────────────────\n"
        + footer + "\n"
        + "────────────────\n"
        + "⛪ Chiesa L'Eterno Nostra Giustizia\n"
        + "#fede #chiesa #bibbia #paroladidio"
    )

    # 4. PUBBLICAZIONE
    successo = publish_to_facebook(img_data, caption_completa)
    
    if successo:
        print("\n🎉 Missione compiuta! Il post è online.")
    else:
        print("\n⚠️ Il post non è stato pubblicato. Controlla il Token.")
