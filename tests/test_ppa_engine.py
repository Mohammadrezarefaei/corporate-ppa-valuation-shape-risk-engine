"""Automated Pytest Suite for Corporate PPA Valuation Engine."""

import pytest
import numpy as np
import pandas as pd
from src.ppa_engine import CorporatePPAEngine


@pytest.fixture
def sample_8760_market_data():
  np.random.seed(42)
  hours = 8760
  h_arr = np.arange(hours)
  hod = h_arr % 24

  solar = 30.0 * np.sin(np.pi * np.clip(hod - 6, 0, 12) / 12)
  spot = 70.0 - 20.0 * (solar / 30.0) + np.random.normal(0, 10.0, hours)
  forecast = solar * (1.0 + np.random.normal(0, 0.1, hours))

  return pd.DataFrame({
      "hour": h_arr,
      "hod": hod,
      "solar_gen_mwh": solar,
      "solar_forecast_mwh": np.clip(forecast, 0, 30.0),
      "spot_price_eur": spot,
  })


def test_ppa_valuation_coherence(sample_8760_market_data):
  engine = CorporatePPAEngine(ppa_strike_eur=65.0)
  _, df_summary, kpis = engine.evaluate_contracts(sample_8760_market_data)

  assert len(df_summary) == 4
  assert kpis["pap_annual_k_eur"] > 0.0
  # Pay-as-Produced should significantly de-risk downside vs merchant (higher CVaR)
  assert kpis["pap_daily_cvar_eur"] > kpis["merchant_daily_cvar_eur"]


def test_zero_generation_edge_case():
  engine = CorporatePPAEngine()
  zero_df = pd.DataFrame({
      "hour": np.arange(24),
      "hod": np.arange(24),
      "solar_gen_mwh": np.zeros(24),
      "solar_forecast_mwh": np.zeros(24),
      "spot_price_eur": np.full(24, 50.0),
  })
  _, df_summary, _ = engine.evaluate_contracts(zero_df)

  pap_row = df_summary[df_summary["contract_structure"] == "Pay-as-Produced"].iloc[0]
  assert pap_row["annual_revenue_k_eur"] == 0.0
