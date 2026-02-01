import threading
import time
import json
import csv
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

class AttackTool(tk.Tk):
    def __init__(self):
        super().__init__()
        self.withdraw()
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.threads = []
        self.lock = threading.Lock()

        # Initialize variables
        self.reset_state()

        # Show login prompt
        self.show_login()

    def show_login(self):
        def on_login_success():
            self.deiconify()
            self.build_ui()
            self.setup_plot()
            self.reset_state()

        LoginPrompt(self, on_login_success)

    def build_ui(self):
        self.title("Yelx V3 - Hacker Panel")
        self.geometry("1300x900")
        self.configure(bg="#2e2e2e")

        # Menu bar
        menu_bar = tk.Menu(self)
        help_menu = tk.Menu(menu_bar, tearoff=0)
        help_menu.add_command(label="Help", command=self.show_help)
        help_menu.add_command(label="About", command=lambda: messagebox.showinfo("About", "Attack Tool v2.0"))
        menu_bar.add_cascade(label="Help", menu=help_menu)

        theme_menu = tk.Menu(menu_bar, tearoff=0)
        theme_menu.add_command(label="Dark Mode", command=self.toggle_dark_mode)
        theme_menu.add_command(label="Light Mode", command=self.toggle_light_mode)
        menu_bar.add_cascade(label="Themes", menu=theme_menu)

        self.config(menu=menu_bar)

        # Main Paned window for layout
        paned = ttk.Panedwindow(self, orient='horizontal')
        paned.pack(fill='both', expand=True, padx=10, pady=10)

        # Left Frame: Controls & Stats
        left_frame = ttk.Frame(paned, width=350)
        paned.add(left_frame, weight=1)

        # Right Frame: Logs & Plot
        right_frame = ttk.Frame(paned)
        paned.add(right_frame, weight=2)

        # --- Left Frame: Controls/Stats ---
        self.build_control_panel(left_frame)
        self.build_stats_panel(left_frame)
        self.build_advanced_settings(left_frame)

        # --- Right Frame: Logs & Plot ---
        self.build_log_view(right_frame)
        self.build_plot_view(right_frame)

        # Status Bar
        self.create_status_bar()

        # Auto-update interval for plot & stats
        self.update_interval = 2000  # ms
        self.after(self.update_interval, self.periodic_update)

    def build_control_panel(self, parent):
        ttk.Label(parent, text="Attack Controls", font=('Segoe UI', 14, 'bold')).pack(pady=5)

        # Target URL
        url_frame = ttk.Frame(parent)
        url_frame.pack(fill='x', pady=3, padx=10)
        ttk.Label(url_frame, text="Target URL:").pack(side='left')
        self.url_entry = ttk.Entry(url_frame)
        self.url_entry.pack(side='left', fill='x', expand=True, padx=5)

        # Username list file
        user_frame = ttk.Frame(parent)
        user_frame.pack(fill='x', pady=3, padx=10)
        ttk.Label(user_frame, text="Usernames File:").pack(side='left')
        self.username_entry = ttk.Entry(user_frame)
        self.username_entry.pack(side='left', fill='x', expand=True, padx=5)
        ttk.Button(user_frame, text="Browse", command=self.browse_usernames).pack(side='left', padx=2)

        # Password list file
        pass_frame = ttk.Frame(parent)
        pass_frame.pack(fill='x', pady=3, padx=10)
        ttk.Label(pass_frame, text="Passwords File:").pack(side='left')
        self.password_entry = ttk.Entry(pass_frame)
        self.password_entry.pack(side='left', fill='x', expand=True, padx=5)
        ttk.Button(pass_frame, text="Browse", command=self.browse_passwords).pack(side='left', padx=2)

        # Thread count & delay
        param_frame = ttk.Frame(parent)
        param_frame.pack(fill='x', pady=5, padx=10)

        ttk.Label(param_frame, text="Threads:").grid(row=0, column=0, sticky='w')
        self.thread_count_var = tk.IntVar(value=10)
        ttk.Spinbox(param_frame, from_=1, to=50, textvariable=self.thread_count_var, width=5).grid(row=0, column=1, padx=5)

        ttk.Label(param_frame, text="Delay (ms):").grid(row=0, column=2, sticky='w')
        self.delay_var = tk.IntVar(value=0)
        ttk.Spinbox(param_frame, from_=0, to=5000, increment=100, textvariable=self.delay_var, width=7).grid(row=0, column=3, padx=5)

        # Success keyword
        ttk.Label(param_frame, text="Success Keyword:").grid(row=1, column=0, sticky='w', pady=3)
        self.success_keyword = ttk.Entry(param_frame)
        self.success_keyword.grid(row=1, column=1, padx=5, pady=3)

        # Buttons: Start, Pause/Resume, Stop, Reset
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(pady=8)

        self.start_btn = ttk.Button(btn_frame, text="Start", command=self.start_attack)
        self.start_btn.grid(row=0, column=0, padx=4)

        self.pause_resume_btn = ttk.Button(btn_frame, text="Pause", command=self.toggle_pause_resume, state='disabled')
        self.pause_resume_btn.grid(row=0, column=1, padx=4)

        self.stop_btn = ttk.Button(btn_frame, text="Stop", command=self.stop_attack, state='disabled')
        self.stop_btn.grid(row=0, column=2, padx=4)

        self.reset_btn = ttk.Button(btn_frame, text="Reset", command=self.reset_all)
        self.reset_btn.grid(row=0, column=3, padx=4)

        # Export buttons
        export_frame = ttk.Frame(parent)
        export_frame.pack(pady=5)
        ttk.Button(export_frame, text="Export CSV", command=self.export_csv).grid(row=0, column=0, padx=4)
        ttk.Button(export_frame, text="Export JSON", command=self.export_json).grid(row=0, column=1, padx=4)
        ttk.Button(export_frame, text="Clear Log", command=self.clear_log).grid(row=0, column=2, padx=4)

        # Progress & stats
        self.progress_var = tk.StringVar()
        self.progress_label = ttk.Label(parent, textvariable=self.progress_var)
        self.progress_label.pack(pady=2)

        self.progress_bar = ttk.Progressbar(parent, length=300, mode='determinate')
        self.progress_bar.pack(pady=2, fill='x', padx=10)

        # Status indicator
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill='x', pady=5)
        ttk.Label(status_frame, text="Status:").pack(side='left')
        self.status_indicator = ttk.Label(status_frame, text="Ready", background='grey', foreground='white', width=10)
        self.status_indicator.pack(side='left', padx=5)

    def build_stats_panel(self, parent):
        ttk.Label(parent, text="Real-Time Stats", font=('Segoe UI', 12, 'bold')).pack(pady=4)
        stats_frame = ttk.Frame(parent, relief='ridge', padding=5)
        stats_frame.pack(fill='x', padx=10, pady=5)

        ttk.Label(stats_frame, text="Attempts:").grid(row=0, column=0, sticky='w')
        self.attempts_var = tk.IntVar(value=0)
        ttk.Label(stats_frame, textvariable=self.attempts_var).grid(row=0, column=1, sticky='w')

        ttk.Label(stats_frame, text="Successes:").grid(row=1, column=0, sticky='w')
        self.successes_var = tk.IntVar(value=0)
        ttk.Label(stats_frame, textvariable=self.successes_var).grid(row=1, column=1, sticky='w')

        ttk.Label(stats_frame, text="Attempts/sec:").grid(row=2, column=0, sticky='w')
        self.rate_var = tk.StringVar(value="0.00")
        ttk.Label(stats_frame, textvariable=self.rate_var).grid(row=2, column=1, sticky='w')

        ttk.Label(stats_frame, text="Elapsed Time:").grid(row=3, column=0, sticky='w')
        self.elapsed_var = tk.StringVar(value="0s")
        ttk.Label(stats_frame, textvariable=self.elapsed_var).grid(row=3, column=1, sticky='w')

        # Progress percentage & ETA
        ttk.Label(stats_frame, text="Progress:").grid(row=4, column=0, sticky='w')
        self.progress_percent_var = tk.StringVar(value="0%")
        ttk.Label(stats_frame, textvariable=self.progress_percent_var).grid(row=4, column=1, sticky='w')

        ttk.Label(stats_frame, text="ETA:").grid(row=5, column=0, sticky='w')
        self.eta_var = tk.StringVar(value="--")
        ttk.Label(stats_frame, textvariable=self.eta_var).grid(row=5, column=1, sticky='w')

    def build_advanced_settings(self, parent):
        # Collapsible or tabbed advanced settings
        ttk.Label(parent, text="Advanced Settings", font=('Segoe UI', 12, 'bold')).pack(pady=4)

        adv_frame = ttk.Frame(parent)
        adv_frame.pack(fill='x', padx=10, pady=4)

        # Example: Toggle for verbose logging
        self.verbose_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(adv_frame, text="Verbose Logging", variable=self.verbose_var).pack(anchor='w')

        # Auto-update interval
        ttk.Label(adv_frame, text="Update Interval (ms):").pack(anchor='w', pady=2)
        self.update_interval_var = tk.IntVar(value=2000)
        ttk.Spinbox(adv_frame, from_=500, to=10000, increment=500, textvariable=self.update_interval_var).pack(anchor='w')

        # Dark mode toggle
        ttk.Button(adv_frame, text="Toggle Dark Mode", command=self.toggle_dark_mode).pack(pady=4)

    def build_log_view(self, parent):
        ttk.Label(parent, text="Logs & Console", font=('Segoe UI', 12, 'bold')).pack(pady=5)
        filter_frame = ttk.Frame(parent)
        filter_frame.pack(fill='x', padx=10)

        ttk.Label(filter_frame, text="Filter:").pack(side='left')
        self.log_filter_var = tk.StringVar()
        filter_entry = ttk.Entry(filter_frame, textvariable=self.log_filter_var)
        filter_entry.pack(side='left', fill='x', expand=True, padx=5)
        filter_entry.bind("<KeyRelease>", self.filter_logs)

        self.log_text = tk.Text(parent, wrap='word', height=15, state='disabled')
        self.log_text.pack(fill='both', expand=True, padx=10, pady=5)

    def build_plot_view(self, parent):
        ttk.Label(parent, text="Progress Plot", font=('Segoe UI', 12, 'bold')).pack(pady=5)
        self.figure = plt.Figure(figsize=(6, 3), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.ax.set_title("Attack Progress")
        self.ax.set_xlabel("Time (s)")
        self.ax.set_ylabel("Count")
        self.canvas = FigureCanvasTkAgg(self.figure, master=parent)
        self.canvas.get_tk_widget().pack(fill='both', expand=True, padx=10, pady=5)

    def create_status_bar(self):
        self.status_var = tk.StringVar(value="Ready")
        self.status_bar = ttk.Label(self, textvariable=self.status_var, relief='sunken', anchor='w')
        self.status_bar.pack(side='bottom', fill='x')
        # Color indicator for status
        self.status_indicator = ttk.Label(self, text="●", foreground='grey', font=('Segoe UI', 12))
        self.status_indicator.place(relx=0.02, rely=0.97, anchor='sw')

    def update_status(self, message, color='grey'):
        self.status_var.set(message)
        self.status_indicator.config(foreground=color)

    def toggle_dark_mode(self):
        # Switch theme: dark/light
        style = ttk.Style()
        if hasattr(self, 'dark_mode') and self.dark_mode:
            # Light mode
            style.theme_use('clam')
            self.configure(bg="#f0f0f0")
            self.update_status("Light Mode", color='black')
            self.dark_mode = False
        else:
            # Dark mode
            style.theme_use('clam')
            self.configure(bg="#2e2e2e")
            self.update_status("Dark Mode", color='white')
            self.dark_mode = True

    def toggle_light_mode(self):
        self.toggle_dark_mode()

    def reset_state(self):
        self.is_running = False
        self.is_paused = False
        self.log_data = []
        self.times = []
        self.attempts_counts = []
        self.success_counts = []
        self.start_time = None
        self.attempts = 0
        self.successful_attempts = 0

        self.usernames = []
        self.passwords = []

        self.update_log_message("System reset and ready.")
        self.progress_var.set("Ready")
        self.progress_bar['value'] = 0
        self.update_status("Ready")
        self.status_indicator.config(foreground='grey')

        # Update stats
        self.attempts_var.set(0)
        self.successes_var.set(0)
        self.rate_var.set("0.00")
        self.elapsed_var.set("0s")
        self.progress_percent_var.set("0%")
        self.eta_var.set("--")

        # Button states
        self.start_btn.config(state='normal')
        self.pause_resume_btn.config(state='disabled', text='Pause')
        self.stop_btn.config(state='disabled')
        self.reset_btn.config(state='normal')

    def update_log_message(self, message):
        if self.verbose_var.get():
            self.log_text['state'] = 'normal'
            self.log_text.insert('end', message + '\n')
            self.log_text.see('end')
            self.log_text['state'] = 'disabled'

    def show_help(self):
        msg = (
            "Upgrade features:\n"
            "- Dark Mode toggle\n"
            "- Real-time stats panel\n"
            "- Progress plot with live updates\n"
            "- Adjustable auto-refresh interval\n"
            "- Log filtering/search\n"
            "- Reset all logs/stats\n"
            "- Theme options via menu\n"
            "- Status indicator with color\n"
        )
        messagebox.showinfo("Help", msg)

    def browse_usernames(self):
        filename = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt;*.csv"), ("All Files", "*.*")])
        if filename:
            self.username_entry.delete(0, 'end')
            self.username_entry.insert(0, filename)
            self.usernames = self.load_list(filename)

    def browse_passwords(self):
        filename = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt;*.csv"), ("All Files", "*.*")])
        if filename:
            self.password_entry.delete(0, 'end')
            self.password_entry.insert(0, filename)
            self.passwords = self.load_list(filename)

    def load_list(self, filepath):
        try:
            with open(filepath, 'r') as f:
                return [line.strip() for line in f if line.strip()]
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file: {e}")
            return []

    def start_attack(self):
        self.target_url = self.url_entry.get()

        # Load lists if not loaded
        if not hasattr(self, 'usernames') or not self.usernames:
            self.usernames = self.load_list(self.username_entry.get())
        if not hasattr(self, 'passwords') or not self.passwords:
            self.passwords = self.load_list(self.password_entry.get())

        if not self.target_url or not self.usernames or not self.passwords:
            messagebox.showerror("Error", "Fill all fields and select valid lists.")
            return

        # Reset logs & plot
        self.reset_state()
        self.start_time = time.time()

        # Launch threads
        self.is_running = True
        self.is_paused = False
        self.threads = []

        thread_count = self.thread_count_var.get()
        for _ in range(thread_count):
            t = threading.Thread(target=self.worker)
            t.daemon = True
            t.start()
            self.threads.append(t)

        # Update buttons
        self.start_btn.config(state='disabled')
        self.pause_resume_btn.config(state='normal', text='Pause')
        self.stop_btn.config(state='normal')
        self.update_status("Running...", color='green')
        self.status_indicator.config(foreground='green')

        # Schedule periodic updates
        self.after(self.update_interval, self.periodic_update)

    def toggle_pause_resume(self):
        if self.is_paused:
            # Resume
            self.is_paused = False
            self.pause_resume_btn.config(text='Pause')
            self.update_status("Running...", color='green')
            self.status_indicator.config(foreground='green')
        else:
            # Pause
            self.is_paused = True
            self.pause_resume_btn.config(text='Resume')
            self.update_status("Paused", color='orange')
            self.status_indicator.config(foreground='orange')

    def stop_attack(self):
        self.is_running = False
        for t in self.threads:
            t.join(timeout=1)
        self.start_btn.config(state='normal')
        self.pause_resume_btn.config(state='disabled', text='Pause')
        self.stop_btn.config(state='disabled')
        self.update_status("Stopped.", color='red')
        self.status_indicator.config(foreground='red')
        self.update_plot()
        self.update_progress(final=True)

    def reset_all(self):
        self.is_running = False
        for t in self.threads:
            t.join(timeout=1)
        self.reset_state()

    def worker(self):
        while self.is_running:
            if self.is_paused:
                time.sleep(0.1)
                continue
            with self.lock:
                index = self.attempts % len(self.usernames)
                username = self.usernames[index]
                password = self.passwords[index]
                self.attempts += 1

            success = self.mock_login(username, password)
            with self.lock:
                if success:
                    self.successful_attempts += 1
                    status = 'Success'
                else:
                    status = 'Fail'

                self.log_data.append({
                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'username': username,
                    'password': password,
                    'status': status
                })

            # Log message
            self.update_log_message(f"{time.strftime('%H:%M:%S')} | {username} | {password} | {status}")

            # Delay
            delay = self.delay_var.get() / 1000
            if delay > 0:
                time.sleep(delay)

            # Update stats
            elapsed = time.time() - self.start_time
            self.times.append(elapsed)
            self.attempts_counts.append(self.attempts)
            self.success_counts.append(self.successful_attempts)

    def mock_login(self, username, password):
        import random
        return random.random() < 0.01

    def periodic_update(self):
        # Update stats
        if self.start_time:
            elapsed = time.time() - self.start_time
        else:
            elapsed = 0

        self.attempts_var.set(self.attempts)
        self.successes_var.set(self.successful_attempts)
        rate = self.attempts / elapsed if elapsed > 0 else 0
        self.rate_var.set(f"{rate:.2f}")

        # Elapsed
        self.elapsed_var.set(f"{int(elapsed)}s")

        # Progress
        total_attempts = self.attempts
        total_targets = len(self.usernames) if hasattr(self, 'usernames') else 1
        progress_pct = (total_attempts / max(1, total_targets)) * 100
        self.progress_bar['value'] = min(100, progress_pct)
        self.progress_percent_var.set(f"{progress_pct:.1f}%")

        # ETA estimate
        remaining = max(0, (total_targets - total_attempts) / rate) if rate > 0 else None
        if remaining:
            eta_seconds = int(remaining)
            self.eta_var.set(f"{eta_seconds}s")
        else:
            self.eta_var.set("--")

        # Schedule next update
        if self.is_running:
            self.after(self.update_interval, self.periodic_update)

        # Update plot
        self.update_plot()

    def update_plot(self):
        self.ax.clear()
        self.ax.plot(self.times, self.attempts_counts, label='Attempts', color='cyan')
        self.ax.plot(self.times, self.success_counts, label='Successes', color='lime')
        self.ax.set_title("Attack Progress")
        self.ax.set_xlabel("Time (s)")
        self.ax.set_ylabel("Count")
        self.ax.legend()
        self.canvas.draw()

    def export_csv(self):
        filename = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])
        if filename:
            try:
                with open(filename, 'w', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=['timestamp', 'username', 'password', 'status'])
                    writer.writeheader()
                    for row in self.log_data:
                        writer.writerow(row)
                messagebox.showinfo("Export", "CSV exported successfully.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export CSV: {e}")

    def export_json(self):
        filename = filedialog.asksaveasfilename(defaultextension=".json")
        if filename:
            try:
                with open(filename, 'w') as f:
                    json.dump(self.log_data, f, indent=4)
                messagebox.showinfo("Export", "JSON exported successfully.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export JSON: {e}")

    def clear_log(self):
        self.log_text['state'] = 'normal'
        self.log_text.delete('1.0', 'end')
        self.log_text['state'] = 'disabled'
        self.log_data = []

    def on_close(self):
        self.is_running = False
        for t in self.threads:
            t.join(timeout=1)
        self.destroy()

