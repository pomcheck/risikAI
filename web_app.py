from main_app import call_gemini_api, save_to_memory # <--- save_to_memory hinzufügen!

import streamlit as st
import json
import time
from data_models import FullAnalysisPayload
from math_engine import run_full_analysis
from main_app import call_gemini_api # Wir klauen uns die schlaue KI-Funktion von deiner anderen Datei!

# --- SEITEN-SETUP ---
st.set_page_config(page_title="KI-Entscheidungs-Assistent", page_icon="⚖️", layout="centered")

# --- FUTURISTIC CSS OVERRIDES (Base44 Style) ---
st.markdown("""
<style>
    .stApp { background-color: #0b0f19; }
    
    /* 1. GRÜNER GLOW: Für alle normalen Buttons UND den Download-Button unten */
    .stButton>button, .stDownloadButton>button {
        border-radius: 8px;
        border: 1px solid rgba(46, 204, 113, 0.4);
        transition: all 0.3s ease;
    }
    .stButton>button:hover, .stDownloadButton>button:hover {
        border-color: #2ecc71;
        box-shadow: 0 0 15px rgba(46, 204, 113, 0.3);
    }
    
    /* 2. ROTER GLOW: Spezial-Regel NUR für den primären "Analyse starten"-Button */
    .stButton>button[kind="primary"] {
        border: 1px solid rgba(255, 75, 75, 0.5) !important;
    }
    .stButton>button[kind="primary"]:hover {
        border-color: #ff4b4b !important;
        box-shadow: 0 0 15px rgba(255, 75, 75, 0.5) !important;
    }
    
    /* Metrik-Boxen */
    div[data-testid="stMetric"] {
        background-color: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.05);
        padding: 15px;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# --- HERO SECTION (Animiert, Massive Fonts & Hover-Effekt) ---
st.markdown("""
<style>
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
        /* Macht den Übergang beim Hover butterweich (Dauer: 0.6 Sekunden) */
        transition: all 0.6s cubic-bezier(0.25, 0.8, 0.25, 1) !important; 
    }

    /* --- DIE NEUE HOVER-MAGIE --- */
    .animated-title:hover {
        letter-spacing: 8px !important; 
        /* Streuung von 40px auf 20px reduziert und Deckkraft von 0.5 auf 0.15 gesenkt */
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
    placeholder="Soll ich Option A oder Option B wählen? Option A kostet..."
)

