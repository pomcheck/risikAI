import matplotlib.pyplot as plt

headers_d = [
    "Test-ID", "Kategorie", "Generierte Option", 
    "Index-Score", "VaR 95%", "CVaR 95%", "γ", "Status"
]

data_d = [
    ["D1: Zeichenabfolge", "Bedeutungslose Eingabe", "Keine (Abbruch)", "–", "–", "–", "–", "Erfolgreich (error)"],
    ["D2: Philosophie", "Offene Sinnfrage", "Philosophische Sinnsuche", "0.90", "-1.4892", "-1.9192", "1.5", "Fehlgeschlagen"],
    ["", "Offene Sinnfrage", "Hedonistische Glückssuche", "36.37", "-0.4922", "-0.6460", "1.5", "Fehlgeschlagen"],
    ["D3: Tatsache", "Narrativer Bericht", "Kauf eines Schoggigipfelis", "51.78", "0.0355", "0.0355", "1.0", "Fehlgeschlagen"],
    ["D4: Einzelfrage", "Fehlende Gegenoption", "Neues Fahrrad kaufen", "38.64", "-0.5773", "-0.7530", "1.5", "Teilerfolg (Ergänzung)"],
    ["", "Fehlende Gegenoption", "Altes Fahrrad behalten", "40.27", "-0.4700", "-0.6509", "1.5", "Teilerfolg (Ergänzung)"]
]

fig, ax = plt.subplots(figsize=(11, 4.5), dpi=300)
ax.axis('off')

# Spaltenbreiten exakt abgestimmt
col_widths = [0.18, 0.18, 0.28, 0.10, 0.10, 0.10, 0.05, 0.17]
tbl = ax.table(cellText=data_d, colLabels=headers_d, loc='center', cellLoc='left', colWidths=col_widths)
tbl.auto_set_font_size(False)
tbl.set_fontsize(8.5)

for (row, col), cell in tbl.get_celld().items():
    cell.set_edgecolor('#d0d7de')
    cell.set_linewidth(0.6)
    if row == 0:
        cell.set_facecolor('#2f6fde')
        cell.set_text_props(weight='bold', color='white')
        cell.set_height(0.055)
    else:
        cell.set_height(0.045)
        # Blockweise Schattierung passend zu den Test-IDs
        if row in [1, 4]:
            cell.set_facecolor('#ffffff')
        else:
            cell.set_facecolor('#f6f8fa')
            
        if col in [3, 4, 5, 6]:
            cell.set_text_props(ha='right')
        elif col in [0, 1, 7]:
            cell.set_text_props(ha='center')

plt.tight_layout()
plt.savefig('Tabelle_Anhang_D2.png', bbox_inches='tight', dpi=300)
print("Bild erfolgreich gespeichert als: Tabelle_Anhang_D2.png")