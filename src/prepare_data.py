"""Clean UCI Online Retail data and write local analysis inputs."""
from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
REQUIRED = {"InvoiceNo", "StockCode", "Description", "Quantity", "InvoiceDate", "UnitPrice", "CustomerID", "Country"}


def prepare(source: Path) -> dict:
    if not source.is_file():
        raise FileNotFoundError(f"Put Online Retail.xlsx in {source.parent}")
    raw = pd.read_excel(source)
    if not REQUIRED <= set(raw.columns):
        raise ValueError(f"Missing columns: {sorted(REQUIRED - set(raw.columns))}")
    frame = raw.drop_duplicates().copy()
    frame["InvoiceNo"] = frame["InvoiceNo"].astype(str)
    frame["InvoiceDate"] = pd.to_datetime(frame["InvoiceDate"], errors="coerce")
    is_cancel = frame["InvoiceNo"].str.upper().str.startswith("C")
    is_sale = (~is_cancel) & frame["Quantity"].gt(0) & frame["UnitPrice"].gt(0) & frame["InvoiceDate"].notna()
    # Negative adjustment rows without C invoice numbers do not count as cancelled orders.
    selected = frame.loc[(is_sale | is_cancel) & frame["InvoiceDate"].notna()].copy()
    selected_is_cancel = selected["InvoiceNo"].str.upper().str.startswith("C")
    # Stable anonymous identifiers across all lines in the same invoice.
    selected["OrderKey"] = pd.factorize(selected["InvoiceNo"], sort=True)[0] + 1
    selected["OrderStatus"] = selected_is_cancel.map({True: "Cancellation", False: "Sale"})
    selected["GrossSalesGBP"] = (selected["Quantity"] * selected["UnitPrice"]).where(~selected_is_cancel, 0)
    selected["UnitsSold"] = selected["Quantity"].where(~selected_is_cancel, 0)
    selected["Month"] = selected["InvoiceDate"].dt.strftime("%Y-%m")
    selected["Country"] = selected["Country"].fillna("Unknown").astype(str).str.strip()
    selected["StockCode"] = selected["StockCode"].astype(str)
    selected["IsMerchandise"] = selected["StockCode"].str.fullmatch(r"\d{5}[A-Za-z]?").fillna(False)
    selected["Product"] = selected["Description"].fillna("Unspecified item").astype(str).str.strip()
    selected["Product"] = selected["Product"].replace("", "Unspecified item")

    out = selected[["OrderKey", "OrderStatus", "InvoiceDate", "Month", "Country",
                    "StockCode", "Product", "IsMerchandise", "GrossSalesGBP", "UnitsSold"]].copy()
    output = ROOT / "data" / "processed" / "retail_activity.csv"
    output.parent.mkdir(exist_ok=True)
    out.to_csv(output, index=False, date_format="%Y-%m-%d %H:%M:%S", float_format="%.4f")

    sale_orders = int(selected.loc[~selected_is_cancel, "OrderKey"].nunique())
    cancelled_orders = int(selected.loc[selected_is_cancel, "OrderKey"].nunique())
    revenue = float(out["GrossSalesGBP"].sum())
    monthly = out.groupby("Month")["GrossSalesGBP"].sum()
    metrics = {
        "source_rows": len(raw), "duplicates_removed": len(raw) - len(frame),
        "valid_sales_lines": int(is_sale.sum()),
        "cancelled_invoice_lines": int(is_cancel.sum()),
        "excluded_other_lines": int((~is_sale & ~is_cancel).sum()),
        "missing_customer_id_in_sales": int(frame.loc[is_sale, "CustomerID"].isna().sum()),
        "gross_sales_gbp": round(revenue, 2), "valid_orders": sale_orders,
        "cancelled_orders": cancelled_orders,
        "cancellation_rate_pct": round(100 * cancelled_orders / (sale_orders + cancelled_orders), 2),
        "average_order_value_gbp": round(revenue / sale_orders, 2),
        "known_customers": int(frame.loc[is_sale, "CustomerID"].nunique()),
        "peak_month": monthly.idxmax(), "peak_month_sales_gbp": round(float(monthly.max()), 2),
        "date_start": str(out["InvoiceDate"].min().date()),
        "date_end": str(out["InvoiceDate"].max().date()),
    }
    (ROOT / "audit.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")

    # A local SQL copy supports independent verification; it is not committed.
    db_path = ROOT / "data" / "retail.sqlite"
    with sqlite3.connect(db_path) as conn:
        out.to_sql("retail_activity", conn, if_exists="replace", index=False, chunksize=5000)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_retail_month_country ON retail_activity(Month, Country)")
    print(json.dumps(metrics, indent=2))
    print(f"Local processed data: {output}")
    return metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=ROOT / "data" / "raw" / "Online Retail.xlsx")
    prepare(parser.parse_args().input)
