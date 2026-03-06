import tkinter as tk
from tkinter import scrolledtext, messagebox
import sqlite3
import requests
import cv2
import numpy as np
from PIL import Image, ImageTk

API_URL = "http://192.168.240.123"


def init_db():
    with sqlite3.connect("users.db") as db:
        db.execute(
            """CREATE TABLE IF NOT EXISTS Users (
                UserID INTEGER PRIMARY KEY AUTOINCREMENT,
                Username TEXT UNIQUE,
                Password TEXT
            )"""
        )


def reparameterize_curve(points, num_points=200):
    points = np.asarray(points)
    if len(points) < 2:
        return points

    seg = np.diff(points, axis=0)
    seg_len = np.sqrt((seg * seg).sum(axis=1))
    arc = np.concatenate(([0.0], np.cumsum(seg_len)))
    total = arc[-1]

    if total == 0:
        return points

    t = arc / total
    t_new = np.linspace(0.0, 1.0, num_points)

    x_new = np.interp(t_new, t, points[:, 0])
    y_new = np.interp(t_new, t, points[:, 1])
    return np.column_stack((x_new, y_new))

def process_frame(frame):
    h, w = frame.shape[:2]
    output = frame.copy()

    # ROI
    roi_top = int(h * 0.20)
    roi_bottom = h
    roi_left = int(w * 0.10)
    roi_right = int(w * 0.90)

    roi = frame[roi_top:roi_bottom, roi_left:roi_right]
    roi_draw = roi.copy()
    rh, rw = roi.shape[:2]

    # Grayscale&Blur
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (5, 5), 0)

    # Threshold bright/strong tape regions
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Morphology
    # Vertical kernel to favor lane-like shapes
    vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 25))
    small_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))

    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, vertical_kernel)
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, small_kernel)

    # Edge fusion for stronger boundaries
    edges = cv2.Canny(gray, 60, 150)
    edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, small_kernel)

    combined = cv2.bitwise_or(binary, edges)

    # clean again
    combined = cv2.morphologyEx(combined, cv2.MORPH_CLOSE, vertical_kernel)
    combined = cv2.morphologyEx(combined, cv2.MORPH_OPEN, small_kernel)

    # Find contours
    contours, _ = cv2.findContours(combined, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    lane_candidates = []

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < 500:
            continue

        x, y, cw, ch = cv2.boundingRect(cnt)
        if ch == 0 or cw == 0:
            continue

        aspect_ratio = cw / float(ch)

        # Keep tall narrow lane-like shapes
        if ch > rh * 0.30 and aspect_ratio < 0.55:
            lane_candidates.append(cnt)

    #If no error, return candidates
    if len(lane_candidates) < 2:
        debug = cv2.cvtColor(combined, cv2.COLOR_GRAY2BGR)
        cv2.putText(debug, "Need 2 lane contours", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        return debug

    #Choose leftmost and rightmost candidates
    lane_candidates = sorted(lane_candidates, key=cv2.contourArea, reverse=True)
    lane_candidates = lane_candidates[:8]

    centers = []
    for cnt in lane_candidates:
        x, y, cw, ch = cv2.boundingRect(cnt)
        cx = x + cw // 2
        centers.append((cx, cnt))

    centers.sort(key=lambda item: item[0])

    left_cnt = centers[0][1]
    right_cnt = centers[-1][1]

    #Fit line through each contour
    def fit_line_points(cnt, y_vals):
        pts = cnt.reshape(-1, 2).astype(np.float32)
        if len(pts) < 2:
            return None

        vx, vy, x0, y0 = cv2.fitLine(pts, cv2.DIST_L2, 0, 0.01, 0.01)
        vx, vy, x0, y0 = float(vx), float(vy), float(x0), float(y0)

        if abs(vy) < 1e-6:
            return None

        points = []
        for y in y_vals:
            x = int(x0 + (y - y0) * vx / vy)
            points.append((x, int(y)))
        return np.array(points, dtype=np.int32)

    y_vals = np.linspace(int(rh * 0.05), rh - 1, 25)

    left_curve = fit_line_points(left_cnt, y_vals)
    right_curve = fit_line_points(right_cnt, y_vals)

    if left_curve is None or right_curve is None:
        return roi_draw

    center_curve = ((left_curve.astype(np.float32) + right_curve.astype(np.float32)) / 2.0).astype(np.int32)

    # Draw inside ROI
    cv2.polylines(roi_draw, [left_curve.reshape(-1, 1, 2)], False, (255, 0, 0), 4)
    cv2.polylines(roi_draw, [right_curve.reshape(-1, 1, 2)], False, (0, 255, 255), 4)
    cv2.polylines(roi_draw, [center_curve.reshape(-1, 1, 2)], False, (0, 0, 255), 5)

    target = center_curve[-1]
    cv2.circle(roi_draw, tuple(target), 7, (0, 255, 0), -1)

    # Put ROI result back into full frame
    output[roi_top:roi_bottom, roi_left:roi_right] = roi_draw

    return output

def motor_automation
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, 100, minLineLength=50, maxLineGap=10)    
    if lines is not None:
        print(f"Detected {len(lines)} lines:")
        for line in lines:
            x1, y1, x2, y2 = line[0]
            print(f"Start point: ({x1}, {y1}), End point: ({x2}, {y2})")
        
        return lines
    else:
        print("No lines detected.")
        return None

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

        for r in range(2):
            self.root.grid_rowconfigure(r, weight=1, uniform="row")
        for c in range(2):
            self.root.grid_columnconfigure(c, weight=1, uniform="col")

        # --- TOP LEFT (RAW CAMERA) ---
        frame_top_left = tk.Frame(root, bg="black")
        frame_top_left.grid(row=0, column=0, sticky="nsew")
        self.raw_label = tk.Label(frame_top_left, bg="black")
        self.raw_label.pack(expand=True, fill="both")

        # --- BOTTOM LEFT (PROCESSED CAMERA) ---
        frame_bottom_left = tk.Frame(root, bg="gray20")
        frame_bottom_left.grid(row=1, column=0, sticky="nsew")
        self.proc_label = tk.Label(frame_bottom_left, bg="gray20")
        self.proc_label.pack(expand=True, fill="both")

        # --- TOP RIGHT (CONTROLS) ---
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
            "■ Stop": ("stop", 1, 1),
        }

        for text, (cmd, r, c) in buttons.items():
            tk.Button(
                frame_top_right,
                text=text,
                width=8 if " " in text else 5,
                height=2,
                command=lambda e=cmd: self.send_command(e),
                fg="green" if "Play" in text else ("red" if "Stop" in text else "black"),
            ).grid(row=r, column=c, padx=5, pady=5, sticky="nsew")

        # --- BOTTOM RIGHT (LOG) ---
        frame_bottom_right = tk.Frame(root, bg="white")
        frame_bottom_right.grid(row=1, column=1, sticky="nsew")

        tk.Label(frame_bottom_right, text="User Log", font=("Arial", 14)).pack(anchor="nw")
        self.log_box = scrolledtext.ScrolledText(
            frame_bottom_right, wrap=tk.WORD, width=60, height=20
        )
        self.log_box.pack(expand=True, fill="both", padx=10, pady=10)

        self.add_log("System Ready.")

        self.cap = cv2.VideoCapture(0)
        self._after_id = None
        self._update_streams()

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _update_streams(self):
        if not self.cap or not self.cap.isOpened():
            self._after_id = self.root.after(500, self._update_streams)
            return

        ok, frame = self.cap.read()
        if ok:
            # raw
            raw_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            raw_imgtk = ImageTk.PhotoImage(Image.fromarray(raw_rgb))
            self.raw_label.configure(image=raw_imgtk)
            self.raw_label.image = raw_imgtk

            # processed
            processed = process_frame(frame.copy())
            proc_rgb = cv2.cvtColor(processed, cv2.COLOR_BGR2RGB)
            proc_imgtk = ImageTk.PhotoImage(Image.fromarray(proc_rgb))
            self.proc_label.configure(image=proc_imgtk)
            self.proc_label.image = proc_imgtk

        self._after_id = self.root.after(15, self._update_streams)

    def _on_close(self):
        if self._after_id is not None:
            try:
                self.root.after_cancel(self._after_id)
            except:
                pass
            self._after_id = None

        if getattr(self, "cap", None) is not None:
            try:
                self.cap.release()
            except:
                pass
            self.cap = None

        self.root.destroy()

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

