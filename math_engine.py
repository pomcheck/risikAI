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
    
    total_weight = weight_money + weight_time + weight_abstract
    
    if abs(total_weight - 1.0) > 0.01:
        raise ValueError(f"Fehler in der Matrix: Die Gewichte ergeben {total_weight * 100}%, sie müssen aber exakt 100% (1.0) sein!")

    final_utility = (score_money * weight_money) + (score_time * weight_time) + (score_abstract * weight_abstract)
    
    return final_utility


def simulate_event(probability: float, expected_utility: float, uncertainty: float, iterations: int = 10000):
    """
    Simuliert ein einzelnes Ereignis 10'000 Mal.
    Gibt eine Liste (Numpy-Array) mit 10'000 möglichen Ausgängen zurück.
    """
    
    occurrences = np.random.rand(iterations) < probability
    
    impacts = np.random.normal(loc=expected_utility, scale=uncertainty, size=iterations)
    
    results = occurrences * impacts
    
    return results


def calculate_risk_metrics(simulated_results: np.ndarray, confidence_level: float = 0.95) -> dict:
    """
    Analysiert 10'000 simulierte Durchläufe und berechnet die Worst-Case-Metriken.
    Gibt ein "Dictionary" (Wörterbuch) mit den Ergebnissen zurück.
    """
    
    percentile = (1.0 - confidence_level) * 100
    
    var_value = np.percentile(simulated_results, percentile)
    
    worst_cases = simulated_results[simulated_results <= var_value]
    
    if len(worst_cases) == 0:
        cvar_value = var_value
    else:
        cvar_value = np.mean(worst_cases)
        
    return {
        "VaR": var_value,
        "CVaR": cvar_value
    }


def calculate_recommendation_index(results: np.ndarray, risk_aversion: float, num_events: int) -> float:
    """
    Berechnet den finalen Empfehlungs-Index auf einer absoluten Skala von 0 bis 100.
    0 = Katastrophe, 50 = Neutral, 100 = Perfekt.
    """
    mean_val = np.mean(results)
    std_val = np.std(results)

    adjusted_std = std_val / math.sqrt(max(1, num_events))
    
    v = mean_val - (risk_aversion * adjusted_std)

    # mean variance
    
    index = (v + 1.0) / 2.0 * 100.0
    
    final_index = max(0.0, min(100.0, index))
    
    return final_index


from data_models import DecisionOption

def run_full_analysis(option, user_weights: dict, risk_aversion: float = 1.0) -> dict:
    
    ANCHOR_MONEY = 2000.0
    ANCHOR_TIME = 600.0

    all_consequences = []
    
    for opp in option.opportunities:
        opp.financial_chf = abs(opp.financial_chf)
        opp.time_minutes = abs(opp.time_minutes)
        opp.utility_score = abs(opp.utility_score)
        all_consequences.append(opp)
        
    for risk in option.risks:
        risk.financial_chf = -abs(risk.financial_chf)
        risk.time_minutes = -abs(risk.time_minutes)
        risk.utility_score = -abs(risk.utility_score)
        all_consequences.append(risk)

    num_events = len(all_consequences)
    
    if num_events == 0:
        return {"error": "Keine Risiken oder Chancen zur Analyse gefunden."}

    np.random.seed(42)
    total_simulation_results = np.zeros(10000)

    for event in all_consequences:
        
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
    index = calculate_recommendation_index(total_simulation_results, risk_aversion, num_events)

    return {
        "option_name": option.name,
        "recommendation_index": index,
        "VaR_95": metrics["VaR"],
        "CVaR": metrics["CVaR"],
        "simulated_data": total_simulation_results 
    }