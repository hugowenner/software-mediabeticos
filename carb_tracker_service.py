# carb_tracker_service.py

import datetime as dt
import shutil
import json # Importar json para trabalhar com arquivos de configuração
from pathlib import Path # Importar Path para manipulação de caminhos

from database import Database
from constants import MEALS, FIELDS, DB_FILE, FIELD_NAMES_MAP, CONFIG_FILE # Import CONFIG_FILE

class CarbTrackerService:
    def __init__(self, db_path: str = DB_FILE, config_path: str = CONFIG_FILE):
        self.db = Database(db_path)
        self.db_path = db_path
        self.config_path = config_path # Caminho do arquivo de configuração
        self.config = self._load_config() # Carregar configurações na inicialização

    def _load_config(self) -> dict:
        """Carrega as configurações do arquivo JSON."""
        if Path(self.config_path).exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                # Se o arquivo estiver corrompido, retorna configurações padrão
                return self._default_config()
        return self._default_config()

    def _default_config(self) -> dict:
        """Retorna as configurações padrão do aplicativo."""
        return {
            "report_date_format": "%d/%m/%Y",
            "report_default_range": "30", # Número de dias para o filtro padrão
            "glicemia_alert_threshold": 180, # Exemplo de configuração futura
            "db_location_override": None # Caminho personalizado do DB
        }

    def save_config(self, new_config: dict):
        """Salva as configurações no arquivo JSON."""
        self.config.update(new_config) # Atualiza apenas as chaves fornecidas
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4)
            return True, "Configurações salvas com sucesso."
        except Exception as e:
            return False, f"Erro ao salvar configurações: {e}"

    def get_config(self, key: str, default=None):
        """Obtém uma configuração específica."""
        return self.config.get(key, default)

    def validate_numeric_input(self, value_str: str, field_key: str, meal_name: str = "") -> tuple[bool, float | None, str]:
        """
        Valida se a string é um número não negativo.
        Retorna (True, float_value, "") se válido, ou (False, None, error_message) se inválido.
        """
        if not value_str:
            return True, None, ""

        try:
            value = float(value_str)
            if value < 0:
                field_title = FIELD_NAMES_MAP.get(field_key, field_key)
                context = f"na {meal_name}" if meal_name else ""
                return False, None, f"Valor inválido para {field_title.split(' ')[0]} {context}. Por favor, insira um número não negativo."
            return True, value, ""
        except ValueError:
            field_title = FIELD_NAMES_MAP.get(field_key, field_key)
            context = f"na {meal_name}" if meal_name else ""
            return False, None, f"Valor inválido para {field_title.split(' ')[0]} {context}. Por favor, insira um número válido."

    def save_daily_data(self, date_iso: str, glargina_value: float, meal_entries_data: dict) -> tuple[bool, str]:
        """
        Salva os dados diários (glargina e refeições) no banco de dados.
        Retorna (True, "Sucesso") ou (False, "Mensagem de Erro").
        """
        self.db.upsert_glargina_dose(date_iso, glargina_value)

        for meal, values in meal_entries_data.items():
            has_data_for_meal = any(v is not None for v in values.values())
            if has_data_for_meal:
                self.db.upsert_entry(date_iso, meal, values)

        return True, f"Dados do dia {dt.date.fromisoformat(date_iso).strftime('%d/%m/%Y')} salvos com sucesso."

    def get_daily_data(self, date_iso: str) -> tuple[float | None, dict]:
        """
        Retorna a dose de Glargina e os dados das refeições para uma data específica.
        """
        glargina_dose = self.db.fetch_glargina_dose(date_iso)
        
        meal_data = {}
        for meal in MEALS:
            data = self.db.fetch_entry(date_iso, meal)
            if data:
                meal_data[meal] = {
                    "carbs": data[0],
                    "glicemia": data[1],
                    "lispro": data[2],
                    "bolus": data[3]
                }
            else:
                meal_data[meal] = {key: None for _, key in FIELDS}
        return glargina_dose, meal_data

    def calculate_period_totals(self, start_iso: str, end_iso: str) -> dict:
        """
        Calcula os totais de carboidratos, glicemia média, insulina Lispro e Glargina
        para um determinado período.
        """
        rows = self.db.fetch_range(start_iso, end_iso)
        glargina_rows = self.db.fetch_glargina_range(start_iso, end_iso)

        totals = {
            "carbs": 0.0,
            "glicemia_sum": 0.0,
            "glicemia_count": 0,
            "lispro": 0.0,
            "bolus": 0.0,
            "glargina_sum": 0.0,
            "glargina_count": 0
        }

        for (_, _, carbs, glicemia, lispro, bolus) in rows:
            totals["carbs"] += carbs or 0
            if glicemia is not None:
                totals["glicemia_sum"] += glicemia
                totals["glicemia_count"] += 1
            totals["lispro"] += lispro or 0
            totals["bolus"] += bolus or 0

        for (_, dose) in glargina_rows:
            if dose is not None and dose > 0:
                totals["glargina_sum"] += dose
                totals["glargina_count"] += 1

        avg_glicemia = (
            totals["glicemia_sum"] / totals["glicemia_count"]
            if totals["glicemia_count"] > 0
            else 0.0
        )
        avg_glargina = (
            totals["glargina_sum"] / totals["glargina_count"]
            if totals["glargina_count"] > 0
            else 0.0
        )
        
        totals["avg_glicemia"] = avg_glicemia
        totals["avg_glargina"] = avg_glargina

        return totals

    def get_report_data_for_pdf(self, start_iso: str, end_iso: str) -> tuple[list, dict]:
        """
        Busca os dados necessários para gerar o relatório PDF.
        """
        rows = self.db.fetch_range(start_iso, end_iso)
        glargina_rows = self.db.fetch_glargina_range(start_iso, end_iso)
        glargina_by_date = {date: dose for date, dose in glargina_rows}
        return rows, glargina_by_date

    def create_backup(self, source_db_path: str, destination_backup_path: str) -> tuple[bool, str]:
        """
        Cria uma cópia do arquivo do banco de dados para um local especificado.
        """
        try:
            self.db.close()
            shutil.copy2(source_db_path, destination_backup_path)
            self.db = Database(self.db_path)
            return True, f"Backup criado com sucesso em: {destination_backup_path}"
        except FileNotFoundError:
            self.db = Database(self.db_path)
            return False, "Arquivo do banco de dados original não encontrado."
        except Exception as e:
            self.db = Database(self.db_path)
            return False, f"Erro ao criar backup: {e}"

    def restore_backup(self, source_backup_path: str, destination_db_path: str) -> tuple[bool, str]:
        """
        Restaura o banco de dados a partir de um arquivo de backup especificado.
        """
        try:
            self.db.close()
            shutil.copy2(source_backup_path, destination_db_path)
            self.db = Database(self.db_path)
            return True, f"Banco de dados restaurado com sucesso de: {source_backup_path}"
        except FileNotFoundError:
            self.db = Database(self.db_path)
            return False, "Arquivo de backup não encontrado."
        except Exception as e:
            self.db = Database(self.db_path)
            return False, f"Erro ao restaurar backup: {e}. Certifique-se de que o arquivo de backup é válido."

    def close_db(self):
        self.db.close()