# --- DER ANALYSE-BUTTON ---
if st.button("Analyse starten", type="primary", use_container_width=True):
    if not user_input.strip():
        st.warning("Bitte gib zuerst einen Text ein!")
    else:
        # 1. Futuristischer Ladebalken für die Simulation
        progress_text = "Simuliere 10'000 Zukunftsszenarien..."
        my_bar = st.progress(0, text=progress_text)

        for percent_complete in range(100):
            time.sleep(0.01) # Simuliert flüssigen Rechenfortschritt
            my_bar.progress(percent_complete + 1, text=progress_text)
            
        my_bar.empty() # Entfernt den Balken wieder, wenn fertig
        
        # 2. Ab hier läuft die echte KI-Analyse & Mathematik
        with st.spinner("Berechne finale Entscheidungswerte..."):
            try:
                # call AI
                gemini_json_string = call_gemini_api(user_input)
                payload = FullAnalysisPayload.model_validate_json(gemini_json_string)
                
                profil = payload.user_profile
                options_list = payload.decision_options
                
            except Exception as e:
                st.error(f"Fehler bei der KI-Analyse: {e}")
                st.stop() # stop if error

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
            
            # Höchster Index zuerst
            all_reports.sort(key=lambda x: x.get('recommendation_index', 0), reverse=True)

        # --- ERGEBNISSE ANZEIGEN ---
        st.success("Analyse erfolgreich abgeschlossen!")
        
        st.subheader("Profil-Analyse der KI")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Risikoaversion", f"{profil.risk_aversion}x")
        col2.metric("Importanz: Geld", f"{user_weights['money']*100:.0f}%")
        col3.metric("Importanz: Zeit", f"{user_weights['time']*100:.0f}%")
        col4.metric("Importanz: Emotionen", f"{user_weights['abstract']*100:.0f}%")
        
        st.divider()
        
        # (Hier folgt direkt deine Schleife mit den Optionen, Expandern und farbigen Badges...)
        
        # Jede Option anzeigen (Zahlen immer sichtbar, Text im Dropdown)
        for i, r in enumerate(all_reports):
            if "error" in r:
                st.error(f"Fehler bei {r.get('option_name', 'Unbekannt')}: {r['error']}")
                continue
            
            rank_text = f"RANG {i+1}"
            
            with st.container(border=True):
                # Perfekt zentrierte Anordnung
                st.markdown(f"<p style='text-align: center; color: #2ecc71; font-weight: bold; margin-bottom: -5px;'>{rank_text}</p>", unsafe_allow_html=True)
                st.markdown(f"<h3 style='text-align: center;'>{r['option_name'].upper()}</h3>", unsafe_allow_html=True)
                
                # Drei schicke Metrik-Boxen für die harten Zahlen (Immer sichtbar)
                m1, m2, m3 = st.columns(3)
                m1.metric("Empfehlungs-Index (0-100)", f"{r['recommendation_index']:.1f} / 100")
                m2.metric("Value at Risk (95%)", f"{r['VaR_95']:.3f}")
                m3.metric("Conditional VaR", f"{r['CVaR']:.3f}")
                
                # Dropdown-Menü NUR für die Gedankengänge
                with st.expander("Gedankengänge der KI & Details einblenden"):
                    for chance in r['opportunities_raw']:
                        st.markdown(
                            f'<div style="background-color: rgba(46, 204, 113, 0.1); padding: 10px; border-radius: 5px; border-left: 5px solid #2ecc71; margin-bottom: 10px;">'
                            f' <b>{chance.name}</b> <em>(Chance: {chance.probability*100}%, CHF: {chance.financial_chf}, Zeit: {chance.time_minutes}, Emotion: {chance.utility_score})</em> <br>{chance.reasoning}'
                            f'</div>', 
                            unsafe_allow_html=True
                        )
                    for risiko in r['risks_raw']:
                        st.markdown(
                            f'<div style="background-color: rgba(231, 76, 60, 0.1); padding: 10px; border-radius: 5px; border-left: 5px solid #e74c3c; margin-bottom: 10px;">'
                            f'<b>{risiko.name}</b> <em>(Chance: {risiko.probability*100}%, CHF: {risiko.financial_chf}, Zeit: {risiko.time_minutes}, Emotion: {risiko.utility_score})</em> <br>{risiko.reasoning}'
                            f'</div>', 
                            unsafe_allow_html=True
                        )

        st.divider()
        
        # --- FINALE FEATURES: TRAINING & EXPORT ---
        st.subheader("System-Training & Daten-Export")
        
        col_train, col_export = st.columns(2)
        
        with col_train:
            st.markdown("**War diese Analyse logisch?**")
            if st.button("Ja, als Vorbild speichern (Lernen)", use_container_width=True):                # Wir speichern den ursprünglichen Text und das JSON in die memory.json
                save_to_memory(user_input, gemini_json_string)
                st.success("Erfolgreich im Erfahrungs-Archiv gespeichert!")
                
        with col_export:
            st.markdown("**Rohdaten exportieren:**")
            # Wir bauen eine simple CSV-Tabelle aus den Resultaten
            csv_data = "Option,Empfehlungs-Index,VaR_95,CVaR\n"
            for r in all_reports:
                if "error" not in r:
                    csv_data += f"{r['option_name']},{r['recommendation_index']:.1f},{r['VaR_95']:.3f},{r['CVaR']:.3f}\n"
            
            st.download_button(
                label="Resultate als .csv herunterladen",
                data=csv_data,
                file_name="entscheidungs_analyse.csv",
                mime="text/csv",
                use_container_width=True
            )