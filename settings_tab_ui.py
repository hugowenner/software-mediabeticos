# settings_tab_ui.py

import datetime as dt
from tkinter import Tk, Label, Entry, Button, StringVar, ttk, messagebox, filedialog, Toplevel, Canvas, Text, Scrollbar

from carb_tracker_service import CarbTrackerService
from constants import APP_VERSION, LAST_UPDATED_DATE
from tooltip import ToolTip

class SettingsTabUI(ttk.Frame):
    def __init__(self, master, service: CarbTrackerService, app_instance):
        super().__init__(master, style="Panel.TFrame")
        self.service = service
        self.app_instance = app_instance

        # Variáveis de UI
        self.report_date_format_var = StringVar()
        self.settings_status_label = None # Será inicializado em _build_ui

        self._build_ui()
        self._load_settings_into_ui() # Carrega as configurações ao inicializar a aba

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=1)
        self.grid_rowconfigure(3, weight=0)

        ttk.Label(self, text="Configurações do Aplicativo", style="Heading.TLabel").grid(row=0, column=0, pady=(15, 20), sticky="ew", padx=20)

        settings_frame = ttk.Frame(self, style="Panel.TFrame", padding=(20, 20))
        settings_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 20))
        settings_frame.grid_columnconfigure(0, weight=0)
        settings_frame.grid_columnconfigure(1, weight=1)

        report_settings_labelframe = ttk.LabelFrame(settings_frame, text="Relatórios", style="SettingSection.TLabelframe")
        report_settings_labelframe.grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=10)
        report_settings_labelframe.grid_columnconfigure(1, weight=1)

        ttk.Label(report_settings_labelframe, text="Formato de Data para PDF:", style="SettingLabel.TLabel").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        self.report_date_format_entry = ttk.Entry(report_settings_labelframe, textvariable=self.report_date_format_var, width=15)
        self.report_date_format_entry.grid(row=0, column=1, sticky="ew", padx=10, pady=5)
        ToolTip(self.report_date_format_entry, "Ex: %d/%m/%Y para 01/01/2023, %Y-%m-%d para 2023-01-01")

        app_info_labelframe = ttk.LabelFrame(settings_frame, text="Sobre o Aplicativo", style="SettingSection.TLabelframe")
        app_info_labelframe.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=10)
        app_info_labelframe.grid_columnconfigure(1, weight=1)

        ttk.Label(app_info_labelframe, text="Versão:", style="SettingLabel.TLabel").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        # CORREÇÃO AQUI: Usando "text_dark"
        ttk.Label(app_info_labelframe, text=APP_VERSION, style="SettingLabel.TLabel", foreground=self.app_instance.colors["text_dark"]).grid(row=0, column=1, sticky="w", padx=10, pady=5)

        ttk.Label(app_info_labelframe, text="Última Atualização:", style="SettingLabel.TLabel").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        # CORREÇÃO AQUI: Usando "text_dark"
        ttk.Label(app_info_labelframe, text=LAST_UPDATED_DATE, style="SettingLabel.TLabel", foreground=self.app_instance.colors["text_dark"]).grid(row=1, column=1, sticky="w", padx=10, pady=5)


        action_settings_frame = ttk.Frame(self, style="Panel.TFrame", padding=(20, 15))
        action_settings_frame.grid(row=3, column=0, pady=(20, 0), sticky="ew", padx=20)
        action_settings_frame.grid_columnconfigure(0, weight=1)

        ttk.Button(action_settings_frame, text="Salvar Configurações", command=self.save_settings, style="TButton").grid(row=0, column=0, padx=8, sticky="ew")
        # CORREÇÃO AQUI: Usando "text_dark" para o status label inicial
        self.settings_status_label = ttk.Label(action_settings_frame, text="", style="LabelField.TLabel", foreground=self.app_instance.colors["text_dark"])
        self.settings_status_label.grid(row=1, column=0, pady=(5, 0), sticky="ew")

    def _load_settings_into_ui(self):
        """Carrega as configurações salvas nos campos da UI desta aba."""
        current_config = self.service.config
        self.report_date_format_var.set(current_config.get("report_date_format", "%d/%m/%Y"))

    def save_settings(self):
        """Salva as configurações inseridas pelo usuário."""
        new_config = {
            "report_date_format": self.report_date_format_var.get(),
        }

        success, message = self.service.save_config(new_config)
        if success:
            messagebox.showinfo("Configurações", message)
            self.settings_status_label.config(text=message, foreground=self.app_instance.colors["success_color"])
        else:
            messagebox.showerror("Configurações", message)
            self.settings_status_label.config(text=message, foreground=self.app_instance.colors["error_color"])