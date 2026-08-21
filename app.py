"""Streamlit Web App: Renewable Corporate PPA Valuation & Volumetric Shape Risk Engine."""

import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from src.ppa_engine import CorporatePPAEngine

st.set_page_config(
    page_title="Corporate PPA Valuation & Shape Risk",
    page_icon="☀️",
    layout="wide"
)

st.title("☀️ Renewable Corporate PPA Valuation & Volumetric Risk Engine")
st.markdown("Quantifying **Solar Cannibalization (Merit-Order Effect)**, capture price degradation, and **Bankability Downside Tail Risks (95% VaR / CVaR)** across standard PPA contract structures.")

# Sidebar Parameters
st.sidebar.header("⚙️ Solar Asset & PPA Terms")
pv_capacity_mw = st.sidebar.slider("Solar PV Capacity (MWp)", 10.0, 150.0, 50.0, 10.0)
ppa_strike = st.sidebar.slider("PPA Fixed Strike (€/MWh)", 40.0, 90.0, 62.0, 1.0)
cannibalization_intensity = st.sidebar.slider("Cannibalization Drag Factor", 10.0, 70.0, 45.0, 5.0)

st.sidebar.header("🛡️ Baseload Collar Structure")
collar_floor = st.sidebar.slider("Collar Floor Price (€/MWh)", 35.0, 60.0, 50.0, 2.5)
collar_cap = st.sidebar.slider("Collar Cap Price (€/MWh)", 65.0, 110.0, 85.0, 2.5)

@st.cache_data
def generate_market_data(capacity, drag):
    np.random.seed(42)
    hours = 8760
    h_arr = np.arange(hours)
    doy = (h_arr // 24) % 365
    hod = h_arr % 24

    solar_elevation = np.sin(np.pi * (hod - 6) / 12) * np.sin(np.pi * (doy + 10) / 365)
    solar_elevation = np.clip(solar_elevation, 0.0, 1.0)
    weather_noise = np.random.beta(5, 2, hours)
    solar_gen = capacity * solar_elevation * weather_noise

    base_price = 75.0 + 25.0 * np.sin(2 * np.pi * (hod - 8) / 24)
    cannibalization = -drag * (solar_gen / capacity) ** 1.3
    gas_volatility = np.random.normal(0, 20.0, hours)
    spot_price = np.clip(base_price + cannibalization + gas_volatility, -15.0, 240.0)

    forecast_error = np.random.normal(0, 0.12, hours)
    solar_forecast = np.clip(solar_gen * (1.0 + forecast_error), 0.0, capacity)

    return pd.DataFrame({
        "hour": h_arr,
        "hod": hod,
        "solar_gen_mwh": solar_gen,
        "solar_forecast_mwh": solar_forecast,
        "spot_price_eur": spot_price
    })

df_market = generate_market_data(pv_capacity_mw, cannibalization_intensity)
engine = CorporatePPAEngine(
    ppa_strike_eur=ppa_strike,
    collar_floor_eur=collar_floor,
    collar_cap_eur=collar_cap
)

df_eval, df_summary, kpis = engine.evaluate_contracts(df_market)

# KPI Row
k1, k2, k3, k4 = st.columns(4)
k1.metric("Pay-as-Produced Revenue", f"€{kpis['pap_annual_k_eur']:,.1f}k / yr")
k2.metric("Merchant Revenue Baseline", f"€{kpis['merchant_annual_k_eur']:,.1f}k / yr")
k3.metric("Pay-as-Produced 95% CVaR", f"€{kpis['pap_daily_cvar_eur']:,.0f} / day")
k4.metric("Merchant 95% CVaR (Tail Risk)", f"€{kpis['merchant_daily_cvar_eur']:,.0f} / day", delta=f"{kpis['pap_daily_cvar_eur'] - kpis['merchant_daily_cvar_eur']:+,.0f} € protection")

col1, col2 = st.columns([1.5, 1])

with col1:
    st.subheader("📉 Cannibalization Effect & Downside Distribution")
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 7))

    hourly_avg = df_eval.groupby("hod").mean()
    ax1.plot(hourly_avg.index, hourly_avg["spot_price_eur"], color="#DC2626", lw=2.2, label="Capture Spot Price (€/MWh)")
    ax1_twin = ax1.twinx()
    ax1_twin.fill_between(hourly_avg.index, 0, hourly_avg["solar_gen_mwh"], color="#F59E0B", alpha=0.3, label="Solar Profile")
    ax1_twin.set_ylabel("Solar Gen [MW]", color="#D97706", fontweight="bold")
    ax1.set_ylabel("Price [€/MWh]", color="#DC2626", fontweight="bold")
    ax1.set_title("Midday Solar Cannibalization (Merit-Order Depression)", fontsize=10, fontweight="bold")
    ax1.grid(True, linestyle=":", alpha=0.6)

    # Daily distribution
    df_daily = df_eval.groupby(df_eval["hour"] // 24).agg({"rev_merchant": "sum", "rev_pay_as_produced": "sum"})
    ax2.hist(df_daily["rev_merchant"] / 1000.0, bins=25, alpha=0.5, color="#94A3B8", label="Merchant", edgecolor="black")
    ax2.hist(df_daily["rev_pay_as_produced"] / 1000.0, bins=25, alpha=0.5, color="#10B981", label="Pay-as-Produced", edgecolor="black")
    ax2.set_xlabel("Daily Cash Flow [k€]", fontweight="bold")
    ax2.set_ylabel("Days", fontweight="bold")
    ax2.set_title("Daily Downside Cashflow Distribution (Bankability Risk)", fontsize=10, fontweight="bold")
    ax2.grid(True, linestyle=":", alpha=0.6)
    ax2.legend(loc="upper right", frameon=True, fontsize=8)

    plt.tight_layout()
    st.pyplot(fig)

with col2:
    st.subheader("📑 Bankability Comparison Matrix")
    st.dataframe(
        df_summary.rename(columns={
            "contract_structure": "Contract Structure",
            "annual_revenue_k_eur": "Annual Revenue [k€]",
            "daily_95_var_eur": "Daily 95% VaR [€]",
            "daily_95_cvar_eur": "Daily 95% CVaR [€]",
            "capture_price_eur_mwh": "Capture Price [€/MWh]"
        }),
        hide_index=True,
        use_container_width=True
    )
    st.markdown("""
    **Structure Breakdown:**
    * **Pay-as-Produced (PaP):** Offtaker absorbs shape and volume risk; maximum bankability for debt financing.
    * **Pay-as-Forecasted:** Generator incurs day-ahead forecasting imbalance penalties (reBAP).
    * **Baseload Collar:** Synthesizes floor protection with upside cap; requires active shape mismatch rebalancing on the spot market.
    """)

st.markdown("---")
st.caption("European Corporate PPA Structuring & Valuation Engine. Quantifies volumetric shape risk for renewable project finance.")
