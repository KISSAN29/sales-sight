"""
SalesSight - Data Loader Module
Handles file loading (CSV/Excel), schema standardization, validation,
and data cleaning with safe handling of missing values and duplicates.
"""

from io import BytesIO, StringIO
from typing import Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd


# Canonical column mappings to support various common column namings
COLUMN_SYNONYMS: Dict[str, List[str]] = {
    "order_id": [
        "order id", "order_id", "orderid", "invoice", "invoiceno", 
        "invoice_no", "invoice no", "transaction_id", "transaction id", "id"
    ],
    "order_date": [
        "order date", "order_date", "date", "invoicedate", "invoice_date", 
        "invoice date", "transaction_date", "order_dt", "purchase_date", "timestamp"
    ],
    "product": [
        "product name", "product_name", "product", "item", "item_name", 
        "description", "title", "product_title", "item description"
    ],
    "category": [
        "category", "product_category", "product category", "item_category", 
        "department", "type", "product_type", "group"
    ],
    "quantity": [
        "quantity", "qty", "units", "units_sold", "items_sold", 
        "volume", "count", "quantity ordered", "quantity_ordered"
    ],
    "unit_price": [
        "unit price", "unit_price", "unitprice", "price", "rate", 
        "price_per_unit", "cost_per_item", "item_price"
    ],
    "sales": [
        "sales", "revenue", "total_amount", "total_sales", "total revenue", 
        "total", "amount", "turnover", "line_total", "total price", "total_price"
    ],
    "region": [
        "region", "area", "territory", "zone", "sales_region"
    ],
    "country": [
        "country", "country_name", "country/region", "nation"
    ],
    "customer": [
        "customer name", "customer_name", "customer", "client", "buyer", 
        "customer_id", "customer id"
    ],
    "payment_method": [
        "payment method", "payment_method", "payment_type", "payment", 
        "payment mode", "mode_of_payment"
    ],
}


def load_file(file_or_path: Union[str, BytesIO, object]) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """
    Load a CSV or Excel file into a pandas DataFrame.
    
    Args:
        file_or_path: File path string or file-like object (e.g. Streamlit UploadedFile)
        
    Returns:
        Tuple of (DataFrame or None, error_message or None)
    """
    try:
        # Determine filename or extension
        name = getattr(file_or_path, "name", str(file_or_path)).lower()
        
        if name.endswith(".csv"):
            # Try UTF-8 first, fallback to Latin-1 if encoding fails
            try:
                df = pd.read_csv(file_or_path, encoding="utf-8")
            except UnicodeDecodeError:
                if hasattr(file_or_path, "seek"):
                    file_or_path.seek(0)
                df = pd.read_csv(file_or_path, encoding="latin1")
        elif name.endswith(".xlsx") or name.endswith(".xls"):
            df = pd.read_excel(file_or_path, engine="openpyxl" if name.endswith(".xlsx") else None)
        else:
            # Attempt to read as CSV by default
            try:
                df = pd.read_csv(file_or_path)
            except Exception:
                return None, "Unsupported file format. Please upload a .csv or .xlsx file."
                
        if df.empty:
            return None, "The uploaded file is empty. Please provide a file containing sales data."
            
        return df, None

    except Exception as e:
        return None, f"Failed to read file: {str(e)}"


def standardize_columns(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, str]]:
    """
    Standardize DataFrame column names to lowercase canonical names using COLUMN_SYNONYMS.
    Preserves other columns as well.
    
    Returns:
        Tuple of (Renamed DataFrame, mapping_dict {original_name: canonical_name})
    """
    df_renamed = df.copy()
    raw_columns = list(df_renamed.columns)
    mapping = {}
    matched_canonical = set()
    
    for raw_col in raw_columns:
        norm_col = str(raw_col).strip().lower().replace("-", "_")
        
        # Look for matching canonical column
        for canonical, synonyms in COLUMN_SYNONYMS.items():
            if canonical in matched_canonical:
                continue
            if norm_col == canonical or norm_col in synonyms:
                mapping[raw_col] = canonical
                matched_canonical.add(canonical)
                break
                
    df_renamed = df_renamed.rename(columns=mapping)
    return df_renamed, mapping