# --- Login prompt class ---
class LoginPrompt(tk.Toplevel):
    def __init__(self, master, on_success):
        super().__init__(master)
        self.on_success = on_success
        self.title("Login")
        self.geometry("350x180")
        self.configure(bg="#111")
        self.resizable(False, False)
        self.setup_widgets()

    def setup_widgets(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('.', background='#111', foreground='white')
        style.configure('TLabel', background='#111', foreground='white')
        style.configure('TEntry', fieldbackground='#222', foreground='white')
        style.configure('TButton', background='#333', foreground='white')
        style.map('TButton', background=[('active', '#555')])

        ttk.Label(self, text="Username:").pack(pady=5)
        self.username_entry = ttk.Entry(self)
        self.username_entry.pack(pady=5, fill='x', padx=20)
        ttk.Label(self, text="Password:").pack(pady=5)
        self.password_entry = ttk.Entry(self, show='*')
        self.password_entry.pack(pady=5, fill='x', padx=20)
        ttk.Button(self, text="Login", command=self.check_credentials).pack(pady=12)

        self.username_entry.focus()

    def check_credentials(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        if username == "Yelx" and password == "Bergue5mb":
            self.destroy()
            self.on_success()
        else:
            messagebox.showerror("Error", "Invalid credentials!")

if __name__ == "__main__":
    app = AttackTool()
    app.mainloop()
