# reports_tab_ui.py

import datetime as dt
from tkinter import Tk, Label, Entry, Button, StringVar, ttk, messagebox, filedialog, Toplevel, Canvas, Text, Scrollbar
import tkinter.font as tkFont

from tkcalendar import DateEntry

from carb_tracker_service import CarbTrackerService
from pdf_report_generator import PdfReportGenerator
from constants import MEALS, FIELDS, FIELD_NAMES_MAP, DB_FILE, CONFIG_FILE, APP_VERSION, LAST_UPDATED_DATE, FIXED_MEALS, DYNAMIC_MEAL_PREFIX
from tooltip import ToolTip

class ReportsTabUI(ttk.Frame):
    def __init__(self, master, service: CarbTrackerService, app_instance):
        super().__init__(master, style="Panel.TFrame")
        self.service = service
        self.app_instance = app_instance

        self.total_label = None

        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=0)
        self.grid_rowconfigure(3, weight=1)

        ttk.Label(self, text="Relatórios e Totais", style="Heading.TLabel").grid(row=0, column=0, pady=(15, 20), sticky="ew", padx=20)

        self._create_report_filters_frame(self, 1)
        self._create_report_buttons_frame(self, 2)
        self._create_totals_display_frame(self, 3)

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
            font=self.app_instance.data_font
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
            font=self.app_instance.data_font
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
        self.grid_rowconfigure(row, weight=1)

        self.total_label = ttk.Label(totals_display_frame, text="", justify="left", style="Totals.TLabel")
        self.total_label.pack(fill="both", expand=True)

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
            f"  • Carboidratos totais: {totals['carbs']:.1f} g\n"
            f"  • Glicemia média: {totals['avg_glicemia']:.1f} mg/dL\n"
            f"  • Insulina Lispro total: {totals['lispro']:.1f} UI\n"
            f"  • Insulina Glargina média diária: {totals['avg_glargina']:.1f} UI\n"
            f"  • Bolus correção total: {totals['bolus']:.1f} UI"
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
            glargina_by_date,
        )
        messagebox.showinfo("PDF gerado", f"Relatório salvo em:\n{path}")

    def _set_default_report_dates(self):
        today = dt.date.today()
        self.start_date_entry.set_date(today)
        self.end_date_entry.set_date(today)