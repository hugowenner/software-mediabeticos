# daily_entry_tab_ui.py

import datetime as dt
from tkinter import Tk, Label, Entry, Button, StringVar, ttk, messagebox, filedialog, Toplevel, Canvas, Text, Scrollbar
import tkinter.font as tkFont

from tkcalendar import DateEntry

# Importar do seu projeto
from carb_tracker_service import CarbTrackerService
from constants import MEALS, FIELDS, FIELD_NAMES_MAP, DYNAMIC_MEAL_PREFIX, FIXED_MEALS
from tooltip import ToolTip

class DailyEntryTabUI(ttk.Frame):
    def __init__(self, master, service: CarbTrackerService, app_instance):
        super().__init__(master, style="Panel.TFrame")
        self.service = service
        self.app_instance = app_instance

        self.glargina_var = StringVar()
        self.entries = {}
        self.dynamic_meal_frames = {}
        self.dynamic_meal_counter = 0

        self.data_modified = False

        self._build_ui()
        self._set_trace_on_entries()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=0)
        self.grid_rowconfigure(3, weight=1)
        self.grid_rowconfigure(4, weight=0)

        ttk.Label(self, text="Registro Diário de Consumo", style="Heading.TLabel").grid(row=0, column=0, pady=(15, 20), sticky="ew", padx=20)
        self._create_date_navigation_frame(self, 1)
        self._create_glargina_entry_frame(self, 2)

        meal_and_add_frame = ttk.Frame(self, style="Panel.TFrame")
        meal_and_add_frame.grid(row=3, column=0, sticky="nsew", padx=20, pady=(0, 20))
        meal_and_add_frame.grid_columnconfigure(0, weight=1)
        meal_and_add_frame.grid_rowconfigure(0, weight=1)
        meal_and_add_frame.grid_rowconfigure(1, weight=0)

        self._create_meal_entry_sections(meal_and_add_frame, 0)
        self._create_add_extra_meal_button(meal_and_add_frame, 1)

        self._create_action_buttons_frame(self, 4)

    def _set_trace_on_entries(self):
        self.glargina_var.trace_add("write", self._on_data_change)

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
            font=self.app_instance.data_font,
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
        self.glargina_entry = ttk.Entry(glargina_frame, textvariable=self.glargina_var, width=8)
        self.glargina_entry.grid(row=0, column=1, sticky="w", padx=10)
        ToolTip(self.glargina_entry, "Dose de Insulina Glargina (longa duração)")

    def _create_meal_entry_sections(self, parent, row):
        scroll_frame = ttk.Frame(parent, style="Panel.TFrame")
        scroll_frame.grid(row=row, column=0, sticky="nsew", padx=0, pady=(0, 0))
        scroll_frame.grid_columnconfigure(0, weight=1)
        scroll_frame.grid_rowconfigure(0, weight=1)

        self.meals_canvas = Canvas(scroll_frame, background=self.app_instance.colors["panel_bg"], highlightthickness=0)
        self.meals_canvas.grid(row=0, column=0, sticky="nsew")

        meals_scrollbar = ttk.Scrollbar(scroll_frame, orient="vertical", command=self.meals_canvas.yview)
        meals_scrollbar.grid(row=0, column=1, sticky="ns")

        self.meals_canvas.configure(yscrollcommand=meals_scrollbar.set)

        self.meals_canvas.bind('<Configure>', self._on_canvas_configure)

        self.meals_sections_container = ttk.Frame(self.meals_canvas, style="Panel.TFrame")
        self.meals_canvas_window = self.meals_canvas.create_window((0, 0), window=self.meals_sections_container, anchor="nw", tags="meals_frame")

        self.meals_sections_container.grid_columnconfigure(0, weight=1)

        for meal in FIXED_MEALS:
            self._create_single_meal_entry_row(meal)

        self.master.bind_all("<MouseWheel>", self._on_mousewheel)
        self.master.bind_all("<Button-4>", self._on_mousewheel)
        self.master.bind_all("<Button-5>", self._on_mousewheel)

    def _create_single_meal_entry_row(self, meal_name: str, dynamic_removable: bool = False):
        """Cria uma única linha de entrada para uma refeição (fixa ou dinâmica)."""
        if meal_name in self.entries and not dynamic_removable:
             return

        row_idx = len(self.meals_sections_container.winfo_children())

        meal_labelframe = ttk.LabelFrame(self.meals_sections_container, style="MealSection.TLabelframe")
        meal_labelframe.grid(row=row_idx, column=0, sticky="ew", pady=(5, 5), padx=5)

        bg_style = "MealRow.TFrame" if row_idx % 2 == 0 else "MealRowAlt.TFrame"
        meal_labelframe.configure(style=bg_style)

        ttk.Label(meal_labelframe, text=meal_name + ":", style="MealName.TLabel" if row_idx % 2 == 0 else "MealNameAlt.TLabel").grid(row=0, column=0, sticky="w", padx=10, rowspan=2)

        meal_labelframe.grid_columnconfigure(0, weight=0, minsize=100)

        num_fields = len(FIELDS) - 1
        obs_field_idx = len(FIELDS) - 1

        for i in range(num_fields):
            meal_labelframe.grid_columnconfigure(i + 1, weight=1, minsize=70)

        meal_labelframe.grid_columnconfigure(obs_field_idx + 1, weight=3, minsize=150)

        for col_idx, (title, _) in enumerate(FIELDS):
            ttk.Label(meal_labelframe, text=title.split(" ")[0], style="MealFieldHeader.TLabel").grid(row=0, column=col_idx+1, padx=5, pady=5, sticky="ew")

        meal_vars = {}
        for col_idx, (_, key) in enumerate(FIELDS):
            var = StringVar()
            entry_width = 8 if key != "observations" else 30
            entry = ttk.Entry(meal_labelframe, textvariable=var, width=entry_width)
            entry.grid(row=1, column=col_idx+1, pady=3, padx=5, sticky="ew")
            meal_vars[key] = var
            var.trace_add("write", self._on_data_change)

        self.entries[meal_name] = meal_vars

        if dynamic_removable:
            remove_button = ttk.Button(meal_labelframe, text="X", style="Exit.TButton",
                                        command=lambda m=meal_name, f=meal_labelframe: self._remove_dynamic_meal(m, f))
            remove_button.grid(row=0, column=len(FIELDS) + 1, padx=5, pady=5, sticky="ne")
            self.dynamic_meal_frames[meal_name] = meal_labelframe

        self.meals_sections_container.update_idletasks()
        self.meals_canvas.config(scrollregion=self.meals_canvas.bbox("all"))


    def _create_add_extra_meal_button(self, parent, row):
        add_meal_frame = ttk.Frame(parent, style="Panel.TFrame", padding=(10, 5))
        add_meal_frame.grid(row=row, column=0, sticky="ew", padx=5, pady=(5,0))
        add_meal_frame.grid_columnconfigure(0, weight=1)

        ttk.Button(add_meal_frame, text="Adicionar Lanche Extra", command=self._add_new_extra_meal, style="TButton").grid(row=0, column=0, pady=5, sticky="ew")

    def _add_new_extra_meal(self):
        self.dynamic_meal_counter += 1
        new_meal_name = f"{DYNAMIC_MEAL_PREFIX} {self.dynamic_meal_counter}"
        self._create_single_meal_entry_row(new_meal_name, dynamic_removable=True)
        self.meals_canvas.yview_moveto(1.0)


    def _remove_dynamic_meal(self, meal_name: str, meal_frame: ttk.LabelFrame):
        response = messagebox.askyesno(
            "Remover Lanche Extra",
            f"Tem certeza que deseja remover '{meal_name}'? Isso apagará os dados associados a ele para a data atual."
        )
        if response:
            meal_frame.destroy()
            if meal_name in self.entries:
                del self.entries[meal_name]
            if meal_name in self.dynamic_meal_frames:
                del self.dynamic_meal_frames[meal_name]

            self.data_modified = True
            self._repack_meals_sections_container()
            self.meals_canvas.config(scrollregion=self.meals_canvas.bbox("all"))
            messagebox.showinfo("Lanche Removido", f"'{meal_name}' foi removido. Salve o dia para que a remoção seja permanente.")


    def _repack_meals_sections_container(self):
        """Reorganiza os widgets no container de refeições após uma remoção, mantendo o zebrado."""
        children = self.meals_sections_container.winfo_children()

        for i, child in enumerate(children):
            child.grid(row=i, column=0, sticky="ew", pady=(5, 5), padx=5)

            bg_style = "MealRow.TFrame" if i % 2 == 0 else "MealRowAlt.TFrame"
            child.configure(style=bg_style)

            for sub_child in child.winfo_children():
                if isinstance(sub_child, ttk.Label) and sub_child.cget("text").endswith(":"):
                    sub_child.configure(style="MealName.TLabel" if i % 2 == 0 else "MealNameAlt.TLabel")
                    break

        self.meals_sections_container.update_idletasks()
        self.meals_canvas.config(scrollregion=self.meals_canvas.bbox("all"))

    def _create_action_buttons_frame(self, parent, row):
        action_button_frame = ttk.Frame(parent, style="Panel.TFrame", padding=(20, 15))
        action_button_frame.grid(row=row, column=0, pady=(20, 0), sticky="ew", padx=20)
        action_button_frame.grid_columnconfigure((0,1,2,3), weight=1)

        ttk.Button(action_button_frame, text="Salvar Dia", command=self.save_day, style="TButton").grid(row=0, column=0, padx=8, sticky="ew")
        ttk.Button(action_button_frame, text="Limpar Campos", command=self.clear_inputs, style="TButton").grid(row=0, column=1, padx=8, sticky="ew")
        ttk.Button(action_button_frame, text="Carregar Dia", command=self.load_current_date_data, style="TButton").grid(row=0, column=2, padx=8, sticky="ew")
        ttk.Button(action_button_frame, text="Sair", command=self.app_instance.ask_quit, style="Exit.TButton").grid(row=0, column=3, padx=8, sticky="ew")


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
        self.app_instance.load_day_data_with_confirmation(self.date_entry.get_date().isoformat())

    def load_current_date_data(self):
        date_str_br = self.date_entry.get().strip()
        try:
            date_obj = dt.datetime.strptime(date_str_br, "%d/%m/%Y").date()
            self.app_instance.load_day_data_with_confirmation(date_obj.isoformat())
        except ValueError:
            messagebox.showerror("Data inválida", f"Data inválida: {date_str_br}. Use DD/MM/AAAA.")


    def go_to_previous_day(self):
        current_date_obj = self.date_entry.get_date()
        previous_day_obj = current_date_obj - dt.timedelta(days=1)
        self.app_instance.load_day_data_with_confirmation(previous_day_obj.isoformat())

    def go_to_next_day(self):
        current_date_obj = self.date_entry.get_date()
        next_day_obj = current_date_obj + dt.timedelta(days=1)
        self.app_instance.load_day_data_with_confirmation(next_day_obj.isoformat())

    def _on_data_change(self, *args):
        self.data_modified = True

    def get_date_iso(self):
        """Retorna a data ISO selecionada no DateEntry desta aba."""
        return self.date_entry.get_date().isoformat()

    def get_data_modified_status(self) -> bool:
        return self.data_modified

    def set_data_modified_status(self, status: bool):
        self.data_modified = status

    def load_day_data(self, date_str_iso: str):
        """Carrega os dados para a data especificada na UI do registro diário."""
        self._reset_daily_entry_ui()

        try:
            self.date_entry.set_date(dt.date.fromisoformat(date_str_iso))
        except ValueError:
            messagebox.showerror("Erro de Data", f"Não foi possível definir a data na UI: {date_str_iso}")
            return

        glargina_dose, meal_data = self.service.get_daily_data(date_str_iso)
        self.glargina_var.set(f"{glargina_dose:.1f}" if glargina_dose is not None else "")

        for meal_name in FIXED_MEALS:
            data = meal_data.get(meal_name, {})
            if meal_name in self.entries:
                for key, var in self.entries[meal_name].items():
                    value = data.get(key)
                    if key in ["carbs", "glicemia", "lispro", "bolus"]:
                        var.set(f"{value:.1f}" if value is not None else "")
                    elif key == "observations":
                        var.set(value if value is not None else "")


        max_dynamic_counter = 0
        for meal_name, data in meal_data.items():
            if meal_name.startswith(DYNAMIC_MEAL_PREFIX):
                try:
                    num = int(meal_name.replace(DYNAMIC_MEAL_PREFIX, "").strip())
                    if num > max_dynamic_counter:
                        max_dynamic_counter = num
                except ValueError:
                    pass

                self._create_single_meal_entry_row(meal_name, dynamic_removable=True)

                if meal_name in self.entries:
                    for key, var in self.entries[meal_name].items():
                        value = data.get(key)
                        if key in ["carbs", "glicemia", "lispro", "bolus"]:
                            var.set(f"{value:.1f}" if value is not None else "")
                        elif key == "observations":
                            var.set(value if value is not None else "")
        self.dynamic_meal_counter = max_dynamic_counter + 1

        self.meals_sections_container.update_idletasks()
        self.meals_canvas.config(scrollregion=self.meals_canvas.bbox("all"))

        self.data_modified = False

    def save_day(self):
        date_str_iso = self.date_entry.get_date().isoformat()

        glargina_text = self.glargina_var.get().strip()
        is_valid_glargina, glargina_value, error_msg = self.service.validate_numeric_input(glargina_text, "glargina")
        if not is_valid_glargina:
            messagebox.showerror("Erro de Entrada", error_msg)
            return

        meal_entries_data = {}
        for meal_name, vars_ in self.entries.items():
            meal_values = {}
            has_data = False
            for key, var in vars_.items():
                text = var.get().strip()
                if key in ["carbs", "glicemia", "lispro", "bolus"]:
                    is_valid, value, error_msg = self.service.validate_numeric_input(text, key, meal_name)
                    if not is_valid:
                        messagebox.showerror("Erro de Entrada", error_msg)
                        return
                    meal_values[key] = value
                    if value is not None and value != "":
                        has_data = True
                elif key == "observations":
                    meal_values[key] = text if text else None
                    if text:
                        has_data = True

            if has_data:
                meal_entries_data[meal_name] = meal_values

        success, msg = self.service.save_daily_data(date_str_iso, glargina_value or 0.0, meal_entries_data)
        if success:
            messagebox.showinfo("Salvo", msg)
            self.data_modified = False
            self.load_day_data(date_str_iso)
        else:
            messagebox.showerror("Erro ao Salvar", msg)

    def clear_inputs(self):
        self._reset_daily_entry_ui()
        self.data_modified = False

    def _reset_daily_entry_ui(self):
        """
        Limpa todos os valores das entradas (fixas e dinâmicas)
        e remove todos os frames de lanches extras dinâmicos da UI.
        Mantém os frames das refeições fixas.
        """
        for meal_name in FIXED_MEALS:
            if meal_name in self.entries:
                for var in self.entries[meal_name].values():
                    var.set("")

        for meal_name in list(self.dynamic_meal_frames.keys()):
            if meal_name.startswith(DYNAMIC_MEAL_PREFIX):
                frame_to_destroy = self.dynamic_meal_frames[meal_name]
                frame_to_destroy.destroy()
                del self.dynamic_meal_frames[meal_name]
                if meal_name in self.entries:
                    del self.entries[meal_name]

        self.glargina_var.set("")
        self.dynamic_meal_counter = 0
        self._repack_meals_sections_container()
        self.meals_canvas.config(scrollregion=self.meals_canvas.bbox("all"))
        self.data_modified = False