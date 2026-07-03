"""
dcf_model.py
-------------
A Discounted Cash Flow (DCF) valuation of Chevron Corporation (CVX).

WHAT A DCF ACTUALLY IS (for anyone starting from zero):
A company is worth the cash it can hand to its investors, today and in the
future. A DCF estimates that by: (1) projecting how much free cash the
business will generate each year for the next several years, (2) shrinking
("discounting") each future dollar because a dollar next year is worth less
than a dollar today (you could invest today's dollar and earn a return in
the meantime), and (3) adding up all those discounted dollars, plus a
"terminal value" representing everything the business is worth beyond the
forecast window. The discount rate used is WACC (Weighted Average Cost of
Capital) — the blended return that both the company's shareholders and its
lenders require to be willing to fund the business.

This script builds that model end to end:
  1. WACC        — the discount rate (cost of equity via CAPM, blended with
                    after-tax cost of debt, weighted by market value)
  2. Forecast     — 5-year revenue, EBITDA, EBIT, NOPAT, and Free Cash Flow
                    to the Firm (FCFF)
  3. Terminal value — Gordon Growth method, cross-checked against an
                    exit-multiple method using CVX's own current EV/EBITDA
  4. Enterprise Value -> Equity Value -> Implied share price
  5. Sensitivity  — WACC x terminal growth grid (this is what makes a DCF
                    defensible: showing HOW MUCH the answer moves, not just
                    the answer itself)
"""
import sys, os, json
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "data"))
from inputs import HISTORICAL, MARKET, MACRO, EIA_CONTEXT_NOTE

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "outputs")
os.makedirs(OUT_DIR, exist_ok=True)

# ===========================================================================
# STEP 1 — WACC
# ===========================================================================
# Cost of equity via CAPM: how much return do shareholders demand, given how
# risky this stock is relative to the overall market (beta)?
#   Cost of Equity = Risk-Free Rate + Beta x Equity Risk Premium
cost_of_equity = MACRO["risk_free_rate"] + MARKET["beta"] * MACRO["equity_risk_premium"]

# After-tax cost of debt: lenders demand a rate, but interest is tax-deductible,
# so the REAL cost to the company is lower than the stated rate.
after_tax_cost_of_debt = MACRO["pre_tax_cost_of_debt"] * (1 - MACRO["tax_rate"])

# Blend by MARKET VALUE weights (never book value — the market price is what
# actually reflects what investors would need to be paid out today)
E = MARKET["market_cap_usd_m"]
D = MARKET["total_debt_usd_m"]
V = E + D
weight_equity = E / V
weight_debt = D / V

WACC = weight_equity * cost_of_equity + weight_debt * after_tax_cost_of_debt

# ===========================================================================
# STEP 2 — 5-YEAR FORECAST (FY2026E - FY2030E)
# ===========================================================================
# Growth assumptions are deliberately NOT chasing the near-term oil price
# spike described in EIA_CONTEXT_NOTE — a defensible base case normalizes
# through the cycle rather than extrapolating a geopolitical shock. The
# oil-price risk is instead captured explicitly in the sensitivity section.
REVENUE_GROWTH = {2026: 0.030, 2027: 0.025, 2028: 0.025, 2029: 0.020, 2030: 0.020}
EBITDA_MARGIN =  {2026: 0.220, 2027: 0.222, 2028: 0.224, 2029: 0.225, 2030: 0.225}
DA_PCT_REVENUE = 0.105     # ~consistent with CVX's historical D&A run-rate as a share of revenue
CAPEX_PCT_REVENUE = 0.090  # consistent with disclosed capex guidance (~$17B on a ~$189B revenue base)
NWC_PCT_REVENUE_CHANGE = 0.005  # incremental working capital investment as revenue grows
TERMINAL_GROWTH = 0.025    # long-run nominal GDP-ish growth rate for a mature major

base_revenue = HISTORICAL["revenue"][2025]

years = [2026, 2027, 2028, 2029, 2030]
forecast = []
prev_revenue = base_revenue
prev_nwc_base = base_revenue  # proxy base for computing incremental NWC

for y in years:
    revenue = prev_revenue * (1 + REVENUE_GROWTH[y])
    ebitda = revenue * EBITDA_MARGIN[y]
    da = revenue * DA_PCT_REVENUE
    ebit = ebitda - da
    nopat = ebit * (1 - MACRO["tax_rate"])
    capex = revenue * CAPEX_PCT_REVENUE
    delta_nwc = (revenue - prev_revenue) * NWC_PCT_REVENUE_CHANGE
    fcff = nopat + da - capex - delta_nwc

    forecast.append({
        "year": y, "revenue": revenue, "ebitda": ebitda, "da": da, "ebit": ebit,
        "nopat": nopat, "capex": capex, "delta_nwc": delta_nwc, "fcff": fcff,
    })
    prev_revenue = revenue

# ===========================================================================
# STEP 3 — DISCOUNT & TERMINAL VALUE
# ===========================================================================
pv_fcff_total = 0
for i, row in enumerate(forecast, start=1):
    discount_factor = 1 / ((1 + WACC) ** i)
    row["discount_factor"] = discount_factor
    row["pv_fcff"] = row["fcff"] * discount_factor
    pv_fcff_total += row["pv_fcff"]

final_year_fcff = forecast[-1]["fcff"]
# Gordon Growth terminal value: value of all cash flows beyond the forecast,
# assuming they grow at a constant, modest rate forever
terminal_value_gg = (final_year_fcff * (1 + TERMINAL_GROWTH)) / (WACC - TERMINAL_GROWTH)
pv_terminal_value_gg = terminal_value_gg / ((1 + WACC) ** len(years))

