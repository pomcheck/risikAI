from pydantic import BaseModel, Field
from typing import List

class Consequence(BaseModel):
    name: str

    reasoning: str = Field(description="Erkläre in 1-2 Sätzen, WARUM du die folgenden Zahlen gewählt hast.")
    
    probability: float = Field(ge=0.0, le=1.0)
    
    financial_chf: float = Field(default=0.0, description="Finanzieller Gewinn/Verlust in CHF. WICHTIG: Wenn im Text keine Zahlen stehen, MUSST du einen realistischen realen Wert schätzen (z.B. -1000 für einen Flug)!")
    
    time_minutes: float = Field(default=0.0, description="Zeitersparnis/Aufwand in Minuten. WICHTIG: Wenn im Text keine Zahlen stehen, MUSST du einen realistischen Wert schätzen!")
    
    utility_score: float = Field(default=0.0, ge=-100.0, le=100.0)
    
    uncertainty: float = Field(default=0.1, ge=0.0, le=1.0)

class DecisionOption(BaseModel):
    name: str
    risks: List[Consequence] = []
    opportunities: List[Consequence] = []

class UserProfile(BaseModel):
    money_importance: int = Field(ge=1, le=10, description="Wie wichtig ist dem Nutzer finanzieller Gewinn/Verlust im Text?")
    time_importance: int = Field(ge=1, le=10, description="Wie wichtig ist dem Nutzer Zeitersparnis oder Aufwand?")
    abstract_importance: int = Field(ge=1, le=10, description="Wie wichtig sind dem Nutzer Emotionen, Stress oder ethische Werte?")
    
    risk_aversion: float = Field(default=1.0, ge=0.5, le=3.0, description="Wie ängstlich oder vorsichtig klingt der Nutzer?")

class FullAnalysisPayload(BaseModel):
    """Das ist das finale Master-Objekt, das die KI zurückgeben muss."""
    user_profile: UserProfile
    decision_options: List[DecisionOption] = Field(description="Eine Liste aller zur Auswahl stehenden Optionen. Wenn der Nutzer 'A oder B' fragt, erstelle hier zwei getrennte Optionen.")