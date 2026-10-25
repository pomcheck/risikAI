import time
import json
import csv
from data_models import FullAnalysisPayload
from main_app import call_gemini_api
from math_engine import run_full_analysis

# Globaler Ergebnis-Speicher
results = []

def benchmark_prompt(test_id, test_series, prompt_text):
    print(f"\nRunning [{test_series}] - {test_id}...")
    
    # 1. API-Aufruf & Latenzmessung
    t0 = time.perf_counter()
    json_str = call_gemini_api(prompt_text)
    t_api = time.perf_counter() - t0
    
    # 2. Validierung & Parsing
    try:
        parsed_dict = json.loads(json_str)
        if "error" in parsed_dict:
            print(f"  -> Abgefangen durch System-Prompt: {parsed_dict['error']}")
            results.append({
                "test_series": test_series,
                "test_id": test_id,
                "status": "Handled_Error",
                "t_api_sec": round(t_api, 3),
                "t_math_sec": 0.0,
                "t_total_sec": round(t_api, 3),
                "option_name": "ABORT_OR_ERROR",
                "index_score": None,
                "var_95": None,
                "cvar_95": None,
                "risk_aversion_gamma": None
            })
            return

        payload = FullAnalysisPayload.model_validate_json(json_str)

    except Exception as parse_err:
        print(f"  -> Parsing-Fehler: {parse_err}")
        results.append({
            "test_series": test_series,
            "test_id": test_id,
            "status": "Parse_Failure",
            "t_api_sec": round(t_api, 3),
            "t_math_sec": 0.0,
            "t_total_sec": round(t_api, 3),
            "option_name": "PARSE_ERROR",
            "index_score": None,
            "var_95": None,
            "cvar_95": None,
            "risk_aversion_gamma": None
        })
        return

    # 3. Gewichte exakt auf Summe 1.0 normalisieren
    m_imp = payload.user_profile.money_importance
    t_imp = payload.user_profile.time_importance
    e_imp = payload.user_profile.emotion_importance
    total_imp = m_imp + t_imp + e_imp

    # Normalisierung auf exakt 1.0 für calculate_weighted_utility
    w_money = m_imp / total_imp
    w_time = t_imp / total_imp
    w_abstract = 1.0 - (w_money + w_time)  # Verhindert Float-Rundungsfehler

    user_weights = {
        "money": w_money,
        "time": w_time,
        "abstract": w_abstract
    }
    gamma = payload.user_profile.risk_aversion

    # 4. Simulation für jede Option in decision_options durchführen
    for option in payload.decision_options:
        t1 = time.perf_counter()
        opt_res = run_full_analysis(option, user_weights=user_weights, risk_aversion=gamma)
        t_math = time.perf_counter() - t1

        rec_idx = opt_res.get("recommendation_index")
        var_val = opt_res.get("VaR_95")
        cvar_val = opt_res.get("CVaR")

        print(f"  -> Option '{option.name}': Index = {round(rec_idx, 2) if rec_idx else 'N/A'}, VaR95 = {round(var_val, 4) if var_val else 'N/A'}")

        results.append({
            "test_series": test_series,
            "test_id": test_id,
            "status": "Success",
            "t_api_sec": round(t_api, 3),
            "t_math_sec": round(t_math, 4),
            "t_total_sec": round(t_api + t_math, 3),
            "option_name": option.name,
            "index_score": round(rec_idx, 2) if rec_idx is not None else None,
            "var_95": round(var_val, 4) if var_val is not None else None,
            "cvar_95": round(cvar_val, 4) if cvar_val is not None else None,
            "risk_aversion_gamma": gamma
        })

# ==========================================
# TEST-BATTERIE DEFINIEREN
# ==========================================

# ==========================================
# TESTREIHE D: Error-Handling & Garbage Input
# ==========================================

prompt_d1 = "asdasd jkllö 123987 ?! --- ####"
prompt_d2 = "Was ist eigentlich der Sinn des Lebens und wie werde ich glücklich?"
prompt_d3 = "Ich habe mir heute beim Bäcker ein Schoggigipfeli gekauft und es war sehr lecker."
prompt_d4 = "Soll ich mir ein neues Fahrrad kaufen?"

benchmark_prompt("Stress_Kauderwelsch", "Testreihe_D", prompt_d1)
benchmark_prompt("Stress_Philosophie", "Testreihe_D", prompt_d2)
benchmark_prompt("Stress_Tatsache", "Testreihe_D", prompt_d3)
benchmark_prompt("Stress_Unvollstaendig", "Testreihe_D", prompt_d4)

# 4. Speichern der Rohdaten als CSV
if len(results) > 0:
    keys = results[0].keys()
    with open("analyse_rohdaten.csv", "w", newline="", encoding="utf-8") as f:
        dict_writer = csv.DictWriter(f, keys)
        dict_writer.writeheader()
        dict_writer.writerows(results)
    print("\n[Erfolg] Alle Testläufe abgeschlossen! Die Rohdaten liegen in 'analyse_rohdaten.csv'.")
else:
    print("\n[Warnung] Keine Daten erfasst.")