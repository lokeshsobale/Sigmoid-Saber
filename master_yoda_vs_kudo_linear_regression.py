import tkinter as tk
from tkinter import messagebox
import random


class LinearRegressionAcademyGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Master Yoda's Linear Regression Academy: Defeat Kudo Step-by-Step")
        self.root.geometry("1150x760")
        self.root.configure(bg="#0b0f19")
        self.root.resizable(False, False)

        # Progression State (4 Stages, 25 HP damage per stage)
        self.kudo_hp = 100
        self.stage = 1
        self.laser_flash = False

        # Stage 1 State: Variable Mapping & Live Data Collection
        self.axes_correct = False
        self.collected_x = []
        self.collected_y = []
        self.s1_true_m = 2.0
        self.s1_true_c = 3.0

        # Stage 2 State: Intercept (c) first, then Slope (m)
        self.s2_step = "INTERCEPT"  # "INTERCEPT" -> "SLOPE"
        self.s2_true_m = 2.0
        self.s2_true_c = 4.0
        self.s2_x = [0, 1, 2, 3, 4, 5, 6]
        self.s2_y = [self.s2_true_m * x + self.s2_true_c for x in self.s2_x]

        # Stage 3 State: Real-World Noise, Residuals & OLS MSE
        self.s3_x = []
        self.s3_y = []
        self.ols_m = 0.0
        self.ols_c = 0.0
        self.ols_mse = 0.0
        self.show_ols_gold = False

        # Stage 4 State: Future Outcome Prediction
        self.future_x = 8.5
        self.future_true_y = 0.0
        self.revealed_kudo = False

        self.build_ui()
        self.load_stage(1)

    # =========================================================================
    # UI CONSTRUCTION
    # =========================================================================
    def build_ui(self):
        # Top Boss Battle Arena Banner
        self.banner = tk.Canvas(
            self.root, width=1110, height=165, bg="#111827",
            highlightthickness=2, highlightbackground="#334155"
        )
        self.banner.pack(padx=15, pady=(10, 6))

        # Lower Split Container
        body = tk.Frame(self.root, bg="#0b0f19")
        body.pack(fill=tk.BOTH, expand=True, padx=15, pady=6)

        # Left Interactive Graph Canvas
        self.graph = tk.Canvas(
            body, width=680, height=545, bg="#0f172a",
            highlightthickness=2, highlightbackground="#334155"
        )
        self.graph.pack(side=tk.LEFT, padx=(0, 12))

        # Right Interactive Lesson & Control Deck
        self.panel = tk.Frame(
            body, width=415, height=545, bg="#1e293b",
            highlightthickness=2, highlightbackground="#334155"
        )
        self.panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self.panel.pack_propagate(False)

        self.stage_header = tk.Label(
            self.panel, text="", font=("Consolas", 12, "bold"),
            fg="#4ade80", bg="#1e293b", wraplength=385, justify="left"
        )
        self.stage_header.pack(anchor="w", padx=14, pady=(12, 6))

        self.lesson_box = tk.Label(
            self.panel, text="", font=("Consolas", 10),
            fg="#e2e8f0", bg="#0f172a", wraplength=375, justify="left",
            padx=10, pady=10, relief=tk.RIDGE, bd=1
        )
        self.lesson_box.pack(fill=tk.X, padx=14, pady=4)

        # Dynamic Controls Frame (Swapped per stage)
        self.controls_area = tk.Frame(self.panel, bg="#1e293b")
        self.controls_area.pack(fill=tk.X, padx=14, pady=6)

        # Live Math Explanation Box
        self.math_box = tk.Label(
            self.panel, text="", font=("Consolas", 10, "bold"),
            fg="#38bdf8", bg="#090d16", wraplength=375, justify="left",
            padx=10, pady=8, relief=tk.SOLID, bd=1
        )
        self.math_box.pack(fill=tk.X, padx=14, pady=6)

        # Feedback / Coach Hint Box
        self.coach_lbl = tk.Label(
            self.panel, text="", font=("Consolas", 9, "italic"),
            fg="#fde047", bg="#1e293b", wraplength=385, justify="left"
        )
        self.coach_lbl.pack(anchor="w", padx=14, pady=4)

        # Bottom Navigation Bar
        nav = tk.Frame(self.panel, bg="#1e293b")
        nav.pack(side=tk.BOTTOM, fill=tk.X, padx=14, pady=10)

        tk.Button(
            nav, text="📘 Full Concept Summary", font=("Consolas", 9, "bold"),
            bg="#475569", fg="white", command=self.show_summary_popup
        ).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 4))

        tk.Button(
            nav, text="🔁 Restart Academy", font=("Consolas", 9, "bold"),
            bg="#7f1d1d", fg="white", command=lambda: self.load_stage(1, reset_all=True)
        ).pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=(4, 0))

    # =========================================================================
    # STAGE MANAGEMENT & CONTROLS BUILDER
    # =========================================================================
    def clear_controls(self):
        for widget in self.controls_area.winfo_children():
            widget.destroy()

    def load_stage(self, stage_num, reset_all=False):
        if reset_all:
            self.kudo_hp = 100
        self.stage = stage_num
        self.laser_flash = False
        self.clear_controls()

        if stage_num == 1:
            self.axes_correct = False
            self.collected_x = []
            self.collected_y = []
            self.s1_true_m = random.choice([1.5, 2.0, 2.5])
            self.s1_true_c = random.choice([2.0, 3.0, 4.0])

            self.stage_header.config(
                text="STAGE 1 (100 -> 75 HP): INDEPENDENT (X) vs. DEPENDENT (Y) VARIABLES"
            )
            self.lesson_box.config(
                text="WHAT IS LINEAR REGRESSION?\n"
                     "It is a method to predict a future outcome (Dependent Variable Y) "
                     "using a known input (Independent Variable X).\n\n"
                     "• Independent Variable (X-Axis): The INPUT we control (Charge Time in sec).\n"
                     "• Dependent Variable (Y-Axis): The OUTPUT that depends on X (Laser Power)."
            )

            tk.Label(
                self.controls_area, text="Step 1: Choose which variable goes on the X-Axis (Input):",
                font=("Consolas", 9, "bold"), fg="#facc15", bg="#1e293b"
            ).pack(anchor="w", pady=(2, 4))

            btn_row = tk.Frame(self.controls_area, bg="#1e293b")
            btn_row.pack(fill=tk.X, pady=2)
            tk.Button(
                btn_row, text="Set X = Charge Time (Input)\nSet Y = Beam Power (Output)",
                font=("Consolas", 9, "bold"), bg="#0284c7", fg="white",
                command=lambda: self.set_axes_choice(True)
            ).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 3))

            tk.Button(
                btn_row, text="Set X = Beam Power\nSet Y = Charge Time",
                font=("Consolas", 9, "bold"), bg="#334155", fg="white",
                command=lambda: self.set_axes_choice(False)
            ).pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=(3, 0))

            self.collect_btn = tk.Button(
                self.controls_area, text="⚡ Step 2: Fire Test Shot to Collect Data (0/6)",
                font=("Consolas", 10, "bold"), bg="#16a34a", fg="white",
                state=tk.DISABLED, pady=6, command=self.collect_next_point
            )
            self.collect_btn.pack(fill=tk.X, pady=(10, 4))

            self.coach_lbl.config(
                text=" Yoda says: 'First, identify which variable is the Cause (X) and which is the Effect (Y)!'"
            )

        elif stage_num == 2:
            self.s2_step = "INTERCEPT"
            self.s2_true_c = float(random.randint(2, 6))
            self.s2_true_m = random.choice([1.5, 2.0, 2.5])
            self.s2_x = [0, 1, 2, 3, 4, 5, 6]
            self.s2_y = [self.s2_true_m * x + self.s2_true_c for x in self.s2_x]

            self.stage_header.config(
                text="STAGE 2 (75 -> 50 HP): HOW A LINE WORKS (y = m*x + c)"
            )
            self.lesson_box.config(
                text="Every straight line follows the formula:  y = m*x + c\n\n"
                     "1. INTERCEPT (c): The starting value of Y when X = 0 (where the line crosses the vertical Y-axis).\n"
                     "2. SLOPE (m): Steepness! How much Y increases every time X goes up by +1."
            )

            tk.Label(
                self.controls_area, text="1. Adjust Baseline Intercept (c) [Value of Y at X = 0]:",
                font=("Consolas", 9, "bold"), fg="#facc15", bg="#1e293b"
            ).pack(anchor="w")
            self.s2_c_slider = tk.Scale(
                self.controls_area, from_=0.0, to=10.0, resolution=0.5,
                orient=tk.HORIZONTAL, bg="#0f172a", fg="white", highlightthickness=0,
                command=lambda _: self.refresh_all()
            )
            self.s2_c_slider.set(0.0)
            self.s2_c_slider.pack(fill=tk.X, pady=(0, 6))

            tk.Label(
                self.controls_area, text="2. Adjust Rate of Change / Slope (m) [Rise per +1 X]:",
                font=("Consolas", 9, "bold"), fg="#38bdf8", bg="#1e293b"
            ).pack(anchor="w")
            self.s2_m_slider = tk.Scale(
                self.controls_area, from_=0.0, to=4.0, resolution=0.25,
                orient=tk.HORIZONTAL, bg="#0f172a", fg="white", highlightthickness=0,
                state=tk.DISABLED, command=lambda _: self.refresh_all()
            )
            self.s2_m_slider.set(0.0)
            self.s2_m_slider.pack(fill=tk.X, pady=(0, 8))

            self.s2_btn = tk.Button(
                self.controls_area, text="🔒 Lock In Intercept (c) at X = 0",
                font=("Consolas", 10, "bold"), bg="#0284c7", fg="white", pady=6,
                command=self.handle_stage2_action
            )
            self.s2_btn.pack(fill=tk.X)
            self.coach_lbl.config(
                text=f"Look at X = 0 on the left axis. Move Intercept (c) to match the first glowing crystal!"
            )

        elif stage_num == 3:
            self.show_ols_gold = False
            self.s3_x = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0]
            base_m = random.choice([1.6, 2.0, 2.4])
            base_c = random.choice([2.0, 3.5, 5.0])
            self.s3_y = [
                round(base_m * x + base_c + random.uniform(-2.2, 2.2), 2)
                for x in self.s3_x
            ]
            # Exact Ordinary Least Squares (OLS) calculation
            n = len(self.s3_x)
            mx = sum(self.s3_x) / n
            my = sum(self.s3_y) / n
            num = sum((self.s3_x[i] - mx) * (self.s3_y[i] - my) for i in range(n))
            den = sum((self.s3_x[i] - mx) ** 2 for i in range(n))
            self.ols_m = num / den
            self.ols_c = my - self.ols_m * mx
            self.ols_mse = sum(
                (self.s3_y[i] - (self.ols_m * self.s3_x[i] + self.ols_c)) ** 2
                for i in range(n)
            ) / n

            self.stage_header.config(
                text="STAGE 3 (50 -> 25 HP): REAL-WORLD NOISE, RESIDUALS & MSE"
            )
            self.lesson_box.config(
                text="In real life, data has random noise—no straight line can touch every point!\n"
                     "• RESIDUAL (Red Dashed Line): Vertical distance between Actual Data (y) and Predicted Line (y_hat):  Error = y - y_hat\n"
                     "• MEAN SQUARED ERROR (MSE): Average of (Error)^2. We square errors so negative and positive gaps don't cancel out!"
            )

            tk.Label(
                self.controls_area, text="Adjust Slope (m) to minimize Red Residuals:",
                font=("Consolas", 9, "bold"), fg="#facc15", bg="#1e293b"
            ).pack(anchor="w")
            self.s3_m_slider = tk.Scale(
                self.controls_area, from_=0.0, to=3.5, resolution=0.05,
                orient=tk.HORIZONTAL, bg="#0f172a", fg="white", highlightthickness=0,
                command=lambda _: self.refresh_all()
            )
            self.s3_m_slider.set(0.5)
            self.s3_m_slider.pack(fill=tk.X, pady=(0, 4))

            tk.Label(
                self.controls_area, text="Adjust Intercept (c) to balance the line:",
                font=("Consolas", 9, "bold"), fg="#facc15", bg="#1e293b"
            ).pack(anchor="w")
            self.s3_c_slider = tk.Scale(
                self.controls_area, from_=-1.0, to=8.0, resolution=0.1,
                orient=tk.HORIZONTAL, bg="#0f172a", fg="white", highlightthickness=0,
                command=lambda _: self.refresh_all()
            )
            self.s3_c_slider.set(1.0)
            self.s3_c_slider.pack(fill=tk.X, pady=(0, 6))

            tk.Button(
                self.controls_area, text="⚡ FIRE BEST-FIT OLS BEAM (COMPARE MSE!)",
                font=("Consolas", 10, "bold"), bg="#16a34a", fg="white", pady=6,
                command=self.handle_stage3_attack
            ).pack(fill=tk.X)

            self.coach_lbl.config(
                text="Shrink the red vertical error bars until 'Your Live MSE' gets close to the Minimum OLS MSE!"
            )

        elif stage_num == 4:
            self.revealed_kudo = False
            self.future_x = random.choice([8.0, 8.5, 9.0, 9.5])
            self.future_true_y = round(self.ols_m * self.future_x + self.ols_c, 2)

            self.stage_header.config(
                text="STAGE 4 (25 -> 0 HP): PREDICTING THE FUTURE OUTCOME!"
            )
            self.lesson_box.config(
                text="WHY DID WE FIND THE BEST-FIT LINE?\n"
                     "So we can PREDICT future outcomes for inputs we have never seen!\n\n"
                     f"We only have past data for X = 1 to 7 sec. Kudo is hiding in the future at "
                     f"X = {self.future_x} sec! Use your equation y_hat = m*x + c to predict his Y height!"
            )

            tk.Label(
                self.controls_area,
                text=f"Aim Yoda's Prediction Crosshair for Future X = {self.future_x}:",
                font=("Consolas", 9, "bold"), fg="#38bdf8", bg="#1e293b"
            ).pack(anchor="w", pady=(4, 2))

            self.s4_pred_slider = tk.Scale(
                self.controls_area, from_=5.0, to=28.0, resolution=0.2,
                orient=tk.HORIZONTAL, bg="#0f172a", fg="white", highlightthickness=0,
                command=lambda _: self.refresh_all()
            )
            self.s4_pred_slider.set(10.0)
            self.s4_pred_slider.pack(fill=tk.X, pady=(0, 10))

            tk.Button(
                self.controls_area, text="🎯 LOCK PREDICTION & FIRE FINAL STRIKE!",
                font=("Consolas", 10, "bold"), bg="#dc2626", fg="white", pady=7,
                command=self.handle_stage4_strike
            ).pack(fill=tk.X)

            self.coach_lbl.config(
                text=f"Plug X = {self.future_x} into your fitted line: y_hat = ({self.ols_m:.2f} * {self.future_x}) + {self.ols_c:.2f}"
            )

        self.refresh_all()

    # =========================================================================
    # INTERACTIVE STAGE HANDLERS
    # =========================================================================
    def set_axes_choice(self, is_correct):
        if not is_correct:
            self.coach_lbl.config(
                text="❌ Wait! Does Beam Power cause Charge Time? No! You control Charge Time (Input X), and Beam Power (Output Y) depends on it!"
            )
            return
        self.axes_correct = True
        self.collect_btn.config(state=tk.NORMAL)
        self.coach_lbl.config(
            text="✅ Correct! Charge Time is the Independent Variable (X) and Beam Power is the Dependent Variable (Y). Now click 'Fire Test Shot' 6 times!"
        )
        self.refresh_all()

    def collect_next_point(self):
        next_x = len(self.collected_x) + 1
        if next_x <= 6:
            y_val = self.s1_true_m * next_x + self.s1_true_c
            self.collected_x.append(next_x)
            self.collected_y.append(y_val)
            self.collect_btn.config(
                text=f"⚡ Step 2: Fire Test Shot to Collect Data ({len(self.collected_x)}/6)"
            )
            self.coach_lbl.config(
                text=f"Observed Data Point #{next_x}: When Input X = {next_x} sec, Output Y = {y_val:.1f} Power! Notice the upward linear pattern!"
            )
            self.refresh_all()

        if len(self.collected_x) == 6:
            self.laser_flash = True
            self.kudo_hp = 75
            self.refresh_all()
            self.root.after(
                600,
                lambda: (
                    messagebox.showinfo(
                        "Stage 1 Complete! (-25 HP to Kudo)",
                        "You discovered Independent (X) vs. Dependent (Y) variables!\n\n"
                        "Notice how as X (Charge Time) increases, Y (Beam Power) increases in a straight-line trend.\n\n"
                        "Next: Let's learn the math equation that draws a line through these points!"
                    ),
                    self.load_stage(2)
                )
            )

    def handle_stage2_action(self):
        if self.s2_step == "INTERCEPT":
            c_guess = self.s2_c_slider.get()
            if abs(c_guess - self.s2_true_c) <= 0.5:
                self.s2_c_slider.set(self.s2_true_c)
                self.s2_c_slider.config(state=tk.DISABLED)
                self.s2_m_slider.config(state=tk.NORMAL)
                self.s2_step = "SLOPE"
                self.s2_btn.config(
                    text="⚡ Fire Calibrated Line (Lock In Slope m!)", bg="#16a34a"
                )
                self.coach_lbl.config(
                    text=f"✅ Awesome! Intercept c = {self.s2_true_c:.1f} is locked at X=0. Now adjust Slope (m) so the beam tilts through all the crystals!"
                )
            else:
                self.coach_lbl.config(
                    text=f"❌ Look at X = 0 on the vertical Y-axis. The first crystal is at Y = {self.s2_true_c:.1f}, not {c_guess:.1f}!"
                )
        else:
            m_guess = self.s2_m_slider.get()
            if abs(m_guess - self.s2_true_m) <= 0.25:
                self.s2_m_slider.set(self.s2_true_m)
                self.laser_flash = True
                self.kudo_hp = 50
                self.refresh_all()
                self.root.after(
                    600,
                    lambda: (
                        messagebox.showinfo(
                            "Stage 2 Complete! (-25 HP to Kudo)",
                            f"Perfect Line Calibration: y = {self.s2_true_m:.1f}x + {self.s2_true_c:.1f}!\n\n"
                            f"• Intercept (c = {self.s2_true_c:.1f}) set the starting height at X = 0.\n"
                            f"• Slope (m = {self.s2_true_m:.1f}) made Y rise by +{self.s2_true_m:.1f} for every +1 step in X.\n\n"
                            "Next: What happens when Kudo adds real-world random noise so the points don't line up perfectly?"
                        ),
                        self.load_stage(3)
                    )
                )
            else:
                self.coach_lbl.config(
                    text=f"❌ Not quite aligned! Every time X goes up by 1, Y increases by {self.s2_true_m:.1f}. Set Slope (m) to {self.s2_true_m:.1f}!"
                )
        self.refresh_all()

    def handle_stage3_attack(self):
        m = self.s3_m_slider.get()
        c = self.s3_c_slider.get()
        n = len(self.s3_x)
        player_mse = sum((self.s3_y[i] - (m * self.s3_x[i] + c)) ** 2 for i in range(n)) / n
        self.show_ols_gold = True
        self.refresh_all()

        if player_mse <= self.ols_mse + 0.45:
            self.laser_flash = True
            self.kudo_hp = 25
            self.refresh_all()
            self.root.after(
                700,
                lambda: (
                    messagebox.showinfo(
                        "Stage 3 Complete! (-25 HP to Kudo)",
                        f"Direct OLS Strike!\nYour MSE: {player_mse:.2f} | Minimum Possible OLS MSE: {self.ols_mse:.2f}\n\n"
                        "You discovered how Linear Regression fits noisy data:\n"
                        "It finds the unique Slope (m) and Intercept (c) that minimize the Mean Squared Error (MSE) of the vertical residuals!\n\n"
                        "Final Stage: Use this fitted line to PREDICT the future and finish Kudo!"
                    ),
                    self.load_stage(4)
                )
            )
        else:
            self.coach_lbl.config(
                text=f"Your MSE ({player_mse:.2f}) is still higher than the Gold OLS Line's MSE ({self.ols_mse:.2f}). Align your green beam closer to the dashed Gold OLS line!"
            )

    def handle_stage4_strike(self):
        pred_y = self.s4_pred_slider.get()
        diff = abs(pred_y - self.future_true_y)
        if diff <= 0.8:
            self.revealed_kudo = True
            self.laser_flash = True
            self.kudo_hp = 0
            self.refresh_all()
            self.root.after(
                700,
                lambda: messagebox.showinfo(
                    "🏆 VICTORY! YOU MASTERED LINEAR REGRESSION!",
                    f"BULLSEYE AT FUTURE X = {self.future_x}, PREDICTED Y = {self.future_true_y:.1f}!\n\n"
                    "You just learned the complete Linear Regression workflow from scratch:\n"
                    "1. Identify Independent Input (X) & Dependent Output (Y).\n"
                    "2. Build a linear model y_hat = m*x + c using Intercept (c) and Slope (m).\n"
                    "3. Handle real-world noise by minimizing squared vertical Residuals (MSE / OLS).\n"
                    "4. Plug in a brand-new X to predict a future outcome Y!"
                )
            )
        else:
            self.coach_lbl.config(
                text=f"❌ Missed! Look at where the green regression line crosses X = {self.future_x}, or compute ({self.ols_m:.2f} * {self.future_x}) + {self.ols_c:.2f}!"
            )

    # =========================================================================
    # GRAPHICS & COORDINATE RENDERING
    # =========================================================================
    def refresh_all(self):
        self.draw_banner()
        self.draw_graph()

    def draw_banner(self):
        c = self.banner
        c.delete("all")

        # Stars
        random.seed(99)
        for _ in range(30):
            sx, sy = random.randint(10, 1100), random.randint(10, 150)
            c.create_oval(sx, sy, sx + 2, sy + 2, fill="#64748b", outline="")
        random.seed(None)

        # Master Yoda (Left)
        yx, yy = 95, 95
        c.create_oval(yx - 42, yy - 42, yx + 42, yy + 42, outline="#4ade80", width=2)
        c.create_polygon(yx - 24, yy + 38, yx + 24, yy + 38, yx + 15, yy - 4, yx - 15, yy - 4, fill="#d4ac6e", outline="#935116", width=2)
        c.create_polygon(yx - 16, yy - 16, yx - 46, yy - 24, yx - 20, yy - 5, fill="#58b368", outline="#2ecc71")
        c.create_polygon(yx + 16, yy - 16, yx + 46, yy - 24, yx + 20, yy - 5, fill="#58b368", outline="#2ecc71")
        c.create_oval(yx - 20, yy - 30, yx + 20, yy + 4, fill="#58b368", outline="#2ecc71", width=2)
        c.create_line(yx + 24, yy + 8, yx + 24, yy - 38, fill="#4ade80", width=6)
        c.create_text(yx, yy + 50, text="MASTER YODA", font=("Consolas", 10, "bold"), fill="#4ade80")

        # 4-Stage Boss Health Bar (Center)
        c.create_text(
            555, 24,
            text=f"DARK LORD KUDO — SHIELD INTEGRITY: {self.kudo_hp}% (4 LEARNING STAGES)",
            font=("Consolas", 12, "bold"), fill="#f8fafc"
        )
        bar_x1, bar_y1, bar_w, bar_h = 235, 42, 640, 30
        c.create_rectangle(bar_x1, bar_y1, bar_x1 + bar_w, bar_y1 + bar_h, fill="#1e293b", outline="#94a3b8", width=2)

        if self.kudo_hp > 0:
            fill_w = int((self.kudo_hp / 100.0) * bar_w)
            c.create_rectangle(bar_x1, bar_y1, bar_x1 + fill_w, bar_y1 + bar_h, fill="#ef4444", outline="")

        # Stage Milestone Dividers on HP Bar
        stage_labels = ["4: Predict Future", "3: Noise & MSE", "2: Slope & Intercept", "1: X vs Y Vars"]
        for i in range(4):
            sx = bar_x1 + i * (bar_w // 4)
            if i > 0:
                c.create_line(sx, bar_y1 - 3, sx, bar_y1 + bar_h + 3, fill="#facc15", width=2)
            c.create_text(sx + 80, bar_y1 + 46, text=stage_labels[i], font=("Consolas", 8, "bold"), fill="#cbd5e1")

        # Dark Lord Kudo (Right)
        kx, ky = 1015, 95
        if self.kudo_hp > 0:
            c.create_polygon(kx - 32, ky + 38, kx + 32, ky + 38, kx + 25, ky - 35, kx, ky - 45, kx - 25, ky - 35, fill="#7f1d1d", outline="#f87171", width=2)
            c.create_oval(kx - 14, ky - 16, kx - 5, ky - 7, fill="#facc15")
            c.create_oval(kx + 5, ky - 16, kx + 14, ky - 7, fill="#facc15")
            c.create_text(kx, ky + 50, text=f"KUDO ({self.kudo_hp} HP)", font=("Consolas", 10, "bold"), fill="#f87171")
        else:
            c.create_text(kx, ky, text="💥 KUDO\nDEFEATED!", font=("Consolas", 13, "bold"), fill="#4ade80")

        if self.laser_flash:
            c.create_line(yx + 30, yy - 12, kx - 30, ky, fill="#4ade80", width=7)
            c.create_line(yx + 30, yy - 12, kx - 30, ky, fill="#ffffff", width=2)

    def to_px(self, x_val, y_val):
        """Maps X in [0, 10] and Y in [0, 28] to the 680x545 graph canvas."""
        left, right = 75, 640
        top, bottom = 45, 480
        px = left + (x_val / 10.0) * (right - left)
        py = bottom - (y_val / 28.0) * (bottom - top)
        return px, py

    def draw_graph(self):
        g = self.graph
        g.delete("all")

        # Draw Grid Lines & Ticks (X: 0..10, Y: 0..28)
        for xv in range(0, 11):
            x1, y1 = self.to_px(xv, 0)
            x2, y2 = self.to_px(xv, 28)
            g.create_line(x1, y1, x2, y2, fill="#334155" if xv == 0 else "#1e293b", width=2 if xv == 0 else 1)
            g.create_text(x1, 496, text=str(xv), font=("Consolas", 9), fill="#94a3b8")

        for yv in range(0, 29, 4):
            x1, y1 = self.to_px(0, yv)
            x2, y2 = self.to_px(10, yv)
            g.create_line(x1, y1, x2, y2, fill="#334155" if yv == 0 else "#1e293b", width=2 if yv == 0 else 1)
            g.create_text(52, y1, text=str(yv), font=("Consolas", 9), fill="#94a3b8")

        # Axis Titles
        x_title = "INDEPENDENT VARIABLE (X): Charge Time (Seconds)" if (self.stage > 1 or self.axes_correct) else "X-AXIS: [Choose Variable on Right Panel]"
        y_title = "DEPENDENT VARIABLE (Y): Lightsaber Beam Power" if (self.stage > 1 or self.axes_correct) else "Y-AXIS: [Choose Variable]"
        g.create_text(360, 524, text=x_title, font=("Consolas", 10, "bold"), fill="#facc15")
        g.create_text(22, 260, text=y_title, font=("Consolas", 10, "bold"), fill="#38bdf8", angle=90)

        # ---------------- STAGE 1 RENDERING ----------------
        if self.stage == 1:
            for x, y in zip(self.collected_x, self.collected_y):
                px, py = self.to_px(x, y)
                g.create_oval(px - 7, py - 7, px + 7, py + 7, fill="#38bdf8", outline="white", width=2)
                g.create_text(px, py - 15, text=f"({x}, {y:.0f})", font=("Consolas", 8, "bold"), fill="#e2e8f0")

            if len(self.collected_x) >= 2:
                x1, y1 = self.to_px(self.collected_x[0], self.collected_y[0])
                x2, y2 = self.to_px(self.collected_x[-1], self.collected_y[-1])
                g.create_line(x1, y1, x2, y2, fill="#4ade80", width=2, dash=(5, 3))

            self.math_box.config(
                text=f"Collected Samples: {len(self.collected_x)} / 6\n"
                     f"Pattern Discovery: Every +1 sec of Charge Time (X) adds +{self.s1_true_m:.1f} Beam Power (Y)!"
            )

        # ---------------- STAGE 2 RENDERING ----------------
        elif self.stage == 2:
            c_val = self.s2_c_slider.get()
            m_val = self.s2_m_slider.get()

            # Draw target crystals
            for x, y in zip(self.s2_x, self.s2_y):
                px, py = self.to_px(x, y)
                col = "#facc15" if x == 0 else "#38bdf8"
                g.create_oval(px - 7, py - 7, px + 7, py + 7, fill=col, outline="white", width=2)

            # Draw Player's Line y = m*x + c
            lx1, ly1 = self.to_px(0, c_val)
            lx2, ly2 = self.to_px(10, m_val * 10 + c_val)
            g.create_line(lx1, ly1, lx2, ly2, fill="#4ade80", width=4)

            # Highlight Intercept at X=0
            g.create_oval(lx1 - 9, ly1 - 9, lx1 + 9, ly1 + 9, outline="#facc15", width=3)
            g.create_text(lx1 + 75, ly1 - 12, text=f"Intercept c = {c_val:.1f}", font=("Consolas", 9, "bold"), fill="#facc15")

            # Draw Rise-over-Run Slope Triangle between X=2 and X=3
            if self.s2_step == "SLOPE" and m_val > 0:
                tx1, ty1 = self.to_px(2, m_val * 2 + c_val)
                tx2, ty2 = self.to_px(3, m_val * 2 + c_val)
                tx3, ty3 = self.to_px(3, m_val * 3 + c_val)
                g.create_line(tx1, ty1, tx2, ty2, fill="#facc15", width=2)
                g.create_line(tx2, ty2, tx3, ty3, fill="#fb7185", width=3)
                g.create_text(tx2 + 45, (ty2 + ty3) / 2, text=f"Rise m = +{m_val:.2f}", font=("Consolas", 8, "bold"), fill="#fb7185")

            self.math_box.config(
                text=f"Your Line Equation : y_hat = {m_val:.2f}*x + {c_val:.1f}\n"
                     f"Target Start (X=0) : c = {self.s2_true_c:.1f}\n"
                     f"Target Steepness   : m = {self.s2_true_m:.1f}"
            )

        # ---------------- STAGE 3 RENDERING ----------------
        elif self.stage == 3:
            m_val = self.s3_m_slider.get()
            c_val = self.s3_c_slider.get()

            mse_accum = 0.0
            raw_error_sum = 0.0
            for x, y in zip(self.s3_x, self.s3_y):
                y_hat = m_val * x + c_val
                err = y - y_hat
                raw_error_sum += err
                mse_accum += err ** 2

                px, py = self.to_px(x, y)
                _, py_hat = self.to_px(x, y_hat)
                # Red Residual Line
                g.create_line(px, py, px, py_hat, fill="#fb7185", width=2, dash=(4, 2))
                g.create_oval(px - 6, py - 6, px + 6, py + 6, fill="#38bdf8", outline="white", width=1.5)

            player_mse = mse_accum / len(self.s3_x)

            if self.show_ols_gold:
                ox1, oy1 = self.to_px(0, self.ols_c)
                ox2, oy2 = self.to_px(10, self.ols_m * 10 + self.ols_c)
                g.create_line(ox1, oy1, ox2, oy2, fill="#facc15", width=3, dash=(6, 4))
                g.create_text(480, 65, text="-- Gold Line: True OLS Minimum MSE", font=("Consolas", 9, "bold"), fill="#facc15")

            lx1, ly1 = self.to_px(0, c_val)
            lx2, ly2 = self.to_px(10, m_val * 10 + c_val)
            g.create_line(lx1, ly1, lx2, ly2, fill="#4ade80", width=4)

            self.math_box.config(
                text=f"Your Equation          : y_hat = {m_val:.2f}*x + {c_val:.2f}\n"
                     f"Sum of Unsquared Errors: {raw_error_sum:+.2f} (+/- cancel out!)\n"
                     f"Your Live MSE (Squared): {player_mse:.2f} (Goal: <= {self.ols_mse + 0.45:.2f})"
            )

        # ---------------- STAGE 4 RENDERING ----------------
        elif self.stage == 4:
            # Draw past known training data (X = 1..7)
            for x, y in zip(self.s3_x, self.s3_y):
                px, py = self.to_px(x, y)
                g.create_oval(px - 5, py - 5, px + 5, py + 5, fill="#64748b", outline="white")

            # Draw fitted OLS Regression Line extending into the Future Zone (X > 7)
            lx1, ly1 = self.to_px(0, self.ols_c)
            lx2, ly2 = self.to_px(10, self.ols_m * 10 + self.ols_c)
            g.create_line(lx1, ly1, lx2, ly2, fill="#4ade80", width=3, dash=(6, 3))

            # Future Zone vertical divider at X = 7.5
            fx_div, _ = self.to_px(7.5, 0)
            g.create_line(fx_div, 45, fx_div, 480, fill="#c084fc", width=2, dash=(4, 4))
            g.create_text(fx_div + 75, 60, text="FUTURE PREDICTION ZONE\n(No Past Data Here!)", font=("Consolas", 8, "bold"), fill="#c084fc")

            # Draw Player's Targeting Crosshair at X = future_x
            pred_y = self.s4_pred_slider.get()
            tx, ty = self.to_px(self.future_x, pred_y)
            _, base_y = self.to_px(self.future_x, 0)

            # Vertical guide line from Future X up to Crosshair
            g.create_line(tx, base_y, tx, ty, fill="#fde047", width=2, dash=(3, 3))
            g.create_oval(tx - 11, ty - 11, tx + 11, ty + 11, outline="#fde047", width=3)
            g.create_line(tx - 16, ty, tx + 16, ty, fill="#fde047", width=2)
            g.create_text(tx - 55, ty - 16, text=f"Aim: ({self.future_x}, {pred_y:.1f})", font=("Consolas", 9, "bold"), fill="#fde047")

            if self.revealed_kudo:
                kx, ky = self.to_px(self.future_x, self.future_true_y)
                g.create_oval(kx - 14, ky - 14, kx + 14, ky + 14, fill="#ef4444", outline="white", width=2)
                g.create_text(kx, ky - 22, text="💥 KUDO HIT!", font=("Consolas", 9, "bold"), fill="#4ade80")

            self.math_box.config(
                text=f"Fitted OLS Equation : y_hat = {self.ols_m:.2f}*x + {self.ols_c:.2f}\n"
                     f"Future Input (X)    : {self.future_x} seconds\n"
                     f"Your Aimed Output Y : {pred_y:.1f}"
            )

    def show_summary_popup(self):
        messagebox.showinfo(
            "Complete Beginner's Guide to Linear Regression",
            "1. WHAT IS LINEAR REGRESSION?\n"
            "Linear Regression predicts a numeric outcome (Dependent Variable Y) from an input (Independent Variable X) by fitting the best straight line through past data.\n\n"
            "2. THE LINE EQUATION (y_hat = m*x + c):\n"
            "• x: Independent Input Variable (what you know/control).\n"
            "• y_hat: Predicted Dependent Output.\n"
            "• c (Intercept): Starting value of y_hat when x = 0.\n"
            "• m (Slope): How much y_hat changes when x increases by 1 unit.\n\n"
            "3. RESIDUALS & MEAN SQUARED ERROR (MSE):\n"
            "• Residual = Actual y - Predicted y_hat.\n"
            "• MSE = Average of (Residual)^2. Ordinary Least Squares (OLS) finds the exact m and c that make MSE as small as possible.\n\n"
            "4. PREDICTING THE FUTURE:\n"
            "Once m and c are found from past data, plug in any new future X to predict its future outcome Y!"
        )


if __name__ == "__main__":
    root = tk.Tk()
    app = LinearRegressionAcademyGame(root)
    root.mainloop()