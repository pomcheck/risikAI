import numpy as np

def normalize_value(value: float, min_val: float, max_val: float) -> float:
    """
    Wandelt einen beliebigen Wert in einen Score zwischen 0.0 und 1.0 um.
    """
    # Sicherheits-Check: Verhindert, dass der Computer durch Null teilt!
    if max_val == min_val:
        return 0.0 
    
    # Die rigorose mathematische Formel
    score = (value - min_val) / (max_val - min_val)
    
    return score


def calculate_weighted_utility(
    score_money: float, weight_money: float,
    score_time: float, weight_time: float,
    score_abstract: float, weight_abstract: float
) -> float:
    """
    Kombiniert die normalisierten Scores (0.0 bis 1.0) anhand von Gewichtungen
    zu einem einzigen, finalen Nutzenwert.
    """
    
    # 1. Rigoroser Check: Ergeben die Gewichte zusammen 100% (1.0)?
    total_weight = weight_money + weight_time + weight_abstract
    
    # Wir nutzen "abs" (Absolutwert) und eine kleine Toleranz (0.01), 
    # weil Computer bei Kommazahlen manchmal winzige Rundungsfehler machen (z.B. 0.999999).
    if abs(total_weight - 1.0) > 0.01:
        raise ValueError(f"Fehler in der Matrix: Die Gewichte ergeben {total_weight * 100}%, sie müssen aber exakt 100% (1.0) sein!")

    # 2. Die finale Berechnung: Score * Gewicht
    final_utility = (score_money * weight_money) + (score_time * weight_time) + (score_abstract * weight_abstract)
    
    return final_utility


def simulate_event(probability: float, expected_utility: float, uncertainty: float, iterations: int = 10000):
    """
    Simuliert ein einzelnes Ereignis 10'000 Mal.
    Gibt eine Liste (Numpy-Array) mit 10'000 möglichen Ausgängen zurück.
    """
    
    # 1. Tritt das Ereignis ein? (Wir würfeln 10'000 Mal gleichzeitig)
    # np.random.rand zieht 10'000 Zufallszahlen zwischen 0.0 und 1.0.
    # Ist die Zahl kleiner als unsere Wahrscheinlichkeit, tritt das Risiko ein (True).
    occurrences = np.random.rand(iterations) < probability
    
    # 2. WENN es eintritt, wie stark ist der Effekt wirklich?
    # Wir ziehen 10'000 Werte aus einer Normalverteilung (Glockenkurve).
    # Die Mitte (loc) ist unser erwarteter Nutzen, die Streuung (scale) ist die Unsicherheit.
    impacts = np.random.normal(loc=expected_utility, scale=uncertainty, size=iterations)
    
    # 3. Das finale Resultat pro Durchlauf
    # True * Impact = Impact (Ereignis fand statt, Schaden/Gewinn wird berechnet)
    # False * Impact = 0 (Ereignis fand nicht statt, es passiert nichts)
    results = occurrences * impacts
    
    return results


def calculate_risk_metrics(simulated_results: np.ndarray, confidence_level: float = 0.95) -> dict:
    """
    Analysiert 10'000 simulierte Durchläufe und berechnet die Worst-Case-Metriken.
    Gibt ein "Dictionary" (Wörterbuch) mit den Ergebnissen zurück.
    """
    
    # 1. Wo liegt unsere Schmerzgrenze? (Bei 95% Sicherheit sind das die untersten 5%)
    percentile = (1.0 - confidence_level) * 100
    
    # 2. VaR berechnen: np.percentile sucht genau die Zahl an dieser 5%-Grenze
    var_value = np.percentile(simulated_results, percentile)
    
    # 3. CVaR berechnen: Wir filtern alle 10'000 Ergebnisse. 
    # Behalte NUR die Ergebnisse, die noch schlechter (kleiner oder gleich) als der VaR sind.
    worst_cases = simulated_results[simulated_results <= var_value]
    
    # Sicherheits-Check: Falls die Liste leer ist (z.B. weil alles komplett ohne Unsicherheit lief)
    if len(worst_cases) == 0:
        cvar_value = var_value
    else:
        cvar_value = np.mean(worst_cases) # Durchschnitt der Worst-Cases
        
    # Wir geben die Resultate als sauberes Paket zurück
    return {
        "VaR": var_value,
        "CVaR": cvar_value
    }


