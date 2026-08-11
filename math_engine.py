import numpy as np
import math

def normalize_utility(value: float) -> float:
    """
    Normalisiert den Utility-Score (-100 bis +100) auf eine Skala von -1.0 bis 1.0.
    Ein negativer Wert (Risiko) bleibt negativ!
    """
    return max(-1.0, min(1.0, value / 100.0))


def normalize_financial_or_time(value: float, reference_max: float) -> float:
        if reference_max == 0.0:
            return 0.0 
        
        return math.tanh(value / reference_max)


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

def run_full_analysis(option, user_weights: dict, risk_aversion: float = 1.0) -> dict:
    
    # 1. FESTE REFERENZ-ANKER (Globaler Massstab für alle Optionen!)
    # Definiert, ab wann ein Wert "extrem" (-1.0 oder +1.0) ist.
    ANCHOR_MONEY = 2000.0  # 2000 CHF ist für Schüler ein sehr hoher Wert
    ANCHOR_TIME = 600.0    # 600 Minuten (10h) aktive Arbeit ist ein massiver Aufwand

    all_consequences = []
    
    # 2. ABSOLUTER SICHERHEITS-FILTER (Polarität erzwingen)
    for opp in option.opportunities:
        # Chancen MÜSSEN positiv sein (Wir nehmen den Betrag mit abs() )
        opp.financial_chf = abs(opp.financial_chf)
        opp.time_minutes = abs(opp.time_minutes)
        all_consequences.append(opp)
        
    for risk in option.risks:
        # Risiken MÜSSEN negativ sein (Wir erzwingen ein Minuszeichen)
        risk.financial_chf = -abs(risk.financial_chf)
        risk.time_minutes = -abs(risk.time_minutes)
        all_consequences.append(risk)
    
    if len(all_consequences) == 0:
        return {"error": "Keine Risiken oder Chancen zur Analyse gefunden."}

    np.random.seed(42)
    total_simulation_results = np.zeros(10000)

    # 3. SAUBERE BERECHNUNG OHNE VORZEICHEN-DREHER
    for event in all_consequences:
        
        # Durch die fixen Anker sind 4 CHF jetzt winzig und 1200 CHF massiv!
        score_money = normalize_financial_or_time(event.financial_chf, ANCHOR_MONEY)
        score_time = normalize_financial_or_time(event.time_minutes, ANCHOR_TIME)
        score_abstract = normalize_utility(event.utility_score)
        
        utility = calculate_weighted_utility(
            score_money, user_weights['money'],
            score_time, user_weights['time'],
            score_abstract, user_weights['abstract']
        )
        
        event_sim = simulate_event(event.probability, utility, event.uncertainty, 10000)
        total_simulation_results += event_sim

    metrics = calculate_risk_metrics(total_simulation_results)
    index = calculate_recommendation_index(total_simulation_results, risk_aversion)

    return {
        "option_name": option.name,
        "recommendation_index": index,
        "VaR_95": metrics["VaR"],
        "CVaR": metrics["CVaR"],
        "simulated_data": total_simulation_results 
    }