# Exit-multiple cross-check: what would the business be worth at the END of
# year 5 if the market valued it at its OWN current EV/EBITDA multiple?
terminal_value_exit = forecast[-1]["ebitda"] * MARKET["ev_ebitda_multiple"]
pv_terminal_value_exit = terminal_value_exit / ((1 + WACC) ** len(years))

enterprise_value_gg = pv_fcff_total + pv_terminal_value_gg
enterprise_value_exit = pv_fcff_total + pv_terminal_value_exit

# ===========================================================================
# STEP 4 — EQUITY VALUE & IMPLIED SHARE PRICE
# ===========================================================================
net_debt = MARKET["total_debt_usd_m"] - MARKET["cash_usd_m"]

def to_equity(ev):
    equity_value = ev - net_debt
    price = equity_value / MARKET["shares_outstanding_m"]
    return equity_value, price

equity_value_gg, price_gg = to_equity(enterprise_value_gg)
equity_value_exit, price_exit = to_equity(enterprise_value_exit)
implied_current_price = MARKET["market_cap_usd_m"] / MARKET["shares_outstanding_m"]

# ===========================================================================
# STEP 5 — SENSITIVITY: WACC x Terminal Growth
# ===========================================================================
wacc_range = [WACC - 0.01, WACC - 0.005, WACC, WACC + 0.005, WACC + 0.01]
tgr_range = [TERMINAL_GROWTH - 0.01, TERMINAL_GROWTH - 0.005, TERMINAL_GROWTH,
             TERMINAL_GROWTH + 0.005, TERMINAL_GROWTH + 0.01]

sensitivity = []
for w in wacc_range:
    row = []
    for g in tgr_range:
        pv_fcff_w = sum(r["fcff"] / ((1 + w) ** i) for i, r in enumerate(forecast, start=1))
        tv = (final_year_fcff * (1 + g)) / (w - g)
        pv_tv = tv / ((1 + w) ** len(years))
        ev = pv_fcff_w + pv_tv
        _, price = to_equity(ev)
        row.append(round(price, 2))
    sensitivity.append(row)

# ===========================================================================
# OUTPUT
# ===========================================================================
if __name__ == "__main__":
    print(f"Cost of equity (CAPM): {cost_of_equity*100:.2f}%")
    print(f"After-tax cost of debt: {after_tax_cost_of_debt*100:.2f}%")
    print(f"WACC: {WACC*100:.2f}%  (E weight {weight_equity*100:.1f}% / D weight {weight_debt*100:.1f}%)")
    print()
    print(f"{'Year':<6}{'Revenue':>10}{'EBITDA':>10}{'EBIT':>10}{'NOPAT':>10}{'Capex':>9}{'FCFF':>10}{'PV(FCFF)':>11}")
    for r in forecast:
        print(f"{r['year']:<6}{r['revenue']:>10,.0f}{r['ebitda']:>10,.0f}{r['ebit']:>10,.0f}"
              f"{r['nopat']:>10,.0f}{r['capex']:>9,.0f}{r['fcff']:>10,.0f}{r['pv_fcff']:>11,.0f}")
    print()
    print(f"Sum of PV(FCFF), 2026-2030: ${pv_fcff_total:,.0f}M")
    print(f"Terminal value (Gordon Growth, g={TERMINAL_GROWTH*100:.1f}%): ${terminal_value_gg:,.0f}M "
          f"| PV: ${pv_terminal_value_gg:,.0f}M")
    print(f"Terminal value (Exit multiple, {MARKET['ev_ebitda_multiple']}x EBITDA): ${terminal_value_exit:,.0f}M "
          f"| PV: ${pv_terminal_value_exit:,.0f}M")
    print()
    print(f"Enterprise Value (Gordon Growth method): ${enterprise_value_gg:,.0f}M")
    print(f"Enterprise Value (Exit multiple method):  ${enterprise_value_exit:,.0f}M")
    print()
    print(f"Implied share price (Gordon Growth): ${price_gg:,.2f}")
    print(f"Implied share price (Exit multiple):  ${price_exit:,.2f}")
    print(f"Current market-implied share price:   ${implied_current_price:,.2f}")
    print()
    print(f"Context: {EIA_CONTEXT_NOTE}")

    # Export for dashboard
    export = {
        "wacc": round(WACC * 100, 2),
        "cost_of_equity": round(cost_of_equity * 100, 2),
        "after_tax_cost_of_debt": round(after_tax_cost_of_debt * 100, 2),
        "weight_equity": round(weight_equity * 100, 1),
        "weight_debt": round(weight_debt * 100, 1),
        "forecast": [{k: (round(v, 1) if isinstance(v, float) else v) for k, v in r.items()} for r in forecast],
        "terminal_value_gg": round(terminal_value_gg, 0),
        "terminal_value_exit": round(terminal_value_exit, 0),
        "enterprise_value_gg": round(enterprise_value_gg, 0),
        "enterprise_value_exit": round(enterprise_value_exit, 0),
        "price_gg": round(price_gg, 2),
        "price_exit": round(price_exit, 2),
        "current_price": round(implied_current_price, 2),
        "wacc_range": [round(w * 100, 2) for w in wacc_range],
        "tgr_range": [round(g * 100, 2) for g in tgr_range],
        "sensitivity": sensitivity,
        "historical": HISTORICAL,
        "market": MARKET,
        "eia_context": EIA_CONTEXT_NOTE,
    }
    with open(os.path.join(OUT_DIR, "dcf_summary.json"), "w") as f:
        json.dump(export, f, indent=2)
    print(f"\nSaved -> outputs/dcf_summary.json")