def calculate_recommendation_index(results: np.ndarray, risk_aversion: float) -> float:
    """
    Berechnet den finalen Empfehlungs-Index auf einer absoluten Skala von 0 bis 100.
    0 = Katastrophe, 50 = Neutral, 100 = Perfekt.
    """
    # 1. Wir berechnen den Erwartungswert und die Schwankung
    mean_val = np.mean(results)
    std_val = np.std(results)
    
    # 2. Risiko-Abzug (Wie vorher)
    v = mean_val - (risk_aversion * std_val)
    
    # 3. ABSOLUTE SKALIERUNG (Das ist der Fix!)
    # Wir mappen den Wert v (der meist zwischen -1.0 und +1.0 liegt) auf 0 bis 100.
    # v = 0.0 ergibt genau 50 (Neutral).
    index = (v + 1.0) / 2.0 * 100.0
    
    # 4. Clipping: Wir verhindern, dass der Wert über 100 oder unter 0 schiesst
    final_index = max(0.0, min(100.0, index))
    
    return final_index



from data_models import DecisionOption

def run_full_analysis(option: DecisionOption, user_weights: dict, risk_aversion: float = 1.0) -> dict:
    """
    Die Haupt-Pipeline. Nimmt ein von der KI generiertes Objekt und 
    jagt es durch die gesamte Mathematik-Engine.
    """
    
    # 1. Wir sammeln alle Konsequenzen (Risiken + Chancen)
    all_consequences = option.opportunities + option.risks
    
    # Not-Aus: Wenn die KI keine Risiken/Chancen gefunden hat
    if len(all_consequences) == 0:
        return {"error": "Keine Risiken oder Chancen zur Analyse gefunden."}

    # 2. Wir definieren die globalen Extremwerte für dieses Szenario (für die Normalisierung)
    # (Wir suchen den absolut höchsten und tiefsten CHF/Minuten-Wert)
    max_money = max([c.financial_chf for c in all_consequences])
    min_money = min([c.financial_chf for c in all_consequences])
    
    max_time = max([c.time_minutes for c in all_consequences])
    min_time = min([c.time_minutes for c in all_consequences])

    np.random.seed(42)
    
    # Hier speichern wir alle 10'000 Simulationen für ALLE Konsequenzen zusammen
    total_simulation_results = np.zeros(10000)

    # 3. Wir gehen jede einzelne Konsequenz durch
    for event in all_consequences:
        
        # A) Werte normalisieren
        score_money = normalize_value(event.financial_chf, min_money, max_money)
        score_time = normalize_value(event.time_minutes, min_time, max_time)
        score_abstract = normalize_value(event.utility_score, -100.0, 100.0)
        
        # B) Gewichteten Nutzen berechnen
        utility = calculate_weighted_utility(
            score_money, user_weights['money'],
            score_time, user_weights['time'],
            score_abstract, user_weights['abstract']
        )
        
        # C) Monte-Carlo-Simulation für dieses Ereignis
        event_sim = simulate_event(event.probability, utility, event.uncertainty, 10000)
        
        # D) Zum Gesamtergebnis hinzufügen
        total_simulation_results += event_sim

    # 4. Finale Metriken für die gesamte Entscheidung berechnen
    metrics = calculate_risk_metrics(total_simulation_results)
    index = calculate_recommendation_index(total_simulation_results, risk_aversion)

    # 5. Ein sauberes Datenpaket (Report) zurückgeben
    return {
        "option_name": option.name,
        "recommendation_index": index,
        "VaR_95": metrics["VaR"],
        "CVaR": metrics["CVaR"],
        "simulated_data": total_simulation_results # Behalten wir für spätere Grafiken!
    }