## Anleitung zum Testen

Um die Web-Applikation risikAI lokal auszuführen, sind folgende Schritte im Terminal erforderlich (Python 3.11 empfohlen):

1. **Repository klonen und Verzeichnis öffnen:**  
   `git clone https://github.com/pomcheck/risikAI.git`  
   `cd risikAI`

2. **Benötigte Bibliotheken installieren:**  
   `pip install streamlit google-genai pydantic numpy`

3. **Gemini API-Schlüssel setzen:**  
   - macOS / Linux: `export GEMINI_API_KEY="IHR_API_KEY"`  
   - Windows (PowerShell): `$env:GEMINI_API_KEY="IHR_API_KEY"`

4. **App starten:**  
   `streamlit run web_app.py`  
   Die Benutzeroberfläche öffnet sich anschliessend automatisch im Browser unter `http://localhost:8501`.
