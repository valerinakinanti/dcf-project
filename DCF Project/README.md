# Chevron (CVX) — DCF Valuation Model

A full discounted cash flow valuation of Chevron Corporation, built from real
historical financials and market data — not textbook placeholder numbers.

**Live dashboard (interactive, adjustable WACC/growth sliders):** `outputs/dashboard.html`
**Investment memo:** `outputs/investment_memo.md`

## Why this project

Every non-modeling-assumption number here is sourced and cited in
`data/inputs.py` — historical revenue/EBITDA (MacroTrends, 10-K based), beta
and market cap (stockanalysis.com), risk-free rate (FRED/Trading Economics),
and current market context (EIA Short-Term Energy Outlook). The point is to
survive a "where did this number come from" question in an interview, not to
produce a plausible-looking number that falls apart under one follow-up.

## What it does

1. **WACC** — CAPM cost of equity (real beta, current 10Y Treasury, standard
   equity risk premium) blended with after-tax cost of debt, weighted by
   market value of equity and debt.
2. **5-year forecast** (`scripts/dcf_model.py`) — Revenue → EBITDA → EBIT →
   NOPAT → FCFF, with growth assumptions that deliberately do NOT chase the
   current oil-price spike (Strait of Hormuz disruption per EIA STEO) —
   that risk is captured in sensitivity, not baked into a single point
   estimate.
3. **Terminal value, two ways** — Gordon Growth perpetuity AND an
   exit-multiple cross-check using Chevron's own current EV/EBITDA multiple.
   The gap between the two methods is itself an insight (see memo).
4. **Sensitivity** — full WACC x terminal-growth grid, plus a live
   interactive version in the dashboard (drag sliders, watch the price move).

## Key output

| Method | Implied price | vs. current ($202.50) |
|---|---|---|
| DCF — Gordon Growth | $209.72 | +3.6% |
| DCF — Exit multiple | $234.05 | +15.6% |

## Stack

Python (no external dependencies beyond the standard library) · HTML/CSS/JS
dashboard with live client-side recalculation (no server required).

## Run it yourself

```bash
cd scripts
python3 dcf_model.py
```

Then open `outputs/dashboard.html` in a browser.

## Project structure

```
dcf-project/
├── data/inputs.py           sourced historical, market, and macro inputs
├── scripts/dcf_model.py     WACC, forecast, terminal value, sensitivity
├── outputs/
│   ├── dashboard.html       interactive valuation dashboard
│   ├── dcf_summary.json
│   └── investment_memo.md
└── README.md
```
