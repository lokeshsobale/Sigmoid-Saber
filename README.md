# IDSE CS3006 Project — Star Wars: The Regression Force

An interactive 2D educational game built in pure Python using Streamlit, NumPy, Scikit-Learn, and Matplotlib. Players channel the Regression Force as Master Yoda to defeat Sith Lord KUDO across three mathematical stages.

## Learning Objectives

1. **Stage 1 — Ordinary Least Squares (OLS):** Manipulate slope ($m$) and intercept ($c$) in real time to minimize residuals and Mean Squared Error (MSE).
2. **Stage 2 — Robustness & Bias-Variance Tradeoff:** Eliminate extreme Sith outliers and select an optimal polynomial degree that minimizes error on unseen test data without overfitting.
3. **Stage 3 — Probabilistic (Logistic) Regression:** Shape the Sigmoid probability curve $P(y=1|x) = \frac{1}{1 + e^{-(wx+b)}}$ and tune the Decision Threshold Gate to balance costly False Negatives against False Positives.

## Project Structure

- **main.py** — Complete single-file pure-Python Streamlit application and 2D Matplotlib renderer.
- **requirements.txt** — Python package dependencies for local and cloud execution.
- **playtest_results.csv** — Recorded peer testing scores and reflections from the built-in Evidence Logger.
- **README.md** — Project documentation, mathematical breakdown, and setup guide.

## How to Run Locally

1. Clone this repository and navigate into the project directory:

```bash
git clone [https://github.com/YOUR_USERNAME/IDSE_CS3006_Project.git](https://github.com/YOUR_USERNAME/IDSE_CS3006_Project.git)
cd IDSE_CS3006_Project
```
