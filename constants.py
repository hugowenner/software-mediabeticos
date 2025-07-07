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
    "Lanche Extra",
]

FIELDS = [
    ("Carboidratos (g)", "carbs"),
    ("Glicemia (mg/dL)", "glicemia"),
    ("Insulina Lispro (UI)", "lispro"),
    ("Bolus correção (UI)", "bolus"),
    ("Observações", "observations"),
]

# Mapeamento para facilitar o acesso ao nome completo do campo pelo seu "key"
FIELD_NAMES_MAP = {key: title for title, key in FIELDS}

# NOVAS CONSTANTES PARA INFORMAÇÕES DO APLICATIVO
APP_VERSION = "1.2.0"
LAST_UPDATED_DATE = "04/07/2025"

# NOVAS CONSTANTES PARA REFEIÇÕES DINÂMICAS
FIXED_MEALS = [m for m in MEALS if m != "Lanche Extra"]
DYNAMIC_MEAL_PREFIX = "Lanche Extra"