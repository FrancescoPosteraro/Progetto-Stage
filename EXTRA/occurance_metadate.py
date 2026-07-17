import json


def analizza_campo_per_tipologia(file_json, campo):

    with open(file_json, "r", encoding="utf-8") as f:
        pubblicazioni = json.load(f)


    tipologie = {}

    for pub in pubblicazioni:

        tipo = pub["dc.collection.name"]

        if tipo not in tipologie:
            tipologie[tipo] = []

        tipologie[tipo].append(pub)


    print(f"\n=== Analisi metadato: {campo} ===\n")
    print(f"Totale pubblicazioni analizzate: {len(pubblicazioni)}\n")


    for tipo, lista_pubblicazioni in tipologie.items():

        totale = len(lista_pubblicazioni)

        presenti = 0


        for pub in lista_pubblicazioni:

            valore = pub.get(campo)

            if valore is not None and valore != "" and valore != []:
                presenti += 1


        percentuale = (presenti / totale) * 100


        print(tipo)
        print(f"Totale: {totale}")
        print(f"Presente: {presenti}")
        print(f"Percentuale: {percentuale:.2f}%")
        print("-" * 40)



JSON_PATH = r"C:\Users\franc\Desktop\Progetto-Stage\publications.json"

analizza_campo_per_tipologia(
    JSON_PATH,
    "dc.type.research"
)