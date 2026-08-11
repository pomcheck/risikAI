from data_models import DecisionOption, Consequence

# Beispiel 1: Fahrrad vs. Auto (Kleine Beträge)
fahrrad_option = DecisionOption(
    name="Mit dem Fahrrad einkaufen",
    opportunities=[
        Consequence(name="Benzin gespart", probability=1.0, financial_impact_chf=3.0)
    ],
    risks=[
        Consequence(name="Regenrisiko", probability=0.3, abstract_impact=-20.0, time_impact_minutes=10.0)
    ]
)

# Beispiel 2: Studium (Grosse Beträge)
studium_option = DecisionOption(
    name="Informatik Studium",
    opportunities=[
        Consequence(name="Hohes Einstiegsgehalt", probability=0.8, financial_impact_chf=500000.0)
    ],
    risks=[
        Consequence(name="Studienabbruch", probability=0.1, financial_impact_chf=-20000.0, abstract_impact=-80.0)
    ]
)

print(f"Szenario 1 geladen: {fahrrad_option.name} mit {len(fahrrad_option.risks)} Risiken.")
print(f"Szenario 2 geladen: {studium_option.name} mit {len(studium_option.opportunities)} Chancen.")