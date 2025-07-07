# carb_tracker_service.py

import datetime as dt
import shutil
import json
from pathlib import Path

from database import Database
from constants import MEALS, FIELDS, DB_FILE, FIELD_NAMES_MAP, CONFIG_FILE

class CarbTrackerService:
    def __init__(self, db_path: str = DB_FILE, config_path: str = CONFIG_FILE):
        self.db = Database(db_path)
        self.db_path = db_path
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> dict:
        if Path(self.config_path).exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                # Se o arquivo estiver corrompido, retorna a configuração padrão
                return self._default_config()
        return self._default_config()

    def _default_config(self) -> dict:
        return {
            "report_date_format": "%d/%m/%Y",
            "glicemia_alert_threshold": 180,
            "db_location_override": None,
            "app_theme": "clam" # NOVO: Tema padrão do aplicativo
        }

    def save_config(self, new_config: dict):
        self.config.update(new_config)
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4)
            return True, "Configurações salvas com sucesso."
        except Exception as e:
            return False, f"Erro ao salvar configurações: {e}"

    def get_config(self, key: str, default=None):
        return self.config.get(key, default)

    def validate_numeric_input(self, value_str: str, field_key: str, meal_name: str = "") -> tuple[bool, float | None, str]:
        if not value_str:
            return True, None, ""

        if field_key == "observations":
            return True, value_str.strip() if value_str.strip() else None, ""

        try:
            value = float(value_str)
            # Para glicemia_alvo, 0 é um valor permitido, então não precisa ser positivo.
            # No entanto, outros campos como carbs, lispro, bolus não devem ser negativos.
            # A validação original já cuidava disso, mantendo a lógica.
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
        self.db.upsert_glargina_dose(date_iso, glargina_value)

        # Primeiro, obtenha as refeições que existem para esta data
        existing_meals = {entry[1] for entry in self.db.fetch_range(date_iso, date_iso) if entry[0] == date_iso}

        # Iterar sobre todas as refeições que podem existir (fixas e dinâmicas salvas)
        # e as que estão sendo enviadas pelo UI.
        # Isso garante que refeições que foram removidas da UI (dinâmicas) sejam apagadas do DB
        # e as que não têm dados na UI mas existem no DB, também sejam apagadas.
        all_potential_meals = set(MEALS) # Refeições fixas do constants
        all_potential_meals.update(meal_entries_data.keys()) # Refeições (fixas + dinâmicas) com dados no UI
        all_potential_meals.update(existing_meals) # Refeições existentes no DB para essa data

        for meal in all_potential_meals:
            if meal in meal_entries_data:
                values = meal_entries_data[meal]
                # Verifica se há dados válidos para esta refeição.
                # 'observations' pode ser uma string vazia, mas ainda é um dado.
                # Os campos numéricos devem ter um valor (não None).
                has_valid_data = False
                for key, val in values.items():
                    if key == "observations":
                        if val is not None and val.strip() != "":
                            has_valid_data = True
                            break
                    else: # Campos numéricos
                        if val is not None:
                            has_valid_data = True
                            break

                if has_valid_data:
                    full_values = {key: values.get(key) for _, key in FIELDS}
                    self.db.upsert_entry(date_iso, meal, full_values)
                else:
                    # Se a refeição existe no DB mas não tem dados na UI, delete-a
                    self.db.delete_entry(date_iso, meal)
            else:
                # Se a refeição existe no DB mas não está presente no meal_entries_data do UI,
                # ou seja, foi removida (caso de lanche extra) ou seus campos foram limpos na UI,
                # então a removemos do DB.
                self.db.delete_entry(date_iso, meal)


        return True, f"Dados do dia {dt.date.fromisoformat(date_iso).strftime('%d/%m/%Y')} salvos com sucesso."

    def get_daily_data(self, date_iso: str) -> tuple[float | None, dict]:
        glargina_dose = self.db.fetch_glargina_dose(date_iso)

        meal_data = {}
        # Primeiro, carregue todas as entradas existentes para o dia
        existing_entries_for_day = self.db.fetch_range(date_iso, date_iso)
        for date, meal, carbs, glicemia, lispro, bolus, observations in existing_entries_for_day:
            if date == date_iso: # Garante que é para o dia correto, fetch_range pode trazer outros dias
                meal_data[meal] = {
                    "carbs": carbs,
                    "glicemia": glicemia,
                    "lispro": lispro,
                    "bolus": bolus,
                    "observations": observations
                }

        # Garanta que todas as refeições FIXAS estejam presentes, mesmo que sem dados.
        # Isso é importante para a UI exibir os campos corretamente.
        for meal in MEALS: # MEALS inclui FIXED_MEALS e "Lanche Extra"
            if meal not in meal_data:
                meal_data[meal] = {key: None for _, key in FIELDS}
                meal_data[meal]["observations"] = None # Garante que observations também é None

        return glargina_dose, meal_data


    def calculate_period_totals(self, start_iso: str, end_iso: str) -> dict:
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

        for (_, _, carbs, glicemia, lispro, bolus, _) in rows:
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
        rows = self.db.fetch_range(start_iso, end_iso)
        glargina_rows = self.db.fetch_glargina_range(start_iso, end_iso)
        glargina_by_date = {date: dose for date, dose in glargina_rows}
        return rows, glargina_by_date

    def get_daily_aggregated_data(self, start_iso: str, end_iso: str) -> dict:
        """
        Retorna dados agregados por dia para o período especificado,
        incluindo totais diários de carboidratos, média de glicemia e dose de glargina.
        """
        raw_entries = self.db.fetch_range(start_iso, end_iso)
        glargina_doses = self.db.fetch_glargina_range(start_iso, end_iso)

        start_date = dt.date.fromisoformat(start_iso)
        end_date = dt.date.fromisoformat(end_iso)

        delta = end_date - start_date
        all_dates = [start_date + dt.timedelta(days=i) for i in range(delta.days + 1)]

        daily_data = {}
        for date_obj in all_dates:
            date_iso = date_obj.isoformat()
            daily_data[date_iso] = {
                "carbs": 0.0,
                "glicemia_sum": 0.0,
                "glicemia_count": 0,
                "glargina": None
            }

        for date_iso, _, carbs, glicemia, _, _, _ in raw_entries:
            if date_iso in daily_data:
                daily_data[date_iso]["carbs"] += carbs or 0
                if glicemia is not None:
                    daily_data[date_iso]["glicemia_sum"] += glicemia
                    daily_data[date_iso]["glicemia_count"] += 1

        for date_iso, dose in glargina_doses:
            if date_iso in daily_data:
                daily_data[date_iso]["glargina"] = dose

        formatted_daily_data = {}
        for date_iso, data in daily_data.items():
            avg_glicemia = (
                data["glicemia_sum"] / data["glicemia_count"]
                if data["glicemia_count"] > 0
                else None
            )
            formatted_daily_data[date_iso] = {
                "carbs": data["carbs"],
                "glicemia": avg_glicemia,
                "glargina": data["glargina"]
            }

        return formatted_daily_data


    def create_backup(self, source_db_path: str, destination_backup_path: str) -> tuple[bool, str]:
        try:
            self.db.close() # Fecha a conexão com o banco de dados antes de copiar
            shutil.copy2(source_db_path, destination_backup_path)
            self.db = Database(self.db_path) # Reabre a conexão
            return True, f"Backup criado com sucesso em: {destination_backup_path}"
        except FileNotFoundError:
            self.db = Database(self.db_path) # Reabre a conexão em caso de erro
            return False, "Arquivo do banco de dados original não encontrado."
        except Exception as e:
            self.db = Database(self.db_path) # Reabre a conexão em caso de erro
            return False, f"Erro ao criar backup: {e}"

    def restore_backup(self, source_backup_path: str, destination_db_path: str) -> tuple[bool, str]:
        try:
            self.db.close() # Fecha a conexão com o banco de dados antes de copiar
            shutil.copy2(source_backup_path, destination_db_path)
            self.db = Database(self.db_path) # Reabre a conexão
            return True, f"Banco de dados restaurado com sucesso de: {source_backup_path}"
        except FileNotFoundError:
            self.db = Database(self.db_path) # Reabre a conexão em caso de erro
            return False, "Arquivo de backup não encontrado."
        except Exception as e:
            self.db = Database(self.db_path) # Reabre a conexão em caso de erro
            return False, f"Erro ao restaurar backup: {e}. Certifique-se de que o arquivo de backup é válido."

    def close_db(self):
        self.db.close()