# E-Commerce Sales Performance Analysis

Reproducible Python and SQL analysis of the [UCI Online Retail dataset](https://archive.ics.uci.edu/dataset/352/online+retail), with a shareable interactive dashboard. The dashboard uses preaggregated data: individual invoices and customer IDs are not published.

**[Open the live dashboard](https://dashboard.wawutriambodo.my.id)** · [Portfolio](https://wawutriambodo.my.id)

## Results

| Metric | Result | Definition |
| --- | ---: | --- |
| Original transaction lines | 541,909 | Raw rows before cleaning |
| Gross sales | £10,642,110.80 | Positive quantities and prices on valid sale invoices; before returns |
| Valid orders | 19,960 | Distinct sale invoice numbers |
| Known customers | 4,338 | Distinct nonmissing CustomerID values among valid sales |
| Peak month | November 2011 · £1,503,866.78 | Gross sales by calendar month |
| Average order value | £533.17 | Gross sales ÷ valid orders |
| Cancellation rate | 16.12% | 3,836 distinct cancelled invoices ÷ (19,960 valid + 3,836 cancelled invoices) |

The cleaning step removes 5,268 exact duplicates. It retains sales with a missing CustomerID for revenue and order metrics, while excluding them from the known customer count. Invoices marked with `C` count as cancellations. Negative adjustment lines without `C` are excluded from valid sales and the cancelled invoice count. December 2010 and December 2011 are partial months.

## Dashboard

The [live dashboard](https://dashboard.wawutriambodo.my.id) provides country and date filters, gross sales, valid orders, average order value, cancellation rate, monthly revenue, top markets, and top merchandise stock codes. The source in `docs/` is a static HTML/CSS/JavaScript dashboard that also opens locally from `docs/index.html`.

The full-period known customer count and peak month are reproducible in `audit.json`; the dashboard does not offer a customer count under filters because its public aggregates contain no customer identifiers. Gross sales do **not** mean net revenue after returns. Country and month filters recalculate the displayed figures.

## Reproduce

1. Download `Online Retail.xlsx` from the [UCI dataset page](https://archive.ics.uci.edu/dataset/352/online+retail) and place it at `data/raw/Online Retail.xlsx`.
2. Install dependencies and run the two stages from the repository root:

   ```bash
   python -m venv .venv
   # Windows: .venv\Scripts\activate
   # macOS/Linux: source .venv/bin/activate
   pip install -r requirements.txt
   python src/prepare_data.py
   python src/build_dashboard.py
   ```

3. Open `docs/index.html` to inspect the rebuilt dashboard. Execute `sql/analysis.sql` against `data/retail.sqlite` using SQLite for independent revenue, order, cancellation, country, and product checks.

The first stage writes `audit.json`, `data/processed/retail_activity.csv`, and `data/retail.sqlite`. The second writes `docs/data.js`. Raw data, processed rows, and SQLite are excluded from Git. The committed `docs/data.js` contains only grouped totals for the public dashboard.

## Structure

```text
src/prepare_data.py      Validation, deduplication, metrics, local SQLite/CSV
src/build_dashboard.py   Public month/country/product aggregates
sql/analysis.sql         Example SQLite analysis queries
docs/                    Static dashboard and preaggregated data
audit.json               Reproducible full-period audit
data/raw/                Local UCI workbook (ignored by Git)
```

Dataset credit: [UCI Machine Learning Repository, Online Retail](https://archive.ics.uci.edu/dataset/352/online+retail), CC BY 4.0.
