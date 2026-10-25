import os
import json
import time
import streamlit as st
from google import genai
from google.genai import types
from data_models import FullAnalysisPayload
from math_engine import run_full_analysis

api_key = st.secrets.get("GOOGLE_API_KEY") or os.environ.get("GOOGLE_API_KEY")
client = genai.Client(api_key=api_key)

MEMORY_FILE = "memory.json"

def load_memory():
    """Lädt bisherige gute Beispiele aus der Datei."""
    if not os.path.exists(MEMORY_FILE):
        return []
    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_to_memory(user_text, ai_json_response):
    """Speichert ein gutes Resultat ab. Behält maximal die 3 neuesten, um Kosten zu sparen."""
    memory = load_memory()
    
    memory.append({
        "user_input": user_text, 
        "ai_response": json.loads(ai_json_response)
    })
    
    if len(memory) > 3:
        memory = memory[-3:]
        
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory, f, indent=2, ensure_ascii=False)

def call_gemini_api(user_text: str, max_retries: int = 3) -> str:
        
    memory_data = load_memory()
    memory_string = ""
    
    if len(memory_data) > 0:
        memory_string = "\n\nHier sind vergangene, perfekte Beispiele von dir. Nutze sie als Referenz für deinen Stil und deine Bewertungen:\n"
        for i, entry in enumerate(memory_data):
            memory_string += f"--- BEISPIEL {i+1} ---\n"
            memory_string += f"Nutzer fragte: {entry['user_input']}\n"
            memory_string += f"Deine ideale Antwort war: {json.dumps(entry['ai_response'])}\n"
        memory_string += "----------------------\n"
    
    prompt = f"""
    Du bist ein rigoroser Risiko-Analyst. Deine Aufgabe ist es, Entscheidungen konsistent zu bewerten.
    Gehe Schritt für Schritt vor. Erkläre im Feld "reasoning" deinen Gedankengang.
    
    WICHTIGE REGEL (MULTI-OPTION):
    Wenn der Nutzer zwischen mehreren Dingen schwankt (z.B. "Soll ich A oder B tun?"), 
    erstelle für JEDE dieser Optionen einen komplett EIGENEN Eintrag in der Liste "decision_options".
    Bewerte die Risiken und Chancen für jede Option separat.
    ACHTUNG: Lass dich NIEMALS von der Reihenfolge beeinflussen, in der die Optionen genannt werden! 
    "A oder B" muss exakt dieselben Zahlen generieren wie "B oder A". Behandle jede Option als isoliertes Vakuum.

    WICHTIGE FEHLERBEHANDLUNG:
    Du bist eine strikte Analyse-Engine. Prüfe den Text des Nutzers rigoros. 
    Wenn die Eingabe zufällige Buchstabenkombinationen (wie "asdasd"), reinen Smalltalk, zusammenhangslose Wörter oder offensichtlichen Unsinn enthält, der keine auswertbare Entscheidung zulässt, brich die Analyse ab. 
    Versuche in solchen Fällen NICHT, Optionen zu erfinden.
    Gib stattdessen zwingend dieses exakte JSON-Format zurück und nichts anderes:
    {{
        "error": "Ungültige Eingabe. Die Engine benötigt eine klar formulierte Entscheidungssituation mit echten Alternativen, um Parameter berechnen zu können."
    }}

    STRENGE REGEL ZUR TRENNUNG VON CHANCEN UND RISIKEN (POLARITÄT):
    - Vermische niemals positive und negative Konsequenzen in demselben Punkt! 
    - Chancen (Opportunities) dürfen AUSSCHLIESSLICH positive Werte und Vorteile abbilden (z.B. finanzieller Gewinn, Zeitersparnis, positive Emotionen). Es dürfen hier keine versteckten Kosten oder Nachteile eingetragen werden.
    - Risiken (Risks) dürfen AUSSCHLIESSLICH negative Werte und Nachteile abbilden (z.B. finanzielle Ausgaben/Verluste, Zeitverlust, Stress, negative Emotionen). 
    - Wenn eine Option sowohl positive als auch negative Aspekte hat (z.B. Autofahren bringt Komfort, kostet aber Benzin), MUSST du diese strikt trennen: Der Komfort wird eine eigene Chance, die Benzinkosten werden ein eigenes Risiko.
    
    REGEL FÜR ZEIT (time_minutes): 
    - Berechne AUSSCHLIESSLICH die aktive, netto aufgewendete Arbeitszeit (z.B. 120 Minuten für das Schreiben einer Bewerbung).
    - Verwende NIEMALS Kalenderzeiten oder Wartezeiten (z.B. "dauert 2 Wochen") als Minuten-Wert. Bewerte Wartezeiten stattdessen nur über den abstrakten Emotionen-Score!

    WICHTIGER MASSSTAB (ANCHORING):
    Nutze für den "utility_score" zwingend dieses feste Lineal:
    +100: Lebensveränderndes Glück
     +80: Grosser Meilenstein
     +50: Deutliche Verbesserung
     +10: Kleine Alltagsfreude
       0: Neutral / Status Quo
     -10: Kleines Ärgernis
     -50: Schwerer Rückschlag
     -70: Massive Krise
    -100: Absoluter Ruin / Tod
    {memory_string}
    
    Analysiere nun dieses NEUE Szenario: "{user_text}"
    
    """
    
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model='gemini-3.1-flash-lite-preview', 
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.0,
                    seed=42,
                    response_mime_type="application/json",
                    response_schema=FullAnalysisPayload,
                )
            )
    
            return response.text

        except Exception as e:
            error_message = str(e)
            
            if "503" in error_message or "UNAVAILABLE" in error_message:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    print(f"\n[ Warnung: Google-Server sind kurzzeitig überlastet. ]")
                    print(f"[ System wartet {wait_time} Sekunden und startet Versuch {attempt + 2}/{max_retries}... ]")
                    time.sleep(wait_time)
                else:
                    raise Exception("Die Google-Server sind aktuell dauerhaft überlastet. Bitte versuche es in ein paar Minuten noch einmal.")
            else:
                raise e