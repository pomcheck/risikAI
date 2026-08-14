import streamlit as st
import json
import time
import html
from data_models import FullAnalysisPayload
from math_engine import run_full_analysis
from main_app import call_gemini_api, save_to_memory

# --- SITE SETUP ---
st.set_page_config(page_title="risikAI", layout="centered")

# --- SESSION STATE ---
if "user_text_input" not in st.session_state:
    st.session_state.user_text_input = ""
if "analysis_data" not in st.session_state:
    st.session_state.analysis_data = None
if "feedback_saved" not in st.session_state:
    st.session_state.feedback_saved = False

# --- CALLBACK FUNCTIONS ---
def reset_app():
    st.session_state.user_text_input = ""
    st.session_state.analysis_data = None
    st.session_state.feedback_saved = False

def save_feedback(text, json_data):
    save_to_memory(text, json_data)
    st.session_state.feedback_saved = True

# --- CSS OVERRIDES ---
st.markdown("""
<style>
    .stApp { background-color: #0b0f19; }
    
    /* Sanfter Einblend-Effekt und leichtes Pulsieren für den Reset-Button */
    @keyframes softPulse {
        0% { box-shadow: 0 0 0 0 rgba(46, 204, 113, 0.2); }
        50% { box-shadow: 0 0 10px 0 rgba(46, 204, 113, 0.1); }
        100% { box-shadow: 0 0 0 0 rgba(46, 204, 113, 0.2); }
    }
    
    @keyframes fadeInDown {
        from { opacity: 0; transform: translateY(-10px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .stButton>button, .stDownloadButton>button {
        border-radius: 8px;
        border: 1px solid rgba(46, 204, 113, 0.4);
        transition: all 0.3s ease;
        animation: fadeInDown 0.5s ease-out, softPulse 3s infinite;
    }
    
    .stButton>button:hover, .stDownloadButton>button:hover {
        border-color: #2ecc71;
        box-shadow: 0 0 15px rgba(46, 204, 113, 0.3);
    }
    
    /* Primär-Button (Analyse starten) ohne das Pulsieren */
    .stButton>button[kind="primary"] {
        border: 1px solid rgba(255, 75, 75, 0.5) !important;
        animation: none !important;
    }
    .stButton>button[kind="primary"]:hover {
        border-color: #ff4b4b !important;
        box-shadow: 0 0 15px rgba(255, 75, 75, 0.5) !important;
    }
    
    div[data-testid="stMetric"] {
        background-color: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.05);
        padding: 15px;
        border-radius: 10px;
    }
    
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500&family=Montserrat:wght@900&display=swap');
    
    @keyframes shimmer {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    @keyframes slideUpFade {
        0% { opacity: 0; transform: translateY(20px); }
        100% { opacity: 1; transform: translateY(0); }
    }
    
    .animated-title {
        font-family: 'Montserrat', sans-serif !important;
        font-size: clamp(4rem, 10vw, 9rem) !important; 
        font-weight: 900 !important;
        letter-spacing: -1px !important; 
        background: linear-gradient(90deg, #2ecc71, #3498db, #8e44ad, #2ecc71);
        background-size: 300% 300%;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: shimmer 12s ease infinite, slideUpFade 0.8s ease-out forwards;
        margin-bottom: 0rem !important;
        line-height: 1.1 !important;
        cursor: default;
        transition: all 0.6s cubic-bezier(0.25, 0.8, 0.25, 1) !important; 
    }
    
    .animated-title:hover {
        letter-spacing: 8px !important; 
        text-shadow: 0px 0px 20px rgba(46, 204, 113, 0.15); 
        transform: scale(1.03); 
    }
    
    .animated-subtitle {
        font-family: 'Inter', sans-serif !important;
        color: #a0aec0 !important;
        font-size: 1.5rem !important;
        font-weight: 500 !important;
        letter-spacing: 2px !important;
        animation: slideUpFade 0.8s ease-out 0.3s forwards;
        opacity: 0; 
    }
</style>
<div style="text-align: center; margin-top: 2rem; margin-bottom: 4rem;">
    <div class="animated-title">risikAI</div>
    <p class="animated-subtitle">KI-gestützte Entscheidungshilfe</p>
</div>
""", unsafe_allow_html=True)
st.divider()

# --- EINGABEBEREICH ---
user_input = st.text_area(
    "Beschreibe deine Entscheidung (füge Alternativen, Zahlen und Emotionen für ein genaueres Ergebnis ein):",
    height=150,
    key="user_text_input",
    placeholder="Soll ich Option A oder Option B wählen? Option A kostet..."
)