def validate_dataset(df: pd.DataFrame) -> Tuple[bool, List[str], List[str], Dict[str, bool]]:
    """
    Validate whether the dataset has required columns for analytics.
    
    Required:
      1. Order Date (order_date)
      2. Product or Category (product or category)
      3. Revenue information (sales OR both quantity and unit_price)
      
    Returns:
      (is_valid, errors_list, warnings_list, detected_features_dict)
    """
    errors: List[str] = []
    warnings: List[str] = []
    cols = df.columns
    
    has_date = "order_date" in cols
    has_product = "product" in cols
    has_category = "category" in cols
    has_sales = "sales" in cols
    has_qty = "quantity" in cols
    has_price = "unit_price" in cols
    has_region = "region" in cols
    has_country = "country" in cols
    
    # 1. Date Validation
    if not has_date:
        errors.append("Missing required date column (e.g. 'Order Date', 'Date', 'InvoiceDate').")
        
    # 2. Item/Product Validation
    if not has_product and not has_category:
        errors.append("Dataset must contain at least a 'Product' or 'Category' column.")
    elif not has_product:
        warnings.append("No specific 'Product' column detected; category will be used as the product dimension.")
    elif not has_category:
        warnings.append("No 'Category' column detected; items will be assigned to a default 'General' category.")
        
    # 3. Revenue Validation
    can_calculate_revenue = has_sales or (has_qty and has_price)
    if not can_calculate_revenue:
        errors.append("Dataset must contain either a 'Sales' / 'Revenue' column, or both 'Quantity' and 'Unit Price'.")
        
    if not has_region and not has_country:
        warnings.append("No 'Region' or 'Country' column detected; regional analytics will be hidden.")

    detected_features = {
        "has_date": has_date,
        "has_product": has_product,
        "has_category": has_category,
        "has_sales": has_sales,
        "has_quantity": has_qty,
        "has_unit_price": has_price,
        "has_region": has_region,
        "has_country": has_country,
        "has_order_id": "order_id" in cols,
    }
    
    is_valid = len(errors) == 0
    return is_valid, errors, warnings, detected_features


def _clean_numeric_series(series: pd.Series) -> pd.Series:
    """Safely convert series to numeric, stripping currency signs and commas."""
    if series.dtype in [np.float64, np.int64, float, int]:
        return pd.to_numeric(series, errors="coerce")
    
    # Convert string representation: remove $, €, £, commas, spaces
    cleaned = (
        series.astype(str)
        .str.replace(r"[\$,€,£, ]", "", regex=True)
        .str.strip()
    )
    return pd.to_numeric(cleaned, errors="coerce")


