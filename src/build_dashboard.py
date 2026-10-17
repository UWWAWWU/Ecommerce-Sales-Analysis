"""Build public, preaggregated dashboard data from the local processed CSV.

Usage: python src/build_dashboard.py [path/to/retail_activity.csv]
"""
import json
import sys
from pathlib import Path

import pandas as pd

root = Path(__file__).resolve().parents[1]
source = Path(sys.argv[1]) if len(sys.argv) > 1 else root / "data" / "processed" / "retail_activity.csv"
if not source.is_file():
    raise FileNotFoundError(f"Missing {source}; run python src/prepare_data.py first.")
frame = pd.read_csv(source, dtype={"StockCode": str})
sales = frame[frame.OrderStatus.eq("Sale")].copy()
cancelled = frame[frame.OrderStatus.eq("Cancellation")].copy()
dimensions = ["Month", "Country"]
sg = sales.groupby(dimensions).agg(revenue=("GrossSalesGBP", "sum"), units=("UnitsSold", "sum"),
                                     lines=("OrderKey", "size"), orders=("OrderKey", "nunique"))
cg = cancelled.groupby(dimensions).agg(cancelledOrders=("OrderKey", "nunique"))
geography = sg.join(cg, how="outer").fillna(0).reset_index()
for key in ("units", "lines", "orders", "cancelledOrders"):
    geography[key] = geography[key].astype(int)
geography["revenue"] = geography.revenue.round(2)
merchandise = sales[sales.IsMerchandise.eq(True)]
products = merchandise.groupby(["Month", "Country", "StockCode"], as_index=False).agg(
    revenue=("GrossSalesGBP", "sum"), units=("UnitsSold", "sum"))
products["revenue"] = products.revenue.round(2)
products["units"] = products.units.astype(int)
products = products.rename(columns={"Month": "month", "Country": "country", "StockCode": "code"})
names = merchandise.groupby(["StockCode", "Product"]).size().sort_values(ascending=False).reset_index(name="n")
names = names.drop_duplicates("StockCode")
audit = {
    **json.loads((root / "audit.json").read_text(encoding="utf-8")),
    "sales_lines": len(sales), "cancellation_lines": len(cancelled),
    "revenue": round(float(sales.GrossSalesGBP.sum()), 2),
    "orders": int(sales.OrderKey.nunique()),
    "cancelledOrders": int(cancelled.OrderKey.nunique()),
    "cancellationRate": round(cancelled.OrderKey.nunique() /
                              (sales.OrderKey.nunique() + cancelled.OrderKey.nunique()), 6),
    "aov": round(sales.GrossSalesGBP.sum() / sales.OrderKey.nunique(), 2),
    "date_start": "2010-12-01", "date_end": "2011-12-09",
}
data = {
    "audit": audit,
    "months": sorted(frame.Month.unique().tolist()),
    "countries": sorted(frame.Country.unique().tolist()),
    "geography": geography.rename(columns={"Month": "month", "Country": "country"}).to_dict("records"),
    "products": products.to_dict("records"),
    "productNames": dict(zip(names.StockCode, names.Product)),
}
output = root / "docs/data.js"
output.write_text("window.RETAIL_DATA = " + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n", encoding="utf-8")
print(json.dumps({"audit": audit, "geography_rows": len(geography), "product_rows": len(products),
                  "output_kb": round(output.stat().st_size / 1024)}, indent=2))