# --- ANALYSE-BUTTON ---
if st.button("Analyse starten", type="primary", use_container_width=True):
    if not user_input or len(user_input.strip()) < 5:
        st.warning("Eingabe zu kurz. Bitte beschreibe eine vollständige Entscheidungssituation mit Alternativen.")
    else:
        progress_text = "Simuliere 10'000 Zukunftsszenarien..."
        my_bar = st.progress(0, text=progress_text)
        for percent_complete in range(100):
            time.sleep(0.01) 
            my_bar.progress(percent_complete + 1, text=progress_text)
        my_bar.empty() 
        
        with st.spinner("Berechne finale Entscheidungswerte..."):
            try:
                gemini_json_string = call_gemini_api(user_input)
                
                analyse_daten = json.loads(gemini_json_string)
                if "error" in analyse_daten:
                    st.error(analyse_daten["error"])
                    st.stop() 
                
                payload = FullAnalysisPayload.model_validate_json(gemini_json_string)
                profil = payload.user_profile
                options_list = payload.decision_options
                
            except json.JSONDecodeError:
                st.error("Es gab ein Problem bei der Verarbeitung der KI-Daten. Bitte versuche es noch einmal.")
                st.stop()
            except Exception as e:
                st.error(f"Fehler bei der KI-Analyse: {e}")
                st.stop() 

        with st.spinner("Führe Monte-Carlo-Analysen aus..."):
            total_points = profil.money_importance + profil.time_importance + profil.abstract_importance
            user_weights = {
                'money': profil.money_importance / total_points,
                'time': profil.time_importance / total_points,
                'abstract': profil.abstract_importance / total_points
            }
            
            all_reports = []
            for option_data in options_list:
                report = run_full_analysis(option_data, user_weights, profil.risk_aversion)
                report['opportunities_raw'] = option_data.opportunities
                report['risks_raw'] = option_data.risks
                all_reports.append(report)
            
            all_reports.sort(key=lambda x: x.get('recommendation_index', 0), reverse=True)
            
            st.session_state.analysis_data = {
                "reports": all_reports,
                "profil": profil,
                "weights": user_weights,
                "raw_json": gemini_json_string,
                "user_text": user_input
            }

# --- RESET BUTTON ---
if st.session_state.analysis_data is not None:
    st.button("Neu starten", on_click=reset_app, use_container_width=True)

# --- BEISPIEL BEREICH ---
if st.session_state.analysis_data is None:
    with st.expander("Wie funktioniert das? (Beispiel einblenden)"):
        st.markdown("""
        **Willkommen bei risikAI.**  
        Diese Engine analysiert deine Situation, ermittelt dein Profil und simuliert mögliche Zukünfte anhand mathematischer Modelle.
        
        **Beispiel-Eingabe:**  
        *Soll ich ein gebrauchtes Auto für 5000 CHF kaufen oder weiter Zug fahren? Ich hasse es, wenn Züge Verspätung haben.*
        """)
        
        st.markdown("---")
        st.markdown("**1. Der Persönlichkeits-Scan:**")
        st.markdown("Die KI liest zwischen den Zeilen und ermittelt aus deinem Text, was dir unterbewusst am wichtigsten ist.")
        
        col_p1, col_p2, col_p3, col_p4 = st.columns(4)
        col_p1.metric("Risikoaversion", "1.5x")
        col_p2.metric("Importanz: Geld", "29%")
        col_p3.metric("Importanz: Zeit", "38%")
        col_p4.metric("Importanz: Emotionen", "33%")
        
        st.markdown("""
        *   **Risikoaversion:** Wie ängstlich formulierst du? (1.0x = normal, 1.5x = vorsichtig). Höhere Werte bestrafen unsichere Optionen in der Mathematik stärker.
        *   **Importanz (Geld, Zeit, Emotionen):** Die Prozentzahlen steuern die Gewichtung der Monte-Carlo-Simulation.
        """)

        st.markdown("---")
        st.markdown("**2. Die Mathematik-Engine berechnet die Optionen:**")
        
        with st.container(border=True):
            st.markdown("<h4 style='text-align: center;'>GEBRAUCHTES AUTO KAUFEN</h4>", unsafe_allow_html=True)
            col_t1, col_t2, col_t3 = st.columns(3)
            col_t1.metric("Empfehlungs-Index (0-100)", "13.2 / 100")
            col_t2.metric("Value at Risk (95%)", "-0.775")
            col_t3.metric("Conditional VaR", "-0.894")
            
        st.markdown("""
        *   **Empfehlungs-Index:** Ein Wert von 0 bis 100. Er fasst Chancen und Risiken zusammen, gewichtet nach deinem Profil.
        *   **Value at Risk (VaR 95%):** Dein erwarteter Verlust-Nutzen. -0.775 bedeutet, dass in 95% der Fälle ein Netto-Schaden von 0.775 (auf einer normalisierten Skala von -1 bis 1) entsteht.
        *   **Conditional VaR:** Wenn absolut alles schiefgeht (das 5% Worst-Case-Szenario), ist das der durchschnittliche Schaden (-0.894), der dich erwartet.
        """)

