from main_app import call_gemini_api, save_to_memory # <--- save_to_memory hinzufügen!

import streamlit as st
import json
from data_models import FullAnalysisPayload
from math_engine import run_full_analysis
from main_app import call_gemini_api # Wir klauen uns die schlaue KI-Funktion von deiner anderen Datei!

# --- SEITEN-SETUP ---
st.set_page_config(page_title="KI-Entscheidungs-Assistent", page_icon="⚖️", layout="centered")

st.title("KI-gestützte Entscheidungshilfe")
st.markdown("**risikAI.com** | Jegliche Entscheidung kann in mathematische Variablen aufgeteilt und deterministisch beurteilt werden.")
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
        st.warning("Bitte gib zuerst eine Entscheidung ein!")
    else:
        with st.spinner("KI liest den Text und extrahiert Parameter..."):
            try:
                # call AI
                gemini_json_string = call_gemini_api(user_input)
                payload = FullAnalysisPayload.model_validate_json(gemini_json_string)
                
                profil = payload.user_profile
                options_list = payload.decision_options
                
            except Exception as e:
                st.error(f"Fehler bei der KI-Analyse: {e}")
                st.stop() # stop if error

        with st.spinner("risikAI berechnet 10'000 mögliche Ausgänge..."):
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
        
        # Jede Option anzeigen (Zahlen immer sichtbar, Text im Dropdown)
        for i, r in enumerate(all_reports):
            if "error" in r:
                st.error(f"Fehler bei {r.get('option_name', 'Unbekannt')}: {r['error']}")
                continue
            
            # Anstatt Emojis nutzen wir eine klare Text-Bezeichnung
            rank_text = f"Rang {i+1}"
            
            # Container mit einem dezenten Akzent anstatt Emojis
            with st.container(border=True):
                # Hier der Header ohne Emojis, dafür mit farbigem Rank-Label
                cols = st.columns([1, 4])
                cols[0].caption(rank_text)
                cols[1].subheader(r['option_name'].upper())
                
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
                            f'<b>{risiko.name}</b> <em>(Chance: {risiko.probability*100}%, CHF: {risiko.financial_chf}, Zeit: {chance.time_minutes}, Emotion: {risiko.utility_score})</em> <br>{risiko.reasoning}'
                            f'</div>', 
                            unsafe_allow_html=True
                        )

        st.divider()
        
        # --- FINALE FEATURES: TRAINING & EXPORT ---
        st.subheader("System-Training & Daten-Export")
        
        col_train, col_export = st.columns(2)
        
        with col_train:
            st.markdown("**War diese Analyse logisch?**")
            if st.button("Ja, als Vorbild speichern (Lernen)"):
                # Wir speichern den ursprünglichen Text und das JSON in die memory.json
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
                mime="text/csv"
            )