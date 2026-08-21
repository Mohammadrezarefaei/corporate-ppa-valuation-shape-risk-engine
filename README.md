# ☀️ Renewable Corporate PPA Valuation & Volumetric Shape Risk Engine

[![CI Pipeline](https://img.shields.io/badge/CI%20Pipeline-passing-brightgreen?logo=github&style=flat-square)](https://github.com/Mohammadrezarefaei/corporate-ppa-valuation-shape-risk-engine/actions)
[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://corporate-ppa-valuation-shape-risk-engine-8yptu5rvdgqklacvyzqc.streamlit.app/)

A quantitative corporate Power Purchase Agreement (PPA) valuation and risk structuring framework. Quantifies **Solar Cannibalization (Merit-Order Effect)**, capture price degradation, and **Bankability Downside Tail Risks (95% VaR / CVaR)** across standard contractual structures.

---

## 🚀 Live Interactive Demo
👉 **[Access the Live Streamlit Web App](https://corporate-ppa-valuation-shape-risk-engine-8yptu5rvdgqklacvyzqc.streamlit.app/)**

---

## 📌 PPA Contract Structures & Risk Allocation

Renewable project finance requires assessing how profile, volume, and balancing risks are allocated between the generator and corporate offtaker:

1. **Pay-as-Produced (PaP):**
   * Generator receives fixed strike (€/MWh) for all realized output. Offtaker absorbs shape and volume risk; maximizes project bankability for debt financing.

2. **Pay-as-Forecasted:**
   * Generator is compensated based on Day-Ahead forecasted generation; generator absorbs real-time balancing and imbalance settlement penalties (reBAP).

3. **Baseload Equivalent with Collar Options:**
   * Synthesizes fixed volume delivery with an asymmetric floor and cap price corridor (Floor <= Price <= Cap), requiring active spot market balancing for volume mismatches.

4. **Cannibalization & Capture Price Modeling:**
   * Simulates the non-linear merit-order depression where peak midday solar feed-in suppresses market clearing prices below baseload averages.

---

## 🔍 Key Performance Insights

* **Downside Tail Protection:** Structuring via Pay-as-Produced secures significantly higher Conditional Value-at-Risk (95% CVaR), insulating equity investors against merchant price collapse.
* **Forecast Error Impact:** Highlights the financial drag of intraday balancing costs when operating under Pay-as-Forecasted structures without co-located BESS flexibility.

---

## 🛠️ Software Architecture & Automated Testing
* **CI/CD Pipeline:** Automated testing via **GitHub Actions** (`pytest` validating contract cashflow bounds, downside distribution metrics, and zero-generation edge cases).
* **Modular Core Engine:** Implemented in `src/ppa_engine.py`.
* **Tech Stack:** Python 3.11, NumPy, Pandas, Matplotlib, Streamlit, Pytest.
