# constants.py

DB_FILE = "carb_tracker.db"
CONFIG_FILE = "carb_tracker_config.json"

MEALS = [
    "Jejum",
    "Café da manhã",
    "Colação",
    "Almoço",
    "Café da tarde",
    "Jantar",
]

FIELDS = [
    ("Carboidratos (g)", "carbs"),
    ("Glicemia (mg/dL)", "glicemia"),
    ("Insulina Lispro (UI)", "lispro"),
    ("Bolus correção (UI)", "bolus"),
]

# Mapeamento para facilitar o acesso ao nome completo do campo pelo seu "key"
FIELD_NAMES_MAP = {key: title for title, key in FIELDS}

# NOVAS CONSTANTES PARA INFORMAÇÕES DO APLICATIVO
APP_VERSION = "1.2.0" # Defina a versão atual do seu aplicativo
LAST_UPDATED_DATE = "04/07/2025" # Data da última alteração relevante (hoje)