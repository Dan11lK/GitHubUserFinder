import json
import webbrowser
from pathlib import Path

import requests
import tkinter as tk
from tkinter import messagebox

FAV_FILE = Path(__file__).with_name("favorites.json")
API_URL = "https://api.github.com/search/users"


class GitHubUserFinder:
    def __init__(self, root):
        self.root = root
        self.root.title("GitHub User Finder")
        self.root.geometry("760x520")
        self.root.minsize(700, 460)

        self.results = []
        self.favorites = self.load_favorites()

        self.build_ui()
        self.refresh_favorites()

    def build_ui(self):
        title = tk.Label(
            self.root,
            text="GitHub User Finder",
            font=("Arial", 18, "bold")
        )
        title.pack(pady=10)

        search_frame = tk.Frame(self.root)
        search_frame.pack(fill="x", padx=15)

        self.search_entry = tk.Entry(search_frame, font=("Arial", 12))
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.search_entry.bind("<Return>", lambda event: self.search_users())

        search_button = tk.Button(search_frame, text="Найти", command=self.search_users)
        search_button.pack(side="left")

        content_frame = tk.Frame(self.root)
        content_frame.pack(fill="both", expand=True, padx=15, pady=15)

        left_frame = tk.LabelFrame(content_frame, text="Результаты поиска", padx=8, pady=8)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 8))

        self.results_listbox = tk.Listbox(left_frame, font=("Arial", 11))
        self.results_listbox.pack(fill="both", expand=True)

        result_buttons = tk.Frame(left_frame)
        result_buttons.pack(fill="x", pady=(8, 0))

        tk.Button(
            result_buttons,
            text="Добавить в избранное",
            command=self.add_to_favorites
        ).pack(side="left", fill="x", expand=True, padx=(0, 4))

        tk.Button(
            result_buttons,
            text="Открыть профиль",
            command=self.open_selected_result
        ).pack(side="left", fill="x", expand=True, padx=(4, 0))

        right_frame = tk.LabelFrame(content_frame, text="Избранные пользователи", padx=8, pady=8)
        right_frame.pack(side="left", fill="both", expand=True, padx=(8, 0))

        self.favorites_listbox = tk.Listbox(right_frame, font=("Arial", 11))
        self.favorites_listbox.pack(fill="both", expand=True)

        favorite_buttons = tk.Frame(right_frame)
        favorite_buttons.pack(fill="x", pady=(8, 0))

        tk.Button(
            favorite_buttons,
            text="Удалить",
            command=self.remove_favorite
        ).pack(side="left", fill="x", expand=True, padx=(0, 4))

        tk.Button(
            favorite_buttons,
            text="Открыть профиль",
            command=self.open_selected_favorite
        ).pack(side="left", fill="x", expand=True, padx=(4, 0))

        self.status_label = tk.Label(self.root, text="Введите логин или имя пользователя GitHub", anchor="w")
        self.status_label.pack(fill="x", padx=15, pady=(0, 10))

    def load_favorites(self):
        if not FAV_FILE.exists():
            return []

        try:
            with open(FAV_FILE, "r", encoding="utf-8") as file:
                data = json.load(file)
                if isinstance(data, list):
                    return data
                return []
        except (json.JSONDecodeError, OSError):
            return []

    def save_favorites(self):
        with open(FAV_FILE, "w", encoding="utf-8") as file:
            json.dump(self.favorites, file, indent=4, ensure_ascii=False)

    def search_users(self):
        query = self.search_entry.get().strip()

        if not query:
            messagebox.showwarning("Ошибка", "Поле поиска не должно быть пустым")
            return

        self.results_listbox.delete(0, tk.END)
        self.results = []
        self.status_label.config(text="Поиск...")
        self.root.update_idletasks()

        try:
            response = requests.get(
                API_URL,
                params={"q": query, "per_page": 20},
                headers={"Accept": "application/vnd.github+json"},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            self.results = data.get("items", [])

            if not self.results:
                self.status_label.config(text="Пользователи не найдены")
                return

            for user in self.results:
                login = user.get("login", "unknown")
                user_type = user.get("type", "User")
                self.results_listbox.insert(tk.END, f"{login} | {user_type}")

            self.status_label.config(text=f"Найдено пользователей: {len(self.results)}")

        except requests.exceptions.HTTPError:
            if response.status_code == 403:
                messagebox.showerror("Ошибка API", "GitHub временно ограничил запросы. Попробуйте позже")
            else:
                messagebox.showerror("Ошибка API", f"Код ошибки: {response.status_code}")
            self.status_label.config(text="Ошибка запроса")
        except requests.exceptions.RequestException:
            messagebox.showerror("Ошибка", "Не удалось подключиться к GitHub API")
            self.status_label.config(text="Ошибка подключения")

    def get_selected_result(self):
        selected = self.results_listbox.curselection()
        if not selected:
            messagebox.showwarning("Ошибка", "Выберите пользователя из списка")
            return None
        return self.results[selected[0]]

    def get_selected_favorite(self):
        selected = self.favorites_listbox.curselection()
        if not selected:
            messagebox.showwarning("Ошибка", "Выберите пользователя из избранного")
            return None
        return self.favorites[selected[0]]

    def add_to_favorites(self):
        user = self.get_selected_result()
        if user is None:
            return

        login = user.get("login")
        if any(item.get("login") == login for item in self.favorites):
            messagebox.showinfo("Информация", "Этот пользователь уже есть в избранном")
            return

        favorite_user = {
            "login": login,
            "html_url": user.get("html_url"),
            "avatar_url": user.get("avatar_url"),
            "type": user.get("type")
        }

        self.favorites.append(favorite_user)
        self.save_favorites()
        self.refresh_favorites()
        self.status_label.config(text=f"Пользователь {login} добавлен в избранное")

    def remove_favorite(self):
        selected = self.favorites_listbox.curselection()
        if not selected:
            messagebox.showwarning("Ошибка", "Выберите пользователя для удаления")
            return

        removed = self.favorites.pop(selected[0])
        self.save_favorites()
        self.refresh_favorites()
        self.status_label.config(text=f"Пользователь {removed.get('login')} удален")

    def refresh_favorites(self):
        self.favorites_listbox.delete(0, tk.END)
        for user in self.favorites:
            login = user.get("login", "unknown")
            user_type = user.get("type", "User")
            self.favorites_listbox.insert(tk.END, f"{login} | {user_type}")

    def open_selected_result(self):
        user = self.get_selected_result()
        if user and user.get("html_url"):
            webbrowser.open(user["html_url"])

    def open_selected_favorite(self):
        user = self.get_selected_favorite()
        if user and user.get("html_url"):
            webbrowser.open(user["html_url"])


if __name__ == "__main__":
    root = tk.Tk()
    app = GitHubUserFinder(root)
    root.mainloop()
