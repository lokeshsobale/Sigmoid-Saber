#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MASTER YODA vs. KURO  -  An Adaptive Linear Regression Platform Game
=====================================================================
A single-file, standard-library-only (tkinter) educational platformer.
Master Yoda battles the four-armed robot Dark Lord Kuro across four worlds.
Each world teaches one part of Linear Regression; every cleared world
removes exactly 25 of Kuro's 100 HP.  Yoda's Learning Droid runs real batch
Gradient Descent on the noisy data and results are stored in a local JSON file.

Run:   python master_yoda_vs_kuro.py
Check: python master_yoda_vs_kuro.py --selftest     (math checks, no window)
"""
import json
import math
import random
import sys
import traceback
import zlib
from datetime import datetime
from pathlib import Path

try:
    import tkinter as tk
    from tkinter import font as tkfont
    from tkinter import messagebox
except Exception:  # Tk missing: --selftest still works
    tk = None
    tkfont = None
    messagebox = None

# --------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------
ARENA_W, ARENA_H = 1100, 330
GROUND_Y = 292
HUD_H = 56
GRAVITY, JUMP_V, WALK_V = 0.8, -13.6, 4.6
FRAME_MS = 33
KURO_X = 940
YODA_MAX_X = 800
STAGE_DAMAGE = 25
KURO_MAX_HP = 100
YODA_MAX_HP = 100
WRONG_PENALTY = 8
N_CLEAN, N_NOISY = 6, 12
N_STAGES = 4

BG = "#0f1120"
PANEL = "#181b30"
PANEL2 = "#20243f"
FG = "#e8ecff"
DIM = "#8f97c4"
GOLD = "#ffcf40"
CYAN = "#4fd8ff"
RED = "#ff4d5e"
GREEN = "#5fe08a"
BLUE = "#4f8dff"
ORANGE = "#ff9a3c"
GOLD_BTN = "#b8860b"
PINK = "#ff6fb5"

WORLDS = [
    dict(name="Crystal Valley", sub="Data Collection", sky=("#3c9be0", "#c9f3ff"),
         ground=("#5fbf4a", "#8a5a35"), brick=("#c8693a", "#8e3f1d"), accent="#7cf7ff"),
    dict(name="Equation Temple", sub="Slope & Intercept", sky=("#ff7a59", "#ffe6a3"),
         ground=("#e0b36a", "#a8743a"), brick=("#d8a24f", "#8d5a22"), accent="#ffd34d"),
    dict(name="Noise Factory", sub="Residuals, MSE & OLS", sky=("#27343a", "#6d8088"),
         ground=("#5a666c", "#2e373b"), brick=("#8a6a55", "#4f3a2d"), accent="#ff9a3c"),
    dict(name="Future Zone", sub="Extrapolation", sky=("#0b0630", "#47209a"),
         ground=("#3a37a0", "#14123a"), brick=("#5a3cc4", "#2c1c78"), accent="#4ff0ff"),
]

# Explicit, measurable learning objectives (shown in the lesson panel, tutorial and README)
LEARNING_OBJECTIVES = [
    ["Name the independent (X) and dependent (Y) variable in a scenario.",
     "Collect data points, then PREDICT a new one from the pattern you found.",
     "Recognise a positive linear relationship."],
    ["Explain the intercept c as the value of Y when X = 0.",
     "Explain the slope m as the change in Y for every +1 in X.",
     "Fit a line by choosing m and c."],
    ["Compute residuals and MSE and explain why residuals are squared.",
     "Find the OLS line from data and know it has the smallest possible MSE.",
     "Run gradient descent and see how the learning rate decides between converging and diverging."],
    ["Use a fitted model to predict an unseen X (extrapolation).",
     "Explain why uncertainty grows the further we predict beyond the training data."],
]

# (question, options, index of the correct option) - used for the pre/post check-up
CHECK_QUESTIONS = [
    ("In y = m*x + c, what does c tell you?",
     ["The predicted Y when X = 0", "How steep the line is", "The average error", "The largest X in the data"], 0),
    ("What is a residual?",
     ["Actual y minus predicted y", "The slope of the line", "The learning rate", "The mean of x"], 0),
    ("Why are residuals squared when computing MSE?",
     ["So errors cannot cancel out and big misses count more", "To make the line steeper",
      "To remove the intercept", "Because Y is always squared"], 0),
    ("During gradient descent the MSE explodes instead of shrinking. The most likely cause is...",
     ["A learning rate that is too large", "Too few data points", "A positive slope", "X and Y being swapped"], 0),
    ("Predicting Y for an X far beyond all your training data is called...",
     ["Extrapolation - and it is riskier than predicting inside the data", "Interpolation - and it is always exact",
      "Regression - and it is impossible", "A residual - and it is harmless"], 0),
]

FONTS = {}


def init_fonts():
    """Pick installed font families and build the font table."""
    fams = set(tkfont.families())

    def pick(cands, default):
        for c in cands:
            if c in fams:
                return c
        return default

    ui = pick(["Segoe UI", "Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"], "TkDefaultFont")
    mono = pick(["Consolas", "Menlo", "DejaVu Sans Mono", "Courier New", "Courier"], "TkFixedFont")
    FONTS.update(
        ui=(ui, 10), ui_b=(ui, 10, "bold"), small=(ui, 9), btn=(ui, 10, "bold"),
        h=(ui, 12, "bold"), mono=(mono, 9), mono_b=(mono, 9, "bold"),
        hud=(ui, 11, "bold"), hud_s=(ui, 9), big=(ui, 34, "bold"), mid=(ui, 16, "bold"),
        sub=(ui, 12), tiny=(ui, 8), label=(ui, 9, "bold"),
    )


# --------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------
def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def lerp(a, b, t):
    return a + (b - a) * t


def mix(c1, c2, t):
    t = clamp(t, 0.0, 1.0)
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02x%02x%02x" % tuple(int(lerp(a[i], b[i], t)) for i in range(3))


def rnd(k, salt=0):
    """Deterministic pseudo-random number in [0,1) for scenery."""
    return ((k * 2654435761 + salt * 40503 + 12345) % 1000003) / 1000003.0


def fmt(v, nd=2):
    try:
        if v is None or math.isnan(v) or math.isinf(v):
            return "n/a"
        return f"{v:.{nd}f}"
    except (TypeError, ValueError):
        return "n/a"


def nice_step(span, target=6):
    if span <= 0:
        return 1.0
    raw = span / target
    mag = 10 ** math.floor(math.log10(raw))
    for m in (1, 2, 2.5, 5, 10):
        if raw <= m * mag:
            return m * mag
    return 10 * mag


# --------------------------------------------------------------------------
# Mathematics - every number in the game comes from these functions
# --------------------------------------------------------------------------
class RegressionMath:
    """Pure functions for simple linear regression:  y_hat = m*x + c."""

    @staticmethod
    def mean(v):
        v = list(v)
        return sum(v) / len(v) if v else 0.0

    @staticmethod
    def predict(m, c, x):
        return m * x + c

    @staticmethod
    def residuals(xs, ys, m, c):
        """Residual = actual - predicted."""
        return [y - (m * x + c) for x, y in zip(xs, ys)]

    @staticmethod
    def sse(xs, ys, m, c):
        return sum(r * r for r in RegressionMath.residuals(xs, ys, m, c))

    @staticmethod
    def mse(xs, ys, m, c):
        """Mean Squared Error. A mean of squares can never be negative."""
        n = len(xs)
        if n == 0:
            return 0.0
        return RegressionMath.sse(xs, ys, m, c) / n

    @staticmethod
    def ols(xs, ys):
        """Ordinary Least Squares closed form, computed from the data."""
        n = len(xs)
        if n == 0 or n != len(ys):
            raise ValueError("dataset must be non-empty and xs/ys the same length")
        xbar, ybar = RegressionMath.mean(xs), RegressionMath.mean(ys)
        sxx = sum((x - xbar) ** 2 for x in xs)
        sxy = sum((x - xbar) * (y - ybar) for x, y in zip(xs, ys))
        m = sxy / sxx if sxx > 1e-12 else 0.0  # all x equal -> flat line through the mean
        c = ybar - m * xbar
        return dict(m=m, c=c, xbar=xbar, ybar=ybar, sxx=sxx, sxy=sxy, n=n,
                    mse=RegressionMath.mse(xs, ys, m, c))

    @staticmethod
    def gradients(xs, ys, m, c):
        """dMSE/dm = 2/n * sum((m x + c - y) x);  dMSE/dc = 2/n * sum(m x + c - y)."""
        n = len(xs)
        errs = [(m * x + c) - y for x, y in zip(xs, ys)]
        dm = (2.0 / n) * sum(e * x for e, x in zip(errs, xs))
        dc = (2.0 / n) * sum(errs)
        return dm, dc

    @staticmethod
    def gd_step(xs, ys, m, c, lr):
        dm, dc = RegressionMath.gradients(xs, ys, m, c)
        return m - lr * dm, c - lr * dc, dm, dc

    @staticmethod
    def lipschitz(xs):
        """Largest curvature L of the MSE surface (Hessian = 2*[[mean x^2, mean x],[mean x, 1]])."""
        a = RegressionMath.mean(x * x for x in xs)
        b = RegressionMath.mean(xs)
        lam = (a + 1) / 2 + math.sqrt(((a - 1) / 2) ** 2 + b * b)
        return 2.0 * lam

    @staticmethod
    def safe_lr(xs):
        """Gradient descent is stable for lr < 2/L; 0.9/L is a comfortable default."""
        L = RegressionMath.lipschitz(xs)
        return 0.9 / L if L > 0 else 0.01


RM = RegressionMath


class DataFactory:
    @staticmethod
    def dataset_id(ys):
        return "%08x" % (zlib.crc32(repr([round(y, 6) for y in ys]).encode()) & 0xFFFFFFFF)

    @staticmethod
    def clean_linear(n=N_CLEAN):
        """Clean (noise-free) Kyber-crystal data  y = m*x + c  with a fresh random law."""
        m = random.choice([k * 0.5 for k in range(6, 13)])  # 3.0 .. 6.0
        c = float(random.randint(2, 10))
        xs = [float(i) for i in range(1, n + 1)]
        ys = [m * x + c for x in xs]
        return dict(xs=xs, ys=ys, m_true=m, c_true=c)

    @staticmethod
    def noisy_linear(m, c, sigma, n=N_NOISY):
        """Noisy observations: y = m*x + c + Gaussian noise (random.gauss)."""
        xs = [float(i) for i in range(1, n + 1)]
        ys = [round(m * x + c + random.gauss(0.0, sigma), 2) for x in xs]
        return dict(xs=xs, ys=ys, m_true=m, c_true=c, sigma=sigma)


# --------------------------------------------------------------------------
# Persistent learning history (JSON)
# --------------------------------------------------------------------------
class HistoryStore:
    FILE = "yoda_kuro_history.json"
    MAX_ATTEMPTS = 200

    def __init__(self, path=None):
        self.error = ""
        self.path = Path(path) if path else self._pick_path()
        self.data = self.default()
        self.load()

    @staticmethod
    def default():
        return {"version": 1, "games_started": 0, "stages_completed": 0, "victories": 0,
                "defeats": 0, "best_mse": None, "best_gap": None, "attempts": [], "evidence": []}

    def _pick_path(self):
        cands = []
        try:
            cands.append(Path(__file__).resolve().with_name(self.FILE))
        except NameError:
            pass
        cands.append(Path.home() / ("." + self.FILE))
        for p in cands:
            try:
                with open(p, "a", encoding="utf-8"):
                    pass
                return p
            except OSError:
                continue
        return cands[-1]

    def load(self):
        try:
            if not self.path.exists():
                return
            raw = self.path.read_text(encoding="utf-8").strip()
            if not raw:
                return
            obj = json.loads(raw)
            if not isinstance(obj, dict):
                raise ValueError("history root must be a JSON object")
            base = self.default()
            for k in base:
                if k in obj:
                    base[k] = obj[k]
            for k in ("games_started", "stages_completed", "victories", "defeats"):
                base[k] = int(base[k]) if isinstance(base[k], (int, float)) else 0
            for k in ("best_mse", "best_gap"):
                if not isinstance(base[k], (int, float)):
                    base[k] = None
            if not isinstance(base["attempts"], list):
                base["attempts"] = []
            base["attempts"] = [a for a in base["attempts"] if isinstance(a, dict)]
            if not isinstance(base["evidence"], list):
                base["evidence"] = []
            base["evidence"] = [e for e in base["evidence"] if isinstance(e, dict)]
            self.data = base
        except (OSError, ValueError, TypeError) as exc:
            self.error = f"History file unreadable ({exc}); starting a fresh one."
            try:
                self.path.replace(self.path.with_suffix(".corrupt.json"))
            except OSError:
                pass
            self.data = self.default()

    def save(self):
        try:
            tmp = self.path.with_suffix(".tmp")
            tmp.write_text(json.dumps(self.data, indent=2), encoding="utf-8")
            tmp.replace(self.path)
            return True
        except (OSError, TypeError, ValueError) as exc:
            self.error = f"Could not save history: {exc}"
            return False

    # ----- recording -----
    def new_attempt(self, dataset_id, sigma, n, ols):
        att = {"id": dataset_id, "time": datetime.now().isoformat(timespec="seconds"),
               "sigma": round(sigma, 3), "n": n,
               "ols": {"m": ols["m"], "c": ols["c"], "mse": ols["mse"]},
               "manual": None, "droid_runs": [], "result": "in_progress"}
        self.data["attempts"].append(att)
        del self.data["attempts"][:-self.MAX_ATTEMPTS]
        return att

    def note_mse(self, mse, ols_mse):
        gap = max(0.0, mse - ols_mse)
        d = self.data
        if d["best_mse"] is None or mse < d["best_mse"]:
            d["best_mse"] = mse
        if d["best_gap"] is None or gap < d["best_gap"]:
            d["best_gap"] = gap

    def add_evidence(self, entry):
        """Store one check-up / feedback record (kept across games, older history files stay valid)."""
        ev = self.data.setdefault("evidence", [])
        ev.append(entry)
        del ev[:-500]
        self.save()

    def evidence_summary(self):
        st = evidence_stats(self.data.get("evidence", []))
        if not st["pairs"]:
            return []
        t = st["pairs"][0]["total"]
        return [f"Check-ups: {len(st['pairs'])} paired; average score {st['mean_pre']:.1f}/{t} before -> "
                f"{st['mean_post']:.1f}/{t} after ({st['mean_gain']:+.1f})"]

    # ----- reporting / adaptation -----
    def _ratios(self):
        out = []
        for a in self.data["attempts"]:
            man, ols = a.get("manual"), a.get("ols")
            try:
                if man and ols and ols["mse"] > 1e-9:
                    out.append(max(0.0, (man["mse"] - ols["mse"]) / ols["mse"]))
            except (KeyError, TypeError):
                continue
        return out

    def summary_lines(self):
        d = self.data
        if d["games_started"] == 0 and not d["attempts"]:
            return ["First launch - no history yet. Your results will be saved locally."]
        lines = [f"Games: {d['games_started']}   Victories: {d['victories']}   "
                 f"Defeats: {d['defeats']}   Stages cleared: {d['stages_completed']}"]
        if d["best_mse"] is not None:
            lines.append(f"Best recorded MSE: {fmt(d['best_mse'], 3)}   "
                         f"(closest gap to OLS: {fmt(d['best_gap'], 3)})")
        atts = [a for a in d["attempts"] if a.get("manual")]
        if atts:
            a = atts[-1]
            lines.append(f"Last manual fit: MSE {fmt(a['manual']['mse'], 2)} vs OLS {fmt(a['ols']['mse'], 2)}"
                         f"{' (assisted)' if a['manual'].get('assisted') else ''}")
        runs = [r for a in d["attempts"] for r in a.get("droid_runs", [])]
        if runs:
            r = runs[-1]
            lines.append(f"Last droid run: {r.get('iters')} iterations, lr {r.get('lr')}, "
                         f"MSE {fmt(r['start']['mse'], 2)} -> {fmt(r['end']['mse'], 2)}")
        ratios = self._ratios()
        if len(ratios) >= 4:
            h = len(ratios) // 2
            old, new = sum(ratios[:h]) / h, sum(ratios[h:]) / (len(ratios) - h)
            if old > 1e-9:
                ch = (old - new) / old * 100
                lines.append(f"Improvement: your fits are {abs(ch):.0f}% "
                             f"{'closer to' if ch >= 0 else 'further from'} OLS than your early attempts.")
        lines += self.evidence_summary()[:1]
        return lines

    def adapt_profile(self):
        """Use *performance* history (never old parameters) to tune difficulty."""
        sigma_factor, iter_factor = 1.0, 1.0
        note = "Adaptive difficulty: standard noise level."
        atts = [a for a in self.data["attempts"] if a.get("manual")][-4:]
        ratios = self._ratios()[-4:]
        if len(ratios) >= 2:
            avg = sum(ratios) / len(ratios)
            assisted = any(a["manual"].get("assisted") for a in atts[-2:])
            if avg < 0.25 and not assisted:
                sigma_factor = 1.3
                note = "Adaptive difficulty: your recent fits were excellent, so the data is noisier."
            elif avg > 1.2 or assisted:
                sigma_factor = 0.75
                note = "Adaptive difficulty: noise lowered a little to help you see the pattern."
        runs = [r for a in self.data["attempts"][-6:] for r in a.get("droid_runs", [])]
        if runs and not runs[-1].get("converged"):
            iter_factor = 1.5
            note += " Droid: your last run had not converged, so more iterations are suggested."
        return dict(sigma_factor=sigma_factor, iter_factor=iter_factor, note=note)


def evidence_stats(entries):
    """Pair pre/post check-ups by play session and summarise learning gain and feedback."""
    pre, post = {}, {}
    for e in entries:
        if not isinstance(e, dict):
            continue
        key = e.get("session") or id(e)
        if e.get("kind") == "pre":
            pre[key] = e
        elif e.get("kind") == "post":
            post[key] = e
    pairs = []
    for k, po in post.items():
        pr = pre.get(k)
        if pr is not None:
            pairs.append(dict(player=po.get("player") or pr.get("player") or "anon", pre=pr.get("score", 0),
                              post=po.get("score", 0), total=po.get("total", len(CHECK_QUESTIONS)),
                              rating=po.get("rating"), comment=po.get("comment", ""),
                              stages=po.get("stages_cleared"), victory=po.get("victory")))

    def mean(v):
        return sum(v) / len(v) if v else None

    return dict(pairs=pairs, n_pre=len(pre), n_post=len(post),
                mean_pre=mean([p["pre"] for p in pairs]), mean_post=mean([p["post"] for p in pairs]),
                mean_gain=mean([p["post"] - p["pre"] for p in pairs]),
                mean_rating=mean([p["rating"] for p in pairs if p["rating"]]),
                post_only=[po for k, po in post.items() if k not in pre])


def build_report(paths):
    """Markdown playtest-evidence table built from one or more history JSON files (python game.py --report a.json b.json)."""
    entries, notes = [], []
    for p in paths:
        try:
            d = json.loads(Path(p).read_text(encoding="utf-8"))
            entries += [e for e in d.get("evidence", []) if isinstance(e, dict)]
        except (OSError, ValueError, AttributeError) as exc:
            notes.append(f"Could not read {p}: {exc}")
    st = evidence_stats(entries)
    out = ["# Playtest evidence (generated by --report)", ""]
    out += [f"> {n}" for n in notes]
    if not st["pairs"]:
        out.append("No paired warm-up/check-up results found yet. Ask players to press K before and after playing.")
        return "\n".join(out)
    t = st["pairs"][0]["total"]
    out += ["| Player | Before | After | Gain | Rating (1-5) | Comment |", "|---|---|---|---|---|---|"]
    for p in st["pairs"]:
        out.append(f"| {p['player']} | {p['pre']}/{t} | {p['post']}/{t} | {p['post'] - p['pre']:+d} | "
                   f"{p['rating'] if p['rating'] else '-'} | {(p['comment'] or '-').replace('|', '/')} |")
    out += ["", f"Players with paired results: {len(st['pairs'])}",
            f"Mean score before: {st['mean_pre']:.2f}/{t}   after: {st['mean_post']:.2f}/{t}   mean gain: {st['mean_gain']:+.2f}",
            f"Mean usefulness rating: {st['mean_rating']:.2f}/5" if st["mean_rating"] is not None else "No ratings recorded."]
    return "\n".join(out)


def run_selftest():
    """Numerical checks of OLS, MSE and gradient descent (no GUI needed)."""
    results = []

    def check(name, cond, detail=""):
        results.append(bool(cond))
        print(("PASS  " if cond else "FAIL  ") + name + ("  " + detail if detail else ""))

    xs, ys = [1, 2, 3, 4, 5], [2, 4, 5, 4, 5]
    o = RM.ols(xs, ys)
    check("OLS slope  = 0.6 (hand calc)", abs(o["m"] - 0.6) < 1e-12, f"got {o['m']}")
    check("OLS intercept = 2.2 (hand calc)", abs(o["c"] - 2.2) < 1e-12, f"got {o['c']}")
    check("MSE at OLS = 0.48 (hand calc)", abs(o["mse"] - 0.48) < 1e-12, f"got {o['mse']}")
    dm, dc = RM.gradients(xs, ys, 0.0, 0.0)
    check("gradient at (0,0): dm=-26.4, dc=-8.0", abs(dm + 26.4) < 1e-12 and abs(dc + 8.0) < 1e-12,
          f"got ({dm}, {dc})")
    dm, dc = RM.gradients(xs, ys, o["m"], o["c"])
    check("gradient is zero at the OLS solution", abs(dm) < 1e-12 and abs(dc) < 1e-12)
    lr = RM.safe_lr(xs)
    m = c = 0.0
    for _ in range(30000):
        m, c, _, _ = RM.gd_step(xs, ys, m, c, lr)
    check("gradient descent converges to OLS", abs(m - 0.6) < 1e-4 and abs(c - 2.2) < 1e-3,
          f"lr={lr:.4f} -> m={m:.5f}, c={c:.5f}")
    big = 2.5 / RM.lipschitz(xs)
    m = c = 0.0
    for _ in range(200):
        m, c, _, _ = RM.gd_step(xs, ys, m, c, big)
    check("lr above 2/L diverges (as theory predicts)", abs(m) > 1e3 or abs(c) > 1e3, f"m={m:.3g}")
    random.seed(7)
    ok = True
    for _ in range(300):
        xs2 = [float(i) for i in range(1, 13)]
        ys2 = [random.uniform(-50, 50) for _ in xs2]
        o2 = RM.ols(xs2, ys2)
        mm, cc = random.uniform(-9, 9), random.uniform(-9, 9)
        ok &= RM.mse(xs2, ys2, mm, cc) >= 0.0 and o2["mse"] <= RM.mse(xs2, ys2, mm, cc) + 1e-9
    check("MSE >= 0 and OLS minimises MSE (300 random trials)", ok)
    d = DataFactory.noisy_linear(4.5, 6.0, 2.5)
    o3 = RM.ols(d["xs"], d["ys"])
    m = c = 0.0
    lr = RM.safe_lr(d["xs"])
    for _ in range(40000):
        m, c, _, _ = RM.gd_step(d["xs"], d["ys"], m, c, lr)
    check("GD matches OLS on a fresh gauss() dataset", abs(m - o3["m"]) < 1e-3 and abs(c - o3["c"]) < 1e-2,
          f"OLS=({o3['m']:.4f},{o3['c']:.4f}) GD=({m:.4f},{c:.4f})")
    o4 = RM.ols([2.0, 2.0, 2.0], [1.0, 2.0, 3.0])
    check("degenerate x (all equal) handled", o4["m"] == 0.0 and abs(o4["c"] - 2.0) < 1e-12)
    ev = [dict(kind="pre", session="s1", player="A", score=1, total=5), dict(kind="post", session="s1", player="A", score=4, total=5, rating=5, comment="clear"),
          dict(kind="pre", session="s2", player="B", score=2, total=5), dict(kind="post", session="s2", player="B", score=3, total=5, rating=3)]
    st = evidence_stats(ev)
    check("evidence_stats pairs sessions and averages the gain", len(st["pairs"]) == 2 and abs(st["mean_gain"] - 2.0) < 1e-12
          and abs(st["mean_pre"] - 1.5) < 1e-12 and abs(st["mean_post"] - 3.5) < 1e-12, str(st["mean_gain"]))
    check("check-up questions are well formed", all(len(o) >= 3 and 0 <= c < len(o) for _, o, c in CHECK_QUESTIONS))
    check("every world has learning objectives", len(LEARNING_OBJECTIVES) == N_STAGES and all(LEARNING_OBJECTIVES))
    print("\nALL SELF-TESTS PASSED" if all(results) else "\nSOME SELF-TESTS FAILED")
    return all(results)


# --------------------------------------------------------------------------
# Effects
# --------------------------------------------------------------------------
BLADES = {"blue": ("#1b3fb8", "#4a90ff", "#eaf6ff"), "red": ("#6e0014", "#ff2a3a", "#ffd9d9")}


def blade(cv, x0, y0, x1, y1, kind="blue", k=1.0):
    """Glowing lightsaber blade drawn as three layered lines."""
    outer, mid, core = BLADES[kind]
    for w, c in ((11 * k, outer), (7 * k, mid), (3 * k, core)):
        cv.create_line(x0, y0, x1, y1, fill=c, width=w, capstyle="round")


class Particles:
    def __init__(self):
        self.items = []

    def burst(self, x, y, color, n=10, speed=3.0, life=24, size=3.0, grav=0.12, up=0.0):
        for _ in range(n):
            a = random.uniform(0, math.tau)
            s = random.uniform(0.3, 1.0) * speed
            self.items.append(dict(x=x, y=y, vx=math.cos(a) * s, vy=math.sin(a) * s - up,
                                   life=life * random.uniform(0.6, 1.0), max=life,
                                   color=color, size=size, grav=grav))
        del self.items[:-420]

    def add(self, x, y, vx, vy, color, life=30, size=3.0, grav=0.0):
        self.items.append(dict(x=x, y=y, vx=vx, vy=vy, life=life, max=life, color=color, size=size, grav=grav))
        del self.items[:-420]

    def update(self):
        keep = []
        for p in self.items:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["vy"] += p["grav"]
            p["life"] -= 1
            if p["life"] > 0:
                keep.append(p)
        self.items = keep

    def draw(self, cv):
        for p in self.items:
            s = max(0.6, p["size"] * p["life"] / p["max"])
            cv.create_rectangle(p["x"] - s, p["y"] - s, p["x"] + s, p["y"] + s, fill=p["color"], outline="")


class Popups:
    def __init__(self):
        self.items = []

    def add(self, x, y, text, color=GOLD, life=50):
        self.items.append(dict(x=x, y=y, text=text, color=color, life=life, max=life))

    def update(self):
        for p in self.items:
            p["y"] -= 0.9
            p["life"] -= 1
        self.items = [p for p in self.items if p["life"] > 0]

    def draw(self, cv):
        for p in self.items:
            cv.create_text(p["x"] + 1, p["y"] + 1, text=p["text"], fill="#000000", font=FONTS["hud"])
            cv.create_text(p["x"], p["y"], text=p["text"], fill=p["color"], font=FONTS["hud"])


# --------------------------------------------------------------------------
# Master Yoda (player)
# --------------------------------------------------------------------------
class Yoda:
    HALF_W = 12
    HEIGHT = 62

    def __init__(self):
        self.reset()

    def reset(self, x=90):
        self.x, self.y = float(x), float(GROUND_Y)
        self.vx = self.vy = 0.0
        self.on_ground, self.facing = True, 1
        self.state, self.walk, self.t = "idle", 0.0, 0
        self.attack_t = self.attack_len = 0
        self.invuln = self.hurt_t = 0
        self.victory = self.auto = False
        self.tip = (float(x), float(GROUND_Y - 60))

    def start_attack(self, frames=16):
        if self.attack_t <= 0:
            self.attack_t = self.attack_len = frames
            return True
        return False

    def hurt(self, direction=-1):
        self.invuln, self.hurt_t = 45, 12
        self.vx, self.vy, self.on_ground = direction * 5.0, -6.0, False

    def update(self, arena, move, jump):
        self.t += 1
        self.attack_t = max(0, self.attack_t - 1)
        self.invuln = max(0, self.invuln - 1)
        self.hurt_t = max(0, self.hurt_t - 1)
        if not self.auto:
            target = self.vx if self.hurt_t > 0 else move * WALK_V
            self.vx += (target - self.vx) * 0.4
            if move != 0:
                self.facing = 1 if move > 0 else -1
        self.x = clamp(self.x + self.vx, 24, arena.x_limit())
        if jump and self.on_ground and not self.auto:
            self.vy, self.on_ground = JUMP_V, False
            arena.particles.burst(self.x, self.y, "#e8e0c8", 6, 1.8, 14, 2, 0.05)
        prev_y = self.y
        self.vy += GRAVITY
        self.y += self.vy
        self.on_ground = False
        if self.y >= GROUND_Y:
            self.y, self.vy, self.on_ground = float(GROUND_Y), 0.0, True
        elif self.vy >= 0:
            for (px, py, pw) in arena.surfaces():
                if px - 6 <= self.x <= px + pw + 6 and prev_y <= py + 0.5 and self.y >= py:
                    self.y, self.vy, self.on_ground = float(py), 0.0, True
                    break
        if self.attack_t > 0:
            self.state = "attack"
        elif not self.on_ground:
            self.state = "jump"
        elif abs(self.vx) > 0.6:
            self.state = "walk"
            self.walk += abs(self.vx) * 0.22
        else:
            self.state = "idle"
        if self.victory:
            self.state = "victory"
        return prev_y

    def draw(self, cv):
        if self.invuln > 0 and self.hurt_t <= 0 and (self.invuln // 3) % 2 == 0:
            return
        t, f, x, st = self.t, self.facing, self.x, self.state
        SK, SKD, SKL = "#9bc86a", "#5f8a3a", "#c9e39a"
        ROBE, ROBED, BOOT = "#8a5a2f", "#5e3b1c", "#4b3220"
        bob = leg = 0.0
        if st == "idle":
            bob = math.sin(t * 0.12) * 1.2
        elif st == "walk":
            bob, leg = -abs(math.sin(self.walk)) * 2.5, math.sin(self.walk) * 7
        elif st == "victory":
            bob = -abs(math.sin(t * 0.25)) * 5
        by = self.y + bob
        sh_w = max(6, 16 - (GROUND_Y - self.y) * 0.05)
        cv.create_oval(x - sh_w, GROUND_Y - 2, x + sh_w, GROUND_Y + 4, fill="#1b2a1b", outline="", stipple="gray50")
        foot_y = by - 4 - (5 if st == "jump" else 0)
        for dx, lg in ((-6, leg), (6, -leg)):
            fx = x + dx + lg
            cv.create_oval(fx - 6, foot_y - 3, fx + 6, foot_y + 3, fill=BOOT, outline="#2a1a0e")
        # robe
        cv.create_polygon(x - 14, by - 8, x + 14, by - 8, x + 10, by - 38, x - 10, by - 38,
                          fill=ROBE, outline=ROBED, width=2)
        cv.create_line(x - 9, by - 10, x - 7, by - 36, fill=ROBED)
        cv.create_line(x + 9, by - 10, x + 7, by - 36, fill=ROBED)
        cv.create_polygon(x - 5, by - 38, x + 5, by - 38, x, by - 26, fill="#e3cf9f", outline="")
        cv.create_rectangle(x - 12, by - 24, x + 12, by - 20, fill="#4a2f18", outline="")
        cv.create_rectangle(x - 2, by - 25, x + 2, by - 19, fill="#c9a227", outline="")
        # ears + head
        hy = by - 47
        flap = math.sin(t * 0.1) * 1.5 if st in ("idle", "walk") else (-5 if st in ("jump", "victory") else 0)
        for s in (-1, 1):
            cv.create_polygon(x + s * 10, hy - 6, x + s * 44, hy - 3 + flap, x + s * 11, hy + 7,
                              fill=SK, outline=SKD)
            cv.create_polygon(x + s * 14, hy - 3, x + s * 33, hy - 1 + flap, x + s * 14, hy + 3,
                              fill=SKL, outline="")
        cv.create_oval(x - 15, hy - 14, x + 15, hy + 12, fill=SK, outline=SKD)
        for a, b in ((-9, -1), (-3, -2), (4, -2), (9, -1)):
            cv.create_line(x + a, hy - 10, x + a + 5, hy - 11 + b, fill=SKD)
        blink = (t % 170) < 5 or self.hurt_t > 0
        for s in (-1, 1):
            ex = x + s * 6
            if blink:
                cv.create_line(ex - 4, hy - 1, ex + 4, hy - 1, fill="#2a3d18", width=2)
            else:
                cv.create_oval(ex - 4.5, hy - 5, ex + 4.5, hy + 3, fill="white", outline="#2a3d18")
                cv.create_oval(ex + f * 1.2 - 2, hy - 3, ex + f * 1.2 + 2, hy + 1, fill="#1a1208", outline="")
                cv.create_line(ex - 5, hy - 6, ex + 5, hy - 6, fill=SKD, width=2)
        cv.create_oval(x - 1.5, hy + 2, x + 1.5, hy + 4, fill=SKD, outline="")
        if self.hurt_t > 0:
            cv.create_arc(x - 5, hy + 5, x + 5, hy + 11, start=20, extent=140, style="arc", outline="#3d5a24", width=2)
        else:
            cv.create_arc(x - 5, hy + 3, x + 5, hy + 9, start=200, extent=140, style="arc", outline="#3d5a24", width=2)
        for a, b in ((-2, -5), (1, -7), (5, -5)):
            cv.create_line(x + a, hy - 13, x + a + b, hy - 20, fill="#e8f0d0")
        # arm + lightsaber
        if st == "attack":
            p = 1 - self.attack_t / max(1, self.attack_len)
            th = -125 + 175 * p
        elif st == "jump":
            th = -110
        elif st == "victory":
            th = -95
        elif st == "walk":
            th = -62 + 6 * math.sin(self.walk * 2)
        else:
            th = -68 + 3 * math.sin(t * 0.12)
        sh = (x + f * 7, by - 34)
        hand = (x + f * (13 + (6 if st == "attack" else 0)), by - 26 + (-8 if st in ("jump", "victory") else 0))
        cv.create_line(sh[0], sh[1], hand[0], hand[1], fill=ROBE, width=7, capstyle="round")
        cv.create_oval(hand[0] - 3.5, hand[1] - 3.5, hand[0] + 3.5, hand[1] + 3.5, fill=SK, outline=SKD)

        def vec(angle):
            return f * math.cos(math.radians(angle)), math.sin(math.radians(angle))

        dx, dy = vec(th)
        if st == "attack":
            for k, col in ((3, "#2a468a"), (2, "#3a63b8"), (1, "#5c8de0")):
                ax, ay = vec(th - 16 * k)
                cv.create_line(hand[0] + ax * 8, hand[1] + ay * 8, hand[0] + ax * 40, hand[1] + ay * 40,
                               fill=col, width=4, capstyle="round")
        cv.create_line(hand[0] - dx * 6, hand[1] - dy * 6, hand[0] + dx * 5, hand[1] + dy * 5,
                       fill="#aab0bd", width=4)
        self.tip = (hand[0] + dx * 43, hand[1] + dy * 43)
        blade(cv, hand[0] + dx * 5, hand[1] + dy * 5, self.tip[0], self.tip[1], "blue")


# --------------------------------------------------------------------------
# Dark Lord Kuro (boss)
# --------------------------------------------------------------------------
class Kuro:
    def __init__(self):
        self.reset(0)

    def reset(self, stage):
        self.stage, self.style = stage, stage
        self.t = self.timer = self.shake = self.flash = self.dying_t = 0
        self.state = "idle"
        self.cooldown = 260

    def interval(self):
        return random.randint(max(150, 330 - 40 * self.stage), max(220, 430 - 40 * self.stage))

    def hit(self):
        self.flash, self.shake = 10, 16

    def die(self):
        self.state, self.dying_t = "dying", 0

    def update(self, arena):
        self.t += 1
        self.flash = max(0, self.flash - 1)
        self.shake = max(0, self.shake - 1)
        if self.state == "idle":
            if arena.attacks_enabled():
                self.cooldown -= 1
                if self.cooldown <= 0:
                    self.state, self.timer = "telegraph", 0
        elif self.state == "telegraph":
            self.timer += 1
            if self.timer >= 45:
                self.state, self.timer = "strike", 0
        elif self.state == "strike":
            self.timer += 1
            if self.timer == 12 or (self.style == 3 and self.timer == 22):
                arena.spawn_wave(self.stage)
            if self.timer >= 28:
                self.state, self.cooldown = "idle", self.interval()
        elif self.state == "dying":
            self.dying_t += 1
            if self.dying_t % 4 == 0:
                arena.particles.burst(KURO_X + random.uniform(-55, 55), GROUND_Y - random.uniform(10, 150),
                                      random.choice(["#ff5a2a", "#ffd23a", "#ffffff"]), 8, 4.5, 28, 3.5, 0.1, 2)
            if self.dying_t >= 140:
                self.state = "dead"

    def _pose(self, pair, side):
        wob = math.sin(self.t * 0.07 + pair * 1.3 + side * 0.9)
        base = 255 if pair == 0 else 205
        if self.state == "telegraph":
            k = min(1.0, self.timer / 45.0)
            return base + (15 if pair == 0 else 55) * k + 4 * wob
        if self.state == "strike":
            p, sty = self.timer / 28.0, self.style
            if sty == 0:
                return 270 - 200 * p if pair == 0 else 260 - 190 * p
            if sty == 1:
                return 300 - 220 * p if pair == 0 else 130 + 160 * p
            if sty == 2:
                return 720 * p + 90 * (pair * 2 + side)
            return 180 + (8 * math.sin(p * 10) if pair else 0)
        if self.state == "dying":
            return lerp(base, 100, min(1.0, self.dying_t / 60.0))
        return base + 8 * wob

    def _arm(self, cv, sx, sy, a3, mirror, col):
        a2 = 0.5 * (a3 + 180)
        a1 = 0.5 * (a2 + 180)
        if mirror:
            a1, a2, a3 = 180 - a1, 180 - a2, 180 - a3
        r = math.radians
        ex, ey = sx + 30 * math.cos(r(a1)), sy + 30 * math.sin(r(a1))
        hx, hy = ex + 28 * math.cos(r(a2)), ey + 28 * math.sin(r(a2))
        for (x0, y0, x1, y1) in ((sx, sy, ex, ey), (ex, ey, hx, hy)):
            cv.create_line(x0, y0, x1, y1, fill="#1c1f27", width=11, capstyle="round")
            cv.create_line(x0, y0, x1, y1, fill=col("#6b768d"), width=7, capstyle="round")
        cv.create_oval(ex - 6, ey - 6, ex + 6, ey + 6, fill=col("#8d97ab"), outline="#1c1f27")
        cv.create_oval(hx - 5, hy - 5, hx + 5, hy + 5, fill=col("#aeb7c8"), outline="#1c1f27")
        dx, dy = math.cos(r(a3)), math.sin(r(a3))
        cv.create_line(hx, hy, hx + dx * 5, hy + dy * 5, fill="#9aa3b5", width=5)
        blade(cv, hx + dx * 5, hy + dy * 5, hx + dx * 52, hy + dy * 52, "red")

    def draw(self, cv):
        if self.state == "dead":
            return
        if self.state == "dying" and (self.dying_t // 3) % 3 == 0:
            return
        cx = KURO_X + (random.uniform(-1, 1) * self.shake * 0.4 if self.shake else 0)
        y = GROUND_Y
        fl = self.flash > 0

        def col(c):
            return mix(c, "#ffffff", 0.75) if fl else c

        pulse = 0.5 + 0.5 * math.sin(self.t * 0.15)
        hot = self.state in ("telegraph", "strike")
        cv.create_oval(cx - 70, y - 4, cx + 70, y + 6, fill="#161616", outline="", stipple="gray50")
        # back arms first (away from Yoda), then body, then front arms
        sides = ((1, True), (-1, False))
        for side, mirror in sides[:1]:
            for pair, sy in ((0, y - 112), (1, y - 84)):
                self._arm(cv, cx + 50 * side, sy, self._pose(pair, 1), mirror, col)
        for s in (-1, 1):
            lx = cx + s * 22
            cv.create_rectangle(lx - 13, y - 52, lx + 13, y, fill=col("#262a35"), outline="#8892a6", width=2)
            cv.create_rectangle(lx - 18 if s < 0 else lx - 14, y - 8, lx + 14 if s < 0 else lx + 18, y,
                                fill=col("#1a1d25"), outline="#8892a6")
            cv.create_oval(lx - 6, y - 34, lx + 6, y - 22, fill=col("#5b657a"), outline="#1c1f27")
        cv.create_rectangle(cx - 34, y - 58, cx + 34, y - 46, fill=col("#1e2129"), outline="#8892a6")
        cv.create_polygon(cx - 54, y - 120, cx + 54, y - 120, cx + 40, y - 52, cx - 40, y - 52,
                          fill=col("#2a2e3a"), outline="#8892a6", width=2)
        cv.create_polygon(cx - 38, y - 112, cx + 38, y - 112, cx + 28, y - 62, cx - 28, y - 62,
                          fill=col("#3a4050"), outline="#59637a")
        for vx in (-20, -10, 10, 20):
            cv.create_line(cx + vx, y - 70, cx + vx, y - 62, fill="#14161c", width=3)
        core = mix("#7a0a10", "#ff4a3a", pulse if not hot else 1.0)
        cv.create_oval(cx - 16, y - 100, cx + 16, y - 68, fill="#220608", outline="#8892a6", width=2)
        cv.create_oval(cx - 11, y - 95, cx + 11, y - 73, fill=core, outline="#ffb0a0")
        for s in (-1, 1):
            cv.create_oval(cx + s * 50 - 15, y - 128, cx + s * 50 + 15, y - 104, fill=col("#4a5163"),
                           outline="#8892a6", width=2)
            cv.create_rectangle(cx + s * 50 - 3, y - 126, cx + s * 50 + 3, y - 108, fill="#b3202c", outline="")
        cv.create_polygon(cx - 22, y - 120, cx + 22, y - 120, cx + 19, y - 150, cx, y - 162, cx - 19, y - 150,
                          fill=col("#2f3442"), outline="#8892a6", width=2)
        cv.create_line(cx, y - 162, cx, y - 172, fill="#b3202c", width=3)
        cv.create_rectangle(cx - 17, y - 147, cx + 17, y - 132, fill="#0b0c10", outline="#59637a")
        er = 4 + (2 if hot else 0) + pulse
        for s in (-1, 1):
            ex = cx + s * 9
            cv.create_oval(ex - er - 2, y - 140 - er - 2, ex + er + 2, y - 140 + er + 2, fill="#5a0610", outline="")
            cv.create_oval(ex - er * 0.7, y - 140 - er * 0.7, ex + er * 0.7, y - 140 + er * 0.7,
                           fill="#ff3b3b", outline="#ffd0d0")
        for pair, sy in ((0, y - 112), (1, y - 84)):
            self._arm(cv, cx - 50, sy, self._pose(pair, 0), False, col)
        if self.state == "telegraph":
            cv.create_text(cx - 95, y - 175, text="!", fill=RED, font=FONTS["big"])


# --------------------------------------------------------------------------
# Yoda's Learning Droid (companion)
# --------------------------------------------------------------------------
class Droid:
    def __init__(self):
        self.x, self.y, self.t = 60.0, 200.0, 0
        self.mode, self.mood_t = "idle", 0
        self.msg, self.msg_t = "", 0

    def speak(self, text, frames=320):
        self.msg, self.msg_t = text, frames

    def mood(self, mode, frames=60):
        self.mode, self.mood_t = mode, frames

    def update(self, yoda):
        self.t += 1
        tx = clamp(yoda.x - yoda.facing * 46, 30, ARENA_W - 30)
        ty = clamp(yoda.y - 92 + math.sin(self.t * 0.08) * 5, HUD_H + 34, GROUND_Y - 30)
        self.x += (tx - self.x) * 0.07
        self.y += (ty - self.y) * 0.09
        self.msg_t = max(0, self.msg_t - 1)
        if self.mood_t > 0:
            self.mood_t -= 1
            if self.mood_t == 0 and self.mode in ("happy", "sad"):
                self.mode = "idle"

    def draw(self, cv):
        x, y, t, mode = self.x, self.y, self.t, self.mode
        fl = 6 + 3 * math.sin(t * 0.9)
        cv.create_polygon(x - 6, y + 14, x + 6, y + 14, x, y + 14 + fl, fill="#ffb347", outline="")
        cv.create_polygon(x - 3, y + 14, x + 3, y + 14, x, y + 14 + fl * 0.6, fill="#fff2b0", outline="")
        for s in (-1, 1):
            cv.create_oval(x + s * 17 - 4, y - 2, x + s * 17 + 4, y + 8, fill="#8e99ad", outline="#4a5366")
        cv.create_line(x, y - 14, x, y - 22, fill="#6b7585", width=2)
        bulb = CYAN if mode == "training" else (RED if (t // 15) % 2 == 0 else GREEN)
        cv.create_oval(x - 3, y - 26, x + 3, y - 20, fill=bulb, outline="")
        cv.create_oval(x - 17, y - 14, x + 17, y + 14, fill="#cfd6e4", outline="#6b7585", width=2)
        cv.create_rectangle(x - 12, y - 8, x + 12, y + 5, fill="#0e1b2b", outline="#4a5366")
        if mode == "training":
            for i in range(5):
                h = 2 + 6 * abs(math.sin(t * 0.3 + i * 1.1))
                cv.create_rectangle(x - 10 + i * 4.4, y + 3 - h, x - 7 + i * 4.4, y + 3, fill=CYAN, outline="")
            for st in (t * 12 % 360, (t * 12 + 180) % 360):
                cv.create_arc(x - 27, y - 27, x + 27, y + 27, start=st, extent=80, style="arc", outline=CYAN, width=2)
        elif mode == "happy":
            for s in (-1, 1):
                cv.create_arc(x + s * 5 - 4, y - 6, x + s * 5 + 4, y + 2, start=0, extent=180, style="arc",
                              outline=GREEN, width=2)
        elif mode == "sad":
            for s in (-1, 1):
                cv.create_line(x + s * 5 - 3, y - 1, x + s * 5 + 3, y - 1, fill=RED, width=2)
        else:
            if (t % 150) < 5:
                for s in (-1, 1):
                    cv.create_line(x + s * 5 - 3, y - 1, x + s * 5 + 3, y - 1, fill=CYAN, width=2)
            else:
                for s in (-1, 1):
                    cv.create_oval(x + s * 5 - 2.5, y - 4, x + s * 5 + 2.5, y + 1, fill=CYAN, outline="")
        cv.create_oval(x - 2.5, y + 8, x + 2.5, y + 13, fill=GOLD if mode == "happy" else "#6b7585", outline="")
        if self.msg_t > 0 and self.msg:
            bx = clamp(self.x, 135, ARENA_W - 135)
            txt = cv.create_text(bx, self.y - 36, text=self.msg, width=250, anchor="s", fill="#0b1b2d",
                                 font=FONTS["small"], justify="center")
            bb = cv.bbox(txt)
            if bb:
                dy = 0
                if bb[1] < HUD_H + 6:
                    dy = HUD_H + 6 - bb[1]
                    cv.move(txt, 0, dy)
                    bb = cv.bbox(txt)
                rect = cv.create_rectangle(bb[0] - 7, bb[1] - 5, bb[2] + 7, bb[3] + 5, fill="#e9fbff",
                                           outline=CYAN, width=2)
                cv.tag_lower(rect, txt)


# --------------------------------------------------------------------------
# World scenery
# --------------------------------------------------------------------------
def row(x0, x1, y, n):
    return [(x0 + (x1 - x0) * i / max(1, n - 1), y) for i in range(n)]


LAYOUTS = [
    dict(platforms=[(140, 214, 120), (320, 176, 100), (480, 214, 120), (660, 176, 100)],
         blocks=[(290, 118), (450, 120), (630, 112)], hazards=[(270, 40), (620, 40)],
         samples=[(80, GROUND_Y - 16), (200, 214 - 18), (370, 176 - 18), (430, GROUND_Y - 16),
                  (540, 214 - 18), (710, 176 - 18)]),
    dict(platforms=[(120, 214, 100), (260, 176, 90), (410, 140, 90), (560, 176, 110), (720, 214, 80)],
         blocks=[(375, 98), (520, 116), (690, 150)], hazards=[(320, 40), (660, 40)], samples=[]),
    dict(platforms=[(130, 214, 100), (290, 180, 100), (450, 144, 90), (610, 180, 100), (755, 214, 60)],
         blocks=[(250, 120), (560, 100), (720, 160)], hazards=[(220, 40), (530, 40)], samples=[]),
    dict(platforms=[(110, 214, 90), (250, 178, 90), (400, 214, 90), (540, 178, 100), (700, 140, 90)],
         blocks=[(210, 118), (500, 118), (660, 98)], hazards=[(345, 40), (630, 40)], samples=[]),
]

GLYPHS = ["y=mx+c", "\u0394y", "m", "c", "\u0394x", "\u0177", "x\u2192y"]


def tiles(cam, factor, spacing):
    base = int(cam * factor // spacing)
    off = (cam * factor) % spacing
    for i in range(-1, int(ARENA_W // spacing) + 2):
        yield base + i, i * spacing - off


def paint_background(cv, w, cam, t):
    c1, c2 = WORLDS[w]["sky"]
    bands = 12
    bh = GROUND_Y / bands
    for i in range(bands):
        cv.create_rectangle(0, i * bh, ARENA_W, (i + 1) * bh + 1, fill=mix(c1, c2, i / (bands - 1)), outline="")
    G = GROUND_Y
    if w == 0:
        for k, x in tiles(cam + t * 0.8, 0.12, 280):
            y = 70 + rnd(k) * 40
            for dx, dy, r in ((0, 0, 20), (22, -8, 26), (48, 0, 18)):
                cv.create_oval(x + dx - r, y + dy - r * 0.6, x + dx + r, y + dy + r * 0.6, fill="white", outline="")
        for k, x in tiles(cam, 0.08, 240):
            h = 70 + rnd(k) * 55
            cv.create_polygon(x, G, x + 120, G - h, x + 240, G, fill="#7d8be0", outline="")
            cv.create_polygon(x + 120 - h * 0.28, G - h + h * 0.34, x + 120, G - h, x + 120 + h * 0.28,
                              G - h + h * 0.34, fill="#f4f7ff", outline="")
        for k, x in tiles(cam, 0.22, 150):
            glow = 0.5 + 0.5 * math.sin(t * 0.06 + k)
            colr = mix(["#2fc9b7", "#e063d8", "#7f95ff"][k % 3], "#ffffff", glow * 0.35)
            h = 40 + rnd(k, 3) * 55
            cv.create_polygon(x + 20, G, x + 30, G - h, x + 42, G - h * 0.8, x + 52, G, fill=colr, outline="#ffffff")
            cv.create_line(x + 30, G - h, x + 34, G - 6, fill="#ffffff")
        for k, x in tiles(cam, 0.45, 90):
            cv.create_oval(x, G - 16, x + 54, G + 6, fill="#2f9a3e", outline="#237a30")
    elif w == 1:
        cv.create_oval(830, 44, 930, 144, fill="#ffe08a", outline="#fff3c2", width=4)
        for k, x in tiles(cam, 0.08, 300):
            for i, wd in enumerate((200, 140, 80)):
                cv.create_rectangle(x + (200 - wd) / 2, G - 30 - i * 26, x + (200 + wd) / 2, G - 4 - i * 26,
                                    fill="#c9794a", outline="#8d4f2a")
        for k, x in tiles(cam, 0.25, 170):
            h = 90 + rnd(k) * 30
            cv.create_rectangle(x, G - h, x + 26, G, fill="#d9a566", outline="#8d5a22")
            cv.create_rectangle(x - 5, G - h - 8, x + 31, G - h, fill="#e8bb7c", outline="#8d5a22")
            cv.create_line(x + 9, G - h, x + 9, G, fill="#b27c42")
            cv.create_line(x + 17, G - h, x + 17, G, fill="#b27c42")
        for k, x in tiles(cam, 0.5, 200):
            cv.create_text(x + 50, 80 + rnd(k, 2) * 90 + math.sin(t * 0.03 + k) * 6, text=GLYPHS[k % len(GLYPHS)],
                           fill="#ffd34d", font=FONTS["mid"])
    elif w == 2:
        for k, x in tiles(cam, 0.08, 200):
            h = 60 + rnd(k) * 50
            cv.create_rectangle(x, G - h, x + 80, G, fill="#3b484e", outline="#2a3338")
            cv.create_rectangle(x + 54, G - h - 40, x + 68, G - h, fill="#2f3b40", outline="#2a3338")
            for i in range(3):
                for j in range(int(h // 24)):
                    cv.create_rectangle(x + 8 + i * 22, G - h + 8 + j * 22, x + 20 + i * 22, G - h + 16 + j * 22,
                                        fill="#ffb84d" if rnd(k, i * 7 + j) > 0.45 else "#26323a", outline="")
            for i in range(3):
                sy = G - h - 50 - ((t * 0.5 + i * 22) % 66)
                cv.create_oval(x + 52 - i * 2, sy, x + 70 + i * 3, sy + 16 + i * 3, fill="#8a979c", outline="")
        for k, x in tiles(cam, 0.22, 210):
            gx, gy = x + 90, 110 + rnd(k, 5) * 60
            ang = t * 1.6 * (1 if k % 2 == 0 else -1)
            for i in range(8):
                a = math.radians(ang + i * 45)
                cv.create_line(gx + math.cos(a) * 30, gy + math.sin(a) * 30, gx + math.cos(a) * 42,
                               gy + math.sin(a) * 42, fill="#4a565c", width=9)
            cv.create_oval(gx - 34, gy - 34, gx + 34, gy + 34, fill="#56646b", outline="#3a464c", width=3)
            cv.create_oval(gx - 10, gy - 10, gx + 10, gy + 10, fill="#2a3338", outline="")
        for k, x in tiles(cam, 0.5, 260):
            h = 50 + rnd(k, 4) * 70
            cv.create_rectangle(x, HUD_H, x + 16, HUD_H + h, fill="#7a5a45", outline="#4f3a2d")
            cv.create_rectangle(x - 3, HUD_H + h - 6, x + 19, HUD_H + h + 4, fill="#936d55", outline="#4f3a2d")
            glow = 0.5 + 0.5 * math.sin(t * 0.1 + k)
            cv.create_oval(x + 2, HUD_H + h + 4, x + 14, HUD_H + h + 16, fill=mix("#a85a1a", "#ffb04a", glow),
                           outline="")
    else:
        for k in range(50):
            sx = (rnd(k) * ARENA_W - cam * 0.03) % ARENA_W
            sy = HUD_H + rnd(k, 1) * (G - HUD_H - 30)
            r = 1 + (math.sin(t * 0.08 + k) > 0.6) * 1.5
            cv.create_rectangle(sx, sy, sx + r, sy + r, fill="#ffffff", outline="")
        px = 220 - cam * 0.05
        cv.create_oval(px - 46, 70, px + 46, 162, fill="#7a4cff", outline="#b9a0ff", width=2)
        cv.create_oval(px - 76, 104, px + 76, 128, outline="#4ff0ff", width=2)
        for k, x in tiles(cam, 0.2, 140):
            h = 70 + rnd(k) * 80
            cv.create_rectangle(x, G - h, x + 54, G, fill="#1a1050", outline="#4ff0ff", width=2)
            for j in range(int(h // 20)):
                if rnd(k, j) > 0.4:
                    cv.create_rectangle(x + 8, G - h + 8 + j * 20, x + 18, G - h + 14 + j * 20, fill="#4ff0ff", outline="")
        for k, x in tiles(cam, 0.45, 200):
            cv.create_line(x, G, x, G - 80 - rnd(k, 2) * 30, fill="#8a5cff", width=3)
            cv.create_oval(x - 5, G - 88 - rnd(k, 2) * 30, x + 5, G - 78 - rnd(k, 2) * 30, fill="#ff6fb5", outline="")


def paint_ground(cv, w, cam, t):
    top, dirt = WORLDS[w]["ground"]
    G = GROUND_Y
    cv.create_rectangle(0, G, ARENA_W, ARENA_H, fill=dirt, outline="")
    cv.create_rectangle(0, G, ARENA_W, G + 12, fill=top, outline="")
    off = cam % 40
    if w == 0:
        for i in range(-1, ARENA_W // 20 + 2):
            x = i * 20 - cam % 20
            cv.create_polygon(x, G, x + 4, G - 7, x + 8, G, fill="#7ee063", outline="")
    for i in range(-1, ARENA_W // 40 + 2):
        x = i * 40 - off
        cv.create_line(x, G + 12, x - 14, ARENA_H, fill=mix(dirt, "#000000", 0.25))
        if w == 3:
            cv.create_line(x, G, x - 10, ARENA_H, fill="#4ff0ff")
    cv.create_line(0, G + 12, ARENA_W, G + 12, fill=mix(top, "#000000", 0.3), width=2)
    if w == 3:
        cv.create_line(0, G + 1, ARENA_W, G + 1, fill="#4ff0ff", width=2)
        cv.create_line(0, G + 20, ARENA_W, G + 20, fill="#4f3cc0")


def paint_platform(cv, w, x, y, wd):
    b1, b2 = WORLDS[w]["brick"]
    cv.create_rectangle(x, y, x + wd, y + 16, fill=b1, outline=b2, width=2)
    cv.create_line(x, y + 8, x + wd, y + 8, fill=b2)
    for i, bx in enumerate(range(int(x), int(x + wd), 20)):
        cv.create_line(bx + (10 if i % 2 else 0), y, bx + (10 if i % 2 else 0), y + 8, fill=b2)
        cv.create_line(bx + (0 if i % 2 else 10), y + 8, bx + (0 if i % 2 else 10), y + 16, fill=b2)
    cv.create_line(x + 1, y + 1, x + wd - 1, y + 1, fill=mix(b1, "#ffffff", 0.5), width=2)


def paint_block(cv, blk, t):
    x, y = blk["x"], blk["y"] - (6 * math.sin(blk["bump"] * 0.3) if blk["bump"] > 0 else 0)
    if blk["used"]:
        cv.create_rectangle(x, y, x + 28, y + 28, fill="#8b6b3a", outline="#4f3a2d", width=2)
        return
    cv.create_rectangle(x, y, x + 28, y + 28, fill="#f0b400", outline="#8a5a00", width=2)
    cv.create_rectangle(x + 3, y + 3, x + 25, y + 25, outline="#ffe27a")
    cv.create_text(x + 14, y + 14, text="?", fill="#fff7d0" if (t // 12) % 4 else "#ffffff", font=FONTS["mid"])


def paint_coin(cv, cn, t):
    rx = 8 * abs(math.cos(t * 0.12 + cn["ph"])) + 1.5
    cv.create_oval(cn["x"] - rx, cn["y"] - 9, cn["x"] + rx, cn["y"] + 9, fill=GOLD, outline="#b07a00", width=2)
    if rx > 4:
        cv.create_line(cn["x"], cn["y"] - 5, cn["x"], cn["y"] + 5, fill="#fff2a8", width=2)


def paint_gem(cv, g, t, r=11, label=None, locked=False):
    x, y = g["x"], g["y"] + math.sin(t * 0.08 + g.get("ph", 0)) * 3
    c1, c2 = ("#6b7280", "#9aa0ad") if locked else ("#4fe8ff", "#e6fbff")
    cv.create_polygon(x, y - r, x + r * 0.8, y - r * 0.2, x + r * 0.5, y + r, x - r * 0.5, y + r, x - r * 0.8,
                      y - r * 0.2, fill=c1, outline=c2, width=2)
    cv.create_line(x - r * 0.8, y - r * 0.2, x + r * 0.8, y - r * 0.2, fill=c2)
    cv.create_line(x, y - r, x, y + r, fill=c2)
    if locked:
        cv.create_text(x, y, text="?", fill="#e5e7eb", font=FONTS["small"])
    if label:
        cv.create_text(x, y - r - 9, text=label, fill="#ffffff", font=FONTS["label"])


def paint_hazard(cv, w, hz, t):
    x, wd, G = hz["x"], hz["w"], GROUND_Y
    if w == 0:
        for i in range(int(wd // 10)):
            cv.create_polygon(x + i * 10, G, x + i * 10 + 5, G - 24, x + i * 10 + 10, G, fill="#a04bff", outline="#e0c0ff")
    elif w == 1:
        for i in range(int(wd // 12)):
            hh = 22 + 6 * math.sin(t * 0.4 + i * 1.7)
            cv.create_polygon(x + i * 12, G, x + i * 12 + 6, G - hh, x + i * 12 + 12, G, fill="#ff6a00", outline="")
            cv.create_polygon(x + i * 12 + 3, G, x + i * 12 + 6, G - hh * 0.6, x + i * 12 + 9, G, fill="#ffe14d", outline="")
    elif w == 2:
        cx, cy = x + wd / 2, G - 17
        a0 = t * 0.5
        for i in range(8):
            a = a0 + i * math.pi / 4
            cv.create_line(cx, cy, cx + math.cos(a) * 20, cy + math.sin(a) * 20, fill="#c8d0d4", width=5)
        cv.create_oval(cx - 14, cy - 14, cx + 14, cy + 14, fill="#9aa5aa", outline="#4a565c", width=2)
        cv.create_oval(cx - 4, cy - 4, cx + 4, cy + 4, fill="#2a3338", outline="")
    else:
        cv.create_line(x, G, x, G - 26, fill="#ff6fb5", width=4)
        cv.create_line(x + wd, G, x + wd, G - 26, fill="#ff6fb5", width=4)
        pts = []
        for i in range(9):
            pts += [x + wd * i / 8, G - 13 + (8 if i % 2 else -8) * math.sin(t * 0.3 + i)]
        cv.create_line(*pts, fill="#4ff0ff", width=3)


# --------------------------------------------------------------------------
# Arena: physics, objects, drawing and cut-scenes
# --------------------------------------------------------------------------
class Arena:
    def __init__(self, game, canvas):
        self.game, self.cv = game, canvas
        self.yoda, self.kuro, self.droid = Yoda(), Kuro(), Droid()
        self.particles, self.popups = Particles(), Popups()
        self.world = 0
        self.waves, self.platforms, self.blocks, self.coins, self.gems, self.hazards, self.samples = [], [], [], [], [], [], []
        self.cut = None
        self.banner_data = None
        self.curtain = None
        self.t = 0
        self.last_deflect_msg = -999
        self.set_world(0)

    # ----- world setup -----
    def set_world(self, w):
        self.world = w
        lay = LAYOUTS[w]
        self.platforms = [tuple(p) for p in lay["platforms"]]
        self.blocks = [dict(x=x, y=y, used=False, bump=0) for x, y in lay["blocks"]]
        self.hazards = [dict(x=x, w=wd) for x, wd in lay["hazards"]]
        self.coins, self.gems, self.waves = [], [], []
        for (px, py, pw) in self.platforms:
            for f in (0.25, 0.5, 0.75):
                self.coins.append(dict(x=px + pw * f, y=py - 22, ph=random.uniform(0, 6)))
        for x in (170, 250, 380, 520, 650, 770):
            if not any(h["x"] - 10 <= x <= h["x"] + h["w"] + 10 for h in self.hazards):
                self.coins.append(dict(x=x, y=GROUND_Y - 22, ph=random.uniform(0, 6)))
        for (px, py, pw) in self.platforms[1:3]:
            self.gems.append(dict(x=px + pw / 2, y=py - 56, ph=random.uniform(0, 6)))
        self.samples = [dict(x=x, y=y, xv=i + 1, got=False, ph=i) for i, (x, y) in enumerate(lay["samples"])]
        self.yoda.reset(90)
        self.kuro.reset(w)
        self.particles.items, self.popups.items = [], []
        self.cut = None

    def surfaces(self):
        for p in self.platforms:
            yield p
        for b in self.blocks:
            yield (b["x"], b["y"], 28)

    def x_limit(self):
        return KURO_X - 78 if self.cut else YODA_MAX_X

    def attacks_enabled(self):
        return self.game.mode == "play" and self.game.stage_started

    def spawn_wave(self, stage):
        self.waves.append(dict(x=KURO_X - 70, speed=4.6 + 0.5 * stage, ph=0))
        self.particles.burst(KURO_X - 70, GROUND_Y - 10, "#ff5a3a", 12, 3.5, 20, 3, 0.05)

    # ----- helpers used by the game -----
    def banner(self, text, sub="", frames=110):
        self.banner_data = dict(text=text, sub=sub, t=0, dur=frames)

    def start_curtain(self, callback):
        self.curtain = dict(t=0, cb=callback)

    def begin_attack(self, final):
        self.cut = dict(phase="run", t=0, final=final, hit=False)
        self.yoda.auto = True
        self.yoda.facing = 1
        self.waves = []

    # ----- per-frame update -----
    def update(self, move, jump, attack):
        self.t += 1
        g, y = self.game, self.yoda
        if attack and y.start_attack():
            self.particles.burst(y.tip[0], y.tip[1], "#9ec8ff", 4, 1.5, 12, 2, 0)
        prev_y = y.update(self, move, jump)
        self._block_bumps(prev_y)
        self._collect()
        self._hazards()
        self._waves()
        self._post()

    def update_idle(self):
        self.t += 1
        self._post(player=False)

    def _post(self, player=True):
        self.kuro.update(self)
        for b in self.blocks:
            b["bump"] = max(0, b["bump"] - 1)
        self.droid.update(self.yoda)
        if self.world == 2 and self.t % 14 == 0:
            self.particles.add(random.uniform(0, ARENA_W), GROUND_Y, 0.3, -1.4, "#c9d1d4", 60, 3, 0)
        if self.world == 3 and self.t % 20 == 0:
            self.particles.add(random.uniform(0, ARENA_W), HUD_H + 4, 0, 1.2, "#4ff0ff", 70, 1.5, 0)
        if self.game.mode == "victory" and self.t % 2 == 0:
            self.particles.add(random.uniform(0, ARENA_W), HUD_H, random.uniform(-1, 1), 2.0,
                               random.choice([GOLD, CYAN, PINK, GREEN]), 80, 2.5, 0.02)
        if self.yoda.state == "victory" and self.t % 3 == 0:
            self.particles.burst(self.yoda.tip[0], self.yoda.tip[1], random.choice([GOLD, CYAN, PINK]), 3, 2.5, 28, 2, 0.05)
        self.particles.update()
        self.popups.update()
        if self.banner_data:
            self.banner_data["t"] += 1
            if self.banner_data["t"] >= self.banner_data["dur"]:
                self.banner_data = None
        if self.curtain:
            self.curtain["t"] += 1
            if self.curtain["t"] == 30:
                self.curtain["cb"]()
            if self.curtain["t"] >= 60:
                self.curtain = None

    def update_cutscene(self):
        self.t += 1
        y, c, g = self.yoda, self.cut, self.game
        if c:
            c["t"] += 1
            tx = KURO_X - 120
            if c["phase"] == "run":
                y.vx = clamp(tx - y.x, -9, 9)
                y.facing = 1
                y.update(self, 0, False)
                if abs(tx - y.x) < 4:
                    c["phase"], c["t"] = ("charge" if c["final"] else "slash"), 0
                    y.vx = 0
            elif c["phase"] == "charge":
                y.vx = 0
                y.update(self, 0, False)
                a = random.uniform(0, math.tau)
                self.particles.add(y.tip[0] + math.cos(a) * 40, y.tip[1] + math.sin(a) * 40,
                                   -math.cos(a) * 2.5, -math.sin(a) * 2.5, CYAN, 16, 2.5)
                if c["t"] > 45:
                    c["phase"], c["t"] = "slash", 0
            elif c["phase"] == "slash":
                y.vx = 0
                if c["t"] == 1:
                    y.attack_t = y.attack_len = 30
                y.update(self, 0, False)
                if c["t"] == 16 and not c["hit"]:
                    c["hit"] = True
                    self.particles.burst(KURO_X - 50, GROUND_Y - 90, "#9ec8ff", 40 if c["final"] else 22, 6, 30, 3.5, 0.1, 1)
                    self.particles.burst(KURO_X - 50, GROUND_Y - 90, "#ffffff", 16, 4, 22, 3, 0.05)
                    g.on_attack_hit(c["final"])
                if c["t"] >= 40:
                    c["phase"], c["t"] = ("wait" if c["final"] else "return"), 0
            elif c["phase"] == "return":
                y.vx = clamp(150 - y.x, -9, 9)
                y.facing = -1 if y.vx < 0 else 1
                y.update(self, 0, False)
                if abs(150 - y.x) < 4:
                    y.vx = 0
                    y.facing = 1
                    self.cut = None
                    y.auto = False
                    g.on_attack_done(False)
            elif c["phase"] == "wait":
                y.vx = 0
                y.update(self, 0, False)
                if self.kuro.state == "dead" and c["t"] > 30:
                    y.victory = True
                    self.cut = None
                    g.on_attack_done(True)
        self._post(player=False)

    # ----- interactions -----
    def _block_bumps(self, prev_y):
        y = self.yoda
        if y.vy >= 0:
            return
        prev_head, head = prev_y - Yoda.HEIGHT, y.y - Yoda.HEIGHT
        for b in self.blocks:
            if abs(y.x - (b["x"] + 14)) < 24 and prev_head >= b["y"] + 28 and head < b["y"] + 28:
                y.y, y.vy = b["y"] + 28 + Yoda.HEIGHT + 1, 1.0
                b["bump"] = 12
                if not b["used"]:
                    b["used"] = True
                    self.game.add_score(50)
                    self.game.heal(5)
                    self.popups.add(b["x"] + 14, b["y"] - 6, "+50", GOLD)
                    self.particles.burst(b["x"] + 14, b["y"], GOLD, 10, 3, 24, 2.5, 0.15, 2)
                    self.game.droid_hint()
                break

    def _collect(self):
        y = self.yoda
        cx, cy = y.x, y.y - 30
        for cn in self.coins[:]:
            if (cn["x"] - cx) ** 2 + (cn["y"] - cy) ** 2 < 26 ** 2:
                self.coins.remove(cn)
                self.game.add_score(10)
                self.popups.add(cn["x"], cn["y"] - 8, "+10", GOLD, 36)
                self.particles.burst(cn["x"], cn["y"], GOLD, 6, 2.5, 18, 2, 0.05)
        for gm in self.gems[:]:
            if (gm["x"] - cx) ** 2 + (gm["y"] - cy) ** 2 < 30 ** 2:
                self.gems.remove(gm)
                self.game.add_score(25)
                self.popups.add(gm["x"], gm["y"] - 10, "+25", CYAN, 40)
                self.particles.burst(gm["x"], gm["y"], CYAN, 10, 3, 22, 2.5, 0.05)
        for s in self.samples:
            if not s["got"] and (s["x"] - cx) ** 2 + (s["y"] - cy) ** 2 < 30 ** 2:
                self.game.stage.crystal_touched(s)

    def _hazards(self):
        y = self.yoda
        if y.invuln > 0:
            return
        for h in self.hazards:
            if h["x"] - 4 < y.x + 8 and y.x - 8 < h["x"] + h["w"] + 4 and y.y > GROUND_Y - 22:
                self.game.damage_yoda(8, "Hazard! ")
                y.hurt(-1 if y.x < h["x"] + h["w"] / 2 else 1)
                self.particles.burst(y.x, y.y - 20, RED, 10, 3, 20, 2.5, 0.1)
                break

    def _waves(self):
        y = self.yoda
        for w in self.waves[:]:
            w["x"] -= w["speed"]
            w["ph"] += 1
            if self.t % 3 == 0:
                self.particles.add(w["x"] + 12, GROUND_Y - random.uniform(0, 20), 1, -0.5, "#ff7a3a", 14, 2)
            if y.attack_t > 0 and y.facing == 1 and 0 < w["x"] - y.x < 75:
                self.waves.remove(w)
                self.particles.burst(w["x"], GROUND_Y - 12, "#9ec8ff", 14, 3.5, 20, 2.5, 0.05)
                self.game.add_score(15)
                self.popups.add(w["x"], GROUND_Y - 40, "Deflected! +15", CYAN, 44)
                continue
            if y.invuln == 0 and abs(w["x"] - y.x) < 20 and y.y > GROUND_Y - 26:
                self.waves.remove(w)
                self.game.damage_yoda(6, "Hit by Kuro's wave! ")
                y.hurt(-1)
                continue
            if w["x"] < -30:
                self.waves.remove(w)
        # sabre swing near Kuro: harmless sparks + hint
        if y.attack_t == y.attack_len - 6 and y.attack_len and abs(y.x - (KURO_X - 60)) < 90 and y.facing == 1:
            self.particles.burst(KURO_X - 58, y.y - 40, "#ffffff", 8, 3, 14, 2, 0.05)
            if self.t - self.last_deflect_msg > 200:
                self.last_deflect_msg = self.t
                self.droid.speak("Kuro's shield absorbs raw force. Finish the lesson to shatter it!", 200)

    # ----- drawing -----
    def draw(self):
        cv, g = self.cv, self.game
        cv.delete("all")
        w = self.world
        cam = self.yoda.x
        cv.create_rectangle(-2000, -2000, 4000, 4000, fill="#05060f", outline="")
        paint_background(cv, w, cam, self.t)
        paint_ground(cv, w, cam, self.t)
        for hz in self.hazards:
            paint_hazard(cv, w, hz, self.t)
        for (px, py, pw) in self.platforms:
            paint_platform(cv, w, px, py, pw)
        for b in self.blocks:
            paint_block(cv, b, self.t)
        for cn in self.coins:
            paint_coin(cv, cn, self.t)
        for gm in self.gems:
            paint_gem(cv, gm, self.t, 10)
        active = g.stage is not None and g.stage.index == 0 and g.stage.phase >= 2
        for s in self.samples:
            if not s["got"]:
                paint_gem(cv, s, self.t, 14, f"X={s['xv']}" if active else None, locked=not active)
        self.kuro.draw(cv)
        for wv in self.waves:
            x = wv["x"]
            cv.create_polygon(x - 18, GROUND_Y, x - 6, GROUND_Y - 14, x - 14, GROUND_Y - 30, x + 4, GROUND_Y - 16,
                              x + 18, GROUND_Y - 4, x + 18, GROUND_Y, fill="#ff3a2a", outline="#ffb04a", width=2)
        self.droid.draw(cv)
        self.yoda.draw(cv)
        if self.cut and self.cut["phase"] in ("charge", "slash"):
            c = self.cut
            if c["phase"] == "charge":
                r = 8 + c["t"] * 0.5
                cv.create_oval(self.yoda.tip[0] - r, self.yoda.tip[1] - r, self.yoda.tip[0] + r, self.yoda.tip[1] + r,
                               outline=CYAN, width=3)
            elif 8 <= c["t"] <= 24:
                k = 3.0 if c["final"] else 1.8
                blade(cv, self.yoda.x + 20, self.yoda.y - 40, KURO_X - 40, GROUND_Y - 90, "blue", k)
        self.particles.draw(cv)
        self.popups.draw(cv)
        self._hud()
        self._overlays()
        self._fit()

    def _fit(self):
        cv = self.cv
        w, h = max(1, cv.winfo_width()), max(1, cv.winfo_height())
        s = min(w / ARENA_W, h / ARENA_H)
        if abs(s - 1.0) > 0.001:
            cv.scale("all", 0, 0, s, s)
        ox, oy = (w - ARENA_W * s) / 2, (h - ARENA_H * s) / 2
        if ox or oy:
            cv.move("all", ox, oy)

    def _hud(self):
        cv, g = self.cv, self.game
        w = self.world
        cv.create_rectangle(0, 0, ARENA_W, HUD_H, fill="#0d0f1c", outline="#2a2f4a", width=2)
        cv.create_text(14, 8, text=f"SCORE {g.score:06d}", anchor="nw", fill=GOLD, font=FONTS["hud"])
        cv.create_text(14, 27, text=f"WORLD {w + 1}-{N_STAGES}  {WORLDS[w]['name']}: {WORLDS[w]['sub']}",
                       anchor="nw", fill=FG, font=FONTS["hud_s"])
        cv.create_text(14, 45, text="YODA", anchor="w", fill=GREEN, font=FONTS["tiny"])
        cv.create_rectangle(48, 41, 248, 49, fill="#1b2a1b", outline="#3f6a3f")
        cv.create_rectangle(48, 41, 48 + 200 * g.yoda_hp / YODA_MAX_HP, 49, fill=GREEN, outline="")
        # learning progress
        prog = g.overall_progress()
        cv.create_text(540, 9, text=f"LEARNING PROGRESS  {int(prog * 100)}%", fill=CYAN, font=FONTS["hud_s"])
        x0, x1, yy = 340, 740, 36
        cv.create_rectangle(x0, yy - 5, x1, yy + 5, fill="#1b1f38", outline="#3a4070")
        cv.create_rectangle(x0, yy - 5, x0 + (x1 - x0) * prog, yy + 5, fill=CYAN, outline="")
        for i in range(N_STAGES):
            nx = x0 + (x1 - x0) * (i + 0.5) / N_STAGES
            done = i < g.stages_done
            cur = i == g.stage_index and g.mode in ("play", "cutscene")
            fillc = GOLD if done else (CYAN if cur else "#3a4070")
            cv.create_oval(nx - 11, yy - 11, nx + 11, yy + 11, fill=fillc, outline="#0d0f1c", width=2)
            cv.create_text(nx, yy, text="\u2713" if done else str(i + 1), fill="#0d0f1c", font=FONTS["label"])
        # Kuro HP
        hp = g.kuro_hp_disp
        cv.create_text(770, 9, text="DARK LORD KURO", anchor="nw", fill=RED, font=FONTS["hud_s"])
        cv.create_text(1086, 9, text=f"HP {int(math.ceil(hp))} / {KURO_MAX_HP}", anchor="ne", fill=FG, font=FONTS["hud_s"])
        cv.create_rectangle(770, 28, 1086, 46, fill="#2a0a10", outline="#7a2030", width=2)
        cv.create_rectangle(772, 30, 772 + 312 * clamp(hp, 0, KURO_MAX_HP) / KURO_MAX_HP, 44, fill=RED, outline="")
        for i in range(1, 4):
            cv.create_line(770 + 316 * i / 4, 28, 770 + 316 * i / 4, 46, fill="#0d0f1c", width=2)

    def _overlays(self):
        cv, g = self.cv, self.game
        if self.banner_data:
            b = self.banner_data
            k = min(1.0, b["t"] / 12, (b["dur"] - b["t"]) / 12)
            hh = 70 * clamp(k, 0, 1)
            cy = 170
            cv.create_rectangle(0, cy - hh, ARENA_W, cy + hh, fill="#0d0f1c", outline=GOLD, width=2)
            if k > 0.8:
                cv.create_text(ARENA_W / 2, cy - 14, text=b["text"], fill=GOLD, font=FONTS["mid"])
                cv.create_text(ARENA_W / 2, cy + 22, text=b["sub"], fill=FG, font=FONTS["sub"], width=900, justify="center")
        if self.curtain:
            t = self.curtain["t"]
            wd = ARENA_W * t / 30 if t < 30 else ARENA_W * (1 - (t - 30) / 30)
            if t < 30:
                cv.create_rectangle(0, 0, wd, ARENA_H, fill="#05060f", outline="")
            else:
                cv.create_rectangle(ARENA_W - wd, 0, ARENA_W, ARENA_H, fill="#05060f", outline="")
        mode = g.mode
        if mode in ("title", "paused", "victory", "defeat"):
            cv.create_rectangle(0, HUD_H, ARENA_W, ARENA_H, fill="#05060f", outline="", stipple="gray75")
            cx = ARENA_W / 2
            if mode == "title":
                cv.create_text(cx, 96, text="MASTER YODA  vs.  DARK LORD KURO", fill=GOLD, font=FONTS["big"])
                cv.create_text(cx, 140, text="A Linear Regression Boss Battle  -  y\u0302 = m\u00b7x + c", fill=CYAN, font=FONTS["mid"])
                for i, line in enumerate(g.history.summary_lines()[:5]):
                    cv.create_text(cx, 178 + i * 20, text=line, fill=FG, font=FONTS["ui"])
                cv.create_text(cx, 296, text="Press ENTER or click START  |  T = tutorial  |  Arrows/AD move, Space jump, F saber",
                               fill=DIM, font=FONTS["ui"])
            elif mode == "paused":
                cv.create_text(cx, 160, text="PAUSED", fill=GOLD, font=FONTS["big"])
                cv.create_text(cx, 210, text="Press P to resume", fill=FG, font=FONTS["sub"])
            elif mode == "victory":
                cv.create_text(cx, 92, text="VICTORY!", fill=GOLD, font=FONTS["big"])
                cv.create_text(cx, 134, text="Kuro is defeated. You trained a regression model and predicted the unseen!",
                               fill=CYAN, font=FONTS["sub"])
                for i, line in enumerate(g.victory_lines):
                    cv.create_text(cx, 166 + i * 21, text=line, fill=FG, font=FONTS["ui"], width=980, justify="center")
                cv.create_text(cx, 300, text="Press ENTER to play again (new random data every time)", fill=DIM, font=FONTS["ui"])
            else:
                cv.create_text(cx, 110, text="YODA HAS FALLEN", fill=RED, font=FONTS["big"])
                cv.create_text(cx, 158, text="Mistakes and hazards cost HP. Every wrong answer is a chance to learn.",
                               fill=FG, font=FONTS["sub"])
                cv.create_text(cx, 190, text=f"Kuro still has {int(g.kuro_hp)} HP.  Score: {g.score}", fill=GOLD, font=FONTS["sub"])
                cv.create_text(cx, 300, text="Press ENTER to retry this world  |  R to restart the whole game", fill=DIM, font=FONTS["ui"])


# --------------------------------------------------------------------------
# Interactive graph (observations, regression lines, residuals)
# --------------------------------------------------------------------------
class GraphView:
    PL, PR, PT, PB = 58, 18, 34, 42

    def __init__(self, game, canvas):
        self.game, self.cv = game, canvas
        self.mouse = None
        self.w = self.h = 400
        self.xmin, self.xmax, self.ymin, self.ymax = 0.0, 10.0, 0.0, 10.0
        canvas.bind("<Motion>", self._motion)
        canvas.bind("<Leave>", lambda e: setattr(self, "mouse", None))

    def _motion(self, e):
        self.mouse = (e.x, e.y)

    # data <-> pixel
    def setup(self, xmin, xmax, ymin, ymax):
        if xmax - xmin < 1e-9:
            xmax = xmin + 1
        if ymax - ymin < 1e-9:
            ymax = ymin + 1
        self.xmin, self.xmax, self.ymin, self.ymax = xmin, xmax, ymin, ymax

    def px(self, x):
        return self.PL + (x - self.xmin) / (self.xmax - self.xmin) * (self.w - self.PL - self.PR)

    def py(self, y):
        return self.h - self.PB - (y - self.ymin) / (self.ymax - self.ymin) * (self.h - self.PT - self.PB)

    def ix(self, px):
        return self.xmin + (px - self.PL) / (self.w - self.PL - self.PR) * (self.xmax - self.xmin)

    def iy(self, py):
        return self.ymin + (self.h - self.PB - py) / (self.h - self.PT - self.PB) * (self.ymax - self.ymin)

    # drawing helpers (data coordinates)
    def axes(self, xlabel, ylabel, title=""):
        cv, L, R, T, B = self.cv, self.PL, self.w - self.PR, self.PT, self.h - self.PB
        cv.create_rectangle(L, T, R, B, fill="#10132a", outline="#2d3364")
        sx, sy = nice_step(self.xmax - self.xmin, 7), nice_step(self.ymax - self.ymin, 6)
        x = math.ceil(self.xmin / sx - 1e-9) * sx
        while x <= self.xmax + 1e-9:
            p = self.px(x)
            cv.create_line(p, T, p, B, fill="#1c2048")
            cv.create_text(p, B + 10, text=f"{x:g}", fill=DIM, font=FONTS["tiny"])
            x += sx
        y = math.ceil(self.ymin / sy - 1e-9) * sy
        while y <= self.ymax + 1e-9:
            p = self.py(y)
            cv.create_line(L, p, R, p, fill="#1c2048")
            cv.create_text(L - 6, p, text=f"{y:g}", fill=DIM, font=FONTS["tiny"], anchor="e")
            y += sy
        if self.xmin <= 0 <= self.xmax:
            cv.create_line(self.px(0), T, self.px(0), B, fill="#6a73c0", width=2)
        if self.ymin <= 0 <= self.ymax:
            cv.create_line(L, self.py(0), R, self.py(0), fill="#6a73c0", width=2)
        cv.create_text((L + R) / 2, self.h - 11, text=xlabel, fill=FG, font=FONTS["small"])
        cv.create_text(13, (T + B) / 2, text=ylabel, fill=FG, font=FONTS["small"], angle=90)
        if title:
            cv.create_text((L + R) / 2, 14, text=title, fill=GOLD, font=FONTS["ui_b"])

    def _clip(self, xa, ya, xb, yb):
        lo, hi = self.ymin, self.ymax
        if (ya < lo and yb < lo) or (ya > hi and yb > hi):
            return None
        x0, y0, x1, y1 = xa, ya, xb, yb

        def at(yv):
            return x0 + (x1 - x0) * (yv - y0) / (y1 - y0) if y1 != y0 else x0

        if y0 < lo:
            xa, ya = at(lo), lo
        elif y0 > hi:
            xa, ya = at(hi), hi
        if y1 < lo:
            xb, yb = at(lo), lo
        elif y1 > hi:
            xb, yb = at(hi), hi
        return xa, ya, xb, yb

    def seg(self, xa, ya, xb, yb, color, width=2, dash=None):
        s = self._clip(xa, ya, xb, yb)
        if s:
            kw = dict(fill=color, width=width)
            if dash:
                kw["dash"] = dash
            self.cv.create_line(self.px(s[0]), self.py(s[1]), self.px(s[2]), self.py(s[3]), **kw)

    def line(self, m, c, color, width=2, dash=None, x0=None, x1=None):
        x0 = self.xmin if x0 is None else x0
        x1 = self.xmax if x1 is None else x1
        self.seg(x0, m * x0 + c, x1, m * x1 + c, color, width, dash)

    def dot(self, x, y, color, r=5, outline="#ffffff"):
        px, py = self.px(x), self.py(y)
        self.cv.create_oval(px - r, py - r, px + r, py + r, fill=color, outline=outline, width=1)

    def ring(self, x, y, r, color, width=2):
        px, py = self.px(x), self.py(y)
        self.cv.create_oval(px - r, py - r, px + r, py + r, outline=color, width=width)

    def txt(self, x, y, text, color=FG, anchor="center", font=None, dx=0, dy=0):
        self.cv.create_text(self.px(x) + dx, self.py(y) + dy, text=text, fill=color, anchor=anchor,
                            font=font or FONTS["small"])

    def rect(self, x0, y0, x1, y1, fill, outline=""):
        self.cv.create_rectangle(self.px(x0), self.py(y1), self.px(x1), self.py(y0), fill=fill, outline=outline)

    def legend(self, items):
        x, y = self.PL + 8, self.PT + 8
        for color, label, dash in items:
            kw = dict(fill=color, width=3)
            if dash:
                kw["dash"] = (4, 3)
            self.cv.create_line(x, y + 6, x + 22, y + 6, **kw)
            self.cv.create_text(x + 28, y + 6, text=label, anchor="w", fill=FG, font=FONTS["tiny"])
            y += 15

    def redraw(self):
        cv, g = self.cv, self.game
        cv.delete("all")
        self.w, self.h = max(260, cv.winfo_width()), max(200, cv.winfo_height())
        cv.create_rectangle(0, 0, self.w, self.h, fill="#0c0e1d", outline="")
        if g.stage is None or g.mode == "title":
            cv.create_text(self.w / 2, self.h / 2, text="Live regression graph\nappears here once the battle starts",
                           fill=DIM, font=FONTS["ui"], justify="center")
            return
        g.stage.draw_graph(self)
        self._hover()

    def _hover(self):
        if not self.mouse or not self.game.stage:
            return
        mx, my = self.mouse
        L, R, T, B = self.PL, self.w - self.PR, self.PT, self.h - self.PB
        if not (L <= mx <= R and T <= my <= B):
            return
        cv = self.cv
        cv.create_line(mx, T, mx, B, fill="#3a4080", dash=(2, 3))
        cv.create_line(L, my, R, my, fill="#3a4080", dash=(2, 3))
        best = None
        for (x, y) in self.game.stage.hover_points():
            d = math.hypot(self.px(x) - mx, self.py(y) - my)
            if d < 16 and (best is None or d < best[0]):
                best = (d, x, y)
        if best:
            self.ring(best[1], best[2], 9, GOLD, 2)
            label = f"({best[1]:g}, {best[2]:.2f})"
        else:
            label = f"x={self.ix(mx):.2f}  y={self.iy(my):.2f}"
        tx = mx + 12 if mx < R - 120 else mx - 12
        ty = my - 14 if my > T + 24 else my + 16
        t = cv.create_text(tx, ty, text=label, anchor="w" if mx < R - 120 else "e", fill="#ffffff", font=FONTS["small"])
        bb = cv.bbox(t)
        if bb:
            r = cv.create_rectangle(bb[0] - 3, bb[1] - 2, bb[2] + 3, bb[3] + 2, fill="#232857", outline="#5a62b0")
            cv.tag_lower(r, t)


# --------------------------------------------------------------------------
# Stages (one per world)
# --------------------------------------------------------------------------
class Stage:
    index = 0

    def __init__(self, game):
        self.game = game
        self.phase = 0
        self.hint_n = {}

    def enter(self):
        pass

    def leave(self):
        pass

    def tick(self):
        pass

    def progress(self):
        return 0.0

    def draw_graph(self, gv):
        pass

    def telemetry(self):
        return ""

    def hover_points(self):
        return []

    def primary_action(self):
        pass

    def crystal_touched(self, s):
        pass

    def hints_for(self, phase):
        return ["Keep going - read the lesson panel."]

    def hint(self):
        hs = self.hints_for(self.phase)
        n = self.hint_n.get(self.phase, 0)
        self.hint_n[self.phase] = n + 1
        return hs[min(n, len(hs) - 1)]


def choice_buttons(game, parent, options, callback):
    """Row of answer buttons; options = [(text, is_correct, feedback)]."""
    for text, ok, fb in options:
        b = game.mk_button(parent, text, lambda o=(ok, fb): callback(*o), BLUE)
        b.config(wraplength=230, justify="left", anchor="w", width=26)
        b.pack(side="left", padx=4, pady=2, fill="y")


class Stage1(Stage):
    """WORLD 1 - data collection, variables, positive linear relationship."""
    index = 0
    X_NAME, Y_NAME = "Kyber crystal charge time", "Lightsaber force output"
    X_NEXT = N_CLEAN + 1  # the unseen sample the player must PREDICT before charging it

    def enter(self):
        g = self.game
        self.d = g.clean
        self.phase, self.hint_n = 0, {}
        self.collected, self.pop = {}, {}
        self.pred_var, self.pred_ok, self.pred_tries = tk.DoubleVar(value=0.0), False, 0
        self.q = [
            [(f"{self.X_NAME} (seconds)", True, ""),
             (f"{self.Y_NAME} (force units)", False,
              "Not quite: force is what we MEASURE after charging. It responds to X, so it is the output."),
             ("Colour of the crystal", False, "A colour is a label, not a number we can increase step by step.")],
            [(f"{self.Y_NAME} (force units)", True, ""),
             (f"{self.X_NAME} (seconds)", False,
              "That is the input we choose, so it is X. Y is the result that changes because of X."),
             ("Yoda's height", False, "Yoda's height does not change when we charge a crystal, so it is not the output.")],
            [("Y goes UP as X goes up (positive linear relationship)", True, ""),
             ("Y goes DOWN as X goes up (negative relationship)", False,
              "Check the table: each new sample has a LARGER force than the one before."),
             ("There is no pattern", False, "Look again: the points line up neatly. That is a strong linear pattern.")],
        ]
        for opts in self.q:
            random.shuffle(opts)
        self.refresh()

    def progress(self):
        extra = len(self.collected) / N_CLEAN if self.phase == 2 else 0
        return clamp((self.phase + extra) / 5, 0, 1)

    def refresh(self):
        g = self.game
        g.clear_controls()
        f = g.stage_ctrl
        if self.phase in (0, 1, 4):
            qi = {0: 0, 1: 1, 4: 2}[self.phase]
            choice_buttons(g, f, self.q[qi], self.answer)
        elif self.phase == 3:
            self.pred_scale = g.mk_scale(f, f"Your prediction of Y at X = {self.X_NEXT}", 0, 80, 0.5, self.pred_var, None, 330)
            self.pred_scale.pack(side="left", padx=6)
            g.mk_button(f, f"Charge crystal X={self.X_NEXT}!", self.check_prediction, GREEN).pack(side="left", padx=6, pady=6)
        else:
            g.mk_button(f, "Collect next sample (C)", self.collect_next, GREEN).pack(side="left", padx=6, pady=6)
            tk.Label(f, text="...or walk Yoda into a glowing crystal", bg=PANEL, fg=DIM, font=FONTS["ui"]).pack(side="left", padx=8)
        title = "WORLD 1 - Crystal Valley: Data Collection"
        if self.phase == 0:
            g.set_lesson(title, [
                ("p", "Kuro's first shield is powered by Kyber crystals. To break it, we must learn how a crystal's charge time relates to the lightsaber force it produces."),
                ("h", "Two kinds of variables"),
                ("p", "\u2022 Independent variable X = the INPUT we choose or control.\n\u2022 Dependent variable Y = the OUTPUT that responds to X."),
                ("tip", "Question 1: which quantity is the input X?")])
        elif self.phase == 1:
            g.set_lesson(title, [
                ("p", f"Correct! X = {self.X_NAME} (seconds)."),
                ("h", "Input versus output"),
                ("p", "The output Y is the thing we measure after changing X. It depends on X - that is why it is called the DEPENDENT variable."),
                ("tip", "Question 2: which quantity is the output Y?")])
        elif self.phase == 2:
            g.set_lesson(title, [
                ("p", f"X = {self.X_NAME}, Y = {self.Y_NAME}."),
                ("h", "Collect six samples"),
                ("p", "Each sample is one data point (X, Y): charge a crystal for X seconds, measure the force Y. Collect X = 1, 2, 3, 4, 5, 6. Every sample adds a point to the live graph."),
                ("tip", "Walk Yoda into the glowing crystals (they are labelled X=1 ... X=6) or press C.")])
        elif self.phase == 3:
            g.set_lesson(title, [
                ("h", "Experiment: predict before you measure"),
                ("p", f"Look at the table: how does Y change each time X goes up by 1? Use that pattern to PREDICT the force for a crystal charged X = {self.X_NEXT} seconds - a point you have not measured yet."),
                ("p", "If your prediction is close, you have discovered the rule hidden in the data. If not, the droid tells you which way you missed."),
                ("tip", f"Set the slider to your prediction, then charge crystal X = {self.X_NEXT}.")])
        else:
            g.set_lesson(title, [
                ("h", "Discover the trend"),
                ("p", "All six samples are on the graph. Compare neighbouring samples in the table below the lesson (telemetry)."),
                ("p", "When the points rise along a straight line, we call it a POSITIVE LINEAR relationship."),
                ("tip", "Final question: what happens to Y as X increases?")])

    def hints_for(self, phase):
        return {0: ["X is the thing WE control: we decide how long to charge the crystal.",
                    "Pick the quantity measured in seconds that we set ourselves."],
                1: ["Y is measured AFTER we change X - it depends on X.",
                    "It is the lightsaber force output."],
                2: ["Touch each glowing crystal, or press C, to measure X = 1 ... 6.",
                    "Crystals on high platforms need a jump (Space)."],
                3: ["Check the last column of the table: Y changes by the same amount every step. Add one more step to the last Y.",
                    f"Y went from {self.d['ys'][-2]:g} to {self.d['ys'][-1]:g} between X={N_CLEAN - 1} and X={N_CLEAN}. Do the same jump once more."],
                4: ["Compare neighbouring samples: does Y grow or shrink when X grows by 1?",
                    "Each step to the right makes Y larger."]}[phase]

    def answer(self, ok, fb):
        g = self.game
        if not ok:
            g.wrong(fb)
            return
        g.add_score(100)
        g.droid.mood("happy", 70)
        if self.phase == 4:
            g.good("Correct! X and Y rise together - a positive linear relationship.")
            self.phase = 5
            g.complete_stage()
            return
        g.good("Correct!")
        self.phase += 1
        self.refresh()

    def crystal_touched(self, s):
        if self.phase == 2:
            self.collect(s["xv"])

    def collect_next(self):
        for xv in range(1, N_CLEAN + 1):
            if xv not in self.collected:
                self.collect(xv)
                return

    def primary_action(self):
        if self.phase == 2:
            self.collect_next()
        elif self.phase == 3:
            self.check_prediction()

    def check_prediction(self):
        """Discovery step: the player predicts an unseen sample; the crystal then reveals the computed truth."""
        g = self.game
        if self.phase != 3:
            return
        true_y = self.d["m_true"] * self.X_NEXT + self.d["c_true"]
        step = self.d["ys"][1] - self.d["ys"][0]
        guess = self.pred_var.get()
        self.pred_tries += 1
        if abs(guess - true_y) <= 0.5 * abs(step) + 1e-9:
            self.collected[self.X_NEXT] = true_y
            self.pop[self.X_NEXT] = g.frame
            self.pred_ok, self.phase = True, 4
            g.add_score(150)
            g.droid.mood("happy", 80)
            g.good(f"Prediction confirmed! Crystal X = {self.X_NEXT} gave Y = {true_y:g}. The rule you found: every +1 in X adds {step:g} to Y.")
            self.refresh()
        else:
            word = "too HIGH" if guess > true_y else "too LOW"
            g.wrong(f"Your prediction {guess:g} is {word}. Look at how much Y grows from one sample to the next and extend the pattern one more step.", 4)

    def collect(self, xv):
        g = self.game
        if self.phase != 2 or xv in self.collected:
            return
        y = self.d["ys"][xv - 1]
        self.collected[xv] = y
        self.pop[xv] = g.frame
        for s in g.arena.samples:
            if s["xv"] == xv and not s["got"]:
                s["got"] = True
                g.arena.particles.burst(s["x"], s["y"], CYAN, 16, 3.5, 26, 3, 0.05)
                g.arena.popups.add(s["x"], s["y"] - 20, f"Y={y:g}", CYAN, 50)
        g.add_score(25)
        g.droid.speak(f"Sample {len(self.collected)}/6: charge X={xv} s gave force Y={y:g}.", 160)
        if len(self.collected) == N_CLEAN:
            self.phase = 3
            g.good("All six samples collected!")
            self.refresh()

    def hover_points(self):
        return sorted(self.collected.items())

    def draw_graph(self, gv):
        d = self.d
        gv.setup(0, self.X_NEXT + 1, 0, (max(d["ys"]) + abs(d["ys"][1] - d["ys"][0])) * 1.2)
        gv.axes("X = ??? (input)" if self.phase < 1 else f"X (input): {self.X_NAME} (s)",
                "Y = ??? (output)" if self.phase < 2 else "Y (output): force (units)",
                "Live data graph")
        pts = sorted(self.collected.items())
        for (xa, ya), (xb, yb) in zip(pts, pts[1:]):
            gv.seg(xa, ya, xb, yb, "#6a73c0", 2, (4, 3))
        for xv, y in pts:
            age = self.game.frame - self.pop.get(xv, -99)
            if age < 24:
                gv.ring(xv, y, 6 + age, GOLD, 2)
            gv.dot(xv, y, GOLD, 6)
        if self.phase >= 3 and len(pts) >= 2:
            (xa, ya), (xb, yb) = pts[0], pts[1]
            gv.seg(xa, ya, xb, ya, GREEN, 3)
            gv.seg(xb, ya, xb, yb, ORANGE, 3)
            gv.txt(xa + 0.5, ya, "+1 X", GREEN, "n", dy=-4)
            gv.txt(xb, (ya + yb) / 2, f" +{yb - ya:g} Y", ORANGE, "w")
        if self.phase == 3:
            gx, gy = self.X_NEXT, self.pred_var.get()
            gv.seg(gx, 0, gx, gv.ymax, PINK, 2, (4, 4))
            gv.dot(gx, gy, PINK, 7)
            gv.txt(gx, gy, f"your prediction: {gy:g}", PINK, "e", dx=-12, dy=-12)
        if not pts:
            gv.cv.create_text(gv.w / 2, gv.h / 2, text="No samples yet", fill=DIM, font=FONTS["ui"])

    def telemetry(self):
        lines = ["SAMPLE TABLE", "  #   X (s)   Y (force)   change in Y"]
        pts = sorted(self.collected.items())
        prev = None
        for i, (xv, y) in enumerate(pts, 1):
            lines.append(f"  {i}   {xv:5g}   {y:9.2f}   {'' if prev is None else f'{y - prev:+.2f}'}")
            prev = y
        lines.append("")
        lines.append(f"Samples collected: {min(len(pts), N_CLEAN)} / {N_CLEAN}"
                     + (f"   + predicted X = {self.X_NEXT} (tries: {self.pred_tries})" if self.pred_ok else ""))
        if len(pts) >= N_CLEAN:
            diffs = [pts[i + 1][1] - pts[i][1] for i in range(len(pts) - 1)]
            lines.append(f"Every +1 in X changes Y by {RM.mean(diffs):+.2f}  ->  upward trend")
        return "\n".join(lines)


class Stage2(Stage):
    """WORLD 2 - slope and intercept, y_hat = m*x + c."""
    index = 1

    def enter(self):
        g = self.game
        self.d = g.clean
        self.xs, self.ys = self.d["xs"], self.d["ys"]
        self.fit = RM.ols(self.xs, self.ys)  # exact for clean data
        self.phase, self.hint_n, self.locked_c = 0, {}, None
        g.clear_controls()
        f = g.stage_ctrl
        self.c_var, self.m_var = tk.DoubleVar(value=0.0), tk.DoubleVar(value=0.0)
        r1 = tk.Frame(f, bg=PANEL)
        r1.pack(side="left", padx=6)
        self.c_scale = g.mk_scale(r1, "Intercept c  (Y when X = 0)", 0, 20, 0.5, self.c_var, None, 250)
        self.c_scale.pack(side="left")
        self.lock_btn = g.mk_button(r1, "Lock intercept", self.lock_c, GOLD_BTN)
        self.lock_btn.pack(side="left", padx=6)
        r2 = tk.Frame(f, bg=PANEL)
        r2.pack(side="left", padx=14)
        self.m_scale = g.mk_scale(r2, "Slope m  (rise per +1 X)", 0, 10, 0.5, self.m_var, None, 250)
        self.m_scale.config(state="disabled")
        self.m_scale.pack(side="left")
        self.fit_btn = g.mk_button(r2, "Fit the line!", self.check_fit, GREEN, state="disabled")
        self.fit_btn.pack(side="left", padx=6)
        self.refresh()

    def progress(self):
        return 0.0 if self.phase == 0 else 0.5 if self.phase == 1 else 1.0

    def refresh(self):
        g = self.game
        t = "WORLD 2 - Equation Temple: Slope & Intercept"
        if self.phase == 0:
            g.set_lesson(t, [
                ("eq", "\u0177 = m\u00b7x + c"),
                ("p", "A straight line needs two numbers. \u0177 (y-hat) is the PREDICTED Y for any X."),
                ("h", "Step 1 - the intercept c"),
                ("p", "c is the starting Y value: where the line crosses the Y axis, at X = 0. Slide c until the line's starting point sits where the data's trend begins."),
                ("tip", "The slope slider stays locked until you lock the correct intercept.")])
        else:
            g.set_lesson(t, [
                ("p", f"Intercept locked at c = {self.locked_c:g}."),
                ("h", "Step 2 - the slope m"),
                ("p", "m is how much Y changes for every +1 increase in X: rise \u00f7 run. The green side of the triangle on the graph is the run (+1 X); the orange side is the rise (+m Y)."),
                ("tip", "Tilt the line until it passes through every data point, then press 'Fit the line!'")])

    def hints_for(self, phase):
        y1, y2 = self.ys[0], self.ys[1]
        if phase == 0:
            return ["Look at the table: each +1 in X adds the same amount to Y. Walk backwards one step from X = 1 to reach X = 0.",
                    f"Y at X=1 is {y1:g} and Y at X=2 is {y2:g}. The step is {y2 - y1:g}, so at X = 0 the value is {y1:g} - {y2 - y1:g}."]
        return ["Slope = how much Y grows when X grows by 1. Compare two neighbouring points.",
                f"From X=1 to X=2, Y goes from {y1:g} to {y2:g}: that is the slope."]

    def lock_c(self):
        g, c = self.game, self.c_var.get()
        if abs(c - self.fit["c"]) <= 0.26:
            self.locked_c = c
            self.phase = 1
            self.c_scale.config(state="disabled")
            self.lock_btn.config(state="disabled")
            self.m_scale.config(state="normal")
            self.fit_btn.config(state="normal")
            g.add_score(100)
            g.droid.mood("happy", 70)
            g.good("Intercept locked! Now the slope slider is unlocked.")
            self.refresh()
        else:
            side = "ABOVE" if c > self.fit["c"] else "BELOW"
            g.wrong(f"Your line starts {side} where the trend meets X = 0. Slide c the other way and try again.")

    def check_fit(self):
        g, m = self.game, self.m_var.get()
        if abs(m - self.fit["m"]) <= 0.26:
            self.phase = 2
            g.add_score(100)
            g.good("The line fits every point - Kuro's second shield cracks!")
            self.fit_btn.config(state="disabled")
            g.complete_stage()
        else:
            word = "too STEEP" if m > self.fit["m"] else "too FLAT"
            g.wrong(f"Your line is {word}. Compare its rise over one +1 step with the gap between neighbouring points.")

    def hover_points(self):
        return list(zip(self.xs, self.ys))

    def draw_graph(self, gv):
        c, m = self.c_var.get(), self.m_var.get()
        if self.locked_c is not None:
            c = self.locked_c
        gv.setup(0, 7.5, 0, max(max(self.ys) * 1.25, c + 5, 22))
        gv.axes("X (charge time, s)", "Y (force output)", "Fit \u0177 = m\u00b7x + c")
        gv.line(m, c, BLUE, 3)
        for x, y in zip(self.xs, self.ys):
            gv.dot(x, y, GOLD, 6)
        pulse = 7 + 2 * math.sin(self.game.frame * 0.2)
        gv.seg(0, 0, 0, c, GREEN, 3)
        gv.dot(0, c, GREEN if self.locked_c is not None else CYAN, pulse)
        gv.txt(0, c, f"  c = {c:g}  (start at X=0)", GREEN, "w", dy=-12)
        if self.phase == 1:
            xa = 3.0
            ya = m * xa + c
            gv.seg(xa, ya, xa + 1, ya, GREEN, 4)
            gv.seg(xa + 1, ya, xa + 1, ya + m, ORANGE, 4)
            gv.seg(xa, ya, xa + 1, ya + m, "#ffffff", 1, (3, 3))
            gv.txt(xa + 0.5, ya, "run = +1", GREEN, "n", dy=4)
            gv.txt(xa + 1, ya + m / 2, f" rise = +{m:g}", ORANGE, "w")
        gv.legend([(BLUE, "your line", None), (GOLD, "measured samples", None)])

    def telemetry(self):
        c = self.locked_c if self.locked_c is not None else self.c_var.get()
        m = self.m_var.get()
        on = sum(1 for x, y in zip(self.xs, self.ys) if abs(m * x + c - y) < 0.01)
        lines = ["LINE EQUATION", f"  \u0177 = {m:g}\u00b7x + {c:g}", "",
                 f"  intercept c = {c:g}   -> \u0177 at X=0 is {c:g}",
                 f"  slope     m = {m:g}   -> every +1 in X adds {m:g} to \u0177",
                 f"  rise / run  = {m:g} / 1 = {m:g}", "", "PREDICTIONS vs DATA", "  X     \u0177       actual Y"]
        for x, y in zip(self.xs, self.ys):
            lines.append(f"  {x:g}   {m * x + c:6.2f}   {y:6.2f}")
        lines += ["", f"Points exactly on your line: {on} / {len(self.xs)}"]
        return "\n".join(lines)


class Stage3(Stage):
    """WORLD 3 - noise, residuals, MSE, OLS and the Learning Droid (gradient descent)."""
    index = 2

    def enter(self):
        g = self.game
        prof = g.profile
        self.sigma = clamp(random.uniform(2.0, 3.4) * prof["sigma_factor"], 1.2, 5.0)
        self.data = DataFactory.noisy_linear(g.clean["m_true"], g.clean["c_true"], self.sigma)
        g.noisy = self.data
        self.xs, self.ys = self.data["xs"], self.data["ys"]
        self.n = len(self.xs)
        self.ols = RM.ols(self.xs, self.ys)
        self.target = self.ols["mse"] * 1.25 + 0.25
        self.L = RM.lipschitz(self.xs)
        self.lr_safe = RM.safe_lr(self.xs)
        self.iters_default = max(500, int(round(1500 * prof["iter_factor"], -2)))
        self.attempt = g.history.new_attempt(DataFactory.dataset_id(self.ys), self.sigma, self.n, self.ols)
        g.attempt = self.attempt
        g.history.save()
        self.manual_ok = self.ols_shown = self.trained_ok = self.assisted = False
        self.checks = 0
        self.training = self.droid_active = False
        self.dm = self.dc = 0.0
        self.epoch = self.total = 0
        self.lr = self.lr_safe
        self.hist, self.last = [], None
        self.start_mse = self.start_params = None
        self.phase, self.hint_n = 0, {}
        self.build_ui()
        self.refresh()
        self.sync()

    # ----- UI -----
    def build_ui(self):
        g = self.game
        g.clear_controls()
        f = g.stage_ctrl
        top, bot = tk.Frame(f, bg=PANEL), tk.Frame(f, bg=PANEL)
        top.pack(fill="x")
        bot.pack(fill="x", pady=(2, 0))
        mmax = max(12.0, math.ceil(2 * abs(self.ols["m"])))
        cmax = max(30.0, math.ceil(2 * abs(self.ols["c"])))
        self.m_var, self.c_var = tk.DoubleVar(value=1.0), tk.DoubleVar(value=5.0)
        self.m_scale = g.mk_scale(top, "Slope m", 0, mmax, 0.05, self.m_var, self.on_slider, 250)
        self.c_scale = g.mk_scale(top, "Intercept c", -10, cmax, 0.1, self.c_var, self.on_slider, 250)
        self.m_scale.pack(side="left", padx=(4, 2))
        self.c_scale.pack(side="left", padx=2)
        self.check_btn = g.mk_button(top, "Check my fit", self.check_fit, GOLD_BTN)
        self.ols_btn = g.mk_button(top, "Reveal OLS", self.reveal_ols, "#8a6d1a")
        self.strike_btn = g.mk_button(top, "Lock model & strike!", self.strike, GREEN)
        for b in (self.check_btn, self.ols_btn, self.strike_btn):
            b.pack(side="left", padx=4, pady=6)
        tk.Label(bot, text="Droid: learning rate", bg=PANEL, fg=CYAN, font=FONTS["small"]).pack(side="left", padx=(4, 2))
        self.lr_var, self.it_var = tk.StringVar(value=f"{self.lr_safe:.5f}"), tk.StringVar(value=str(self.iters_default))
        e1 = tk.Entry(bot, textvariable=self.lr_var, width=9, font=FONTS["mono"], bg="#0d0f1c", fg=FG, insertbackground=FG)
        tk.Label(bot, text="iterations", bg=PANEL, fg=CYAN, font=FONTS["small"]).pack(side="left", padx=(8, 2))
        e2 = tk.Entry(bot, textvariable=self.it_var, width=7, font=FONTS["mono"], bg="#0d0f1c", fg=FG, insertbackground=FG)
        e1.pack(side="left")
        e2.pack(side="left")
        for e in (e1, e2):
            e.bind("<Return>", lambda ev: g.root.focus_set())
        self.train_btn = g.mk_button(bot, "Train Droid (from my line)", self.start_training, "#1e8fb8")
        self.cont_btn = g.mk_button(bot, "Continue", self.continue_training, "#1e8fb8")
        self.step_btn = g.mk_button(bot, "One step", self.one_step, "#1e8fb8")
        self.reset_btn = g.mk_button(bot, "Reset droid", self.reset_droid, "#555a80")
        for b in (self.train_btn, self.cont_btn, self.step_btn, self.reset_btn):
            b.config(padx=6, pady=1)
            b.pack(side="left", padx=3)

    def sync(self):
        tr = self.training

        def st(b, on):
            b.config(state="normal" if on and not tr else "disabled")

        st(self.check_btn, not self.manual_ok)
        st(self.ols_btn, self.manual_ok and not self.ols_shown)
        st(self.train_btn, self.ols_shown)
        st(self.cont_btn, self.ols_shown and self.droid_active)
        st(self.step_btn, self.ols_shown)
        st(self.reset_btn, self.droid_active)
        st(self.strike_btn, self.manual_ok and self.ols_shown and self.trained_ok)
        for s in (self.m_scale, self.c_scale):
            s.config(state="disabled" if tr else "normal")
        self.phase = int(self.manual_ok) + int(self.ols_shown) + int(self.trained_ok)

    def progress(self):
        base = int(self.manual_ok) + int(self.ols_shown) + int(self.trained_ok)
        extra = 0.0
        if self.training and self.total:
            extra = 0.5 * self.epoch / self.total
        return clamp((base + extra) / 4.0, 0, 1)

    def refresh(self):
        g = self.game
        t = "WORLD 3 - Noise Factory: Residuals, MSE & OLS"
        if not self.manual_ok:
            g.set_lesson(t, [
                ("p", "Real-world measurements are NOISY: sensors wobble, so points scatter around the true line instead of sitting on it."),
                ("h", "Residuals"),
                ("eq", "residual = actual y  -  predicted \u0177"),
                ("p", "The red dashed lines are residuals: how far each observation is from your line."),
                ("h", "Mean Squared Error"),
                ("eq", "MSE = (1/n) \u00b7 \u03a3 (y\u1d62 - \u0177\u1d62)\u00b2"),
                ("p", "Squaring makes every error positive and punishes big misses. A smaller MSE means a better line."),
                ("tip", f"Mission: tune m and c until MSE \u2264 {self.target:.2f}, then press 'Check my fit'.")])
        elif not self.ols_shown:
            g.set_lesson(t, [
                ("p", "Nice fit! Can we find the BEST possible line without guessing?"),
                ("h", "Ordinary Least Squares (OLS)"),
                ("p", "OLS uses calculus to find the line with the smallest possible MSE, straight from the data:"),
                ("eq", "m = \u03a3(x-x\u0304)(y-y\u0304) / \u03a3(x-x\u0304)\u00b2\nc = y\u0304 - m\u00b7x\u0304      (x\u0304, y\u0304 = averages)"),
                ("tip", "Press 'Reveal OLS' to draw the gold reference line.")])
        elif not self.trained_ok:
            g.set_lesson(t, [
                ("p", "OLS had a formula. The Learning Droid has no formula - it LEARNS by rolling downhill on the MSE surface (gradient descent)."),
                ("eq", "dMSE/dm = (2/n)\u00b7\u03a3((m\u00b7x+c - y)\u00b7x)\ndMSE/dc = (2/n)\u00b7\u03a3(m\u00b7x+c - y)\nm \u2190 m - lr\u00b7dMSE/dm\nc \u2190 c - lr\u00b7dMSE/dc"),
                ("p", "Each epoch: predict, measure error, find which way is downhill, take one small step. The learning rate (lr) is the step size: too small is slow, above 2/L = %.4f it overshoots and DIVERGES." % (2.0 / self.L)),
                ("tip", "The droid starts from YOUR current slider line. Press 'Train Droid', or 'One step' to watch a single update.")])
        else:
            g.set_lesson(t, [
                ("p", "The droid's line landed on the gold OLS line: two different methods, one answer."),
                ("p", "OLS = exact formula. Gradient descent = iterative learning that scales to huge models."),
                ("tip", "Press 'Lock model & strike!' - World 4 uses this fitted model to predict the unseen.")])

    def hints_for(self, phase):
        xs, ys = self.xs, self.ys
        if phase == 0:
            return ["Shorter red lines = smaller MSE. Tilt the line with m first, then slide it up or down with c.",
                    f"Rough start: the data climbs from about {ys[0]:.0f} at X={xs[0]:g} to {ys[-1]:.0f} at X={xs[-1]:g}, so m is about "
                    f"{(ys[-1] - ys[0]) / (xs[-1] - xs[0]):.1f}."]
        if phase == 1:
            return ["Press 'Reveal OLS' to see the mathematically best line."]
        if phase == 2:
            return [f"Keep lr below the safe limit 2/L = {2.0 / self.L:.4f}. If MSE explodes, lower it.",
                    f"A default of {self.lr_safe:.5f} with {self.iters_default} iterations works well on this data."]
        return ["Press 'Lock model & strike!'"]

    # ----- state helpers -----
    def params(self):
        if self.droid_active:
            return self.dm, self.dc
        return self.m_var.get(), self.c_var.get()

    def on_slider(self):
        if self.training:
            return
        self.droid_active = False
        self.sync()

    def hover_points(self):
        return list(zip(self.xs, self.ys))

    # ----- manual fitting -----
    def check_fit(self):
        g = self.game
        if self.manual_ok or self.training:
            return
        m, c = self.m_var.get(), self.c_var.get()
        mse = RM.mse(self.xs, self.ys, m, c)
        self.checks += 1
        if mse <= self.target:
            self._accept_manual(m, c, mse, False)
            g.add_score(150)
            g.droid.mood("happy", 80)
            g.good(f"Great fit! Your MSE {mse:.3f} is within the target {self.target:.3f}.")
        elif self.checks >= 4:
            self._accept_manual(m, c, mse, True)
            self.ols_shown = True
            g.droid.mood("happy", 80)
            g.info(f"Droid assist: after {self.checks} checks the gold OLS line is revealed to guide you (your MSE {mse:.3f}).")
        else:
            g.wrong(f"MSE {mse:.3f} is above the target {self.target:.3f}. Shrink the red dashed lines "
                    f"({4 - self.checks} more tries before the droid helps).", 4)

    def _accept_manual(self, m, c, mse, assisted):
        self.manual_ok, self.assisted = True, assisted
        self.attempt["manual"] = dict(m=m, c=c, mse=mse, gap=max(0.0, mse - self.ols["mse"]),
                                      assisted=assisted, checks=self.checks)
        g = self.game
        g.history.note_mse(mse, self.ols["mse"])
        g.history.save()
        self.sync()
        self.refresh()

    def reveal_ols(self):
        g = self.game
        if not self.manual_ok or self.ols_shown:
            return
        self.ols_shown = True
        g.add_score(100)
        g.droid.speak("The gold line is the OLS solution. Your MSE can never beat it!", 240)
        g.good(f"OLS computed from the data: m = {self.ols['m']:.3f}, c = {self.ols['c']:.3f}, minimum MSE = {self.ols['mse']:.3f}.")
        self.sync()
        self.refresh()

    # ----- Learning Droid: batch gradient descent -----
    def _read_params(self):
        g = self.game
        try:
            lr, iters = float(self.lr_var.get()), int(float(self.it_var.get()))
        except ValueError:
            g.bad("Learning rate and iterations must be numbers.")
            return None
        if not (math.isfinite(lr) and lr > 0):
            g.bad("The learning rate must be a positive number (try %.5f)." % self.lr_safe)
            return None
        if not 1 <= iters <= 50000:
            g.bad("Iterations must be between 1 and 50000.")
            return None
        return lr, iters

    def start_training(self):
        if self.training or not self.ols_shown:
            return
        p = self._read_params()
        if p:
            self._begin(p[0], p[1], fresh=True)

    def continue_training(self):
        if self.training or not self.droid_active:
            return
        p = self._read_params()
        if p:
            self._begin(p[0], p[1], fresh=False)

    def _begin(self, lr, iters, fresh):
        g = self.game
        if fresh:
            m, c = self.m_var.get(), self.c_var.get()
            self.dm, self.dc, self.epoch = m, c, 0
            self.start_params = (m, c)
            self.start_mse = RM.mse(self.xs, self.ys, m, c)
            self.hist = [self.start_mse]
            self.trained_ok = False
        self.droid_active, self.training = True, True
        self.lr = lr
        self.total = self.epoch + iters
        self.batch = max(1, math.ceil(iters / 160))
        g.droid.mode = "training"
        g.droid.speak("Training... I measure the error, find downhill, and step!", 200)
        g.info(f"Droid training: lr = {lr:g}, {iters} iterations, starting at m = {self.dm:.3f}, c = {self.dc:.3f}.")
        self.sync()

    def tick(self):
        if not self.training:
            return
        diverged = False
        for _ in range(self.batch):
            if self.epoch >= self.total:
                break
            nm, nc, gm, gc = RM.gd_step(self.xs, self.ys, self.dm, self.dc, self.lr)
            self.last = (self.dm, self.dc, gm, gc, nm, nc)
            self.dm, self.dc = nm, nc
            self.epoch += 1
            if not (math.isfinite(nm) and math.isfinite(nc)) or abs(nm) > 1e9 or abs(nc) > 1e9:
                diverged = True
                break
        mse = RM.mse(self.xs, self.ys, self.dm, self.dc)
        if diverged or not math.isfinite(mse) or mse > 1e12:
            self._finish(diverged=True)
            return
        self.hist.append(mse)
        del self.hist[:-400]
        if self.epoch >= self.total:
            self._finish(diverged=False)

    def one_step(self):
        g = self.game
        if self.training or not self.ols_shown:
            return
        p = self._read_params()
        if not p:
            return
        if not self.droid_active:
            m, c = self.m_var.get(), self.c_var.get()
            self.dm, self.dc, self.epoch = m, c, 0
            self.start_params = (m, c)
            self.start_mse = RM.mse(self.xs, self.ys, m, c)
            self.hist = [self.start_mse]
            self.trained_ok = False
            self.droid_active = True
        self.lr = p[0]
        nm, nc, gm, gc = RM.gd_step(self.xs, self.ys, self.dm, self.dc, self.lr)
        self.last = (self.dm, self.dc, gm, gc, nm, nc)
        self.dm, self.dc, self.epoch = nm, nc, self.epoch + 1
        self.total = max(self.total, self.epoch)
        mse = RM.mse(self.xs, self.ys, nm, nc)
        if not math.isfinite(mse) or mse > 1e12:
            self.total = self.epoch
            self._finish(diverged=True)
            return
        self.hist.append(mse)
        g.droid.mood("happy", 20)
        if mse <= self.ols["mse"] * 1.02 + 1e-9:
            self.total = self.epoch
            self._finish(diverged=False)
        else:
            self.sync()

    def reset_droid(self):
        if self.training:
            return
        self.droid_active = False
        self.game.info("Droid reset. The graph shows your slider line again.")
        self.sync()

    def _finish(self, diverged):
        g = self.game
        self.training = False
        g.droid.mode = "idle"
        end_mse = RM.mse(self.xs, self.ys, self.dm, self.dc)
        converged = (not diverged) and math.isfinite(end_mse) and end_mse <= self.ols["mse"] * 1.02 + 1e-9
        sm, sc = self.start_params
        run = dict(lr=self.lr, iters=self.epoch, start=dict(m=sm, c=sc, mse=self.start_mse),
                   end=dict(m=self.dm if not diverged else None, c=self.dc if not diverged else None,
                            mse=end_mse if not diverged and math.isfinite(end_mse) else None),
                   gap_to_ols=(end_mse - self.ols["mse"]) if not diverged and math.isfinite(end_mse) else None,
                   converged=converged, diverged=diverged)
        self.attempt["droid_runs"].append(run)
        if not diverged and math.isfinite(end_mse):
            g.history.note_mse(end_mse, self.ols["mse"])
        g.history.save()
        if diverged:
            self.droid_active = False
            g.droid.mood("sad", 120)
            g.droid.speak("Whoa - I overshot the valley! Lower the learning rate.", 240)
            g.wrong(f"Diverged: lr {self.lr:g} is above the stability limit 2/L = {2.0 / self.L:.4f}. "
                    f"Try about {self.lr_safe:.5f}.", 5)
        elif converged:
            self.trained_ok = True
            g.droid_model = dict(m=self.dm, c=self.dc, mse=end_mse)
            g.add_score(200)
            g.droid.mood("happy", 120)
            g.droid.speak("Converged! My line matches OLS.", 240)
            g.good(f"Droid converged after {self.epoch} epochs: MSE {self.start_mse:.3f} -> {end_mse:.3f} "
                   f"(OLS minimum {self.ols['mse']:.3f}).")
            self.refresh()
        else:
            g.droid.mood("idle")
            g.info(f"Not converged yet (MSE {end_mse:.3f}, OLS minimum {self.ols['mse']:.3f}). "
                   f"Press 'Continue' for more iterations, or raise the learning rate a little.")
        self.sync()

    def strike(self):
        g = self.game
        if not (self.manual_ok and self.ols_shown and self.trained_ok) or self.training:
            return
        g.model = dict(m=self.ols["m"], c=self.ols["c"], xs=list(self.xs), ys=list(self.ys),
                       mse=self.ols["mse"], sigma=self.sigma)
        self.attempt["stage3_cleared"] = True
        g.history.save()
        g.good("Model locked: the fitted OLS line goes forward to World 4.")
        g.complete_stage()

    # ----- graph and telemetry -----
    def draw_graph(self, gv):
        xs, ys = self.xs, self.ys
        gv.setup(0, max(xs) + 1, min(0, min(ys) - 2), max(ys) * 1.15 + 2)
        gv.axes("X (input)", "Y (output)", "Noise, residuals and fitted lines")
        m, c = self.params()
        col = CYAN if self.droid_active else BLUE
        if self.ols_shown:
            gv.line(self.ols["m"], self.ols["c"], GOLD, 3)
        gv.line(m, c, col, 3)
        for x, y in zip(xs, ys):
            gv.seg(x, y, x, m * x + c, RED, 2, (3, 3))
        for x, y in zip(xs, ys):
            gv.dot(x, y, "#ffe9a8", 5, "#ffffff")
            gv.txt(x, (y + m * x + c) / 2, f"{y - (m * x + c):+.1f}", "#ff9aa5", "w", FONTS["tiny"], dx=5)
        items = [(col, "droid line" if self.droid_active else "your line", None),
                 (RED, "residuals (y - \u0177)", (4, 3)), ("#ffe9a8", "observations", None)]
        if self.ols_shown:
            items.append((GOLD, "OLS solution", None))
        gv.legend(items)
        if len(self.hist) >= 2:
            self._inset(gv)

    def _inset(self, gv):
        cv = gv.cv
        w, h = 150, 66
        x1, y1 = gv.w - gv.PR - 8, gv.h - gv.PB - 8
        x0, y0 = x1 - w, y1 - h
        cv.create_rectangle(x0, y0, x1, y1, fill="#0c0e1d", outline="#3a4080")
        vals = [math.log(max(v, 1e-9)) for v in self.hist]
        floor = math.log(max(self.ols["mse"], 1e-9))
        lo, hi = min(min(vals), floor), max(vals)
        span = max(hi - lo, 1e-9)
        pts = []
        for i, v in enumerate(vals):
            pts += [x0 + 4 + (w - 8) * i / (len(vals) - 1), y1 - 4 - (h - 16) * (v - lo) / span]
        cv.create_line(*pts, fill=CYAN, width=2)
        fy = y1 - 4 - (h - 16) * (floor - lo) / span
        cv.create_line(x0 + 2, fy, x1 - 2, fy, fill=GOLD, dash=(3, 2))
        cv.create_text(x0 + 4, y0 + 7, text="MSE per epoch (log)", anchor="w", fill=DIM, font=FONTS["tiny"])

    def telemetry(self):
        m, c = self.params()
        res = RM.residuals(self.xs, self.ys, m, c)
        sse = sum(r * r for r in res)
        mse = sse / self.n
        who = "Droid's line" if self.droid_active else "Your line"
        L = [f"{who}:  \u0177 = {m:.4f}\u00b7x + {c:.4f}",
             f"SSE = \u03a3 residual\u00b2 = {sse:.3f}     n = {self.n}",
             f"MSE = SSE / n = {mse:.4f}   (never negative)"]
        if not self.manual_ok:
            L.append(f"Goal: MSE \u2264 {self.target:.3f}      checks used: {self.checks}")
        L.append("")
        if self.ols_shown:
            o = self.ols
            L += ["OLS (computed from this dataset)",
                  f"  x\u0304 = {o['xbar']:.3f}   \u0233 = {o['ybar']:.3f}   \u03a3(x-x\u0304)(y-\u0233) = {o['sxy']:.3f}   \u03a3(x-x\u0304)\u00b2 = {o['sxx']:.3f}",
                  f"  m = {o['sxy']:.3f} / {o['sxx']:.3f} = {o['m']:.4f}",
                  f"  c = {o['ybar']:.3f} - {o['m']:.4f}\u00b7{o['xbar']:.3f} = {o['c']:.4f}",
                  f"  minimum possible MSE = {o['mse']:.4f}   (yours: {mse:.4f})", ""]
        if self.droid_active or self.hist:
            L.append("LEARNING DROID - batch gradient descent")
            L.append(f"  epoch {self.epoch} / {max(self.total, self.epoch)}    lr = {self.lr:g}   safe limit 2/L = {2.0 / self.L:.4f}")
            if self.start_mse is not None:
                L.append(f"  MSE before training: {self.start_mse:.4f}   now: {mse:.4f}")
            if self.droid_active:
                L.append(f"  droid  m = {self.dm:.4f}   c = {self.dc:.4f}")
                L.append(f"  OLS    m = {self.ols['m']:.4f}   c = {self.ols['c']:.4f}")
                L.append(f"  difference: dm = {self.dm - self.ols['m']:+.5f}   dc = {self.dc - self.ols['c']:+.5f}   "
                         f"MSE gap = {mse - self.ols['mse']:+.5f}")
            if self.last:
                m0, c0, gm, gc, m1, c1 = self.last
                L += ["", f"What the droid just did (epoch {self.epoch}), in plain words:",
                      f"  1. Predict with m = {m0:.4f}, c = {c0:.4f} and measure every error.",
                      f"  2. Which way is downhill?  dMSE/dm = {gm:+.4f} -> {'m is too big, lower it' if gm > 0 else 'm is too small, raise it'}",
                      f"                             dMSE/dc = {gc:+.4f} -> {'c is too big, lower it' if gc > 0 else 'c is too small, raise it'}",
                      f"  3. Small step (lr = {self.lr:g}):  m = {m0:.4f} - {self.lr:g}\u00d7({gm:+.4f}) = {m1:.4f}",
                      f"                                  c = {c0:.4f} - {self.lr:g}\u00d7({gc:+.4f}) = {c1:.4f}"]
            L.append("")
        L.append(f"CHECKLIST  [{'x' if self.manual_ok else ' '}] manual fit   [{'x' if self.ols_shown else ' '}] OLS revealed   "
                 f"[{'x' if self.trained_ok else ' '}] droid trained")
        L += ["", "RESIDUAL TABLE   residual = actual - predicted",
              "  i     x    actual y   predicted \u0177   residual   residual\u00b2"]
        for i, (x, y, r) in enumerate(zip(self.xs, self.ys, res), 1):
            L.append(f"  {i:<2d} {x:5g}  {y:9.2f}  {m * x + c:11.2f}  {r:+9.2f}  {r * r:9.2f}")
        return "\n".join(L)


class Stage4(Stage):
    """WORLD 4 - extrapolation with the fitted OLS model."""
    index = 3

    def enter(self):
        g = self.game
        mdl = g.model
        if mdl is None:  # defensive: rebuild from the noisy dataset
            d = g.noisy or DataFactory.noisy_linear(g.clean["m_true"], g.clean["c_true"], 2.5)
            o = RM.ols(d["xs"], d["ys"])
            mdl = dict(m=o["m"], c=o["c"], xs=d["xs"], ys=d["ys"], mse=o["mse"], sigma=d.get("sigma", 2.5))
            g.model = mdl
        self.mdl = mdl
        self.m, self.c = mdl["m"], mdl["c"]
        self.xs, self.ys = mdl["xs"], mdl["ys"]
        self.xmax = max(self.xs)
        self.xf = self.xmax + random.randint(2, 5)
        self.yhat = RM.predict(self.m, self.c, self.xf)
        self.answered, self.phase, self.hint_n = False, 0, {}
        self.locked = False
        yl = self.ys[-1]
        cands = [(yl, "That just repeats the last observation. A regression model extends the TREND, so Y keeps rising with X."),
                 (self.m * self.xf, "That forgets the intercept c. The model is \u0177 = m\u00b7x + c - both parts count."),
                 (RM.mean(self.ys), "That is the average of Y, a flat line that ignores X. The fitted line keeps climbing.")]
        opts = [(self.yhat, True, "")]
        for val, fb in cands:
            if abs(val - self.yhat) < 1.0:
                val = self.yhat + (3.0 if val >= self.yhat else -3.0)
            opts.append((val, False, fb))
        random.shuffle(opts)
        self.opts = opts
        self.build_ui()
        self.refresh()

    def build_ui(self):
        g = self.game
        g.clear_controls()
        f = g.stage_ctrl
        self.aim_var = tk.DoubleVar(value=self.xmax)
        self.aim = g.mk_scale(f, "Aim: X coordinate", 1, self.xf + 3, 0.5, self.aim_var, self.on_aim, 300)
        self.aim.pack(side="left", padx=6)
        box = tk.Frame(f, bg=PANEL)
        box.pack(side="left", padx=6)
        tk.Label(box, text="Where will the unseen point land?  (aim at the target X first)", bg=PANEL, fg=CYAN,
                 font=FONTS["small"]).pack(anchor="w")
        row = tk.Frame(box, bg=PANEL)
        row.pack()
        self.ans = []
        for i, (val, ok, fb) in enumerate(self.opts):
            b = g.mk_button(row, f"({self.xf:g}, {val:.1f})", lambda i=i: self.choose(i), "#7a3cc4", state="disabled")
            b.pack(side="left", padx=4, pady=2)
            self.ans.append(b)

    def on_aim(self):
        locked = abs(self.aim_var.get() - self.xf) < 1e-9
        if locked != self.locked:
            self.locked = locked
            for b in self.ans:
                b.config(state="normal" if locked and not self.answered else "disabled")
            self.phase = 1 if locked else 0
            self.refresh()
            if locked:
                self.game.good(f"Target locked at X = {self.xf:g}. Now choose the predicted coordinate.")
                self.game.droid.mood("happy", 50)

    def progress(self):
        return 0.0 if not self.locked else 0.5

    def refresh(self):
        g = self.game
        t = "WORLD 4 - Future Zone: Extrapolation"
        base = [("p", "Kuro hides his weak point in the FUTURE: an X value larger than any we ever measured. The fitted OLS line from World 3 is our crystal ball."),
                ("eq", f"\u0177 = {self.m:.3f}\u00b7x + {self.c:.3f}"),
                ("h", "Interpolation vs extrapolation"),
                ("p", f"Training data covers X = {self.xs[0]:g} ... {self.xmax:g}. Predicting beyond that is EXTRAPOLATION - useful, but the further we go, the riskier it gets (noise is amplified and the trend may change). Slide the aim and watch the purple band: it widens as you leave the data behind.")]
        if not self.locked:
            base.append(("tip", f"Step 1: slide the aim to the target X = {self.xf:g} (pink dashed line)."))
        else:
            base.append(("tip", f"Step 2: compute \u0177 = m\u00b7x + c at X = {self.xf:g} and pick the matching coordinate."))
        g.set_lesson(t, base)

    def hints_for(self, phase):
        if phase == 0:
            return [f"Drag the Aim slider until it reads X = {self.xf:g}. The crosshair rides along the fitted line."]
        return ["Multiply the slope by x, then add the intercept: \u0177 = m\u00b7x + c.",
                f"{self.m:.3f} \u00d7 {self.xf:g} + {self.c:.3f} = ?"]

    def choose(self, i):
        g = self.game
        if self.answered or not self.locked:
            return
        val, ok, fb = self.opts[i]
        if not ok:
            g.wrong(fb)
            return
        self.answered = True
        for b in self.ans:
            b.config(state="disabled")
        self.aim.config(state="disabled")
        m_true, c_true, sigma = g.clean["m_true"], g.clean["c_true"], self.mdl.get("sigma", 2.5)
        actual = m_true * self.xf + c_true + random.gauss(0.0, sigma)
        g.reality_text = (f"Reality check: the real unseen outcome at X = {self.xf:g} was {actual:.1f}; the model predicted "
                          f"{self.yhat:.1f} (error {abs(actual - self.yhat):.1f}). Noise limits perfection, but the trend held.")
        g.add_score(300)
        g.good(f"Correct! \u0177({self.xf:g}) = {self.m:.3f}\u00d7{self.xf:g} + {self.c:.3f} = {self.yhat:.2f}. Fire the final strike!")
        g.complete_stage()

    def hover_points(self):
        return list(zip(self.xs, self.ys))

    def _pm(self, x):
        """Approximate 95% prediction half-width at x: 1.96*s*sqrt(1 + 1/n + (x-xbar)^2/Sxx), computed from this dataset."""
        n = len(self.xs)
        if n < 3:
            return 0.0
        xbar = RM.mean(self.xs)
        sxx = sum((v - xbar) ** 2 for v in self.xs)
        s = math.sqrt(RM.sse(self.xs, self.ys, self.m, self.c) / (n - 2))
        return 1.96 * s * math.sqrt(1 + 1.0 / n + ((x - xbar) ** 2 / sxx if sxx > 1e-12 else 0.0))

    def draw_graph(self, gv):
        xr = self.xf + 4
        ytop = max(max(self.ys), self.m * xr + self.c) * 1.1
        gv.setup(0, xr, 0, ytop)
        gv.axes("X (input)", "Y (output)", "Extrapolating the fitted model")
        cv = gv.cv
        cv.create_rectangle(gv.px(self.xmax), gv.py(ytop), gv.px(xr), gv.py(0), fill="#3a2f7a", outline="", stipple="gray25")
        cv.create_text(gv.px((self.xmax + xr) / 2), gv.PT + 18, text="UNSEEN TERRITORY (future)", fill="#c9b8ff", font=FONTS["small"])
        up, lo = [], []
        for i in range(41):
            bx = self.xs[0] + (xr - self.xs[0]) * i / 40
            by, pm = self.m * bx + self.c, self._pm(bx)
            up += [gv.px(bx), clamp(gv.py(by + pm), gv.PT, gv.h - gv.PB)]
            lo = [gv.px(bx), clamp(gv.py(by - pm), gv.PT, gv.h - gv.PB)] + lo
        cv.create_polygon(*(up + lo), fill="#6b5cff", outline="#9a8cff", stipple="gray50")
        gv.line(self.m, self.c, GOLD, 3, x0=0, x1=self.xmax)
        gv.line(self.m, self.c, GOLD, 2, (5, 4), x0=self.xmax, x1=xr)
        for x, y in zip(self.xs, self.ys):
            gv.dot(x, y, "#ffe9a8", 5)
        gv.seg(self.xf, 0, self.xf, ytop, PINK, 2, (4, 4))
        gv.txt(self.xf, ytop, f"target X = {self.xf:g}", PINK, "n", dy=14)
        ax = self.aim_var.get()
        ay = self.m * ax + self.c
        r = 9 + 2 * math.sin(self.game.frame * 0.25)
        col = GREEN if self.locked else CYAN
        gv.seg(ax, 0, ax, ay, col, 1, (3, 3))
        gv.seg(0, ay, ax, ay, col, 1, (3, 3))
        gv.ring(ax, ay, r, col, 2)
        gv.dot(ax, ay, col, 3, col)
        gv.txt(ax, ay, f"\u0177({ax:g}) = {ay:.2f}", col, "e" if ax > xr * 0.6 else "w", dx=-12 if ax > xr * 0.6 else 12, dy=-14)
        if self.answered:
            gv.ring(self.xf, self.yhat, 14, "#ffffff", 3)
            gv.dot(self.xf, self.yhat, RED, 6)
        gv.legend([(GOLD, "fitted model (solid = trained, dashed = extrapolated)", None), ("#ffe9a8", "training data", None),
                   ("#9a8cff", "approx. 95% prediction band", None), (col, "your crosshair", None)])

    def telemetry(self):
        ax = self.aim_var.get()
        ay = self.m * ax + self.c
        L = ["FITTED MODEL (OLS from World 3)", f"  \u0177 = {self.m:.4f}\u00b7x + {self.c:.4f}",
             f"  training X range: {self.xs[0]:g} ... {self.xmax:g}   (n = {len(self.xs)})", "",
             "CROSSHAIR", f"  x = {ax:g}", f"  \u0177 = m\u00b7x + c = {self.m:.4f}\u00d7{ax:g} + {self.c:.4f} = {ay:.3f}",
             f"  {'EXTRAPOLATION: x is beyond all training data' if ax > self.xmax else 'interpolation: x lies inside the training range'}",
             f"  approx. 95% range for a new Y here: {ay - self._pm(ax):.2f} ... {ay + self._pm(ax):.2f}   (+/-{self._pm(ax):.2f})",
             f"  uncertainty +/-{self._pm(self.xmax):.2f} at the last training X={self.xmax:g}  vs  +/-{self._pm(self.xf):.2f} at the target X={self.xf:g}", "",
             f"TARGET  X = {self.xf:g}   (greater than every training X: {self.xf > self.xmax})"]
        dm = self.game.droid_model
        if dm:
            dy = dm["m"] * self.xf + dm["c"]
            L += ["", "LEARNING DROID'S GRADIENT-DESCENT MODEL",
                  f"  \u0177 = {dm['m']:.4f}\u00b7x + {dm['c']:.4f}   predicts {dy:.3f} at X = {self.xf:g}",
                  f"  difference from OLS prediction: {dy - self.yhat:+.4f}"]
        L += ["", f"Training MSE of the model: {self.mdl['mse']:.4f}",
              "Remember: the farther beyond the data we predict, the less we should trust it."]
        return "\n".join(L)


# --------------------------------------------------------------------------
# Pre/post check-up dialog (evidence of learning + playtest feedback)
# --------------------------------------------------------------------------
class CheckupDialog:
    """5-question concept check-up (pre or post) plus optional feedback; saved to the history JSON."""

    def __init__(self, game, kind):
        self.game, self.kind = game, kind
        win = self.win = tk.Toplevel(game.root)
        win.title("Warm-up check" if kind == "pre" else "Check-up and playtest feedback")
        win.configure(bg=BG)
        tk.Label(win, text="Warm-up (before you play)" if kind == "pre" else "Check-up (after you played)",
                 bg=BG, fg=GOLD, font=FONTS["h"]).pack(anchor="w", padx=14, pady=(10, 0))
        tk.Label(win, text="Answer what you can - guessing is fine. Results are saved locally to measure what the game taught.",
                 bg=BG, fg=DIM, font=FONTS["small"], wraplength=620, justify="left").pack(anchor="w", padx=14)
        row = tk.Frame(win, bg=BG)
        row.pack(fill="x", padx=14, pady=4)
        tk.Label(row, text="Name / nickname:", bg=BG, fg=FG, font=FONTS["ui"]).pack(side="left")
        self.name_var = tk.StringVar(value=game.player_name)
        tk.Entry(row, textvariable=self.name_var, width=22, font=FONTS["ui"]).pack(side="left", padx=6)
        self.vars = []
        for qi, (prompt, opts, _ok) in enumerate(CHECK_QUESTIONS):
            tk.Label(win, text=f"{qi + 1}. {prompt}", bg=BG, fg=FG, font=FONTS["ui"], wraplength=640,
                     justify="left").pack(anchor="w", padx=14, pady=(6, 0))
            v = tk.IntVar(value=-1)
            self.vars.append(v)
            order = list(range(len(opts)))
            random.shuffle(order)
            for oi in order:
                tk.Radiobutton(win, text=opts[oi], variable=v, value=oi, bg=BG, fg=FG, selectcolor="#232857",
                               activebackground=BG, activeforeground=GOLD, anchor="w", justify="left",
                               font=FONTS["small"], takefocus=0).pack(anchor="w", padx=30)
        self.rating_var, self.comment_var = tk.DoubleVar(value=4), tk.StringVar()
        if kind == "post":
            game.mk_scale(win, "How much did the game help you understand regression? (1 = not at all, 5 = a lot)",
                          1, 5, 1, self.rating_var, None, 440).pack(anchor="w", padx=14, pady=(6, 0))
            tk.Label(win, text="What did you learn, or what was confusing?", bg=BG, fg=FG,
                     font=FONTS["small"]).pack(anchor="w", padx=14)
            tk.Entry(win, textvariable=self.comment_var, width=80, font=FONTS["ui"]).pack(anchor="w", padx=14, pady=2)
        btns = tk.Frame(win, bg=BG)
        btns.pack(pady=8)
        game.mk_button(btns, "Submit", self.submit, GREEN).pack(side="left", padx=6)
        game.mk_button(btns, "Skip", self.close, "#555a80").pack(side="left", padx=6)
        win.protocol("WM_DELETE_WINDOW", self.close)

    def submit(self):
        g = self.game
        correct = [v.get() == CHECK_QUESTIONS[i][2] for i, v in enumerate(self.vars)]
        name = self.name_var.get().strip()[:40]
        entry = dict(time=datetime.now().isoformat(timespec="seconds"), kind=self.kind, session=g.session_id,
                     player=name, score=sum(correct), total=len(correct), correct=correct)
        if self.kind == "post":
            entry.update(rating=int(self.rating_var.get()), comment=self.comment_var.get().strip()[:500],
                         stages_cleared=g.stages_done, victory=g.mode == "victory")
        g.player_name = name
        g.history.add_evidence(entry)
        self.close()
        g.on_checkup_done(entry)

    def close(self):
        self.game.close_checkup()


# --------------------------------------------------------------------------
# Tutorial text
# --------------------------------------------------------------------------
TUTORIAL = """HOW TO PLAY
Master Yoda must defeat Dark Lord Kuro (100 HP). Each of four worlds teaches one idea of Linear Regression; finishing a world's lesson makes Yoda strike Kuro for exactly 25 HP.

