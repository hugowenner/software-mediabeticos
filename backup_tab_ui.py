# backup_tab_ui.py

import datetime as dt
from pathlib import Path
from tkinter import Tk, Label, Entry, Button, StringVar, ttk, messagebox, filedialog, Toplevel, Canvas, Text, Scrollbar

from carb_tracker_service import CarbTrackerService
from constants import DB_FILE
from tooltip import ToolTip

class BackupTabUI(ttk.Frame):
    def __init__(self, master, service: CarbTrackerService, app_instance):
        super().__init__(master, style="Panel.TFrame")
        self.service = service
        self.app_instance = app_instance

        self.backup_status_label = None

        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)

        ttk.Label(self, text="Backup do Banco de Dados", style="Heading.TLabel").grid(row=0, column=0, pady=(15, 20), sticky="ew", padx=20)

        backup_frame = ttk.Frame(self, style="Panel.TFrame", padding=(20, 20))
        backup_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        backup_frame.grid_columnconfigure(0, weight=1)
        backup_frame.grid_columnconfigure(1, weight=1)

        ttk.Label(backup_frame, text="Selecione um local para salvar o backup do banco de dados:",
                  style="LabelField.TLabel", wraplength=400).grid(row=0, column=0, columnspan=2, pady=(0, 15), sticky="ew")

        ttk.Button(backup_frame, text="Criar Backup", command=self.create_backup, style="TButton").grid(row=1, column=0, padx=5, pady=10, sticky="ew")
        ttk.Button(backup_frame, text="Restaurar Backup", command=self.restore_backup, style="TButton").grid(row=1, column=1, padx=5, pady=10, sticky="ew")

        # CORREÇÃO AQUI: Usando "text_dark" em vez de "text_primary"
        self.backup_status_label = ttk.Label(self, text="", style="LabelField.TLabel", foreground=self.app_instance.colors["text_dark"])
        self.backup_status_label.grid(row=2, column=0, pady=(10, 15), sticky="ew", padx=20)

    def create_backup(self):
        # A lógica de confirmação de salvamento é delegada ao app_instance
        if not self.app_instance.confirm_save_all_modified_data_before_action():
            self.backup_status_label.config(text="Criação de backup cancelada. Há dados não salvos.", foreground=self.app_instance.colors["warning_color"])
            return

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
                    self.backup_status_label.config(text=f"Último backup: {Path(backup_path).name} em {dt.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", foreground=self.app_instance.colors["success_color"])
                else:
                    messagebox.showerror("Erro no Backup", message)
                    self.backup_status_label.config(text=f"Erro: {message}", foreground=self.app_instance.colors["error_color"])
            else:
                self.backup_status_label.config(text="Criação de backup cancelada.", foreground=self.app_instance.colors["text_secondary"])
        except Exception as e:
            messagebox.showerror("Erro Inesperado", f"Ocorreu um erro inesperado ao criar o backup: {e}")
            self.backup_status_label.config(text=f"Erro inesperado: {e}", foreground=self.app_instance.colors["error_color"])


    def restore_backup(self):
        # A lógica de confirmação de salvamento é delegada ao app_instance
        if not self.app_instance.confirm_save_all_modified_data_before_action():
            self.backup_status_label.config(text="Restauração cancelada. Há dados não salvos.", foreground=self.app_instance.colors["warning_color"])
            return

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
                        self.backup_status_label.config(text=f"Banco de dados restaurado de {Path(source_backup_path).name} em {dt.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", foreground=self.app_instance.colors["success_color"])
                        current_date = self.app_instance.daily_entry_tab_instance.get_date_iso()
                        self.app_instance.daily_entry_tab_instance.load_day_data(current_date)
                    else:
                        messagebox.showerror("Erro na Restauração", message)
                        self.backup_status_label.config(text=f"Erro: {message}", foreground=self.app_instance.colors["error_color"])
                else:
                    self.backup_status_label.config(text="Restauração de backup cancelada.", foreground=self.app_instance.colors["text_secondary"])
            except Exception as e:
                messagebox.showerror("Erro Inesperado", f"Ocorreu um erro inesperado ao restaurar o backup: {e}")
                self.backup_status_label.config(text=f"Erro inesperado: {e}", foreground=self.app_instance.colors["error_color"])