"""
inputs.py — every number in this DCF that ISN'T a modeling assumption is
sourced from a real, named source, with the source written right next to it.
This is the single most interview-defensible habit in a portfolio DCF: when
asked "where did this number come from," the answer should never be "I made
it up" or "I don't remember."

Company: Chevron Corporation (NYSE: CVX)
Why Chevron: integrated oil & gas major — directly comparable to the
commodity trading exposure (SAP/ETRM reconciliation, physical crude/products)
from the ADNOC Global Trading internship, so the sector knowledge carries
across both this DCF and Project A.
"""

# ---------------------------------------------------------------------------
# HISTORICAL FINANCIALS (USD millions unless noted)
# Source: MacroTrends (macrotrends.net/stocks/charts/CVX/chevron/*),
#         Stock Analysis on Net (10-K based), fetched during model build.
# ---------------------------------------------------------------------------
HISTORICAL = {
    "revenue":    {2021: 162465, 2022: 246252, 2023: 200949, 2024: 202792, 2025: 189031},
    "ebitda":     {2022: 66509, 2023: 47379, 2024: 45382, 2025: 41479},
    "net_income": {2022: 35465, 2024: 17661},  # 2022 peak and 2024 as disclosed
}

# ---------------------------------------------------------------------------
# MARKET DATA (as fetched — see model note for "as of" date)
# Source: stockanalysis.com/stocks/cvx/statistics
# ---------------------------------------------------------------------------
MARKET = {
    "beta": 0.66,                       # 5Y monthly beta vs S&P 500
    "market_cap_usd_m": 375645,         # current market capitalization
    "total_debt_usd_m": 46740,          # total debt (balance sheet)
    "cash_usd_m": 6300,                 # cash & equivalents
    "shares_outstanding_m": 1855,       # derived: LTM net income / LTM diluted EPS = 12300/6.63
    "ev_ebitda_multiple": 11.51,        # current market-implied EV/EBITDA — used as a cross-check, not the primary method
    "current_ratio": 1.15,
    "debt_to_equity": 0.24,
}

# ---------------------------------------------------------------------------
# MACRO INPUTS
# Source: FRED / tradingeconomics.com (10Y US Treasury yield),
#         Damodaran-style long-run US equity risk premium (~5.0%, widely used
#         academic/practitioner default — cite explicitly, don't present as fact)
# ---------------------------------------------------------------------------
MACRO = {
    "risk_free_rate": 0.045,     # 10Y US Treasury yield, ~4.48-4.49% as of early Jul 2026, rounded
    "equity_risk_premium": 0.050,  # long-run US ERP assumption (Damodaran-style default)
    "pre_tax_cost_of_debt": 0.055,  # investment-grade energy major credit spread over risk-free
    "tax_rate": 0.21,             # US federal statutory corporate tax rate
}

# ---------------------------------------------------------------------------
# EIA context (Short-Term Energy Outlook, fetched during research) — used to
# JUSTIFY the shape of the revenue forecast, not hard-coded into it. As of
# mid-2026 the EIA's base case assumed Brent averaging ~$105/bbl in the near
# term due to a Strait of Hormuz disruption, normalizing toward ~$79/bbl by
# 2027 as flows resume. This is exactly the kind of assumption a top-tier GIR
# or IB analyst would call out explicitly rather than silently bake into a
# single-point forecast — which is why this model treats near-term oil price
# risk as a SENSITIVITY, not a base-case assumption baked into one number.
# ---------------------------------------------------------------------------
EIA_CONTEXT_NOTE = (
    "EIA STEO (mid-2026): near-term Brent ~$105/bbl on Strait of Hormuz "
    "disruption, normalizing to ~$79/bbl by 2027 as flows resume."
)