CONTROLS
  Left/Right or A/D .... walk          Space / Up / W ... jump
  F or X ............... lightsaber swing (deflects Kuro's ground waves)
  C .................... collect next sample (World 1)
  H .................... ask the Learning Droid for a hint
  Enter ................ confirm / start / retry
  P pause    T tutorial    K check-up    R restart    Esc close this window

PLATFORM FUN
  Coins +10, gems +25, question blocks +50 (+5 HP and a droid hint). Jump over hazards (-8 HP).
  Kuro sends red ground waves: jump them or swing your saber (+15). Wrong answers cost 8 HP.

THE FOUR WORLDS
  1 Crystal Valley   X vs Y, input vs output, collect six samples, see a positive linear trend.
  2 Equation Temple  y_hat = m*x + c. Lock the intercept c, then fit the slope m (rise over run).
  3 Noise Factory    Noisy data, residuals, MSE, Ordinary Least Squares (gold line) and the
                     Learning Droid, which runs real batch gradient descent from YOUR line.
  4 Future Zone      Extrapolate the fitted model to an unseen X and name the predicted point.

THE LEARNING DROID
  dMSE/dm = (2/n)*sum((m*x+c-y)*x)      dMSE/dc = (2/n)*sum(m*x+c-y)
  m = m - lr*dMSE/dm                    c = c - lr*dMSE/dc
  Keep lr below the safe limit shown in the telemetry or the droid overshoots.

HISTORY
  Your attempts, MSE values, trained parameters, stages cleared, victories and best MSE are saved in
  a local JSON file next to the game. Each new game uses fresh random data; old parameters are never
  reused - history is only used to compare performance and tune difficulty.
"""
TUTORIAL += "\nLEARNING OBJECTIVES\n" + "".join(
    f"  World {i + 1} ({WORLDS[i]['name']}):\n" + "".join(f"    - {o}\n" for o in objs)
    for i, objs in enumerate(LEARNING_OBJECTIVES)) + (
    "\nLEARN BY EXPERIMENTING\n"
    "  You do not just read the ideas: you predict an unseen sample (World 1), search for c and m (World 2),\n"
    "  watch MSE react to your sliders and try learning rates that converge or diverge (World 3), and watch\n"
    "  the uncertainty band widen as you extrapolate (World 4).\n"
    "\nCHECK-UP (EVIDENCE OF LEARNING)\n"
    "  Press K for a 5-question concept check before and after playing, plus optional feedback.\n"
    "  Results are saved in the history file; run  python master_yoda_vs_kuro.py --report  to summarise them.\n")


# --------------------------------------------------------------------------
# Game controller
# --------------------------------------------------------------------------
class GameApp:
    JUMP_KEYS = ("up", "w", "space")

    def __init__(self, root):
        self.root = root
        self.history = HistoryStore()
        self.mode, self.frame = "title", 0
        self.score, self.yoda_hp, self.kuro_hp, self.kuro_hp_disp = 0, YODA_MAX_HP, KURO_MAX_HP, float(KURO_MAX_HP)
        self.clean = DataFactory.clean_linear()
        self.noisy = self.model = self.droid_model = self.attempt = None
        self.profile = self.history.adapt_profile()
        self.stage_index = self.stages_done = 0
        self.stage = None
        self.stage_started = self.stage_locked = False
        self.victory_lines, self.reality_text = [], ""
        self.down, self._rel = set(), {}
        self.jump_req = self.attack_req = False
        self.err_count = 0
        self.tut = None
        self._tut_prev = None
        self.chk = self._chk_prev = None
        self.player_name, self.session_id = "", ""
        self.pre_done = self.post_done = self.skip_pre_prompt = False
        self._lesson_key = self._tel_last = None
        self._build_ui()
        self.arena = Arena(self, self.arena_cv)
        self.graph = GraphView(self, self.graph_cv)
        self.droid = self.arena.droid
        self.stages = [Stage1(self), Stage2(self), Stage3(self), Stage4(self)]
        root.report_callback_exception = self._callback_error
        root.protocol("WM_DELETE_WINDOW", self.on_close)
        root.bind_all("<KeyPress>", self.on_key_press)
        root.bind_all("<KeyRelease>", self.on_key_release)
        self.set_lesson("Welcome, young Padawan", [
            ("p", "Press START (or Enter). You will learn Linear Regression by fighting Kuro, one world at a time."),
            ("tip", "Press T for the tutorial and controls.")])
        if self.history.error:
            self.info(self.history.error)
        self._sync_main_button()
        self.tick()

    # ----- UI construction -----
    def _build_ui(self):
        r = self.root
        r.configure(bg=BG)
        self.arena_cv = tk.Canvas(r, width=ARENA_W, height=ARENA_H, bg="#05060f", highlightthickness=0)
        self.arena_cv.pack(fill="x")
        self.arena_cv.bind("<Button-1>", lambda e: r.focus_set())
        mid = tk.Frame(r, bg=BG)
        mid.pack(fill="both", expand=True)
        self.graph_cv = tk.Canvas(mid, width=540, height=330, bg="#0c0e1d", highlightthickness=1,
                                  highlightbackground="#2d3364")
        self.graph_cv.pack(side="left", fill="both", expand=True, padx=(8, 4), pady=6)
        panel = tk.Frame(mid, bg=BG, width=530)
        panel.pack(side="right", fill="both", padx=(4, 8), pady=6)
        panel.pack_propagate(False)
        self.lesson = self._text(panel, 9)
        self.lesson.pack(fill="both", expand=True)
        self.fb = tk.Label(panel, text="", bg=PANEL2, fg=FG, font=FONTS["ui"], wraplength=510, justify="left",
                           anchor="w", height=3, padx=8)
        self.fb.pack(fill="x", pady=4)
        self.tel = self._text(panel, 11, mono=True)
        self.tel.pack(fill="both", expand=True)
        for name, kw in (("title", dict(font=FONTS["h"], foreground=GOLD, spacing3=4)),
                         ("h", dict(font=FONTS["ui_b"], foreground=CYAN, spacing1=6)),
                         ("p", dict(font=FONTS["ui"], foreground=FG, spacing3=3)),
                         ("eq", dict(font=FONTS["mono_b"], foreground=GOLD, background="#232857", lmargin1=10, lmargin2=10,
                                     spacing1=3, spacing3=3)),
                         ("tip", dict(font=FONTS["ui_b"], foreground=GREEN, spacing1=4)),
                         ("obj", dict(font=FONTS["small"], foreground="#b8c0ee", spacing3=4)),
                         ("warn", dict(font=FONTS["ui_b"], foreground=ORANGE))):
            self.lesson.tag_configure(name, **kw)
        bottom = tk.Frame(r, bg=PANEL)
        bottom.pack(fill="x", padx=8, pady=(0, 8))
        self.stage_ctrl = tk.Frame(bottom, bg=PANEL, height=96)
        self.stage_ctrl.pack(side="left", fill="both", expand=True, padx=4, pady=4)
        glob = tk.Frame(bottom, bg=PANEL)
        glob.pack(side="right", padx=6, pady=4)
        self.btn_main = self.mk_button(glob, "START", self.on_enter, GREEN)
        self.btn_main.grid(row=0, column=0, padx=3, pady=2, sticky="ew")
        self.mk_button(glob, "Restart (R)", lambda: self.restart(True), "#a8323e").grid(row=0, column=1, padx=3, pady=2, sticky="ew")
        self.mk_button(glob, "Tutorial (T)", self.show_tutorial, "#555a80").grid(row=1, column=0, padx=3, pady=2, sticky="ew")
        self.mk_button(glob, "Hint (H)", self.hint, "#1e8fb8").grid(row=1, column=1, padx=3, pady=2, sticky="ew")
        self.mk_button(glob, "Pause (P)", self.toggle_pause, "#555a80").grid(row=2, column=0, columnspan=2, padx=3, pady=2, sticky="ew")
        self.mk_button(glob, "Check-up (K)", self.open_checkup, "#7a3cc4").grid(row=3, column=0, columnspan=2, padx=3, pady=2, sticky="ew")

    def _text(self, parent, height, mono=False):
        t = tk.Text(parent, wrap="word" if not mono else "none", height=height, bg="#12142a", fg=FG, bd=0, padx=8, pady=6,
                    font=FONTS["mono"] if mono else FONTS["ui"], state="disabled", cursor="arrow", takefocus=0,
                    highlightthickness=1, highlightbackground="#2d3364")
        t.bind("<FocusIn>", lambda e: self.root.focus_set())
        return t

    def mk_button(self, parent, text, cmd, color=BLUE, state="normal"):
        return tk.Button(parent, text=text, command=cmd, bg=color, fg="white", activebackground=mix(color, "#ffffff", 0.25),
                         activeforeground="white", disabledforeground="#a0a6c4", relief="raised", bd=2, padx=10, pady=3,
                         font=FONTS["btn"], takefocus=0, state=state, cursor="hand2")

    def mk_scale(self, parent, label, frm, to, res, var, cmd, length=240):
        kw = dict(from_=frm, to=to, resolution=res, orient="horizontal", length=length, label=label, variable=var,
                  bg=PANEL, fg=FG, troughcolor="#0d0f1c", highlightthickness=0, bd=0, takefocus=0,
                  font=FONTS["small"], activebackground=BLUE)
        if cmd:
            kw["command"] = lambda v: cmd()
        s = tk.Scale(parent, **kw)
        s.bind("<ButtonRelease-1>", lambda e: self.root.focus_set(), add="+")
        return s

    def clear_controls(self):
        for w in self.stage_ctrl.winfo_children():
            w.destroy()

    def _sync_main_button(self):
        txt = {"title": "START (Enter)", "victory": "Play again (Enter)", "defeat": "Retry world (Enter)"}.get(
            self.mode, "Action (Enter)")
        self.btn_main.config(text=txt)

    # ----- lesson / feedback / telemetry -----
    def set_lesson(self, title, blocks):
        blocks = list(blocks)
        if self.stage is not None and self.mode in ("play", "paused", "cutscene"):
            objs = LEARNING_OBJECTIVES[self.stage.index]
            blocks.insert(0, ("obj", "Learning objectives: " + "   ".join(f"({i + 1}) {o}" for i, o in enumerate(objs))))
        key = (title, tuple(blocks))
        if key == self._lesson_key:
            return
        self._lesson_key = key
        t = self.lesson
        t.config(state="normal")
        t.delete("1.0", "end")
        t.insert("end", title + "\n", "title")
        for style, text in blocks:
            t.insert("end", text + "\n", style)
        t.config(state="disabled")
        t.yview_moveto(0)

    def _feedback(self, msg, color):
        self.fb.config(text=msg, fg=color)

    def good(self, msg):
        self._feedback("\u2714 " + msg, GREEN)

    def bad(self, msg):
        self._feedback("\u2718 " + msg, RED)

    def info(self, msg):
        self._feedback("\u2139 " + msg, CYAN)

    def _refresh_telemetry(self):
        if self.stage and self.mode != "title":
            s = self.stage.telemetry()
        else:
            s = "\n".join(["LEARNING HISTORY (saved locally)"] + self.history.summary_lines() +
                          ["", f"History file: {self.history.path}"])
        if s == self._tel_last:
            return
        self._tel_last = s
        first = self.tel.yview()[0]
        self.tel.config(state="normal")
        self.tel.delete("1.0", "end")
        self.tel.insert("end", s)
        self.tel.config(state="disabled")
        self.tel.yview_moveto(first)

    # ----- score / health -----
    def add_score(self, n):
        self.score += int(n)

    def heal(self, n):
        before = self.yoda_hp
        self.yoda_hp = min(YODA_MAX_HP, self.yoda_hp + n)
        if self.yoda_hp > before:
            self.arena.popups.add(self.arena.yoda.x, self.arena.yoda.y - 80, f"+{self.yoda_hp - before} HP", GREEN)

    def damage_yoda(self, amount, why=""):
        if self.mode != "play":
            return
        self.yoda_hp = max(0, self.yoda_hp - amount)
        self.arena.popups.add(self.arena.yoda.x, self.arena.yoda.y - 80, f"-{amount} HP", RED, 55)
        if self.yoda_hp <= 0:
            self.defeat()

    def wrong(self, msg, dmg=WRONG_PENALTY):
        self.bad(f"{msg}  (-{dmg} HP)")
        self.droid.mood("sad", 60)
        self.damage_yoda(dmg)

    def droid_hint(self):
        if self.stage and self.mode == "play":
            txt = self.stage.hint()
            self.droid.speak(txt, 360)
            self.info("Droid hint: " + txt)

    def hint(self):
        self.droid_hint()

    def overall_progress(self):
        cur = 0.0
        if self.stage and self.mode == "play" and not self.stage_locked:
            cur = self.stage.progress()
        return clamp((self.stages_done + cur) / N_STAGES, 0, 1)

    # ----- game flow -----
    def new_game(self):
        self.finish_attempt("abandoned")
        if self.stage:
            self.stage.leave()
        self.score, self.yoda_hp = 0, YODA_MAX_HP
        self.kuro_hp, self.kuro_hp_disp = KURO_MAX_HP, float(KURO_MAX_HP)
        self.clean = DataFactory.clean_linear()
        self.noisy = self.model = self.droid_model = self.attempt = None
        self.reality_text, self.stages_done = "", 0
        self.profile = self.history.adapt_profile()
        self.history.data["games_started"] += 1
        self.history.save()
        self.arena.yoda.victory = False
        self.arena.yoda.auto = False
        self.arena.curtain = None
        self.session_id = datetime.now().strftime("%Y%m%d-%H%M%S-") + "%04d" % random.randint(0, 9999)
        self.pre_done = self.post_done = False
        self.start_stage(0)
        self.info(self.profile["note"])
        if not self.skip_pre_prompt:
            self.root.after(1500, self._offer_precheck)

    def start_stage(self, idx, retry=False):
        if self.stage:
            self.stage.leave()
        self.stage_index, self.stage = idx, self.stages[idx]
        self.stage_locked = self.stage_started = False
        self.arena.set_world(idx)
        self.arena.yoda.auto = False
        self.clear_controls()
        self.mode = "play"
        self.stage.enter()
        self.stage_started = True
        w = WORLDS[idx]
        self.arena.banner(f"WORLD {idx + 1}: {w['name']}", w["sub"], 100)
        self.droid.speak(f"World {idx + 1}! Press H for hints, hit ? blocks for bonuses.", 220)
        self._sync_main_button()

    def complete_stage(self):
        if self.mode != "play" or self.stage_locked:
            return
        self.stage_locked = True
        self.stages_done += 1
        self.history.data["stages_completed"] += 1
        self.history.save()
        self.add_score(250 + self.yoda_hp * 2)
        self.clear_controls()
        self.mode = "cutscene"
        self.arena.begin_attack(self.stage_index == N_STAGES - 1)

    def on_attack_hit(self, final):
        self.kuro_hp = max(0, self.kuro_hp - STAGE_DAMAGE)
        self.arena.kuro.hit()
        self.arena.popups.add(KURO_X - 20, GROUND_Y - 175, f"-{STAGE_DAMAGE} HP", RED, 70)
        if self.kuro_hp <= 0:
            self.arena.kuro.die()

    def on_attack_done(self, final):
        if final:
            self.victory()
        else:
            self.arena.start_curtain(lambda: self.start_stage(self.stage_index + 1))

    def victory(self):
        self.mode = "victory"
        self.score += 500
        self.history.data["victories"] += 1
        self.finish_attempt("victory")
        lines = [f"Final score {self.score}   |   Yoda HP left {self.yoda_hp}   |   Kuro HP {self.kuro_hp}"]
        if self.reality_text:
            lines.append(self.reality_text)
        if self.model:
            lines.append(f"Fitted model: y_hat = {self.model['m']:.3f}x + {self.model['c']:.3f}   (OLS MSE {self.model['mse']:.3f})")
        if self.droid_model:
            lines.append(f"Learning Droid (gradient descent): y_hat = {self.droid_model['m']:.3f}x + {self.droid_model['c']:.3f}"
                         f"   (MSE {self.droid_model['mse']:.3f})")
        lines += self.history.summary_lines()[1:3]
        lines.append("Press K for the 5-question check-up and playtest feedback.")
        self.victory_lines = lines
        self.history.save()
        self.clear_controls()
        self.good("Victory! Kuro is defeated. Press Enter to play again.")
        self._sync_main_button()
        self.root.after(3000, self._offer_postcheck)

    def defeat(self):
        if self.mode != "play":
            return
        self.mode = "defeat"
        self.history.data["defeats"] += 1
        self.finish_attempt("defeat")
        self.history.save()
        if self.stage:
            self.stage.leave()
        self.clear_controls()
        self.bad("Yoda has fallen! Press Enter to retry this world.")
        self._sync_main_button()

    def retry_stage(self):
        self.yoda_hp = YODA_MAX_HP
        self.start_stage(self.stage_index, retry=True)
        self.info("New attempt - fresh data for this world.")

    def finish_attempt(self, result):
        if self.attempt and self.attempt.get("result") == "in_progress":
            self.attempt["result"] = result
            self.history.save()

    def restart(self, ask=False):
        if ask and self.mode in ("play", "paused", "cutscene"):
            if not messagebox.askyesno("Restart", "Restart the whole game? Current progress will be lost."):
                return
        self.new_game()

    def on_enter(self):
        if self.mode in ("title", "victory"):
            self.new_game()
        elif self.mode == "defeat":
            self.retry_stage()
        elif self.mode == "play" and self.stage:
            self.stage.primary_action()

    def toggle_pause(self):
        if self.mode == "play":
            self.mode = "paused"
        elif self.mode == "paused":
            self.mode = "play"

    def show_tutorial(self):
        if self.tut is not None:
            try:
                self.tut.lift()
                return
            except tk.TclError:
                self.tut = None
        self._tut_prev = self.mode
        if self.mode == "play":
            self.mode = "paused"
        win = tk.Toplevel(self.root)
        win.title("Tutorial - Master Yoda vs. Kuro")
        win.configure(bg=BG)
        t = tk.Text(win, wrap="word", width=92, height=34, bg="#12142a", fg=FG, font=FONTS["mono"], padx=12, pady=10, bd=0)
        t.insert("end", TUTORIAL)
        t.config(state="disabled")
        sb = tk.Scrollbar(win, command=t.yview, takefocus=0)
        t.config(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y", pady=8)
        t.pack(fill="both", expand=True, padx=8, pady=8)
        self.mk_button(win, "Close (Esc)", self.close_tutorial, GREEN).pack(pady=(0, 8))
        win.protocol("WM_DELETE_WINDOW", self.close_tutorial)
        win.bind("<Escape>", lambda e: self.close_tutorial())
        self.tut = win

    def close_tutorial(self):
        if self.tut is not None:
            try:
                self.tut.destroy()
            except tk.TclError:
                pass
            self.tut = None
        if self.mode == "paused" and self._tut_prev == "play":
            self.mode = "play"
        self.root.focus_set()

    def _offer_precheck(self):
        if self.pre_done or self.chk is not None or self.tut is not None or self.mode != "play":
            return
        if messagebox.askyesno("Warm-up check", "Take the optional 5-question warm-up (about 1 minute)?\n"
                               "It lets the game measure what you learn. You can also press K at any time."):
            self.open_checkup("pre")
        else:
            self.skip_pre_prompt = True

    def _offer_postcheck(self):
        if self.mode == "victory" and not self.post_done and self.chk is None and self.tut is None:
            self.open_checkup("post")

    def open_checkup(self, kind=None):
        if self.chk is not None:
            try:
                self.chk.win.lift()
                return
            except tk.TclError:
                self.chk = None
        if self.tut is not None:
            return
        if self.mode == "title":
            self.info("Start a game first - the check-up is tied to your play session.")
            return
        if kind is None:
            kind = "post" if (self.pre_done or self.mode == "victory") else "pre"
        self._chk_prev = self.mode
        if self.mode == "play":
            self.mode = "paused"
        self.chk = CheckupDialog(self, kind)

    def close_checkup(self):
        if self.chk is not None:
            try:
                self.chk.win.destroy()
            except tk.TclError:
                pass
            self.chk = None
        if self.mode == "paused" and self._chk_prev == "play":
            self.mode = "play"
        self.root.focus_set()

    def on_checkup_done(self, entry):
        t = entry["total"]
        if entry["kind"] == "pre":
            self.pre_done = True
            self.good(f"Warm-up saved: {entry['score']}/{t}. Now go and learn something!")
            return
        self.post_done = True
        pre = next((e for e in reversed(self.history.data["evidence"])
                    if e.get("kind") == "pre" and e.get("session") == self.session_id), None)
        if pre:
            self.good(f"Check-up saved: {pre['score']}/{t} before -> {entry['score']}/{t} after ({entry['score'] - pre['score']:+d}). Thank you for the feedback!")
        else:
            self.good(f"Check-up saved: {entry['score']}/{t}. (No warm-up this session, so no before/after comparison.)")

    def on_close(self):
        self.finish_attempt("abandoned")
        self.history.save()
        self.root.destroy()

    # ----- input -----
    def _typing(self):
        try:
            w = self.root.focus_get()
        except (KeyError, tk.TclError):
            return False
        return isinstance(w, tk.Entry)

    def on_key_press(self, e):
        if self._typing():
            return
        k = e.keysym.lower()
        if self.chk is not None or (self.tut is not None and k != "escape"):
            return
        job = self._rel.pop(k, None)
        if job:
            self.root.after_cancel(job)
        first = k not in self.down
        self.down.add(k)
        if not first:
            return
        if k in self.JUMP_KEYS:
            self.jump_req = True
        elif k in ("f", "x"):
            self.attack_req = True
        elif k == "c" and self.mode == "play" and self.stage:
            self.stage.primary_action()
        elif k == "h":
            self.hint()
        elif k == "t":
            self.show_tutorial()
        elif k == "k":
            self.open_checkup()
        elif k == "r":
            self.restart(True)
        elif k == "p":
            self.toggle_pause()
        elif k in ("return", "kp_enter"):
            self.on_enter()
        elif k == "escape":
            if self.tut is not None:
                self.close_tutorial()
            elif self.mode == "paused":
                self.toggle_pause()

    def on_key_release(self, e):
        k = e.keysym.lower()
        if k in self._rel:
            self.root.after_cancel(self._rel[k])
        self._rel[k] = self.root.after(35, lambda k=k: (self.down.discard(k), self._rel.pop(k, None)))

    # ----- main loop -----
    def tick(self):
        try:
            self.frame += 1
            self._update()
            self.arena.draw()
            if self.frame % 2 == 0:
                self.graph.redraw()
            if self.frame % 5 == 0:
                self._refresh_telemetry()
            self.err_count = 0
        except Exception:
            self.err_count += 1
            traceback.print_exc()
            self.bad("Internal error (see console). The game keeps running.")
            if self.err_count == 5 and messagebox:
                try:
                    messagebox.showerror("Game error", "Repeated errors occurred; check the console output.")
                except Exception:
                    pass
        finally:
            self.root.after(FRAME_MS, self.tick)

    def _update(self):
        d = self.kuro_hp - self.kuro_hp_disp
        self.kuro_hp_disp += clamp(d, -0.6, 0.6)
        if abs(self.kuro_hp - self.kuro_hp_disp) < 0.6:
            self.kuro_hp_disp = float(self.kuro_hp)
        if self.mode == "play":
            left = bool(self.down & {"left", "a"})
            right = bool(self.down & {"right", "d"})
            jump, atk = self.jump_req, self.attack_req
            self.jump_req = self.attack_req = False
            self.stage.tick()
            self.arena.update((1 if right else 0) - (1 if left else 0), jump, atk)
        elif self.mode == "cutscene":
            self.jump_req = self.attack_req = False
            self.arena.update_cutscene()
        elif self.mode == "paused":
            pass
        else:
            self.jump_req = self.attack_req = False
            self.arena.update_idle()

    def _callback_error(self, exc, val, tb):
        traceback.print_exception(exc, val, tb)
        try:
            self.bad(f"Internal error: {val}")
        except Exception:
            pass


def main():
    if "--selftest" in sys.argv:
        sys.exit(0 if run_selftest() else 1)
    if "--report" in sys.argv:
        files = [a for a in sys.argv[sys.argv.index("--report") + 1:] if not a.startswith("--")]
        print(build_report(files or [str(HistoryStore().path)]))
        sys.exit(0)
    if tk is None:
        print("Tkinter is not available in this Python installation. Install the 'python3-tk' package "
              "(Linux) or use the python.org installer, then run again.")
        sys.exit(1)
    try:
        root = tk.Tk()
    except tk.TclError as exc:
        print(f"Cannot open a window: {exc}")
        sys.exit(1)
    init_fonts()
    root.title("Master Yoda vs. Kuro - Linear Regression Boss Battle")
    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    w, h = min(1100, sw - 20), min(830, sh - 70)
    root.geometry(f"{w}x{h}+{max(0, (sw - w) // 2)}+{max(0, (sh - h) // 3)}")
    root.minsize(900, 640)
    GameApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
