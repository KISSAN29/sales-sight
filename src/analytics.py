"""
SalesSight - Analytics Module
Provides pure, modular analytical aggregations, KPI computations,
filtering routines, and automated business insights.
Designed cleanly so functions can be ported to PySpark or SQL.
"""

from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd


def compute_kpis(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Compute primary executive KPIs:
    - Total Revenue
    - Total Orders
    - Total Units Sold
    - Average Order Value (AOV)
    - Average Units per Order
    """
    if df.empty:
        return {
            "total_revenue": 0.0,
            "total_orders": 0,
            "total_units": 0,
            "aov": 0.0,
            "avg_units_per_order": 0.0,
            "total_products": 0,
            "total_categories": 0,
        }

    total_revenue = float(df["sales"].sum())
    
    # Use distinct order_id count if available, otherwise total rows
    if "order_id" in df.columns:
        total_orders = int(df["order_id"].nunique())
    else:
        total_orders = len(df)
        
    total_units = int(df["quantity"].sum()) if "quantity" in df.columns else total_orders
    aov = float(total_revenue / total_orders) if total_orders > 0 else 0.0
    avg_units_per_order = float(total_units / total_orders) if total_orders > 0 else 0.0
    total_products = int(df["product"].nunique()) if "product" in df.columns else 0
    total_categories = int(df["category"].nunique()) if "category" in df.columns else 0

    return {
        "total_revenue": total_revenue,
        "total_orders": total_orders,
        "total_units": total_units,
        "aov": aov,
        "avg_units_per_order": avg_units_per_order,
        "total_products": total_products,
        "total_categories": total_categories,
    }


def get_monthly_sales_trend(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate sales metrics by month (year_month) chronologically.
    Returns DataFrame with:
    - year_month
    - month_label
    - revenue
    - orders
    - units_sold
    - aov
    """
    if df.empty or "order_date" not in df.columns:
        return pd.DataFrame(columns=["year_month", "month_label", "revenue", "orders", "units_sold", "aov"])

    grouped = df.groupby(["year", "month", "year_month", "month_name"]).agg(
        revenue=("sales", "sum"),
        orders=("order_id", "nunique") if "order_id" in df.columns else ("sales", "count"),
        units_sold=("quantity", "sum") if "quantity" in df.columns else ("sales", "count"),
    ).reset_index()

    # Sort chronologically by year and month
    grouped = grouped.sort_values(by=["year", "month"]).reset_index(drop=True)
    grouped["aov"] = grouped["revenue"] / grouped["orders"].replace(0, 1)
    grouped["month_label"] = grouped["month_name"]
    
    # Calculate month-over-month revenue growth rate
    grouped["revenue_growth_%"] = grouped["revenue"].pct_change() * 100

    return grouped


def get_top_selling_products(df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    """
    Compute top selling products ranked by revenue.
    Returns DataFrame with:
    - product
    - category (if available)
    - total_revenue
    - units_sold
    - total_orders
    - avg_unit_price
    - revenue_share_%
    """
    if df.empty or "product" not in df.columns:
        return pd.DataFrame()

    agg_dict = {
        "sales": "sum",
        "quantity": "sum" if "quantity" in df.columns else "count",
        "order_id": "nunique" if "order_id" in df.columns else "count",
    }
    
    # If category is available, include it in grouping
    if "category" in df.columns:
        grouped = df.groupby(["product", "category"]).agg(**{
            "total_revenue": ("sales", "sum"),
            "units_sold": ("quantity", "sum") if "quantity" in df.columns else ("sales", "count"),
            "total_orders": ("order_id", "nunique") if "order_id" in df.columns else ("sales", "count"),
        }).reset_index()
    else:
        grouped = df.groupby("product").agg(**{
            "total_revenue": ("sales", "sum"),
            "units_sold": ("quantity", "sum") if "quantity" in df.columns else ("sales", "count"),
            "total_orders": ("order_id", "nunique") if "order_id" in df.columns else ("sales", "count"),
        }).reset_index()

    total_revenue_overall = df["sales"].sum()
    grouped["revenue_share_%"] = (
        (grouped["total_revenue"] / total_revenue_overall * 100)
        if total_revenue_overall > 0 else 0.0
    )
    grouped["avg_unit_price"] = grouped["total_revenue"] / grouped["units_sold"].replace(0, 1)

    sorted_df = grouped.sort_values(by="total_revenue", ascending=False).head(top_n).reset_index(drop=True)
    return sorted_df


def get_sales_by_category(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute sales breakdown by product category.
    Returns DataFrame with:
    - category
    - total_revenue
    - units_sold
    - order_count
    - revenue_share_%
    """
    if df.empty or "category" not in df.columns:
        return pd.DataFrame()

    grouped = df.groupby("category").agg(
        total_revenue=("sales", "sum"),
        units_sold=("quantity", "sum") if "quantity" in df.columns else ("sales", "count"),
        order_count=("order_id", "nunique") if "order_id" in df.columns else ("sales", "count"),
    ).reset_index()

    total_sales = df["sales"].sum()
    grouped["revenue_share_%"] = (
        (grouped["total_revenue"] / total_sales * 100)
        if total_sales > 0 else 0.0
    )
    
    return grouped.sort_values(by="total_revenue", ascending=False).reset_index(drop=True)


def get_sales_by_region(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute sales breakdown by sales region.
    """
    if df.empty or "region" not in df.columns:
        return pd.DataFrame()

    grouped = df.groupby("region").agg(
        total_revenue=("sales", "sum"),
        units_sold=("quantity", "sum") if "quantity" in df.columns else ("sales", "count"),
        total_orders=("order_id", "nunique") if "order_id" in df.columns else ("sales", "count"),
    ).reset_index()

    total_sales = df["sales"].sum()
    grouped["revenue_share_%"] = (
        (grouped["total_revenue"] / total_sales * 100)
        if total_sales > 0 else 0.0
    )
    return grouped.sort_values(by="total_revenue", ascending=False).reset_index(drop=True)


def get_sales_by_country(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute sales breakdown by country.
    """
    if df.empty or "country" not in df.columns:
        return pd.DataFrame()

    grouped = df.groupby("country").agg(
        total_revenue=("sales", "sum"),
        units_sold=("quantity", "sum") if "quantity" in df.columns else ("sales", "count"),
        total_orders=("order_id", "nunique") if "order_id" in df.columns else ("sales", "count"),
    ).reset_index()

    total_sales = df["sales"].sum()
    grouped["revenue_share_%"] = (
        (grouped["total_revenue"] / total_sales * 100)
        if total_sales > 0 else 0.0
    )
    return grouped.sort_values(by="total_revenue", ascending=False).reset_index(drop=True)


def generate_automated_insights(df: pd.DataFrame) -> List[Dict[str, str]]:
    """
    Generate meaningful, data-driven executive bullet points based strictly
    on the current filtered dataset. Never uses hardcoded numbers.
    """
    if df.empty:
        return [{"type": "info", "title": "No Data", "text": "No data available to generate insights."}]

    insights: List[Dict[str, str]] = []
    total_sales = df["sales"].sum()

    # 1. Top Product Insight
    if "product" in df.columns:
        prod_agg = df.groupby("product")["sales"].sum().sort_values(ascending=False)
        if not prod_agg.empty:
            top_prod_name = prod_agg.index[0]
            top_prod_sales = prod_agg.iloc[0]
            prod_pct = (top_prod_sales / total_sales * 100) if total_sales > 0 else 0.0
            insights.append({
                "type": "star",
                "title": "Top Performing Product",
                "text": f"'{top_prod_name}' leads revenue generation with ${top_prod_sales:,.2f} ({prod_pct:.1f}% of total sales)."
            })

    # 2. Top Category Insight
    if "category" in df.columns:
        cat_agg = df.groupby("category")["sales"].sum().sort_values(ascending=False)
        if not cat_agg.empty:
            top_cat = cat_agg.index[0]
            top_cat_sales = cat_agg.iloc[0]
            cat_pct = (top_cat_sales / total_sales * 100) if total_sales > 0 else 0.0
            insights.append({
                "type": "chart",
                "title": "Dominant Category",
                "text": f"'{top_cat}' is the highest grossing category, accounting for ${top_cat_sales:,.2f} ({cat_pct:.1f}% share)."
            })

    # 3. Monthly Peak & Low Insight
    if "order_date" in df.columns and "month_name" in df.columns:
        monthly = df.groupby(["year", "month", "month_name"])["sales"].sum().reset_index()
        if len(monthly) >= 2:
            best_month_row = monthly.loc[monthly["sales"].idxmax()]
            worst_month_row = monthly.loc[monthly["sales"].idxmin()]
            insights.append({
                "type": "calendar",
                "title": "Peak Sales Period",
                "text": f"Peak performance occurred in {best_month_row['month_name']} (${best_month_row['sales']:,.2f}), whereas {worst_month_row['month_name']} had lowest sales (${worst_month_row['sales']:,.2f})."
            })

    # 4. Regional or Geographical Leader
    if "region" in df.columns and df["region"].nunique() > 1:
        reg_agg = df.groupby("region")["sales"].sum().sort_values(ascending=False)
        top_region = reg_agg.index[0]
        top_reg_sales = reg_agg.iloc[0]
        reg_pct = (top_reg_sales / total_sales * 100) if total_sales > 0 else 0.0
        insights.append({
            "type": "globe",
            "title": "Top Geographic Zone",
            "text": f"The '{top_region}' region contributed the largest share: ${top_reg_sales:,.2f} ({reg_pct:.1f}% of total revenue)."
        })
    elif "country" in df.columns and df["country"].nunique() > 1:
        ctry_agg = df.groupby("country")["sales"].sum().sort_values(ascending=False)
        top_ctry = ctry_agg.index[0]
        top_ctry_sales = ctry_agg.iloc[0]
        ctry_pct = (top_ctry_sales / total_sales * 100) if total_sales > 0 else 0.0
        insights.append({
            "type": "globe",
            "title": "Top International Market",
            "text": f"Customers in '{top_ctry}' generated the highest revenue: ${top_ctry_sales:,.2f} ({ctry_pct:.1f}% share)."
        })

    # 5. Order Value Profile
    order_col = "order_id" if "order_id" in df.columns else None
    if order_col:
        order_totals = df.groupby(order_col)["sales"].sum()
        max_order = order_totals.max()
        median_order = order_totals.median()
        insights.append({
            "type": "money",
            "title": "Basket Size Analysis",
            "text": f"Median order ticket is ${median_order:,.2f}, while the largest recorded individual order value reached ${max_order:,.2f}."
        })

    return insights


def filter_dataset(
    df: pd.DataFrame,
    date_range: Optional[Tuple[pd.Timestamp, pd.Timestamp]] = None,
    categories: Optional[List[str]] = None,
    regions: Optional[List[str]] = None,
    countries: Optional[List[str]] = None,
    products: Optional[List[str]] = None,
) -> pd.DataFrame:
    """
    Pure filtering function applying user selections.
    """
    if df.empty:
        return df

    filtered = df.copy()

    # 1. Date filter
    if date_range and len(date_range) == 2 and "order_date" in filtered.columns:
        start_date, end_date = date_range
        if start_date is not None and end_date is not None:
            # Normalize to include the entire end date day
            start_ts = pd.to_datetime(start_date)
            end_ts = pd.to_datetime(end_date) + pd.Timedelta(days=1) - pd.Timedelta(nanoseconds=1)
            filtered = filtered[(filtered["order_date"] >= start_ts) & (filtered["order_date"] <= end_ts)]

    # 2. Category filter
    if categories and "category" in filtered.columns:
        filtered = filtered[filtered["category"].isin(categories)]

    # 3. Region filter
    if regions and "region" in filtered.columns:
        filtered = filtered[filtered["region"].isin(regions)]

    # 4. Country filter
    if countries and "country" in filtered.columns:
        filtered = filtered[filtered["country"].isin(countries)]

    # 5. Product filter
    if products and "product" in filtered.columns:
        filtered = filtered[filtered["product"].isin(products)]

    return filtered
