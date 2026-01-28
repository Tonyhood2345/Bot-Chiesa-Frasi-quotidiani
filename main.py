# --- 5. GRAFICA (SISTEMATA PER UN LOOK PIÙ ORDINATO) ---
def create_verse_image(row):
    prompt = get_image_prompt(row['Categoria'])
    base_img = get_ai_image(prompt).resize((1080, 1080))
    overlay = Image.new('RGBA', base_img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    W, H = base_img.size
    
    # --- NUOVE DIMENSIONI FONT (Ridotte per ordine) ---
    # Ho ridotto il font principale da 150 a 95 per farlo assomigliare alla seconda immagine.
    font_size_main = 95  
    # Ho ridotto proporzionalmente anche il riferimento.
    font_size_ref = 55   
    
    font_txt = load_font(font_size_main)
    font_ref = load_font(font_size_ref)
    
    text = f"“{row['Frase']}”"
    
    # --- MODIFICA FONDAMENTALE AL WRAP ---
    # Poiché il font è più piccolo, possiamo aumentare il numero di caratteri per riga.
    # Passando da width=12 a width=20 (o 22), le parole non verranno più spezzate a metà
    # e il testo risulterà più compatto orizzontalmente.
    lines = textwrap.wrap(text, width=22) 
    
    # Calcoli dimensioni
    # Spazio tra le righe (font size + un po' di respiro)
    line_height = font_size_main + 25 
    total_h = (len(lines) * line_height) + 80
    
    # Calcolo punto di inizio Y per centrare verticalmente.
    # Il "- 60" serve a spostare il blocco leggermente in alto per fare spazio al logo in basso.
    start_y = ((H - total_h) / 2) - 60
    
    # Sfondo scuro adattato al nuovo blocco di testo
    # Ho stretto i margini verticali (start_y - 30 invece di -40)
    draw.rectangle([(40, start_y - 30), (W - 40, start_y + total_h + 40)], fill=(0, 0, 0, 140))
    
    final_img = Image.alpha_composite(base_img, overlay)
    draw_final = ImageDraw.Draw(final_img)
    
    curr_y = start_y
    for line in lines:
        bbox = draw_final.textbbox((0, 0), line, font=font_txt)
        w = bbox[2] - bbox[0]
        # Disegno la riga centrata orizzontalmente
        draw_final.text(((W - w)/2, curr_y), line, font=font_txt, fill="white")
        curr_y += line_height
        
    ref = str(row['Riferimento'])
    bbox_ref = draw_final.textbbox((0, 0), ref, font=font_ref)
    w_ref = bbox_ref[2] - bbox_ref[0]
    # Sposto il riferimento un po' più in basso rispetto all'ultima riga di testo
    draw_final.text(((W - w_ref)/2, curr_y + 20), ref, font=font_ref, fill="#FFD700")
    
    return final_img
