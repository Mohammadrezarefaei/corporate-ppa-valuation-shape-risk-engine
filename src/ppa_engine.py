"""
Corporate PPA Valuation & Volumetric Shape Risk Engine.
Models solar cannibalization, capture price dynamics, and bankability metrics (VaR / CVaR).
"""

from typing import Dict, Tuple
import numpy as np
import pandas as pd


class CorporatePPAEngine:

  def __init__(
      self,
      ppa_strike_eur: float = 62.0,
      collar_floor_eur: float = 50.0,
      collar_cap_eur: float = 85.0,
      imbalance_penalty_pct: float = 0.25,
  ):
    self.ppa_strike = ppa_strike_eur
    self.collar_floor = collar_floor_eur
    self.collar_cap = collar_cap_eur
    self.imbalance_penalty_pct = imbalance_penalty_pct

  def evaluate_contracts(
      self, df_market: pd.DataFrame
  ) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, float]]:
    """Evaluates Merchant, Pay-as-Produced, Pay-as-Forecasted, and Baseload Collar structures."""
    df = df_market.copy()

    # 1. Merchant Exposure Baseline
    df["rev_merchant"] = df["solar_gen_mwh"] * df["spot_price_eur"]

    # 2. Pay-as-Produced (Offtaker absorbs shape/volume risk)
    df["rev_pay_as_produced"] = df["solar_gen_mwh"] * self.ppa_strike

    # 3. Pay-as-Forecasted (Generator covers day-ahead forecast imbalance penalties)
    imbalance_vol = df["solar_gen_mwh"] - df["solar_forecast_mwh"]
    imbalance_cashflow = np.where(
        imbalance_vol >= 0,
        imbalance_vol * df["spot_price_eur"] * (1.0 - self.imbalance_penalty_pct),
        imbalance_vol * df["spot_price_eur"] * (1.0 + self.imbalance_penalty_pct),
    )
    df["rev_pay_as_forecasted"] = (
        df["solar_forecast_mwh"] * self.ppa_strike
    ) + imbalance_cashflow

    # 4. Baseload Equivalent with Synthetic Collar Option
    mean_hourly_gen = df["solar_gen_mwh"].mean()
    collar_price = np.clip(
        df["spot_price_eur"], self.collar_floor, self.collar_cap
    )
    shape_mismatch_vol = df["solar_gen_mwh"] - mean_hourly_gen
    df["rev_baseload_collar"] = (mean_hourly_gen * collar_price) + (
        shape_mismatch_vol * df["spot_price_eur"]
    )

    # Aggregate Daily for Bankability Metrics (VaR / CVaR 95%)
    df_daily = df.groupby(df["hour"] // 24).agg({
        "rev_merchant": "sum",
        "rev_pay_as_produced": "sum",
        "rev_pay_as_forecasted": "sum",
        "rev_baseload_collar": "sum",
    })

    total_gen_mwh = df["solar_gen_mwh"].sum()
    contracts = [
        "Merchant Baseline",
        "Pay-as-Produced",
        "Pay-as-Forecasted",
        "Baseload Collar",
    ]
    cols = [
        "rev_merchant",
        "rev_pay_as_produced",
        "rev_pay_as_forecasted",
        "rev_baseload_collar",
    ]

    summary_records = []
    for name, col in zip(contracts, cols):
      series = df_daily[col]
      ann_rev = float(series.sum())
      var_95 = float(np.percentile(series, 5))
      cvar_95 = float(series[series <= var_95].mean())
      capture_price = (
          float(ann_rev / total_gen_mwh) if total_gen_mwh > 0 else 0.0
      )

      summary_records.append({
          "contract_structure": name,
          "annual_revenue_k_eur": round(ann_rev / 1000.0, 1),
          "daily_95_var_eur": round(var_95, 0),
          "daily_95_cvar_eur": round(cvar_95, 0),
          "capture_price_eur_mwh": round(capture_price, 2),
      })

    df_summary = pd.DataFrame(summary_records)
    
    kpis = {
        "pap_annual_k_eur": round(df_daily["rev_pay_as_produced"].sum() / 1000.0, 1),
        "merchant_annual_k_eur": round(df_daily["rev_merchant"].sum() / 1000.0, 1),
        "pap_daily_cvar_eur": round(float(df_daily["rev_pay_as_produced"][df_daily["rev_pay_as_produced"] <= np.percentile(df_daily["rev_pay_as_produced"], 5)].mean()), 0),
        "merchant_daily_cvar_eur": round(float(df_daily["rev_merchant"][df_daily["rev_merchant"] <= np.percentile(df_daily["rev_merchant"], 5)].mean()), 0),
    }

    return df, df_summary, kpis
