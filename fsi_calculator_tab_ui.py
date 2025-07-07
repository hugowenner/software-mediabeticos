# fsi_calculator_tab_ui.py

from tkinter import StringVar, messagebox, ttk
from tooltip import ToolTip

class FSICalculatorTabUI(ttk.Frame):
    def __init__(self, master, app_instance):
        super().__init__(master, style="Panel.TFrame")
        self.app_instance = app_instance
        self._create_widgets()

    def _create_widgets(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0) # Title
        self.grid_rowconfigure(1, weight=1) # Input frame
        self.grid_rowconfigure(2, weight=0) # Result frame
        self.grid_rowconfigure(3, weight=0) # Buttons

        ttk.Label(self, text="Calculadora de FSI (Regra dos 1800)", style="Heading.TLabel").grid(row=0, column=0, pady=(15, 20), sticky="ew", padx=20)

        input_frame = ttk.Frame(self, style="Panel.TFrame", padding=(20, 15))
        input_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        input_frame.grid_columnconfigure(0, weight=1)
        input_frame.grid_columnconfigure(1, weight=1)

        self.vars = {
            "total_daily_insulin": StringVar()
        }

        ttk.Label(input_frame, text="Insulina Total Diária (UI):", style="TLabel").grid(row=0, column=0, sticky="w", pady=5, padx=10)
        entry = ttk.Entry(input_frame, textvariable=self.vars["total_daily_insulin"], width=15)
        entry.grid(row=0, column=1, sticky="ew", pady=5, padx=10)
        ToolTip(entry, "Soma de todas as doses de insulina (basal + bolus) em um dia típico.")

        self.result_var = StringVar()
        self.result_label = ttk.Label(self, textvariable=self.result_var, style="Result.TLabel")
        self.result_label.grid(row=2, column=0, pady=(10, 20), sticky="ew", padx=20)

        button_frame = ttk.Frame(self, style="Panel.TFrame", padding=(20, 15))
        button_frame.grid(row=3, column=0, pady=(0, 20), sticky="ew", padx=20)
        button_frame.grid_columnconfigure((0, 1), weight=1)

        ttk.Button(button_frame, text="Calcular FSI", command=self._calculate_fsi, style="TButton").grid(row=0, column=0, padx=8, sticky="ew")
        ttk.Button(button_frame, text="Limpar", command=self._clear_fields, style="TButton").grid(row=0, column=1, padx=8, sticky="ew")

    def _validate_input(self, value_str, field_name):
        if not value_str:
            return None, f"O campo '{field_name}' não pode estar vazio."
        try:
            value = float(value_str.replace(",", "."))
            if value <= 0:
                return None, f"O campo '{field_name}' deve ser um número positivo."
            return value, None
        except ValueError:
            return None, f"O campo '{field_name}' deve ser um número válido."

    def _calculate_fsi(self):
        total_daily_insulin, err = self._validate_input(self.vars["total_daily_insulin"].get(), "Insulina Total Diária")
        if err: return messagebox.showerror("Erro de Entrada", err)

        if total_daily_insulin == 0:
            messagebox.showerror("Erro de Cálculo", "A Insulina Total Diária não pode ser zero.")
            return

        fsi = 1800 / total_daily_insulin

        self.result_var.set(f"Fator de Sensibilidade à Insulina (FSI): {fsi:.1f} mg/dL/UI")

    def _clear_fields(self):
        for var in self.vars.values():
            var.set("")
        self.result_var.set("")