# insulin_calculator_tab_ui.py

from tkinter import StringVar, messagebox, ttk
from tooltip import ToolTip

class InsulinCalculatorTabUI(ttk.Frame):
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

        ttk.Label(self, text="Calculadora de Insulina", style="Heading.TLabel").grid(row=0, column=0, pady=(15, 20), sticky="ew", padx=20)

        input_frame = ttk.Frame(self, style="Panel.TFrame", padding=(20, 15))
        input_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        input_frame.grid_columnconfigure(0, weight=1)
        input_frame.grid_columnconfigure(1, weight=1)

        self.vars = {
            "carbs": StringVar(),
            "glicemia_atual": StringVar(),
            "glicemia_alvo": StringVar(),
            "carb_ratio": StringVar(),
            "fsi": StringVar()
        }

        labels_texts = {
            "carbs": "Carboidratos (g):",
            "glicemia_atual": "Glicemia Atual (mg/dL):",
            "glicemia_alvo": "Glicemia Alvo (mg/dL):",
            "carb_ratio": "Relação Carboidrato/Insulina (g/UI):",
            "fsi": "Fator de Sensibilidade à Insulina (mg/dL/UI):"
        }

        row_idx = 0
        for key, text in labels_texts.items():
            ttk.Label(input_frame, text=text, style="TLabel").grid(row=row_idx, column=0, sticky="w", pady=5, padx=10)
            entry = ttk.Entry(input_frame, textvariable=self.vars[key], width=15)
            entry.grid(row=row_idx, column=1, sticky="ew", pady=5, padx=10)
            row_idx += 1

        self.result_var = StringVar()
        self.result_label = ttk.Label(self, textvariable=self.result_var, style="Result.TLabel")
        self.result_label.grid(row=2, column=0, pady=(10, 20), sticky="ew", padx=20)

        button_frame = ttk.Frame(self, style="Panel.TFrame", padding=(20, 15))
        button_frame.grid(row=3, column=0, pady=(0, 20), sticky="ew", padx=20)
        button_frame.grid_columnconfigure((0, 1), weight=1)

        ttk.Button(button_frame, text="Calcular", command=self._calculate_insulin, style="TButton").grid(row=0, column=0, padx=8, sticky="ew")
        ttk.Button(button_frame, text="Limpar", command=self._clear_fields, style="TButton").grid(row=0, column=1, padx=8, sticky="ew")

    def _validate_input(self, value_str, field_name):
        if not value_str:
            return None, f"O campo '{field_name}' não pode estar vazio."
        try:
            value = float(value_str.replace(",", "."))
            if value <= 0 and field_name not in ["Glicemia Alvo (mg/dL)"]:
                return None, f"O campo '{field_name}' deve ser um número positivo."
            return value, None
        except ValueError:
            return None, f"O campo '{field_name}' deve ser um número válido."

    def _calculate_insulin(self):
        carbs, err = self._validate_input(self.vars["carbs"].get(), "Carboidratos (g)")
        if err: return messagebox.showerror("Erro de Entrada", err)
        glicemia_atual, err = self._validate_input(self.vars["glicemia_atual"].get(), "Glicemia Atual (mg/dL)")
        if err: return messagebox.showerror("Erro de Entrada", err)
        glicemia_alvo, err = self._validate_input(self.vars["glicemia_alvo"].get(), "Glicemia Alvo (mg/dL)")
        if err: return messagebox.showerror("Erro de Entrada", err)
        carb_ratio, err = self._validate_input(self.vars["carb_ratio"].get(), "Relação Carboidrato/Insulina")
        if err: return messagebox.showerror("Erro de Entrada", err)
        fsi, err = self._validate_input(self.vars["fsi"].get(), "Fator de Sensibilidade à Insulina")
        if err: return messagebox.showerror("Erro de Entrada", err)

        if carb_ratio == 0 or fsi == 0:
            messagebox.showerror("Erro de Cálculo", "Relação Carboidrato/Insulina e FSI não podem ser zero.")
            return

        bolus_carbs = carbs / carb_ratio
        bolus_correcao = (glicemia_atual - glicemia_alvo) / fsi

        total_insulina = bolus_carbs + bolus_correcao

        self.result_var.set(f"Insulina Total Necessária: {total_insulina:.1f} UI\n"
                            f"(Bolus Carboidratos: {bolus_carbs:.1f} UI, Bolus Correção: {bolus_correcao:.1f} UI)")

    def _clear_fields(self):
        for var in self.vars.values():
            var.set("")
        self.result_var.set("")