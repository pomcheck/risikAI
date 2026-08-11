import numpy as np
from data_models import DecisionOption, Consequence
from math_engine import normalize_value, calculate_weighted_utility, simulate_event, calculate_risk_metrics, calculate_recommendation_index

print("--- Starte Datenaufnahme ---")

chance_benzin = Consequence(
    name="Benzin gespart",
    probability=1.0,         
    financial_chf=3.0,       
    time_minutes=0.0,        
    utility_score=10.0,      
    uncertainty=0.0          
)

risiko_regen = Consequence(
    name="Nass werden im Regen",
    probability=0.3,         
    financial_chf=0.0,       
    time_minutes=-10.0,      
    utility_score=-30.0,     
    uncertainty=0.2          
)

option_fahrrad = DecisionOption(
    name="Mit dem Fahrrad einkaufen",
    opportunities=[chance_benzin],
    risks=[risiko_regen]
)

print(f"Option erstellt: {option_fahrrad.name}")
print(f"Anzahl Chancen: {len(option_fahrrad.opportunities)}")
print(f"Anzahl Risiken: {len(option_fahrrad.risks)}")

print(f"Die Regen-Wahrscheinlichkeit ist: {option_fahrrad.risks[0].probability * 100}%")


print("\n--- Starte Normalisierung (Mathematik) ---")

# Wir testen das am Faktor Zeit:
# Angenommen: Auto = 0 Minuten Verlust (Best Case), Fahrrad = 10 Minuten Verlust (Worst Case)
bester_zeitwert = 0.0    # 0 Minuten verloren (Max_val, weil weniger Verlust = besser)
schlechtester_zeitwert = -10.0 # 10 Minuten verloren (Min_val)

# Wir holen uns den Zeitwert von unserem Fahrrad-Risiko (das war -10.0)
fahrrad_zeit = option_fahrrad.risks[0].time_minutes

# Wir schicken die Zahl durch unsere Maschine
zeit_score = normalize_value(value=fahrrad_zeit, min_val=schlechtester_zeitwert, max_val=bester_zeitwert)

print(f"Ursprünglicher Zeitverlust: {fahrrad_zeit} Minuten")
print(f"Normalisierter Score (0.0 bis 1.0): {zeit_score}")

# Test 2: Was wäre, wenn wir nur 5 Minuten verloren hätten?
halber_zeit_score = normalize_value(value=-5.0, min_val=schlechtester_zeitwert, max_val=bester_zeitwert)
print(f"Score bei -5 Minuten: {halber_zeit_score}")



print("\n--- Starte Gewichtung (Weighted Utility) ---")

# Angenommen, wir haben unsere Fahrrad-Option normalisiert und folgende Scores erhalten:
# (1.0 ist perfekt, 0.0 ist miserabel)
score_geld = 1.0   # Wir sparen 3 CHF (Perfekt!)
score_zeit = 0.0   # Wir verlieren 10 Minuten (Miserabel!)
score_gefühl = 0.2 # Wir werden nass, aber haben frische Luft (Eher schlecht)

# Jetzt definieren wir den Nutzer (später macht das die KI anhand des Textes).
# Dieser Nutzer ist ein armer Schüler, der viel Zeit, aber wenig Geld hat:
gewicht_geld = 0.6    # Geld ist sehr wichtig (60%)
gewicht_zeit = 0.1    # Zeit ist fast egal (10%)
gewicht_gefühl = 0.3  # Nicht nass werden ist auch etwas wichtig (30%)

# Wir werfen alles in unsere neue Maschine:
finales_resultat = calculate_weighted_utility(
    score_money=score_geld, weight_money=gewicht_geld,
    score_time=score_zeit, weight_time=gewicht_zeit,
    score_abstract=score_gefühl, weight_abstract=gewicht_gefühl
)

print(f"Nutzer-Profil: Geld {gewicht_geld*100}%, Zeit {gewicht_zeit*100}%, Gefühl {gewicht_gefühl*100}%")
print(f"Der finale, kombinierte Nutzen-Score für das Fahrrad ist: {finales_resultat}")


print("\n--- Starte Monte-Carlo-Simulation (10'000 Durchläufe) ---")

# Wir nehmen unser Regen-Risiko von vorhin.
# Nehmen wir an, wir haben seinen finalen Nutzen-Score bereits auf -0.5 berechnet.
wahrscheinlichkeit = 0.3    # 30% Chance auf Regen
nutzen_schaden = -0.5       # Tut weh (negativer Score)
unsicherheit = 0.1          # 10% Schwankung (Vielleicht regnet es stärker oder schwächer)

# Wir werfen die Zeitmaschine an:
simulierte_zukunft = simulate_event(
    probability=wahrscheinlichkeit, 
    expected_utility=nutzen_schaden, 
    uncertainty=unsicherheit, 
    iterations=10000
)

# simulierte_zukunft ist jetzt eine Liste mit 10'000 Zahlen! Wir werten sie aus:
anzahl_regen = np.count_nonzero(simulierte_zukunft) # Wie oft hat es geregnet?
schlimmster_fall = np.min(simulierte_zukunft)       # Der absolut tiefste Wert in 10'000 Versuchen
durchschnitt = np.mean(simulierte_zukunft)          # Der statistische Erwartungswert

print(f"Simulation abgeschlossen! In 10'000 Paralleluniversen...")
print(f"Hat es {anzahl_regen} Mal geregnet (Erwartet waren ca. 3000).")
print(f"War der durchschnittliche Nutzen-Effekt: {durchschnitt:.3f}")
print(f"War das absolut schlimmste Universum: {schlimmster_fall:.3f}")


print("\n--- Starte Risiko-Analyse (VaR & CVaR) ---")

# Wir werfen unsere 10'000 Resultate von vorhin in die neue Maschine
# Wir nutzen 95% Sicherheit (0.95 ist der Industrie-Standard)
risiko_kennzahlen = calculate_risk_metrics(simulated_results=simulierte_zukunft, confidence_level=0.95)

# Werte aus dem Paket (Dictionary) auslesen
var_95 = risiko_kennzahlen["VaR"]
cvar_95 = risiko_kennzahlen["CVaR"]

print(f"Value at Risk (95%): {var_95:.3f}")
print(f" -> 'Mit 95% Sicherheit wird dein Nutzen-Schaden nicht tiefer sein als {var_95:.3f}'")

print(f"Conditional VaR:     {cvar_95:.3f}")
print(f" -> 'FALLS das Worst-Case-Szenario eintritt, liegt der durchschnittliche Schaden bei {cvar_95:.3f}'")


print("\n--- Starte Finale Index-Berechnung ---")

# Wir testen das mit zwei verschiedenen Nutzer-Typen:

# Typ A: Ein normaler Nutzer (Risikoaversion = 1.0)
index_normal = calculate_recommendation_index(simulated_results=simulierte_zukunft, risk_aversion=1.0)

# Typ B: Ein extrem ängstlicher Nutzer (Risikoaversion = 2.5)
# Ihn stört die Unsicherheit der Regen-Wahrscheinlichkeit massiv!
index_aengstlich = calculate_recommendation_index(simulated_results=simulierte_zukunft, risk_aversion=2.5)

print(f"Empfehlungs-Index für normalen Nutzer:      {index_normal:.1f} / 100")
print(f"Empfehlungs-Index für ängstlichen Nutzer:   {index_aengstlich:.1f} / 100")

if index_normal > 50:
    print("-> System-Fazit: Eher empfehlenswert!")
else:
    print("-> System-Fazit: Eher NICHT empfehlenswert!")