def clean_dataset(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Union[int, bool]]]:
    """
    Clean dataset safely:
    - Deduplicate rows
    - Parse dates safely (drop invalid dates)
    - Convert numeric fields (quantity, unit_price, sales)
    - Compute sales = quantity * unit_price if needed
    - Fill missing categorical fields with meaningful defaults
    - Extract date features (year, month, year_month)
    
    Returns:
        (cleaned_df, cleaning_summary_dict)
    """
    initial_rows = len(df)
    df_clean = df.copy()
    
    # 1. Remove duplicate rows
    df_clean = df_clean.drop_duplicates()
    duplicates_removed = initial_rows - len(df_clean)
    
    # 2. Date parsing
    invalid_dates_dropped = 0
    if "order_date" in df_clean.columns:
        parsed_dates = pd.to_datetime(df_clean["order_date"], errors="coerce")
        invalid_dates_mask = parsed_dates.isna()
        invalid_dates_dropped = int(invalid_dates_mask.sum())
        df_clean["order_date"] = parsed_dates
        df_clean = df_clean.dropna(subset=["order_date"])
        
        # Add derived date attributes for efficient slicing and plotting
        df_clean["year"] = df_clean["order_date"].dt.year
        df_clean["month"] = df_clean["order_date"].dt.month
        df_clean["year_month"] = df_clean["order_date"].dt.to_period("M").astype(str)
        df_clean["month_name"] = df_clean["order_date"].dt.strftime("%b %Y")
        
    # 3. Clean numeric fields
    if "quantity" in df_clean.columns:
        df_clean["quantity"] = _clean_numeric_series(df_clean["quantity"]).fillna(1)
        # Quantities should be positive
        df_clean["quantity"] = df_clean["quantity"].apply(lambda q: max(1, abs(int(round(q)))))
    else:
        df_clean["quantity"] = 1
        
    if "unit_price" in df_clean.columns:
        df_clean["unit_price"] = _clean_numeric_series(df_clean["unit_price"]).fillna(0.0)
        df_clean["unit_price"] = df_clean["unit_price"].apply(lambda p: max(0.0, float(p)))
        
    # 4. Handle Revenue (Sales)
    calculated_from_qty_price = False
    if "sales" in df_clean.columns:
        df_clean["sales"] = _clean_numeric_series(df_clean["sales"])
        # If sales has nulls or zeros but quantity & unit_price exist, fill them
        if "unit_price" in df_clean.columns:
            fallback_sales = df_clean["quantity"] * df_clean["unit_price"]
            df_clean["sales"] = df_clean["sales"].fillna(fallback_sales)
            zero_mask = (df_clean["sales"] == 0) & (fallback_sales > 0)
            df_clean.loc[zero_mask, "sales"] = fallback_sales[zero_mask]
    elif "unit_price" in df_clean.columns:
        df_clean["sales"] = df_clean["quantity"] * df_clean["unit_price"]
        calculated_from_qty_price = True
    else:
        df_clean["sales"] = 0.0
        
    # Guarantee sales is non-negative float
    df_clean["sales"] = df_clean["sales"].fillna(0.0).apply(lambda s: max(0.0, float(s)))

    # Backfill unit_price if missing but sales & quantity exist
    if "unit_price" not in df_clean.columns and "quantity" in df_clean.columns:
        df_clean["unit_price"] = df_clean["sales"] / df_clean["quantity"].replace(0, 1)

    # 5. Clean categorical columns
    if "product" not in df_clean.columns:
        if "category" in df_clean.columns:
            df_clean["product"] = df_clean["category"]
        else:
            df_clean["product"] = "General Product"
    else:
        df_clean["product"] = df_clean["product"].fillna("Unknown Product").astype(str).str.strip()

    if "category" not in df_clean.columns:
        df_clean["category"] = "General"
    else:
        df_clean["category"] = df_clean["category"].fillna("Uncategorized").astype(str).str.strip()

    if "region" in df_clean.columns:
        df_clean["region"] = df_clean["region"].fillna("Unknown").astype(str).str.strip()

    if "country" in df_clean.columns:
        df_clean["country"] = df_clean["country"].fillna("Unknown").astype(str).str.strip()

    if "order_id" not in df_clean.columns:
        # Generate synthetic order ID for consistent order counting
        df_clean["order_id"] = [f"ORD-{i+1:05d}" for i in range(len(df_clean))]
    else:
        df_clean["order_id"] = df_clean["order_id"].fillna(
            pd.Series([f"ORD-{i+1:05d}" for i in range(len(df_clean))], index=df_clean.index)
        ).astype(str)

    # Final sort by date
    if "order_date" in df_clean.columns:
        df_clean = df_clean.sort_values("order_date").reset_index(drop=True)

    summary = {
        "original_rows": initial_rows,
        "cleaned_rows": len(df_clean),
        "duplicates_removed": duplicates_removed,
        "invalid_dates_dropped": invalid_dates_dropped,
        "revenue_calculated_from_qty_price": calculated_from_qty_price,
    }

    return df_clean, summary


def get_sample_csv_template() -> str:
    """
    Generate a clean sample CSV template string for users to download and follow.
    """
    template_data = [
        "Order ID,Order Date,Customer Name,Product Name,Category,Quantity,Unit Price,Region,Country,Payment Method",
        "ORD-1001,2024-01-15,Alice Smith,Wireless Headphones,Electronics,2,99.99,North,United States,Credit Card",
        "ORD-1002,2024-01-18,Bob Jones,Ergonomic Chair,Furniture,1,249.50,West,Canada,PayPal",
        "ORD-1003,2024-02-05,Charlie Brown,Mechanical Keyboard,Electronics,1,85.00,East,United Kingdom,Credit Card",
        "ORD-1004,2024-02-12,Diana Prince,Coffee Maker,Home & Kitchen,3,45.00,South,Germany,Debit Card",
        "ORD-1005,2024-03-01,Evan Wright,Gel Pen Set,Office Supplies,5,12.50,Central,Australia,Credit Card",
    ]
    return "\n".join(template_data)
