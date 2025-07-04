# carb_tracker_app.py

import datetime as dt
from pathlib import Path
from tkinter import Tk, Label, Entry, Button, StringVar, ttk, messagebox, filedialog, Toplevel, Canvas
import tkinter.font as tkFont

from tkcalendar import DateEntry

from carb_tracker_service import CarbTrackerService
from pdf_report_generator import PdfReportGenerator
from constants import MEALS, FIELDS, FIELD_NAMES_MAP, DB_FILE, CONFIG_FILE, APP_VERSION, LAST_UPDATED_DATE
from tooltip import ToolTip

class CarbTrackerApp(Tk):
    def __init__(self):
        super().__init__()
        self.title("Carb Tracker")
        self.geometry("700x700")
        self.service = CarbTrackerService(db_path=DB_FILE, config_path=CONFIG_FILE)

        self.style = ttk.Style(self)
        self.style.theme_use("clam")

        self.colors = {
            "background": "#F8F8F8",
            "panel_bg": "#FFFFFF",
            "border_color": "#E0E0E0",
            "text_primary": "#333333",
            "text_secondary": "#666666",
            "accent_color": "#007BFF",
            "accent_hover": "#0056B3",
            "success_color": "#28A745",
            "warning_color": "#FFC107",
            "error_color": "#DC3545",
        }

        self.configure(bg=self.colors["background"])

        self.base_font = ("Segoe UI", 10, "normal")
        self.button_font = ("Segoe UI", 10, "bold")
        self.label_font = ("Segoe UI", 10, "bold")
        self.heading_font = ("Segoe UI", 14, "bold")
        self.sub_heading_font = ("Segoe UI", 12, "bold")
        self.data_font = ("Segoe UI", 10, "normal")
        self.totals_font = ("Segoe UI", 11, "bold")

        self.apply_styles()

        self.today_str = dt.date.today().isoformat()
        self.data_modified = False 

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(expand=True, fill="both", padx=10, pady=10)

        self.daily_entry_tab = ttk.Frame(self.notebook, style="Panel.TFrame")
        self.reports_tab = ttk.Frame(self.notebook, style="Panel.TFrame")
        self.backup_tab = ttk.Frame(self.notebook, style="Panel.TFrame")
        self.settings_tab = ttk.Frame(self.notebook, style="Panel.TFrame")

        self.notebook.add(self.daily_entry_tab, text="  Registro Diário  ")
        self.notebook.add(self.reports_tab, text="  Relatórios  ")
        self.notebook.add(self.backup_tab, text="  Backup  ")
        self.notebook.add(self.settings_tab, text="  Configurações  ")

        self._build_daily_entry_tab()
        self._build_reports_tab()
        self._build_backup_tab()
        self._build_settings_tab()

        self.protocol("WM_DELETE_WINDOW", self.ask_quit) 

        self.load_day_data(self.today_str)
        self._load_settings_into_ui()

    def apply_styles(self):
        self.style.configure("TLabel", font=self.base_font, background=self.colors["panel_bg"], foreground=self.colors["text_primary"])
        self.style.configure("TButton", font=self.button_font, background=self.colors["accent_color"], foreground="#FFFFFF", relief="flat", borderwidth=0, padding=(8, 5))
        self.style.map("TButton",
                       background=[('active', self.colors["accent_hover"])],
                       foreground=[('active', '#FFFFFF')])
        
        self.style.configure("TEntry", font=self.data_font, fieldbackground=self.colors["panel_bg"], borderwidth=1, relief="flat", bordercolor=self.colors["border_color"], padding=(5,3))
        self.style.map("TEntry", fieldbackground=[('focus', '#FFFFFF')])

        self.style.configure("TNotebook", background=self.colors["background"], borderwidth=0)
        self.style.configure("TNotebook.Tab", background=self.colors["background"], foreground=self.colors["text_secondary"], font=self.label_font, padding=[10, 5])
        self.style.map("TNotebook.Tab", background=[("selected", self.colors["accent_color"])], foreground=[("selected", "#FFFFFF")])
        
        self.style.configure("Panel.TFrame", background=self.colors["panel_bg"], borderwidth=1, relief="flat", bordercolor=self.colors["border_color"])

        self.style.configure("Heading.TLabel", font=self.heading_font, background=self.colors["panel_bg"], foreground=self.colors["text_primary"])
        self.style.configure("SubHeading.TLabel", font=self.sub_heading_font, background=self.colors["panel_bg"], foreground=self.colors["text_secondary"])
        self.style.configure("LabelField.TLabel", font=self.label_font, background=self.colors["panel_bg"], foreground=self.colors["text_secondary"])
        
        self.style.configure("DateNav.TFrame", background=self.colors["background"], borderwidth=0, relief="flat", padding=(8,5))
        self.style.configure("DateNav.TButton", font=self.button_font, background=self.colors["accent_color"], foreground="#FFFFFF", width=3, relief="flat")
        self.style.map("DateNav.TButton", background=[('active', self.colors["accent_hover"])])

        self.style.configure("Table.Header.TLabel", font=self.label_font, background=self.colors["background"], foreground=self.colors["text_primary"], anchor="center", padding=(5,5))
        
        self.style.configure("MealName.TLabel", font=("Segoe UI", 12, "bold"), foreground=self.colors["text_primary"], background=self.colors["panel_bg"])
        self.style.configure("MealNameAlt.TLabel", font=("Segoe UI", 12, "bold"), foreground=self.colors["text_primary"], background=self.colors["background"])

        self.style.configure("MealRow.TLabel", font=self.base_font, foreground=self.colors["text_primary"], background=self.colors["panel_bg"])
        self.style.configure("MealRowAlt.TLabel", font=self.base_font, foreground=self.colors["text_primary"], background=self.colors["background"])
        self.style.configure("MealRow.TFrame", background=self.colors["panel_bg"])
        self.style.configure("MealRowAlt.TFrame", background=self.colors["background"])

        self.style.configure("Glargina.TLabel", font=self.label_font, foreground=self.colors["text_primary"], background=self.colors["panel_bg"])
        
        self.style.configure("Totals.TLabel", font=self.totals_font, foreground=self.colors["text_primary"], background=self.colors["background"], borderwidth=1, relief="solid", bordercolor=self.colors["border_color"], padding=(15, 15), anchor="center")

        self.style.configure("MealSection.TLabel", font=self.label_font, foreground=self.colors["text_secondary"], background=self.colors["panel_bg"])
        self.style.configure("MealSection.TLabelframe", background=self.colors["panel_bg"], borderwidth=1, relief="solid", bordercolor=self.colors["border_color"])
        self.style.configure("MealSection.TLabelframe.Label", background=self.colors["panel_bg"], foreground=self.colors["text_primary"])

        self.style.configure("MealFieldHeader.TLabel", font=self.base_font, foreground=self.colors["text_secondary"], background=self.colors["panel_bg"], anchor="center")

        self.style.configure("Exit.TButton", background=self.colors["error_color"], foreground="#FFFFFF")
        self.style.map("Exit.TButton",
                       background=[('active', "#B00020")],
                       foreground=[('active', '#FFFFFF')])
        self.style.configure("SettingSection.TLabelframe", background=self.colors["panel_bg"], borderwidth=1, relief="solid", bordercolor=self.colors["border_color"])
        self.style.configure("SettingSection.TLabelframe.Label", background=self.colors["panel_bg"], foreground=self.colors["text_primary"])
        self.style.configure("SettingLabel.TLabel", font=self.base_font, background=self.colors["panel_bg"], foreground=self.colors["text_primary"])


    def _build_daily_entry_tab(self):
        self.daily_entry_tab.grid_columnconfigure(0, weight=1)
        self.daily_entry_tab.grid_rowconfigure(0, weight=0)
        self.daily_entry_tab.grid_rowconfigure(1, weight=0)
        self.daily_entry_tab.grid_rowconfigure(2, weight=0)
        self.daily_entry_tab.grid_rowconfigure(3, weight=1)
        self.daily_entry_tab.grid_rowconfigure(4, weight=0)

        ttk.Label(self.daily_entry_tab, text="Registro Diário de Consumo", style="Heading.TLabel").grid(row=0, column=0, pady=(15, 20), sticky="ew", padx=20)

        self._create_date_navigation_frame(self.daily_entry_tab, 1)
        self._create_glargina_entry_frame(self.daily_entry_tab, 2)
        self._create_meal_entry_sections(self.daily_entry_tab, 3)
        self._create_action_buttons_frame(self.daily_entry_tab, 4)

    def _create_date_navigation_frame(self, parent, row):
        date_nav_frame = ttk.Frame(parent, style="DateNav.TFrame")
        date_nav_frame.grid(row=row, column=0, sticky="ew", pady=(0, 20), padx=20)
        date_nav_frame.grid_columnconfigure(0, weight=1)
        date_nav_frame.grid_columnconfigure(1, weight=0)
        date_nav_frame.grid_columnconfigure(2, weight=0)
        date_nav_frame.grid_columnconfigure(3, weight=0)
        date_nav_frame.grid_columnconfigure(4, weight=0)
        date_nav_frame.grid_columnconfigure(5, weight=1)

        btn_prev = ttk.Button(date_nav_frame, text="<", style="DateNav.TButton", command=self.go_to_previous_day)
        btn_prev.grid(row=0, column=1, padx=(0, 8))
        ToolTip(btn_prev, "Dia Anterior")
        
        ttk.Label(date_nav_frame, text="Data:").grid(row=0, column=2, padx=(0, 8))
        
        self.date_entry = DateEntry(
            date_nav_frame,
            width=10,
            background="darkblue",
            foreground="white",
            borderwidth=0,
            date_pattern="dd/mm/yyyy",
            font=self.data_font,
            command=self._on_date_selected_from_calendar
        )
        self.date_entry.grid(row=0, column=3, sticky="ew", padx=(8, 8))

        btn_next = ttk.Button(date_nav_frame, text=">", style="DateNav.TButton", command=self.go_to_next_day)
        btn_next.grid(row=0, column=4, padx=(8, 0))
        ToolTip(btn_next, "Próximo Dia")

    def _create_glargina_entry_frame(self, parent, row):
        glargina_frame = ttk.Frame(parent, style="Panel.TFrame", padding=(15, 10))
        glargina_frame.grid(row=row, column=0, sticky="ew", pady=(0, 25), padx=20)
        glargina_frame.grid_columnconfigure(0, weight=0)
        glargina_frame.grid_columnconfigure(1, weight=1)
        
        ttk.Label(glargina_frame, text="Insulina Glargina (UI):", style="Glargina.TLabel").grid(row=0, column=0, sticky="w", padx=10)
        self.glargina_var = StringVar()
        self.glargina_entry = ttk.Entry(glargina_frame, textvariable=self.glargina_var, width=8)
        self.glargina_entry.grid(row=0, column=1, sticky="w", padx=10)
        ToolTip(self.glargina_entry, "Dose de Insulina Glargina (longa duração)")
        self.glargina_var.trace_add("write", self._on_data_change)

    def _create_meal_entry_sections(self, parent, row):
        scroll_frame = ttk.Frame(parent, style="Panel.TFrame")
        scroll_frame.grid(row=row, column=0, sticky="nsew", padx=20, pady=(0, 20))
        scroll_frame.grid_columnconfigure(0, weight=1)
        scroll_frame.grid_rowconfigure(0, weight=1)

        self.meals_canvas = Canvas(scroll_frame, background=self.colors["panel_bg"], highlightthickness=0)
        self.meals_canvas.grid(row=0, column=0, sticky="nsew")

        meals_scrollbar = ttk.Scrollbar(scroll_frame, orient="vertical", command=self.meals_canvas.yview)
        meals_scrollbar.grid(row=0, column=1, sticky="ns")

        self.meals_canvas.configure(yscrollcommand=meals_scrollbar.set)
        
        self.meals_canvas.bind('<Configure>', self._on_canvas_configure)
        
        self.meals_sections_container = ttk.Frame(self.meals_canvas, style="Panel.TFrame")
        self.meals_canvas_window = self.meals_canvas.create_window((0, 0), window=self.meals_sections_container, anchor="nw", tags="meals_frame")
        
        self.meals_sections_container.grid_columnconfigure(0, weight=1)

        self.entries = {}
        for row_idx, meal in enumerate(MEALS):
            meal_labelframe = ttk.LabelFrame(self.meals_sections_container, style="MealSection.TLabelframe")
            meal_labelframe.grid(row=row_idx, column=0, sticky="ew", pady=(5, 5), padx=5)
            
            bg_style = "MealRow.TFrame" if row_idx % 2 == 0 else "MealRowAlt.TFrame"
            meal_labelframe.configure(style=bg_style)

            ttk.Label(meal_labelframe, text=meal + ":", style="MealName.TLabel" if row_idx % 2 == 0 else "MealNameAlt.TLabel").grid(row=0, column=0, sticky="w", padx=10, rowspan=2)

            meal_labelframe.grid_columnconfigure(0, weight=0, minsize=100)
            
            for i in range(len(FIELDS)):
                meal_labelframe.grid_columnconfigure(i + 1, weight=1, minsize=70)
            
            for col_idx, (title, _) in enumerate(FIELDS):
                ttk.Label(meal_labelframe, text=title.split(" ")[0], style="MealFieldHeader.TLabel").grid(row=0, column=col_idx+1, padx=5, pady=5, sticky="ew")

            meal_vars = {}
            for col_idx, (_, key) in enumerate(FIELDS):
                var = StringVar()
                entry = ttk.Entry(meal_labelframe, textvariable=var, width=8)
                entry.grid(row=1, column=col_idx+1, pady=3, padx=5, sticky="ew")
                meal_vars[key] = var
                var.trace_add("write", self._on_data_change)
            self.entries[meal] = meal_vars

        self.bind_all("<MouseWheel>", self._on_mousewheel)
        self.bind_all("<Button-4>", self._on_mousewheel)
        self.bind_all("<Button-5>", self._on_mousewheel)

    def _create_action_buttons_frame(self, parent, row):
        action_button_frame = ttk.Frame(parent, style="Panel.TFrame", padding=(20, 15))
        action_button_frame.grid(row=row, column=0, pady=(20, 0), sticky="ew", padx=20)
        action_button_frame.grid_columnconfigure((0,1,2,3), weight=1)

        ttk.Button(action_button_frame, text="Salvar Dia", command=self.save_day, style="TButton").grid(row=0, column=0, padx=8, sticky="ew")
        ttk.Button(action_button_frame, text="Limpar Campos", command=self.clear_inputs, style="TButton").grid(row=0, column=1, padx=8, sticky="ew")
        ttk.Button(action_button_frame, text="Carregar Dia", command=self.load_current_date_data, style="TButton").grid(row=0, column=2, padx=8, sticky="ew")
        ttk.Button(action_button_frame, text="Sair", command=self.ask_quit, style="Exit.TButton").grid(row=0, column=3, padx=8, sticky="ew")

    def _build_reports_tab(self):
        self.reports_tab.grid_columnconfigure(0, weight=1)
        self.reports_tab.grid_rowconfigure(0, weight=0)
        self.reports_tab.grid_rowconfigure(1, weight=0)
        self.reports_tab.grid_rowconfigure(2, weight=0)
        self.reports_tab.grid_rowconfigure(3, weight=1)

        ttk.Label(self.reports_tab, text="Relatórios e Totais", style="Heading.TLabel").grid(row=0, column=0, pady=(15, 20), sticky="ew", padx=20)

        self._create_report_filters_frame(self.reports_tab, 1)

        self._create_report_buttons_frame(self.reports_tab, 2)
        self._create_totals_display_frame(self.reports_tab, 3)

    def _create_report_filters_frame(self, parent, row):
        filter_date_frame = ttk.Frame(parent, style="DateNav.TFrame")
        filter_date_frame.grid(row=row, column=0, sticky="ew", pady=(0, 20), padx=20)
        filter_date_frame.grid_columnconfigure(0, weight=0)
        filter_date_frame.grid_columnconfigure(1, weight=1)
        filter_date_frame.grid_columnconfigure(2, weight=0)
        filter_date_frame.grid_columnconfigure(3, weight=1)

        ttk.Label(filter_date_frame, text="Início:").grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.start_date_entry = DateEntry(
            filter_date_frame,
            width=10,
            background="darkblue",
            foreground="white",
            borderwidth=0,
            date_pattern="dd/mm/yyyy",
            font=self.data_font
        )
        self.start_date_entry.grid(row=0, column=1, sticky="ew", padx=(0, 12))

        ttk.Label(filter_date_frame, text="Fim:").grid(row=0, column=2, sticky="w", padx=(0, 8))
        self.end_date_entry = DateEntry(
            filter_date_frame,
            width=10,
            background="darkblue",
            foreground="white",
            borderwidth=0,
            date_pattern="dd/mm/yyyy",
            font=self.data_font
        )
        self.end_date_entry.grid(row=0, column=3, sticky="ew")

    def _create_report_buttons_frame(self, parent, row):
        report_button_frame = ttk.Frame(parent, style="Panel.TFrame", padding=(15, 10))
        report_button_frame.grid(row=row, column=0, pady=(15, 20), sticky="ew", padx=20)
        report_button_frame.grid_columnconfigure(0, weight=1)
        report_button_frame.grid_columnconfigure(1, weight=1)

        ttk.Button(report_button_frame, text="Calcular Totais", command=self.calculate_totals, style="TButton").grid(row=0, column=0, padx=8, sticky="ew")
        ttk.Button(report_button_frame, text="Gerar PDF", command=self.generate_pdf, style="TButton").grid(row=0, column=1, padx=8, sticky="ew")

    def _create_totals_display_frame(self, parent, row):
        totals_display_frame = ttk.Frame(parent, style="Panel.TFrame")
        totals_display_frame.grid(row=row, column=0, sticky="nsew", pady=(15, 0), padx=20)
        totals_display_frame.grid_columnconfigure(0, weight=1)
        self.reports_tab.grid_rowconfigure(row, weight=1)

        self.total_label = ttk.Label(totals_display_frame, text="", justify="left", style="Totals.TLabel")
        self.total_label.pack(fill="both", expand=True)

    def _build_backup_tab(self):
        self.backup_tab.grid_columnconfigure(0, weight=1)
        self.backup_tab.grid_rowconfigure(0, weight=0)
        self.backup_tab.grid_rowconfigure(1, weight=1)
        self.backup_tab.grid_rowconfigure(2, weight=0)

        ttk.Label(self.backup_tab, text="Backup do Banco de Dados", style="Heading.TLabel").grid(row=0, column=0, pady=(15, 20), sticky="ew", padx=20)

        backup_frame = ttk.Frame(self.backup_tab, style="Panel.TFrame", padding=(20, 20))
        backup_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        backup_frame.grid_columnconfigure(0, weight=1)
        backup_frame.grid_columnconfigure(1, weight=1)

        ttk.Label(backup_frame, text="Selecione um local para salvar o backup do banco de dados:",
                  style="LabelField.TLabel", wraplength=400).grid(row=0, column=0, columnspan=2, pady=(0, 15), sticky="ew")

        ttk.Button(backup_frame, text="Criar Backup", command=self.create_backup, style="TButton").grid(row=1, column=0, padx=5, pady=10, sticky="ew")
        ttk.Button(backup_frame, text="Restaurar Backup", command=self.restore_backup, style="TButton").grid(row=1, column=1, padx=5, pady=10, sticky="ew")

        self.backup_status_label = ttk.Label(self.backup_tab, text="", style="LabelField.TLabel", foreground=self.colors["text_primary"])
        self.backup_status_label.grid(row=2, column=0, pady=(10, 15), sticky="ew", padx=20)

    def _build_settings_tab(self):
        self.settings_tab.grid_columnconfigure(0, weight=1)
        self.settings_tab.grid_rowconfigure(0, weight=0)
        self.settings_tab.grid_rowconfigure(1, weight=0) # Linha para as configurações de relatório
        self.settings_tab.grid_rowconfigure(2, weight=0) # Linha para o local do DB
        self.settings_tab.grid_rowconfigure(3, weight=1) # Nova linha para informações do app (ocupa o espaço restante)
        self.settings_tab.grid_rowconfigure(4, weight=0) # Linha para o botão salvar e status

        ttk.Label(self.settings_tab, text="Configurações do Aplicativo", style="Heading.TLabel").grid(row=0, column=0, pady=(15, 20), sticky="ew", padx=20)

        settings_frame = ttk.Frame(self.settings_tab, style="Panel.TFrame", padding=(20, 20))
        settings_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 20))
        settings_frame.grid_columnconfigure(0, weight=0)
        settings_frame.grid_columnconfigure(1, weight=1)

        # Seção de Configurações de Relatório
        report_settings_labelframe = ttk.LabelFrame(settings_frame, text="Relatórios", style="SettingSection.TLabelframe")
        report_settings_labelframe.grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=10)
        report_settings_labelframe.grid_columnconfigure(1, weight=1)

        ttk.Label(report_settings_labelframe, text="Formato de Data para PDF:", style="SettingLabel.TLabel").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        self.report_date_format_var = StringVar()
        self.report_date_format_entry = ttk.Entry(report_settings_labelframe, textvariable=self.report_date_format_var, width=15)
        self.report_date_format_entry.grid(row=0, column=1, sticky="ew", padx=10, pady=5)
        ToolTip(self.report_date_format_entry, "Ex: %d/%m/%Y para 01/01/2023, %Y-%m-%d para 2023-01-01")

        # Seção de Local do Banco de Dados
        db_location_labelframe = ttk.LabelFrame(settings_frame, text="Local do Banco de Dados", style="SettingSection.TLabelframe")
        db_location_labelframe.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=10)
        db_location_labelframe.grid_columnconfigure(0, weight=1)

        ttk.Label(db_location_labelframe, text="Caminho atual:", style="SettingLabel.TLabel").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        self.current_db_path_label = ttk.Label(db_location_labelframe, text=DB_FILE, style="SettingLabel.TLabel", foreground=self.colors["text_secondary"], wraplength=400)
        self.current_db_path_label.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        
        # NOVA SEÇÃO: Informações sobre o Aplicativo
        app_info_labelframe = ttk.LabelFrame(settings_frame, text="Sobre o Aplicativo", style="SettingSection.TLabelframe")
        app_info_labelframe.grid(row=2, column=0, columnspan=2, sticky="ew", padx=5, pady=10)
        app_info_labelframe.grid_columnconfigure(1, weight=1)

        ttk.Label(app_info_labelframe, text="Versão:", style="SettingLabel.TLabel").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        ttk.Label(app_info_labelframe, text=APP_VERSION, style="SettingLabel.TLabel", foreground=self.colors["text_secondary"]).grid(row=0, column=1, sticky="w", padx=10, pady=5)

        ttk.Label(app_info_labelframe, text="Última Atualização:", style="SettingLabel.TLabel").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        ttk.Label(app_info_labelframe, text=LAST_UPDATED_DATE, style="SettingLabel.TLabel", foreground=self.colors["text_secondary"]).grid(row=1, column=1, sticky="w", padx=10, pady=5)


        # Botão Salvar Configurações
        action_settings_frame = ttk.Frame(self.settings_tab, style="Panel.TFrame", padding=(20, 15))
        action_settings_frame.grid(row=4, column=0, pady=(20, 0), sticky="ew", padx=20)
        action_settings_frame.grid_columnconfigure(0, weight=1)

        ttk.Button(action_settings_frame, text="Salvar Configurações", command=self.save_settings, style="TButton").grid(row=0, column=0, padx=8, sticky="ew")
        self.settings_status_label = ttk.Label(action_settings_frame, text="", style="LabelField.TLabel", foreground=self.colors["text_primary"])
        self.settings_status_label.grid(row=1, column=0, pady=(5, 0), sticky="ew")

    def _load_settings_into_ui(self):
        """Carrega as configurações salvas nos campos da UI da aba de configurações."""
        current_config = self.service.config
        self.report_date_format_var.set(current_config.get("report_date_format", "%d/%m/%Y"))
        
        db_path_to_display_raw = self.service.get_config("db_location_override")
        if db_path_to_display_raw is None:
            db_path_to_display = DB_FILE
        else:
            db_path_to_display = db_path_to_display_raw

        self.current_db_path_label.config(text=f"Caminho atual: {Path(db_path_to_display).resolve()}")
        
        # Define as datas de início e fim nas DateEntry na aba de Relatórios
        # para um período padrão (ex: últimos 30 dias) ao iniciar o app.
        today = dt.date.today()
        default_report_start_date = today - dt.timedelta(days=29) 
        self.start_date_entry.set_date(default_report_start_date)
        self.end_date_entry.set_date(today)


    def save_settings(self):
        """Salva as configurações inseridas pelo usuário."""
        new_config = {
            "report_date_format": self.report_date_format_var.get(),
        }

        success, message = self.service.save_config(new_config)
        if success:
            messagebox.showinfo("Configurações", message)
            self.settings_status_label.config(text=message, foreground=self.colors["success_color"])
        else:
            messagebox.showerror("Configurações", message)
            self.settings_status_label.config(text=message, foreground=self.colors["error_color"])
    
    def _on_canvas_configure(self, event):
        canvas_width = event.width
        self.meals_canvas.itemconfig(self.meals_canvas_window, width=canvas_width)
        self.meals_canvas.configure(scrollregion=self.meals_canvas.bbox("all"))

    def _on_mousewheel(self, event):
        if event.delta:
            self.meals_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        elif event.num == 4:
            self.meals_canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.meals_canvas.yview_scroll(1, "units")

    def _on_date_selected_from_calendar(self):
        if not self._confirm_save_if_modified():
            return
        selected_date_obj = self.date_entry.get_date()
        self.load_day_data(selected_date_obj.isoformat())

    def load_current_date_data(self):
        if not self._confirm_save_if_modified():
            return
        date_str_br = self.date_entry.get().strip()
        try:
            date_obj = dt.datetime.strptime(date_str_br, "%d/%m/%Y").date()
            self.load_day_data(date_obj.isoformat())
        except ValueError:
            messagebox.showerror("Data inválida", f"Data inválida: {date_str_br}. Use DD/MM/AAAA.")

    def go_to_previous_day(self):
        if not self._confirm_save_if_modified():
            return
        current_date_obj = self.date_entry.get_date()
        previous_day_obj = current_date_obj - dt.timedelta(days=1)
        self.load_day_data(previous_day_obj.isoformat())

    def go_to_next_day(self):
        if not self._confirm_save_if_modified():
            return
        current_date_obj = self.date_entry.get_date()
        next_day_obj = current_date_obj + dt.timedelta(days=1)
        self.load_day_data(next_day_obj.isoformat())

    def _on_data_change(self, *args):
        """Callback chamado quando qualquer StringVar é modificado."""
        self.data_modified = True

    def _confirm_save_if_modified(self) -> bool:
        """
        Verifica se os dados foram modificados e pergunta ao usuário se ele quer salvar.
        Retorna True se o usuário prosseguir (salvou ou descartou), False se ele cancelar.
        """
        if self.data_modified:
            response = messagebox.askyesnocancel(
                "Dados não salvos",
                "Você tem dados não salvos para o dia atual. Deseja salvá-los antes de continuar?"
            )
            if response is True: # Usuário clicou em Sim (quer salvar)
                self.save_day()
                return True # Prossegue após salvar
            elif response is False: # Usuário clicou em Não (não quer salvar, quer descartar)
                self.data_modified = False # Desativa a flag pois os dados serão descartados
                return True # Prossegue descartando as mudanças
            else: # Usuário clicou em Cancelar (None)
                return False # Não prossegue
        return True # Nenhuma modificação, pode prosseguir

    def load_day_data(self, date_str_iso: str):
        self.clear_inputs()
        try:
            self.date_entry.set_date(dt.date.fromisoformat(date_str_iso))
        except ValueError:
            messagebox.showerror("Erro de Data", f"Não foi possível carregar dados para a data: {date_str_iso}")
            return
        
        glargina_dose, meal_data = self.service.get_daily_data(date_str_iso)
        self.glargina_var.set(f"{glargina_dose:.1f}" if glargina_dose is not None else "")

        for meal in MEALS:
            data = meal_data.get(meal, {key: None for _, key in FIELDS})
            for key, var in self.entries[meal].items():
                value = data.get(key)
                var.set(f"{value:.1f}" if value is not None else "")
        
        self.data_modified = False

    def save_day(self):
        date_str_iso = self.date_entry.get_date().isoformat()
        
        glargina_text = self.glargina_var.get().strip()
        is_valid_glargina, glargina_value, error_msg = self.service.validate_numeric_input(glargina_text, "glargina")
        if not is_valid_glargina:
            messagebox.showerror("Erro de Entrada", error_msg)
            return

        meal_entries_data = {}
        for meal in MEALS:
            meal_values = {}
            vars_ = self.entries[meal]
            for key, var in vars_.items():
                text = var.get().strip()
                is_valid, value, error_msg = self.service.validate_numeric_input(text, key, meal)
                if not is_valid:
                    messagebox.showerror("Erro de Entrada", error_msg)
                    return
                meal_values[key] = value
            meal_entries_data[meal] = meal_values

        success, msg = self.service.save_daily_data(date_str_iso, glargina_value or 0.0, meal_entries_data)
        if success:
            messagebox.showinfo("Salvo", msg)
            self.data_modified = False
        else:
            messagebox.showerror("Erro ao Salvar", msg)

    def clear_inputs(self):
        for vars_ in self.entries.values():
            for var in vars_.values():
                var.set("")
        self.glargina_var.set("")
        self.data_modified = False

    def calculate_totals(self):
        start_date_obj = self.start_date_entry.get_date()
        end_date_obj = self.end_date_entry.get_date()

        start_iso = start_date_obj.isoformat()
        end_iso = end_date_obj.isoformat()

        totals = self.service.calculate_period_totals(start_iso, end_iso)

        if not any(totals[k] > 0 for k in ["carbs", "glicemia_sum", "lispro", "bolus", "glargina_sum"]):
            self.total_label.config(text="Não há registros para o período informado.")
            return

        date_format = self.service.get_config("report_date_format", "%d/%m/%Y")
        msg = (
            f"Período {start_date_obj.strftime(date_format)} a {end_date_obj.strftime(date_format)}:\n"
            f"  • <b>Carboidratos totais</b>: {totals['carbs']:.1f} g\n"
            f"  • <b>Glicemia média</b>: {totals['avg_glicemia']:.1f} mg/dL\n"
            f"  • <b>Insulina Lispro total</b>: {totals['lispro']:.1f} UI\n"
            f"  • <b>Insulina Glargina média diária</b>: {totals['avg_glargina']:.1f} UI\n"
            f"  • <b>Bolus correção total</b>: {totals['bolus']:.1f} UI"
        )
        self.total_label.config(text=msg)

    def generate_pdf(self):
        start_date_obj = self.start_date_entry.get_date()
        end_date_obj = self.end_date_entry.get_date()

        start_iso = start_date_obj.isoformat()
        end_iso = end_date_obj.isoformat()

        rows, glargina_by_date = self.service.get_report_data_for_pdf(start_iso, end_iso)

        if not rows and not glargina_by_date:
            messagebox.showwarning("Sem dados", "Não há registros para o período informado.")
            return
            
        path = filedialog.asksaveasfilename(
            defaultextension=".pdf", filetypes=[("PDF", "*.pdf")]
        )
        if not path:
            return
        
        date_format = self.service.get_config("report_date_format", "%d/%m/%Y")
        PdfReportGenerator.generate_report(
            path,
            start_date_obj.strftime(date_format),
            end_date_obj.strftime(date_format),
            rows,
            glargina_by_date
        )
        messagebox.showinfo("PDF gerado", f"Relatório salvo em:\n{path}")

    def create_backup(self):
        if self._confirm_save_if_modified():
            try:
                backup_path = filedialog.asksaveasfilename(
                    defaultextension=".db",
                    filetypes=[("Database files", "*.db"), ("All files", "*.*")],
                    initialfile=f"carb_tracker_backup_{dt.date.today().isoformat()}.db",
                    title="Salvar backup do banco de dados como"
                )
                if backup_path:
                    success, message = self.service.create_backup(DB_FILE, backup_path)
                    if success:
                        messagebox.showinfo("Backup Criado", message)
                        self.backup_status_label.config(text=f"Último backup: {Path(backup_path).name} em {dt.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", foreground=self.colors["success_color"])
                    else:
                        messagebox.showerror("Erro no Backup", message)
                        self.backup_status_label.config(text=f"Erro: {message}", foreground=self.colors["error_color"])
                else:
                    self.backup_status_label.config(text="Criação de backup cancelada.", foreground=self.colors["text_secondary"])
            except Exception as e:
                messagebox.showerror("Erro Inesperado", f"Ocorreu um erro inesperado ao criar o backup: {e}")
                self.backup_status_label.config(text=f"Erro inesperado: {e}", foreground=self.colors["error_color"])
        else:
            self.backup_status_label.config(text="Backup cancelado. Há dados não salvos.", foreground=self.colors["warning_color"])


    def restore_backup(self):
        if self._confirm_save_if_modified():
            response = messagebox.askyesno(
                "Confirmar Restauração",
                "Tem certeza que deseja restaurar um backup? Isso substituirá o banco de dados atual e todas as informações não salvas serão perdidas. Recomenda-se fazer um backup antes de restaurar."
            )
            if response:
                try:
                    source_backup_path = filedialog.askopenfilename(
                        filetypes=[("Database files", "*.db"), ("All files", "*.*")],
                        title="Selecionar arquivo de backup para restaurar"
                    )
                    if source_backup_path:
                        success, message = self.service.restore_backup(source_backup_path, DB_FILE)
                        if success:
                            messagebox.showinfo("Backup Restaurado", message)
                            self.backup_status_label.config(text=f"Banco de dados restaurado de {Path(source_backup_path).name} em {dt.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", foreground=self.colors["success_color"])
                            self.load_day_data(self.date_entry.get_date().isoformat())
                        else:
                            messagebox.showerror("Erro na Restauração", message)
                            self.backup_status_label.config(text=f"Erro: {message}", foreground=self.colors["error_color"])
                    else:
                        self.backup_status_label.config(text="Restauração de backup cancelada.", foreground=self.colors["text_secondary"])
                except Exception as e:
                    messagebox.showerror("Erro Inesperado", f"Ocorreu um erro inesperado ao restaurar o backup: {e}")
                    self.backup_status_label.config(text=f"Erro inesperado: {e}", foreground=self.colors["error_color"])
        else:
            self.backup_status_label.config(text="Restauração cancelada. Há dados não salvos.", foreground=self.colors["warning_color"])

    def ask_quit(self):
        # AQUI ESTÁ A CORREÇÃO
        # Se _confirm_save_if_modified() retornar True, significa que o usuário salvou ou descartou,
        # então podemos sair. Se retornar False, ele clicou em "Cancelar", e não devemos sair.
        if self._confirm_save_if_modified():
            self.on_exit()
        # else: Não precisamos de um 'else' aqui, pois se retornar False, a função simplesmente termina.

    def on_exit(self):
        self.service.close_db()
        self.destroy()

if __name__ == "__main__":
    app = CarbTrackerApp()
    app.mainloop()