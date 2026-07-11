"""
========================================================
AUTORE: Francesco Posteraro
DESCRIZIONE:
Script utlizzato solo per capire il tempo medio che 
lo script web_scraper.py impiega solo per la creazione del file jsons

========================================================
"""

def calcola_media(file_path):
    valori = []

    with open(file_path, 'r') as file:
        for linea in file:
            linea = linea.strip()
            if linea:  # evita righe vuote
                try:
                    valori.append(float(linea))
                except ValueError:
                    print(f"Valore non valido ignorato: {linea}")

    if not valori:
        print("Nessun valore valido trovato.")
        return

    media_secondi = sum(valori) / len(valori)
    media_minuti = media_secondi / 60

    print(f"Media: {media_secondi:.4f} secondi")
    print(f"Media: {media_minuti:.4f} minuti")


# Percorso completo del file
file_input = r"C:\Users\franc\Desktop\Progetto-Stage\extra\seconds.txt"

calcola_media(file_input)