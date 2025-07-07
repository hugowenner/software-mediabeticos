# settings_tab_ui.py

from tkinter import Tk, Label, Entry, Button, StringVar, ttk, messagebox, filedialog, Toplevel, Canvas, Text, Scrollbar
from datetime import datetime
from tooltip import ToolTip # Certifique-se de que ToolTip está disponível

class SettingsTabUI(ttk.Frame):
    def __init__(self, master, service, app_instance):
        super().__init__(master, style="Panel.TFrame")
        self.service = service
        self.app_instance = app_instance

        self.report_date_format_var = StringVar()
        self.glicemia_alert_threshold_var = StringVar()
        self.selected_theme_var = StringVar() # Variável para o tema

        self._build_ui()
        self._load_current_settings()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)

        ttk.Label(self, text="Configurações", style="Heading.TLabel").grid(row=0, column=0, pady=(15, 20), sticky="ew", padx=20)

        settings_frame = ttk.Frame(self, style="Panel.TFrame", padding=(20, 20))
        settings_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        settings_frame.grid_columnconfigure(0, weight=1)
        settings_frame.grid_columnconfigure(1, weight=1)

        row_idx = 0

        # Formato de Data do Relatório
        ttk.Label(settings_frame, text="Formato de Data do Relatório:").grid(row=row_idx, column=0, sticky="w", pady=5, padx=10)
        entry_format = ttk.Entry(settings_frame, textvariable=self.report_date_format_var)
        entry_format.grid(row=row_idx, column=1, sticky="ew", pady=5, padx=10)
        ToolTip(entry_format, "Formato para exibir datas em relatórios (ex: %d/%m/%Y para 01/01/2023)")
        row_idx += 1

        # Limite de Alerta de Glicemia
        ttk.Label(settings_frame, text="Limite de Alerta de Glicemia (mg/dL):").grid(row=row_idx, column=0, sticky="w", pady=5, padx=10)
        entry_glicemia_alert = ttk.Entry(settings_frame, textvariable=self.glicemia_alert_threshold_var)
        entry_glicemia_alert.grid(row=row_idx, column=1, sticky="ew", pady=5, padx=10)
        ToolTip(entry_glicemia_alert, "Valor de glicemia a partir do qual um alerta pode ser exibido.")
        row_idx += 1

        # Seleção de Tema
        ttk.Label(settings_frame, text="Tema da Interface:").grid(row=row_idx, column=0, sticky="w", pady=5, padx=10)
        theme_combobox = ttk.Combobox(settings_frame, textvariable=self.selected_theme_var,
                                      values=self.app_instance.available_themes, state="readonly")
        theme_combobox.grid(row=row_idx, column=1, sticky="ew", pady=5, padx=10)
        theme_combobox.bind("<<ComboboxSelected>>", self._on_theme_selected)
        ToolTip(theme_combobox, "Selecione o tema visual do aplicativo.")
        row_idx += 1


        # Botões de Ação
        button_frame = ttk.Frame(self, style="Panel.TFrame", padding=(20, 15))
        button_frame.grid(row=2, column=0, pady=(10, 20), sticky="ew", padx=20)
        button_frame.grid_columnconfigure((0, 1), weight=1)

        ttk.Button(button_frame, text="Salvar Configurações", command=self.save_settings, style="TButton").grid(row=0, column=0, padx=8, sticky="ew")
        ttk.Button(button_frame, text="Redefinir Padrões", command=self.reset_to_defaults, style="TButton").grid(row=0, column=1, padx=8, sticky="ew")

    def _load_current_settings(self):
        self.report_date_format_var.set(self.service.get_config("report_date_format", "%d/%m/%Y"))
        self.glicemia_alert_threshold_var.set(str(self.service.get_config("glicemia_alert_threshold", 180)))
        self.selected_theme_var.set(self.service.get_config("app_theme", "clam")) # Carrega o tema atual

    def _on_theme_selected(self, event):
        selected_theme = self.selected_theme_var.get()
        self.app_instance.apply_theme(selected_theme) # Aplica o tema imediatamente
        # A configuração será salva quando o botão "Salvar Configurações" for clicado

    def save_settings(self):
        new_format = self.report_date_format_var.get().strip()
        new_glicemia_alert_str = self.glicemia_alert_threshold_var.get().strip()
        new_theme = self.selected_theme_var.get().strip()

        # Validação do formato de data
        if new_format:
            try:
                datetime.now().strftime(new_format)
            except Exception:
                messagebox.showerror("Erro de Formato", "Formato de data inválido. Use um formato válido como %d/%m/%Y.")
                return

        # Validação do limite de glicemia
        if new_glicemia_alert_str:
            try:
                new_glicemia_alert = float(new_glicemia_alert_str)
                if new_glicemia_alert < 0:
                    messagebox.showerror("Erro de Entrada", "O limite de alerta de glicemia deve ser um número não negativo.")
                    return
            except ValueError:
                messagebox.showerror("Erro de Entrada", "O limite de alerta de glicemia deve ser um número válido.")
                return
        else:
            new_glicemia_alert = None # Ou um valor padrão se preferir

        # Salvar as configurações
        config_to_save = {
            "report_date_format": new_format,
            "glicemia_alert_threshold": new_glicemia_alert,
            "app_theme": new_theme # Salva o tema selecionado
        }
        success, message = self.service.save_config(config_to_save)
        if success:
            messagebox.showinfo("Configurações Salvas", message)
        else:
            messagebox.showerror("Erro", message)

    def reset_to_defaults(self):
        response = messagebox.askyesno("Redefinir Configurações", "Tem certeza que deseja redefinir todas as configurações para os valores padrão?")
        if response:
            default_config = self.service._default_config()
            success, message = self.service.save_config(default_config)
            if success:
                messagebox.showinfo("Configurações Redefinidas", message)
                self._load_current_settings() # Recarrega as configurações padrão na UI
                self.app_instance.load_theme_from_config() # Aplica o tema padrão imediatamente
            else:
                messagebox.showerror("Erro", message)