# --- ERGEBNISSE ANZEIGEN ---
if st.session_state.analysis_data is not None:
    data = st.session_state.analysis_data
    reports = data["reports"]
    profil = data["profil"]
    weights = data["weights"]
    
    st.divider()
    
    st.success("Analyse erfolgreich abgeschlossen!")
    
    st.subheader("Profil-Analyse der KI")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Risikoaversion", f"{profil.risk_aversion}x")
    col2.metric("Importanz: Geld", f"{weights['money']*100:.0f}%")
    col3.metric("Importanz: Zeit", f"{weights['time']*100:.0f}%")
    col4.metric("Importanz: Emotionen", f"{weights['abstract']*100:.0f}%")
    
    st.divider()
    
    for i, r in enumerate(reports):
        if "error" in r:
            st.error(f"Fehler bei {r.get('option_name', 'Unbekannt')}: {r['error']}")
            continue
        
        rank_text = f"RANG {i+1}"
        
        with st.container(border=True):
            st.markdown(f"<p style='text-align: center; color: #2ecc71; font-weight: bold; margin-bottom: -5px;'>{rank_text}</p>", unsafe_allow_html=True)
            st.markdown(f"<h3 style='text-align: center;'>{r['option_name'].upper()}</h3>", unsafe_allow_html=True)
            
            m1, m2, m3 = st.columns(3)
            m1.metric("Empfehlungs-Index (0-100)", f"{r['recommendation_index']:.1f} / 100")
            m2.metric("Value at Risk (95%)", f"{r['VaR_95']:.3f}")
            m3.metric("Conditional VaR", f"{r['CVaR']:.3f}")
            
            with st.expander("Gedankengänge der KI & Details einblenden"):
                for chance in r['opportunities_raw']:
                    safe_name = html.escape(chance.name)
                    safe_reasoning = html.escape(chance.reasoning)
                    
                    st.markdown(
                        f'<div style="background-color: rgba(46, 204, 113, 0.1); padding: 10px; border-radius: 5px; border-left: 5px solid #2ecc71; margin-bottom: 10px;">'
                        f' <b>{safe_name}</b> <em>(Chance: {chance.probability*100}%, CHF: {chance.financial_chf}, Zeit: {chance.time_minutes}, Emotion: {chance.utility_score})</em> <br>{safe_reasoning}'
                        f'</div>', 
                        unsafe_allow_html=True
                    )
                for risiko in r['risks_raw']:
                    safe_name = html.escape(risiko.name)
                    safe_reasoning = html.escape(risiko.reasoning)
                    
                    st.markdown(
                        f'<div style="background-color: rgba(231, 76, 60, 0.1); padding: 10px; border-radius: 5px; border-left: 5px solid #e74c3c; margin-bottom: 10px;">'
                        f'<b>{safe_name}</b> <em>(Risiko: {risiko.probability*100}%, CHF: {risiko.financial_chf}, Zeit: {risiko.time_minutes}, Emotion: {risiko.utility_score})</em> <br>{safe_reasoning}'
                        f'</div>', 
                        unsafe_allow_html=True
                    )

    st.divider()
    
    st.subheader("System-Training & Daten-Export")
    col_train, col_export = st.columns(2)
    
    with col_train:
        st.markdown("**War diese Analyse logisch?**")
        if not st.session_state.feedback_saved:
            st.button("Ja, als Vorbild speichern", on_click=save_feedback, args=(data["user_text"], data["raw_json"]), use_container_width=True)
        else:
            st.button("Erfolgreich im Erfahrungs-Archiv gespeichert!", disabled=True, use_container_width=True)
            
    with col_export:
        st.markdown("**Rohdaten exportieren:**")
        csv_data = "Option,Empfehlungs-Index,VaR_95,CVaR\n"
        for r in reports:
            if "error" not in r:
                csv_data += f"{r['option_name']},{r['recommendation_index']:.1f},{r['VaR_95']:.3f},{r['CVaR']:.3f}\n"
        
        st.download_button(
            label="Resultate als .csv herunterladen",
            data=csv_data,
            file_name="entscheidungs_analyse.csv",
            mime="text/csv",
            use_container_width=True
        )