# --- 3. AI, IMMAGINI E FALLBACK ---
def get_ai_image(prompt_text):
    print(f"🎨 Tentativo Generazione AI (Pollinations): {prompt_text}")
    
    # TENTATIVO 1: Pollinations.ai
    try:
        # Usiamo urllib per codificare in modo sicuro TUTTI i caratteri speciali (non solo gli spazi)
        clean_prompt = urllib.parse.quote(prompt_text)
        url = f"https://image.pollinations.ai/prompt/{clean_prompt}?width=1080&height=1080&nologo=true"
        
        # Aggiungiamo un User-Agent per non farci bloccare dall'API
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
        
        response = requests.get(url, headers=headers, timeout=25)
        if response.status_code == 200:
            return Image.open(BytesIO(response.content)).convert("RGBA")
        else:
            print(f"⚠️ Pollinations ha risposto con codice {response.status_code}")
    except Exception as e:
        print(f"⚠️ Errore AI Pollinations: {e}")

    # TENTATIVO 2: Scarica un'immagine da Internet
    print("🌐 Pollinations fallito. Provo a scaricare un'immagine di backup da internet...")
    try:
        # Picsum fornisce immagini fotografiche casuali bellissime. 
        # ?blur=2 aggiunge una leggera sfocatura perfetta come sfondo per dei testi
        url_fallback = "https://picsum.photos/1080/1080?blur=2"
        res_fall = requests.get(url_fallback, timeout=15)
        if res_fall.status_code == 200:
            return Image.open(BytesIO(res_fall.content)).convert("RGBA")
    except Exception as e:
        print(f"⚠️ Errore download da internet: {e}")

    # TENTATIVO 3: Generazione Sfondo Pastello con Linee e Ombre
    print("🎨 Internet fallito. Genero un bellissimo sfondo pastello locale...")
    return generate_pastel_background()

def generate_pastel_background():
    # Crea una tela bianca
    img = Image.new('RGBA', (1080, 1080), (255, 255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Crea un colore di base pastello (valori alti di RGB)
    bg_r = random.randint(200, 255)
    bg_g = random.randint(200, 255)
    bg_b = random.randint(200, 255)
    draw.rectangle([0, 0, 1080, 1080], fill=(bg_r, bg_g, bg_b, 255))

    # Disegna grandi linee/ombre con colori pastello incrociate
    for _ in range(15):
        # Coordinate che escono anche fuori dai bordi
        x1, y1 = random.randint(-300, 1300), random.randint(-300, 1300)
        x2, y2 = random.randint(-300, 1300), random.randint(-300, 1300)
        
        # Spessore importante per creare l'effetto "macchia di colore/ombra"
        width = random.randint(150, 450)
        
        # Colori delicati
        r = random.randint(180, 255)
        g = random.randint(180, 255)
        b = random.randint(180, 255)
        
        draw.line([(x1, y1), (x2, y2)], fill=(r, g, b, 200), width=width)
    
    # Applica una forte sfocatura (Gaussian Blur) per ammorbidire le linee e renderle ombre eleganti
    img = img.filter(ImageFilter.GaussianBlur(radius=80))
    return img
