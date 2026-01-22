import tkinter as tk
from tkinter import scrolledtext, messagebox
import sqlite3
import requests

API_URL = "http://192.168.240.6"

def init_db():
    with sqlite3.connect("users.db") as db:
        db.execute("""CREATE TABLE IF NOT EXISTS Users (
                        UserID INTEGER PRIMARY KEY AUTOINCREMENT,
                        Username TEXT UNIQUE,
                        Password TEXT
                      )""")

class LoginWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Login System")
        self.root.geometry("300x200")

        tk.Label(root, text="Username").pack(pady=5)
        self.entry_user = tk.Entry(root)
        self.entry_user.pack()

        tk.Label(root, text="Password").pack(pady=5)
        self.entry_pass = tk.Entry(root, show="*")
        self.entry_pass.pack()

        tk.Button(root, text="Login", command=self.login).pack(pady=5)
        tk.Button(root, text="Register", command=self.register).pack(pady=5)

    def register(self):
        u, p = self.entry_user.get(), self.entry_pass.get()
        if not u or not p:
            messagebox.showwarning("Error", "Enter both username and password")
            return
        try:
            with sqlite3.connect("users.db") as db:
                db.execute("INSERT INTO Users (Username, Password) VALUES (?, ?)", (u, p))
            messagebox.showinfo("Success", "User registered!")
        except:
            messagebox.showerror("Error", "Username already exists")

    def login(self):
        u, p = self.entry_user.get(), self.entry_pass.get()
        with sqlite3.connect("users.db") as db:
           cur = db.execute("SELECT * FROM Users WHERE Username=? AND Password=?", (u, p))
        if cur.fetchone():
            messagebox.showinfo("Welcome", f"Hello {u}!")
            self.root.destroy()
            open_robot_gui()
        else:
            messagebox.showerror("Error", "Invalid login")

class RobotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Robot Controller")
        self.root.geometry("1920x1080")

        for r in range(2): self.root.grid_rowconfigure(r, weight=1, uniform="row")
        for c in range(2): self.root.grid_columnconfigure(c, weight=1, uniform="col")

        frame_top_left = tk.Frame(root, bg="black")
        frame_top_left.grid(row=0, column=0, sticky="nsew")
        tk.Label(frame_top_left, text="Video Stream 1", fg="white", bg="black", font=("Arial", 20)).place(relx=0.5, rely=0.5, anchor="center")

        frame_bottom_left = tk.Frame(root, bg="gray20")
        frame_bottom_left.grid(row=1, column=0, sticky="nsew")
        tk.Label(frame_bottom_left, text="Video Stream 2", fg="white", bg="gray20", font=("Arial", 20)).place(relx=0.5, rely=0.5, anchor="center")

        frame_top_right = tk.Frame(root, bg="lightblue")
        frame_top_right.grid(row=0, column=1, sticky="nsew")
        frame_top_right.grid_rowconfigure((0, 1, 2), weight=1)
        frame_top_right.grid_columnconfigure((0, 1, 2), weight=1)

        buttons = {
            "↑": ("forward", 0, 1),
            "↓": ("backward", 2, 1),
            "←": ("left", 1, 0),
           "→": ("right", 1, 2),
            "▶ Play": ("start", 1, 1),
            "■ Stop": ("stop", 1, 1)
        }
        for text, (cmd, r, c) in buttons.items():
            tk.Button(
                frame_top_right, text=text, width=8 if " " in text else 5, height=2,
                command=lambda e=cmd: self.send_command(e),
                fg="green" if "Play" in text else ("red" if "Stop" in text else "black")
            ).grid(row=r, column=c, padx=5, pady=5, sticky="nsew")

        frame_bottom_right = tk.Frame(root, bg="white")
        frame_bottom_right.grid(row=1, column=1, sticky="nsew")
        tk.Label(frame_bottom_right, text="User Log", font=("Arial", 14)).pack(anchor="nw")
        self.log_box = scrolledtext.ScrolledText(frame_bottom_right, wrap=tk.WORD, width=60, height=20)
        self.log_box.pack(expand=True, fill="both", padx=10, pady=10)

        self.add_log("System Ready.")

    def send_command(self, cmd):
        try:
            res = requests.get(f"{API_URL}/{cmd}")
            if res.ok:
                self.add_log(res.json().get("message", "No response"))
            else:
                self.add_log(f"Error {res.status_code}")
        except Exception as e:
            self.add_log(f"API Error: {e}")

    def add_log(self, msg):
        self.log_box.insert(tk.END, msg + "\n")
        self.log_box.see(tk.END)

def open_robot_gui():
    r = tk.Tk()
    app = RobotGUI(r)
    r.mainloop()

if __name__ == "__main__":
    init_db()
    root = tk.Tk()
    login_app = LoginWindow(root)
    root.mainloop()

