import customtkinter as ctk
import requests
import json
from tkinter import messagebox

# Настройки оформления
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Интеграция модулей через API")
        self.geometry("700x500")

        self.api_url = "http://127.0.0.1:8000/items"

        # Сетка
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Боковая панель (навигация)
        self.sidebar_frame = ctk.CTkFrame(self, width=140, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="API Client", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.refresh_button = ctk.CTkButton(self.sidebar_frame, text="Обновить список", command=self.load_items)
        self.refresh_button.grid(row=1, column=0, padx=20, pady=10)

        # Основная область
        self.main_frame = ctk.CTkFrame(self, corner_radius=10)
        self.main_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)

        # Форма добавления
        self.form_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.form_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        self.title_entry = ctk.CTkEntry(self.form_frame, placeholder_text="Название")
        self.title_entry.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        self.desc_entry = ctk.CTkEntry(self.form_frame, placeholder_text="Описание")
        self.desc_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        self.add_button = ctk.CTkButton(self.form_frame, text="Добавить", width=100, command=self.add_item)
        self.add_button.grid(row=0, column=2, padx=5, pady=5)

        # Список элементов
        self.scrollable_frame = ctk.CTkScrollableFrame(self.main_frame, label_text="Список данных из API")
        self.scrollable_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.scrollable_frame.grid_columnconfigure(0, weight=1)

        # Первичная загрузка
        self.after(100, self.load_items)

    def load_items(self):
        """Получение данных через GET запрос"""
        try:
            response = requests.get(self.api_url, timeout=5)
            if response.status_code == 200:
                items = response.json()
                self.update_list(items)
            else:
                messagebox.showerror("Ошибка", f"Сервер вернул код {response.status_code}")
        except requests.exceptions.ConnectionError:
            messagebox.showerror("Ошибка", "Не удалось подключиться к серверу API")

    def update_list(self, items):
        """Обновление UI списка"""
        # Очистка старых элементов
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        for idx, item in enumerate(items):
            item_frame = ctk.CTkFrame(self.scrollable_frame)
            item_frame.grid(row=idx, column=0, padx=5, pady=5, sticky="ew")
            item_frame.grid_columnconfigure(0, weight=1)

            label_text = f"ID: {item['id']} | {item['title']}\n{item['description']}"
            label = ctk.CTkLabel(item_frame, text=label_text, justify="left")
            label.grid(row=0, column=0, padx=10, pady=5, sticky="w")

            del_btn = ctk.CTkButton(item_frame, text="Удалить", width=60, fg_color="red", 
                                    hover_color="darkred", command=lambda i=item['id']: self.delete_item(i))
            del_btn.grid(row=0, column=1, padx=10, pady=5)

    def add_item(self):
        """Отправка данных через POST запрос"""
        title = self.title_entry.get()
        desc = self.desc_entry.get()

        if not title or not desc:
            messagebox.showwarning("Внимание", "Заполните все поля")
            return

        payload = {"title": title, "description": desc, "status": "active"}
        try:
            response = requests.post(self.api_url, json=payload)
            if response.status_code == 200:
                self.title_entry.delete(0, 'end')
                self.desc_entry.delete(0, 'end')
                self.load_items()
            else:
                messagebox.showerror("Ошибка", "Не удалось добавить данные")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def delete_item(self, item_id):
        """Удаление через DELETE запрос"""
        try:
            response = requests.delete(f"{self.api_url}/{item_id}")
            if response.status_code == 200:
                self.load_items()
            else:
                messagebox.showerror("Ошибка", "Не удалось удалить")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

if __name__ == "__main__":
    app = App()
    app.mainloop()
