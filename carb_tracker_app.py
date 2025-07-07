# carb_tracker_app.py

import tkinter as tk
from tkinter import ttk, messagebox
import tkinter.font as tkFont
import datetime as dt
import os

from daily_entry_tab_ui import DailyEntryTabUI
from reports_tab_ui import ReportsTabUI
from backup_tab_ui import BackupTabUI
from settings_tab_ui import SettingsTabUI
from insulin_calculator_tab_ui import InsulinCalculatorTabUI
from fsi_calculator_tab_ui import FSICalculatorTabUI

from carb_tracker_service import CarbTrackerService
from constants import DB_FILE, APP_VERSION, LAST_UPDATED_DATE, CONFIG_FILE

class CarbTrackerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"Carb Tracker v{APP_VERSION}")
        self.geometry("900x700")
        self.protocol("WM_DELETE_WINDOW", self.ask_quit)

        self.service = CarbTrackerService(db_path=DB_FILE, config_path=CONFIG_FILE)

        # Temas disponíveis
        self.available_themes = ["clam", "alt", "default", "vista", "xpnative"] # Adicione ou remova temas conforme o ttk suporta

        self._configure_styles()
        self._set_fonts()

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(expand=True, fill="both")

        self._create_tabs()

        # Carregar o tema salvo ou o padrão ao iniciar
        self.load_theme_from_config()

        self.after(100, lambda: self.daily_entry_tab_instance.load_day_data(dt.date.today().isoformat()))

    def _configure_styles(self):
        self.colors = {
            "primary": "#4CAF50",
            "secondary": "#8BC34A",
            "accent": "#FFC107",
            "text_dark": "#212121",
            "text_light": "#000000",
            "bg": "#F5F5F5",
            "panel_bg": "#FFFFFF",
            "border": "#E0E0E0",
            "error": "#F44336",
            "success": "#4CAF50",
            "warning_color": "#FF9800", # Adicionado para o status de backup
            "text_secondary": "#757575", # Adicionado para o status de backup
            "date_nav_bg": "#E8F5E9",
            "glargina_bg": "#E3F2FD",
            "meal_row_bg": "#FFFFFF",
            "meal_row_alt_bg": "#F9FBE7",
            "exit_button_bg": "#D32F2F",
            "exit_button_fg": "#FFFFFF",
            "result_bg": "#BBDEFB",
            "report_header_bg": "#E0F2F7",
        }

        style = ttk.Style(self)
        self.style = style
        # self.style.theme_use("clam") # Removido para permitir o carregamento do tema via configuração

        style.configure(".", font=("Helvetica", 10), background=self.colors["bg"], foreground=self.colors["text_dark"])
        style.configure("TFrame", background=self.colors["bg"])
        style.configure("Panel.TFrame", background=self.colors["panel_bg"], relief="flat", borderwidth=1, bordercolor=self.colors["border"])
        style.configure("TLabel", background=self.colors["panel_bg"], foreground=self.colors["text_dark"])
        style.configure("Heading.TLabel", font=("Helvetica", 16, "bold"), foreground=self.colors["primary"], background=self.colors["bg"])
        style.configure("Result.TLabel", font=("Helvetica", 12, "bold"), foreground=self.colors["text_dark"], background=self.colors["result_bg"], padding=10)

        style.configure("TNotebook", background=self.colors["bg"], borderwidth=0)
        style.configure("TNotebook.Tab", background=self.colors["secondary"], foreground=self.colors["text_light"],
                        font=("Helvetica", 10, "bold"), padding=[10, 5])
        style.map("TNotebook.Tab",
                  background=[("selected", self.colors["primary"]), ("active", self.colors["primary"])],
                  foreground=[("selected", self.colors["text_light"]), ("active", self.colors["text_light"])])

        style.configure("TButton",
                        background=self.colors["primary"],
                        foreground=self.colors["text_light"],
                        font=("Helvetica", 10, "bold"),
                        relief="flat",
                        padding=8)
        style.map("TButton",
                  background=[("active", self.colors["secondary"])],
                  foreground=[("active", self.colors["text_light"])])

        style.configure("Exit.TButton",
                        background=self.colors["exit_button_bg"],
                        foreground=self.colors["exit_button_fg"],
                        font=("Helvetica", 10, "bold"),
                        relief="flat",
                        padding=8)
        style.map("Exit.TButton",
                  background=[("active", "#EF5350")])

        style.configure("TEntry", fieldbackground=self.colors["panel_bg"], foreground=self.colors["text_dark"],
                        borderwidth=1, relief="solid", bordercolor=self.colors["border"])

        style.configure("DateNav.TFrame", background=self.colors["date_nav_bg"])
        style.configure("DateNav.TButton",
                        background=self.colors["primary"],
                        foreground=self.colors["text_light"],
                        font=("Helvetica", 10, "bold"),
                        relief="flat",
                        padding=[5, 2])
        style.map("DateNav.TButton",
                  background=[("active", self.colors["secondary"])])

        style.configure("Glargina.TLabel", background=self.colors["glargina_bg"], foreground=self.colors["text_dark"], font=("Helvetica", 10, "bold"))
        style.configure("GlarginaEntry.TEntry", fieldbackground=self.colors["glargina_bg"])

        style.configure("MealSection.TLabelframe", background=self.colors["panel_bg"], borderwidth=0)
        style.configure("MealSection.TLabelframe.Label", background=self.colors["panel_bg"], foreground=self.colors["text_dark"], font=("Helvetica", 10, "bold"))

        style.configure("MealRow.TFrame", background=self.colors["meal_row_bg"])
        style.configure("MealRowAlt.TFrame", background=self.colors["meal_row_alt_bg"])

        style.configure("MealName.TLabel", background=self.colors["meal_row_bg"], foreground=self.colors["text_dark"], font=("Helvetica", 10, "bold"))
        style.configure("MealNameAlt.TLabel", background=self.colors["meal_row_alt_bg"], foreground=self.colors["text_dark"], font=("Helvetica", 10, "bold"))

        style.configure("MealFieldHeader.TLabel", background=self.colors["panel_bg"], foreground=self.colors["text_dark"], font=("Helvetica", 9, "bold"))
        style.configure("MealField.TEntry", fieldbackground=self.colors["panel_bg"])

        style.configure("ReportHeader.TLabel", background=self.colors["report_header_bg"], foreground=self.colors["text_dark"], font=("Helvetica", 12, "bold"))
        style.configure("ReportTotal.TLabel", background=self.colors["panel_bg"], foreground=self.colors["text_dark"], font=("Helvetica", 10, "bold"))
        style.configure("ReportEntry.TEntry", fieldbackground=self.colors["panel_bg"])
        style.configure("ReportDateNav.TFrame", background=self.colors["date_nav_bg"])
        style.configure("ReportDateNav.TButton",
                        background=self.colors["primary"],
                        foreground=self.colors["text_light"],
                        font=("Helvetica", 10, "bold"),
                        relief="flat",
                        padding=[5, 2])
        style.map("ReportDateNav.TButton",
                  background=[("active", self.colors["secondary"])])

        style.configure("Treeview",
                        background=self.colors["panel_bg"],
                        foreground=self.colors["text_dark"],
                        fieldbackground=self.colors["panel_bg"],
                        rowheight=25)
        style.map("Treeview", background=[("selected", self.colors["primary"])])
        style.configure("Treeview.Heading",
                        font=("Helvetica", 10, "bold"),
                        background=self.colors["secondary"],
                        foreground=self.colors["text_light"])
        style.map("Treeview.Heading",
                  background=[("active", self.colors["primary"])])
        style.layout("Treeview.Row",
                     [('Treeview.row', {'children': [('Treeview.padding', {'children': [('Treeview.treearea', {'sticky': 'nswe'})], 'sticky': 'nswe'})], 'sticky': 'nswe'})])
        style.configure("Totals.TLabel", background=self.colors["panel_bg"], foreground=self.colors["text_dark"], font=("Helvetica", 10), padding=10) # Estilo adicionado para o label de totais


    def _set_fonts(self):
        self.default_font = tkFont.Font(family="Helvetica", size=10)
        self.heading_font = tkFont.Font(family="Helvetica", size=16, weight="bold")
        self.data_font = tkFont.Font(family="Helvetica", size=10)

    def _create_tabs(self):
        # 1. Registro Diário
        self.daily_entry_tab_instance = DailyEntryTabUI(self.notebook, self.service, self)
        self.notebook.add(self.daily_entry_tab_instance, text="Registro Diário")

        # 2. Calc. Insulina
        self.insulin_calculator_tab_instance = InsulinCalculatorTabUI(self.notebook, self)
        self.notebook.add(self.insulin_calculator_tab_instance, text="Calc. Insulina")

        # 3. Calc. FSI
        self.fsi_calculator_tab_instance = FSICalculatorTabUI(self.notebook, self)
        self.notebook.add(self.fsi_calculator_tab_instance, text="Calc. FSI")

        # 4. Relatórios
        self.reports_tab_instance = ReportsTabUI(self.notebook, self.service, self)
        self.notebook.add(self.reports_tab_instance, text="Relatórios")

        # 5. Backup/Restauração
        self.backup_tab_instance = BackupTabUI(self.notebook, self.service, self)
        self.notebook.add(self.backup_tab_instance, text="Backup/Restauração")

        # 6. Configurações
        self.settings_tab_instance = SettingsTabUI(self.notebook, self.service, self)
        self.notebook.add(self.settings_tab_instance, text="Configurações")

    def load_theme_from_config(self):
        """Carrega o tema salvo no arquivo de configuração e o aplica."""
        saved_theme = self.service.get_config("app_theme", "clam") # 'clam' como padrão se não houver tema salvo
        self.apply_theme(saved_theme)

    def apply_theme(self, theme_name: str):
        """Aplica o tema ttk especificado."""
        if theme_name in self.style.theme_names():
            self.style.theme_use(theme_name)
            # Reconfigurar estilos customizados após a mudança de tema, se necessário.
            # Isso garante que cores e fontes que dependem de nossos 'colors' dict sejam aplicadas.
            self._configure_styles()
        else:
            messagebox.showwarning("Tema Inválido", f"O tema '{theme_name}' não é suportado pelo ttk. Usando o tema padrão.")
            self.style.theme_use("clam") # Fallback para um tema conhecido

    def confirm_save_all_modified_data_before_action(self) -> bool:
        """
        Confirma com o usuário para salvar dados não salvos antes de uma ação crítica.
        Retorna True se o usuário prosseguir (salvando ou descartando), False se cancelar.
        """
        if self.daily_entry_tab_instance.get_data_modified_status():
            response = messagebox.askyesnocancel(
                "Dados Não Salvos",
                "Você tem dados não salvos. Deseja salvar antes de prosseguir?"
            )
            if response is True:
                self.daily_entry_tab_instance.save_day()
                # Verificar novamente o status de modificado após a tentativa de salvar
                return not self.daily_entry_tab_instance.get_data_modified_status()
            elif response is False:
                self.daily_entry_tab_instance.set_data_modified_status(False)
                return True
            else:
                return False # Usuário cancelou
        return True # Não há dados modificados, pode prosseguir

    def load_day_data_with_confirmation(self, date_iso: str):
        if self.confirm_save_all_modified_data_before_action():
            self.daily_entry_tab_instance.load_day_data(date_iso)


    def ask_quit(self):
        if self.daily_entry_tab_instance.get_data_modified_status():
            if messagebox.askyesno(
                "Sair",
                "Você tem dados não salvos. Deseja sair sem salvar?"
            ):
                self.service.close_db()
                self.destroy()
            else:
                pass
        else:
            self.service.close_db()
            self.destroy()

if __name__ == "__main__":
    app = CarbTrackerApp()
    app.mainloop()