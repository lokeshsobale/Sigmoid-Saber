import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.metrics import mean_squared_error, log_loss
import os

# ==========================================
# 1. PAGE SETUP
# ==========================================
st.set_page_config(
    page_title="Star Wars: Master Yoda vs. Sith Lord KUDO",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Use @st.fragment for fast, low-lag partial reruns in pure Python
fragment = getattr(st, "fragment", lambda f: f)

# ==========================================
# 2. SESSION STATE & SCIKIT-LEARN DATA
# ==========================================
def init_game_state():
    if "initialized" not in st.session_state:
        st.session_state.initialized = True
        np.random.seed(42)

        # Progression & Boss State
        st.session_state.level = 1
        st.session_state.show_tutorial = True
        st.session_state.score = 0
        st.session_state.kudo_hp = 100
        st.session_state.l2_unlocked = False
        st.session_state.l3_unlocked = False
        st.session_state.strike_active = False
        st.session_state.yoda_quote = "Stationed I am. Angle the Regression Force Beam, you must!"
        st.session_state.kudo_quote = "Your feeble linear math cannot stop the Dark Side!"

        # Starfield coordinates (in Axes 0..1 space)
        st.session_state.stars_x = np.random.uniform(0.02, 0.98, 65)
        st.session_state.stars_y = np.random.uniform(0.05, 0.95, 65)
        st.session_state.stars_s = np.random.uniform(5, 25, 65)

        # --- STAGE 1: Simple Linear Regression (OLS) ---
        l1_x = np.linspace(1.0, 9.0, 20)
        l1_y = 2.8 * l1_x + 4.0 + np.random.randn(20) * 3.0
        ols = LinearRegression().fit(l1_x.reshape(-1, 1), l1_y)
        st.session_state.l1_x = l1_x
        st.session_state.l1_y = l1_y
        st.session_state.ols_m = float(ols.coef_[0])
        st.session_state.ols_c = float(ols.intercept_)
        st.session_state.ols_mse = float(mean_squared_error(l1_y, ols.predict(l1_x.reshape(-1, 1))))
        st.session_state.m = 1.0
        st.session_state.c = 2.0
        st.session_state.l1_locked = False

        # --- STAGE 2: Sith Outliers & Polynomial Overfitting ---
        x_clean = np.linspace(-4.5, 4.5, 18)
        y_clean = 0.45 * (x_clean ** 2) + 0.8 * x_clean + 2.0 + np.random.randn(18) * 1.5
        x_out = np.array([-3.5, 0.2, 3.8])
        y_out = np.array([26.0, -18.0, 29.0])
        st.session_state.l2_x_train = np.concatenate([x_clean, x_out])
        st.session_state.l2_y_train = np.concatenate([y_clean, y_out])

        x_test = np.linspace(-4.5, 4.5, 40)
        y_test = 0.45 * (x_test ** 2) + 0.8 * x_test + 2.0 + np.random.randn(40) * 1.5
        st.session_state.l2_x_test = x_test
        st.session_state.l2_y_test = y_test
        st.session_state.zapped = []
        st.session_state.degree = 1
        st.session_state.l2_evaluated = False

        # --- STAGE 3: Logistic Regression (Sigmoid Shield) ---
        l3_temp = np.linspace(25, 95, 45)
        z_true = 0.16 * (l3_temp - 62.0)
        p_true = 1.0 / (1.0 + np.exp(-z_true))
        l3_fail = np.random.binomial(1, p_true)
        log_reg = LogisticRegression().fit(l3_temp.reshape(-1, 1), l3_fail)
        st.session_state.l3_temp = l3_temp
        st.session_state.l3_fail = l3_fail
        st.session_state.opt_w = float(log_reg.coef_[0][0])
        st.session_state.opt_b = float(log_reg.intercept_[0])
        st.session_state.w = 0.10
        st.session_state.b = -6.0
        st.session_state.threshold = 0.50

init_game_state()

# ==========================================
# 3. PURE PYTHON MATPLOTLIB 2D ARENA RENDERER
# ==========================================
def draw_yoda_and_kudo(ax):
    """Draws stationary Master Yoda (left) and Sith Lord KUDO (right) using pure Matplotlib patches."""
    trans = ax.transAxes

    # --- STATIONARY MASTER YODA (Left Pedestal: x=0.07, y=0.18) ---
    # Jedi Hover Pedestal
    ax.add_patch(patches.Ellipse((0.07, 0.10), 0.10, 0.04, facecolor="#2d333b", edgecolor="#3fb950", lw=2, transform=trans, zorder=10))
    # Jedi Robe
    ax.add_patch(patches.FancyBboxPatch((0.045, 0.12), 0.05, 0.10, boxstyle="round,pad=0.01", facecolor="#c9b18c", edgecolor="#5c4033", lw=1.5, transform=trans, zorder=11))
    # Yoda Head & Iconic Green Ears
    ax.add_patch(patches.Polygon([[0.04, 0.25], [0.005, 0.27], [0.04, 0.23]], closed=True, facecolor="#6ab04c", transform=trans, zorder=11))
    ax.add_patch(patches.Polygon([[0.10, 0.25], [0.135, 0.27], [0.10, 0.23]], closed=True, facecolor="#6ab04c", transform=trans, zorder=11))
    ax.add_patch(patches.Circle((0.07, 0.25), 0.024, facecolor="#6ab04c", edgecolor="#2d333b", transform=trans, zorder=12))
    # Yoda Eyes
    ax.plot([0.062, 0.078], [0.253, 0.253], "ko", markersize=3, transform=trans, zorder=13)
    # Yoda Green Lightsaber
    ax.plot([0.10, 0.125], [0.17, 0.31], color="#39ff14", lw=4, transform=trans, zorder=13)
    ax.text(0.07, 0.04, "MASTER YODA\n(Stationary)", color="#3fb950", fontsize=8, fontweight="bold", ha="center", transform=trans, zorder=14)

    # --- SITH LORD KUDO (Right Dark Platform: x=0.93, y=0.76) ---
    ax.add_patch(patches.Ellipse((0.93, 0.68), 0.10, 0.04, facecolor="#1c1f26", edgecolor="#ff3333", lw=2, transform=trans, zorder=10))
    # Dark Sith Cloak & Hood
    cloak_color = "#ff5555" if st.session_state.strike_active else "#111318"
    ax.add_patch(patches.Polygon([[0.89, 0.70], [0.93, 0.89], [0.97, 0.70]], closed=True, facecolor=cloak_color, edgecolor="#ff3333", lw=1.5, transform=trans, zorder=11))
    # Glowing Red Sith Eyes
    ax.plot([0.922, 0.938], [0.82, 0.82], "ro", markersize=3.5, transform=trans, zorder=12)
    # KUDO Crimson Lightsaber
    ax.plot([0.89, 0.855], [0.75, 0.87], color="#ff1e1e", lw=4, transform=trans, zorder=13)
    ax.text(0.93, 0.62, f"DARTH KUDO\nHP: {st.session_state.kudo_hp}%", color="#ff5555", fontsize=8, fontweight="bold", ha="center", transform=trans, zorder=14)

    # Force Lightning Beam when striking KUDO
    if st.session_state.strike_active:
        lx = np.linspace(0.12, 0.90, 12)
        ly = np.linspace(0.28, 0.78, 12) + np.random.uniform(-0.04, 0.04, 12)
        ax.plot(lx, ly, color="#ffe81f", lw=3, transform=trans, zorder=15)
        st.session_state.strike_active = False


def render_2d_starwars_canvas():
    """Renders the 2D Star Wars Regression Arena purely in Python Matplotlib."""
    fig, ax = plt.subplots(figsize=(9.5, 4.6), facecolor="#05070b")
    ax.set_facecolor("#090d16")

    # Draw Space Starfield in background (Axes coordinates)
    ax.scatter(st.session_state.stars_x, st.session_state.stars_y, s=st.session_state.stars_s, color="white", alpha=0.35, transform=ax.transAxes, zorder=1)

    lvl = st.session_state.level

    # ------------------------------------------
    # STAGE 1 VISUALS: OLS LIGHTSABER BEAM
    # ------------------------------------------
    if lvl == 1:
        x, y = st.session_state.l1_x, st.session_state.l1_y
        y_pred = st.session_state.m * x + st.session_state.c
        mse = mean_squared_error(y, y_pred)

        # Residual Error Tethers
        ax.vlines(x, y_pred, y, color="#ff5555", linestyle=":", alpha=0.7, lw=1.8, label="Residuals (Error)", zorder=3)
        # Kyber Data Orbs
        ax.scatter(x, y, color="#00d2ff", s=55, edgecolors="white", lw=1, label="Kyber Data Orbs", zorder=5)
        # Yoda's Green Linear Force Beam
        x_line = np.linspace(0, 10, 100)
        ax.plot(x_line, st.session_state.m * x_line + st.session_state.c, color="#39ff14", lw=3.5, label=f"Yoda Beam (y={st.session_state.m:.2f}x+{st.session_state.c:.1f})", zorder=6)

        if st.session_state.l1_locked:
            ax.plot(x_line, st.session_state.ols_m * x_line + st.session_state.ols_c, color="#ffe81f", linestyle="--", lw=2.5, label=f"True Scikit-Learn OLS (MSE={st.session_state.ols_mse:.2f})", zorder=7)

        ax.set_xlim(-1.2, 11.2)
        ax.set_ylim(-8, 42)
        ax.set_title(f"STAGE 1: OLS LIGHTSABER BEAM  |  Your MSE: {mse:.2f}", color="#ffe81f", fontsize=11, fontweight="bold")

    # ------------------------------------------
    # STAGE 2 VISUALS: OUTLIERS & OVERFITTING
    # ------------------------------------------
    elif lvl == 2:
        x_tr, y_tr = st.session_state.l2_x_train, st.session_state.l2_y_train
        mask = np.ones(len(x_tr), dtype=bool)
        mask[st.session_state.zapped] = False
        x_clean, y_clean = x_tr[mask], y_tr[mask]

        poly = PolynomialFeatures(degree=st.session_state.degree)
        model = LinearRegression().fit(poly.fit_transform(x_clean.reshape(-1, 1)), y_clean)

        x_grid = np.linspace(-4.8, 4.8, 120).reshape(-1, 1)
        y_grid = model.predict(poly.transform(x_grid))
        train_mse = mean_squared_error(y_clean, model.predict(poly.fit_transform(x_clean.reshape(-1, 1))))
        test_mse = mean_squared_error(st.session_state.l2_y_test, model.predict(poly.transform(st.session_state.l2_x_test.reshape(-1, 1))))

        # Plot Polynomial Force Curve
        ax.plot(x_grid, y_grid, color="#d2a8ff", lw=3, label=f"Degree {st.session_state.degree} Force Curve", zorder=6)

        # Plot Training Points & Sith Outliers
        for i in range(len(x_tr)):
            if i in st.session_state.zapped:
                continue
            is_sith = i >= 18
            c = "#ff1e1e" if is_sith else "#ffa657"
            sz = 95 if is_sith else 45
            ax.scatter(x_tr[i], y_tr[i], color=c, s=sz, edgecolors="white", zorder=7)
            if is_sith:
                ax.annotate(f"SITH #{i}", (x_tr[i], y_tr[i] + 2.0), color="#ff7b72", fontsize=8, fontweight="bold", ha="center", zorder=8)

        if st.session_state.l2_evaluated:
            ax.scatter(st.session_state.l2_x_test, st.session_state.l2_y_test, color="#39ff14", alpha=0.45, s=25, label=f"Unseen Test Set (MSE={test_mse:.2f})", zorder=4)

        ax.set_xlim(-6.5, 6.5)
        ax.set_ylim(-28, 38)
        title_extra = f" | Hidden Test MSE: {test_mse:.2f}" if st.session_state.l2_evaluated else " | Right-Click Strike to Reveal Test MSE"
        ax.set_title(f"STAGE 2: SITH OUTLIERS & OVERFITTING  |  Train MSE: {train_mse:.2f}{title_extra}", color="#ffe81f", fontsize=11, fontweight="bold")

    # ------------------------------------------
    # STAGE 3 VISUALS: SIGMOID FORCE SHIELD
    # ------------------------------------------
    elif lvl == 3:
        temp, fail = st.session_state.l3_temp, st.session_state.l3_fail
        w, b, th = st.session_state.w, st.session_state.b, st.session_state.threshold

        # Flawed Linear Regression Reference
        lin_mod = LinearRegression().fit(temp.reshape(-1, 1), fail)
        t_grid = np.linspace(20, 100, 120)
        ax.plot(t_grid, lin_mod.predict(t_grid.reshape(-1, 1)), color="#8b949e", linestyle="--", alpha=0.6, label="Flawed Linear Fit (<0 or >1)", zorder=3)

        # Yoda's Sigmoid Curve
        p_grid = 1.0 / (1.0 + np.exp(-(w * t_grid + b)))
        ax.plot(t_grid, p_grid, color="#39ff14", lw=3.5, label="Yoda Sigmoid Force Shield", zorder=6)

        # Decision Threshold Gate
        ax.axhline(th, color="#ffe81f", linestyle="-.", lw=2.2, label=f"Decision Threshold Gate ({th:.2f})", zorder=7)

        # Predictions & Confusion Matrix
        p_actual = np.clip(1.0 / (1.0 + np.exp(-(w * temp + b))), 1e-7, 1 - 1e-7)
        preds = (p_actual >= th).astype(int)
        colors = ["#00d2ff" if p == a else "#ff1e1e" for p, a in zip(preds, fail)]
        ax.scatter(temp, fail, color=colors, s=50, edgecolors="white", zorder=8, label="Detonators (Red = Misclassified)")

        ax.set_xlim(5, 115)
        ax.set_ylim(-0.25, 1.25)
        ax.set_title(f"STAGE 3: SIGMOID FORCE SHIELD  |  Log-Loss: {log_loss(fail, p_actual):.3f}", color="#ffe81f", fontsize=11, fontweight="bold")

    # Draw Stationary Characters (Yoda & Darth KUDO)
    draw_yoda_and_kudo(ax)

    # Style Axes
    ax.grid(True, color="#21262d", linestyle="--", alpha=0.5)
    ax.tick_params(colors="#8b949e", labelsize=8)
    for spine in ax.spines.values():
        spine.set_color("#30363d")
    ax.legend(loc="upper center", facecolor="#0d1117", edgecolor="#30363d", labelcolor="white", fontsize=8, ncol=3)
    plt.tight_layout()
    return fig


# ==========================================
# 4. TOP BAR: LEFT LOGGER & RIGHT 3-DOTS MENU
# ==========================================
top_left, top_center, top_right = st.columns([2.2, 6.4, 1.4])

# TOP-LEFT CORNER: Evidence Logger
with top_left:
    with st.popover("📝 Evidence Logger", use_container_width=True):
        st.markdown("### 📝 Jedi Playtest Logger")
        with st.form("playtest_form"):
            tester_name = st.text_input("Padawan / Tester Name")
            q1_ans = st.text_area("Q1: What did you discover about Sith Outliers and Polynomial Degree in Stage 2?")
            q2_ans = st.text_area("Q2: How did moving the Sigmoid Threshold Gate change False Negatives vs. Profit in Stage 3?")
            submitted = st.form_submit_button("Save Playtest to CSV")

            if submitted and tester_name:
                row = pd.DataFrame({
                    "Name": [tester_name],
                    "Score": [st.session_state.score],
                    "L2_Discovery": [q1_ans],
                    "L3_Discovery": [q2_ans]
                })
                exists = os.path.isfile("playtest_results.csv")
                row.to_csv("playtest_results.csv", mode="a", header=not exists, index=False)
                st.success("Saved to `playtest_results.csv`!")

        if os.path.isfile("playtest_results.csv"):
            df_log = pd.read_csv("playtest_results.csv")
            st.dataframe(df_log, use_container_width=True)
            st.download_button("⬇️ Download CSV", df_log.to_csv(index=False), "playtest_results.csv", "text/csv")

# TOP-CENTER: Title & Boss HP Bar
with top_center:
    st.markdown("<h4 style='text-align:center; margin:0; color:#ffe81f;'>⚔️ STAR WARS: MASTER YODA vs. SITH LORD KUDO ⚔️</h4>", unsafe_allow_html=True)
    st.progress(st.session_state.kudo_hp / 100.0, text=f"Sith Lord KUDO HP: {st.session_state.kudo_hp}%  |  Force Score: {st.session_state.score} pts")

# TOP-RIGHT CORNER: 3-Dots Menu (Extra Info, Math & Diagnostics)
with top_right:
    with st.popover("⋮", use_container_width=True):
        st.markdown("### 📊 Jedi Archives & Math Lab")
        st.markdown("""
        **Learning Objectives:**
        1. **Stage 1 (OLS):** Fit $y = mx + c$ to minimize $MSE = \\frac{1}{n}\\sum(y_i - \\hat{y}_i)^2$.
        2. **Stage 2 (Bias-Variance):** Remove extreme outliers and avoid high-degree polynomial overfitting on unseen Test Data.
        3. **Stage 3 (Logistic Sigmoid):** Map binary probabilities with $P(y=1|x) = \\frac{1}{1+e^{-(wx+b)}}$ and tune the Decision Threshold Gate.
        """)
        st.divider()
        st.caption("**True Scikit-Learn Parameters (Reference):**")
        st.write(f"- Stage 1 Optimal OLS: `m = {st.session_state.ols_m:.2f}`, `c = {st.session_state.ols_c:.2f}`, `MSE = {st.session_state.ols_mse:.2f}`")
        st.write(f"- Stage 2 Sith Outlier Indices: `18, 19, 20` (Optimal Degree: `2`)")
        st.write(f"- Stage 3 Optimal Logistic Fit: `w = {st.session_state.opt_w:.2f}`, `b = {st.session_state.opt_b:.2f}`")


# ==========================================
# 5. MAIN PURE-PYTHON GAME FRAGMENT
# ==========================================
@fragment
def run_starwars_game():
    # Stage Navigation Bar
    nav1, nav2, nav3, nav4 = st.columns(4)
    with nav1:
        if st.button("⚔️ Stage 1: OLS Beam", use_container_width=True, type="primary" if st.session_state.level == 1 else "secondary"):
            st.session_state.level = 1
            st.session_state.show_tutorial = True
            st.rerun()
    with nav2:
        if st.button("⚔️ Stage 2: Sith Outliers" if st.session_state.l2_unlocked else "🔒 Stage 2 (Need 75+ in Stg 1)", disabled=not st.session_state.l2_unlocked, use_container_width=True, type="primary" if st.session_state.level == 2 else "secondary"):
            st.session_state.level = 2
            st.session_state.show_tutorial = True
            st.rerun()
    with nav3:
        if st.button("⚔️ Stage 3: Sigmoid Shield" if st.session_state.l3_unlocked else "🔒 Stage 3 (Need Test MSE < 10)", disabled=not st.session_state.l3_unlocked, use_container_width=True, type="primary" if st.session_state.level == 3 else "secondary"):
            st.session_state.level = 3
            st.session_state.show_tutorial = True
            st.rerun()
    with nav4:
        if st.button("❓ Stage Tutorial", use_container_width=True):
            st.session_state.show_tutorial = True
            st.rerun()

    # ------------------------------------------
    # PRE-GAME TUTORIAL MODAL BEFORE EVERY STAGE
    # ------------------------------------------
    if st.session_state.show_tutorial:
        with st.container(border=True):
            if st.session_state.level == 1:
                st.subheader("✨ JEDI HOLOCRON TUTORIAL — STAGE 1: THE OLS LIGHTSABER BEAM")
                st.write("**Mission:** Sith Lord KUDO has scattered Kyber Data Orbs across space! Master Yoda remains stationed on his Jedi Pedestal and channels a Linear Force Beam ($y = mx + c$).")
                st.markdown("""
                - **Controls (`WASD` / `QE` / `Mouse`):**
                  - **`W` / `S`** (or Scroll Input): Tilt the Force Beam **Slope ($m$)** Up or Down.
                  - **`Q` / `E`** or **`A` / `D`**: Shift the **Intercept ($c$)** Down or Up while Yoda stays in one place.
                  - **Right-Click Strike (`⚔️ Strike KUDO`):** Lock in your line, reveal the true Scikit-Learn OLS line, and blast KUDO!
                - **Goal:** Score **75+ points** by minimizing Mean Squared Error (MSE) to unlock Stage 2.
                """)
            elif st.session_state.level == 2:
                st.subheader("✨ JEDI HOLOCRON TUTORIAL — STAGE 2: SITH OUTLIERS & OVERFITTING")
                st.write("**Mission:** Darth KUDO planted **3 Red Sith Outlier Holocrons (`#18`, `#19`, `#20`)** to skew your line! Worse, using too high a Polynomial Degree will overfit noise and fail on unseen Test Data.")
                st.markdown("""
                - **Controls (`WASD` / `QE` / `Mouse`):**
                  - **Left-Click Zap Buttons:** Shoot Force Lightning to destroy up to 3 corrupted Sith Outliers.
                  - **`W` / `S`** or **`Q` / `E`** or **`A` / `D`**: Increase or decrease **Polynomial Degree (1 to 8)**.
                  - **Right-Click Strike (`⚔️ Strike KUDO`):** Evaluate your model against the Hidden Test Set!
                - **Goal:** Get **Hidden Test Set MSE below 10.0** to damage KUDO and unlock Stage 3.
                """)
            elif st.session_state.level == 3:
                st.subheader("✨ JEDI HOLOCRON TUTORIAL — STAGE 3: THE SIGMOID FORCE SHIELD")
                st.write("**Mission:** Darth KUDO fires Thermal Detonators (`1 = Explode`, `0 = Safe`). Linear Regression fails on binary outcomes! Shape Yoda's Sigmoid Probability Curve and tune the Decision Threshold Gate.")
                st.markdown("""
                - **Controls (`WASD` / `QE` / `Mouse`):**
                  - **`W` / `S`**: Raise or lower the **Probability Decision Threshold Gate (0.05 to 0.95)**.
                  - **`A` / `D`**: Adjust Logistic **Weight ($w$)**.
                  - **`Q` / `E`**: Adjust Logistic **Bias ($b$)**.
                  - **Right-Click Strike (`⚔️ Strike KUDO`):** Deflect the detonators and deal the final blow to KUDO!
                - **Goal:** Missed Detonators (False Negatives) cost **-50 pts**; False Alarms cost **-10 pts**. Reach **Net Profit > 100 pts**!
                """)

            if st.button("⚔️ START STAGE (Close Tutorial)", type="primary", use_container_width=True):
                st.session_state.show_tutorial = False
                st.rerun()
        return

    # ------------------------------------------
    # ACTIVE 2D GAME SCREEN + WASD/QE CONTROL DECK
    # ------------------------------------------
    col_canvas, col_controls = st.columns([7.2, 2.8])

    with col_canvas:
        fig = render_2d_starwars_canvas()
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)
        st.caption(f"🟢 **Master Yoda:** *\"{st.session_state.yoda_quote}\"*  |  🔴 **Darth KUDO:** *\"{st.session_state.kudo_quote}\"*")

    with col_controls:
        with st.container(border=True):
            st.markdown("#### 🎮 Jedi Force Deck")
            st.caption("Use `WASD` / `QE` pads or mouse scroll inputs below:")

            # --- STAGE 1 CONTROLS ---
            if st.session_state.level == 1:
                c1, c2 = st.columns(2)
                if c1.button("⬆️ W (Slope +)", use_container_width=True):
                    st.session_state.m = min(8.0, round(st.session_state.m + 0.3, 2))
                    st.rerun()
                if c2.button("⬇️ S (Slope -)", use_container_width=True):
                    st.session_state.m = max(-5.0, round(st.session_state.m - 0.3, 2))
                    st.rerun()

                c3, c4 = st.columns(2)
                if c3.button("⬅️ Q/A (Int -)", use_container_width=True):
                    st.session_state.c = max(-10.0, round(st.session_state.c - 1.0, 1))
                    st.rerun()
                if c4.button("➡️ E/D (Int +)", use_container_width=True):
                    st.session_state.c = min(20.0, round(st.session_state.c + 1.0, 1))
                    st.rerun()

                # Mouse Scroll / Fine Tune Inputs
                st.session_state.m = st.number_input("🖱️ Scroll/Fine Slope (m)", -5.0, 8.0, float(st.session_state.m), step=0.1)
                st.session_state.c = st.number_input("🖱️ Scroll/Fine Intercept (c)", -10.0, 20.0, float(st.session_state.c), step=0.5)

                if st.button("⚔️ Right-Click: Strike KUDO (Lock In)", type="primary", use_container_width=True):
                    st.session_state.l1_locked = True
                    st.session_state.strike_active = True
                    player_mse = mean_squared_error(st.session_state.l1_y, st.session_state.m * st.session_state.l1_x + st.session_state.c)
                    pts = max(0, int(100 - (abs(player_mse - st.session_state.ols_mse) / st.session_state.ols_mse) * 100))
                    if pts >= 75:
                        if not st.session_state.l2_unlocked:
                            st.session_state.l2_unlocked = True
                            st.session_state.score += pts
                            st.session_state.kudo_hp = min(st.session_state.kudo_hp, 66)
                        st.session_state.yoda_quote = f"Strong with OLS you are! Score: {pts}/100. Stage 2 Unlocked!"
                        st.session_state.kudo_quote = "Augh! Wait until my Sith Outliers corrupt your curve!"
                    else:
                        st.session_state.yoda_quote = f"Score: {pts}/100. Align closer to the gold OLS line for 75+!"
                    st.rerun()

            # --- STAGE 2 CONTROLS ---
            elif st.session_state.level == 2:
                st.markdown("**⚡ Left-Click Force Zapper (Max 3):**")
                z1, z2, z3 = st.columns(3)
                for idx, col_z in zip([18, 19, 20], [z1, z2, z3]):
                    is_zapped = idx in st.session_state.zapped
                    if col_z.button(f"{'✅' if is_zapped else '⚡'} #{idx}", key=f"zap_{idx}", use_container_width=True):
                        if is_zapped:
                            st.session_state.zapped.remove(idx)
                        elif len(st.session_state.zapped) < 3:
                            st.session_state.zapped.append(idx)
                        st.rerun()

                st.markdown("**Polynomial Degree (`WASD` / `QE`):**")
                d1, d2 = st.columns(2)
                if d1.button("⬇️ S/Q (Deg -)", use_container_width=True):
                    st.session_state.degree = max(1, st.session_state.degree - 1)
                    st.rerun()
                if d2.button("⬆️ W/E (Deg +)", use_container_width=True):
                    st.session_state.degree = min(8, st.session_state.degree + 1)
                    st.rerun()

                st.session_state.degree = st.number_input("🖱️ Scroll/Select Degree (1-8)", 1, 8, int(st.session_state.degree), step=1)

                if st.button("⚔️ Right-Click: Strike KUDO (Test Set)", type="primary", use_container_width=True):
                    st.session_state.l2_evaluated = True
                    st.session_state.strike_active = True
                    mask = np.ones(len(st.session_state.l2_x_train), dtype=bool)
                    mask[st.session_state.zapped] = False
                    poly = PolynomialFeatures(degree=st.session_state.degree)
                    mod = LinearRegression().fit(poly.fit_transform(st.session_state.l2_x_train[mask].reshape(-1, 1)), st.session_state.l2_y_train[mask])
                    t_mse = mean_squared_error(st.session_state.l2_y_test, mod.predict(poly.transform(st.session_state.l2_x_test.reshape(-1, 1))))

                    if t_mse < 10.0:
                        if not st.session_state.l3_unlocked:
                            st.session_state.l3_unlocked = True
                            st.session_state.score += 100
                            st.session_state.kudo_hp = min(st.session_state.kudo_hp, 33)
                        st.session_state.yoda_quote = f"Test MSE {t_mse:.2f} (<10)! Defeated overfitting you have! Stage 3 Unlocked!"
                        st.session_state.kudo_quote = "Impossible! You destroyed my outliers and avoided overfitting!"
                    else:
                        st.session_state.yoda_quote = f"Test MSE exploded to {t_mse:.1f}! Zap #18, #19, #20 and use Degree 2!"
                    st.rerun()

            # --- STAGE 3 CONTROLS ---
            elif st.session_state.level == 3:
                g1, g2 = st.columns(2)
                if g1.button("⬆️ W (Gate +)", use_container_width=True):
                    st.session_state.threshold = min(0.95, round(st.session_state.threshold + 0.05, 2))
                    st.rerun()
                if g2.button("⬇️ S (Gate -)", use_container_width=True):
                    st.session_state.threshold = max(0.05, round(st.session_state.threshold - 0.05, 2))
                    st.rerun()

                w1, w2 = st.columns(2)
                if w1.button("⬅️ A (Weight -)", use_container_width=True):
                    st.session_state.w = max(-0.20, round(st.session_state.w - 0.02, 2))
                    st.rerun()
                if w2.button("➡️ D (Weight +)", use_container_width=True):
                    st.session_state.w = min(0.40, round(st.session_state.w + 0.02, 2))
                    st.rerun()

                b1, b2 = st.columns(2)
                if b1.button("⬅️ Q (Bias -)", use_container_width=True):
                    st.session_state.b = max(-20.0, round(st.session_state.b - 1.0, 1))
                    st.rerun()
                if b2.button("➡️ E (Bias +)", use_container_width=True):
                    st.session_state.b = min(5.0, round(st.session_state.b + 1.0, 1))
                    st.rerun()

                p_act = 1.0 / (1.0 + np.exp(-(st.session_state.w * st.session_state.l3_temp + st.session_state.b)))
                preds = (p_act >= st.session_state.threshold).astype(int)
                fail = st.session_state.l3_fail
                tp = int(np.sum((fail == 1) & (preds == 1)))
                fp = int(np.sum((fail == 0) & (preds == 1)))
                tn = int(np.sum((fail == 0) & (preds == 0)))
                fn = int(np.sum((fail == 1) & (preds == 0)))
                profit = (tp * 10) + (tn * 10) - (fp * 10) - (fn * 50)

                st.metric("Net Force Profit (Goal > 100)", f"{profit} pts", f"FN: {fn} (-50 ea) | FP: {fp} (-10 ea)")

                if st.button("⚔️ Right-Click: Final Strike on KUDO!", type="primary", use_container_width=True):
                    st.session_state.strike_active = True
                    if profit > 100:
                        if st.session_state.kudo_hp > 0:
                            st.session_state.score += 100
                            st.session_state.kudo_hp = 0
                        st.session_state.yoda_quote = f"Victory! Net Profit {profit} pts! Defeated Sith Lord KUDO is!"
                        st.session_state.kudo_quote = "NOOO! Defeated by Logistic Sigmoid probabilities!"
                    else:
                        st.session_state.yoda_quote = f"Net Profit is {profit} pts. Lower Threshold Gate (S) to stop False Negatives!"
                    st.rerun()

run_starwars_game()