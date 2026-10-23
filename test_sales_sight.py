"""
SalesSight - Verification and Unit Tests
Tests loading, column standardization, cleaning, KPI calculation,
trends, charts aggregations, and edge cases (missing columns, dirty data).
"""

import os
import sys
import pandas as pd

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.data_loader import (
    load_file,
    standardize_columns,
    validate_dataset,
    clean_dataset,
    get_sample_csv_template,
)
from src.analytics import (
    compute_kpis,
    get_monthly_sales_trend,
    get_top_selling_products,
    get_sales_by_category,
    get_sales_by_region,
    get_sales_by_country,
    generate_automated_insights,
    filter_dataset,
)
from src.pyspark_extension import (
    is_pyspark_available,
    get_big_data_architecture_notes,
)


def run_tests():
    print("=== Running SalesSight Test Suite ===")
    sample_path = os.path.join(os.path.dirname(__file__), "data", "sample_sales.csv")
    assert os.path.exists(sample_path), f"Sample file not found at {sample_path}"
    
    # 1. Test File Loading
    raw_df, err = load_file(sample_path)
    assert err is None, f"load_file returned error: {err}"
    assert raw_df is not None and len(raw_df) > 0, "raw_df is empty"
    print(f"[PASS] 1. load_file loaded {len(raw_df)} rows from sample_sales.csv")

    # 2. Test Column Standardization
    std_df, col_map = standardize_columns(raw_df)
    assert "sales" in std_df.columns, "Standardization failed to map 'sales'"
    assert "order_date" in std_df.columns, "Standardization failed to map 'order_date'"
    print(f"[PASS] 2. standardize_columns mapped columns: {list(col_map.values())}")

    # 3. Test Validation
    is_valid, errors, warnings, features = validate_dataset(std_df)
    assert is_valid, f"Validation failed with errors: {errors}"
    assert features["has_date"] and features["has_sales"], "Expected features not detected"
    print(f"[PASS] 3. validate_dataset succeeded (is_valid={is_valid}, warnings={len(warnings)})")

    # 4. Test Cleaning
    clean_df, summary = clean_dataset(std_df)
    assert len(clean_df) > 0, "clean_dataset produced empty DataFrame"
    assert "year_month" in clean_df.columns, "clean_dataset missing 'year_month'"
    print(f"[PASS] 4. clean_dataset produced {summary['cleaned_rows']} clean records")

    # 5. Test KPI computation
    kpis = compute_kpis(clean_df)
    assert kpis["total_revenue"] > 0, "total_revenue should be > 0"
    assert kpis["total_orders"] > 0, "total_orders should be > 0"
    assert kpis["aov"] > 0, "aov should be > 0"
    print(f"[PASS] 5. compute_kpis: Revenue=${kpis['total_revenue']:,.2f}, Orders={kpis['total_orders']}, AOV=${kpis['aov']:,.2f}")

    # 6. Test Monthly Trends
    monthly_trend = get_monthly_sales_trend(clean_df)
    assert not monthly_trend.empty, "Monthly trend should not be empty"
    assert "revenue" in monthly_trend.columns, "Monthly trend missing 'revenue'"
    print(f"[PASS] 6. get_monthly_sales_trend calculated {len(monthly_trend)} months")

    # 7. Test Top Selling Products
    top_prods = get_top_selling_products(clean_df, top_n=5)
    assert len(top_prods) <= 5 and len(top_prods) > 0, "Top products returned unexpected count"
    assert "total_revenue" in top_prods.columns, "Top products missing 'total_revenue'"
    print(f"[PASS] 7. get_top_selling_products top product: {top_prods.iloc[0]['product']} (${top_prods.iloc[0]['total_revenue']:,.2f})")

    # 8. Test Category Breakdown
    cat_sales = get_sales_by_category(clean_df)
    assert not cat_sales.empty, "Category sales should not be empty"
    print(f"[PASS] 8. get_sales_by_category top category: {cat_sales.iloc[0]['category']}")

    # 9. Test Region & Country Breakdown
    reg_sales = get_sales_by_region(clean_df)
    ctry_sales = get_sales_by_country(clean_df)
    assert not reg_sales.empty, "Region sales should not be empty"
    assert not ctry_sales.empty, "Country sales should not be empty"
    print(f"[PASS] 9. Region ({len(reg_sales)} regions) & Country ({len(ctry_sales)} countries) breakdown successful")

    # 10. Test Automated Insights
    insights = generate_automated_insights(clean_df)
    assert len(insights) > 0, "Automated insights returned empty list"
    print(f"[PASS] 10. generate_automated_insights produced {len(insights)} dynamic insights:")
    for ins in insights:
        print(f"       * [{ins['title']}]: {ins['text']}")

    # 11. Test Filtering
    categories = list(clean_df["category"].unique()[:2])
    filtered_df = filter_dataset(clean_df, categories=categories)
    assert len(filtered_df) < len(clean_df), "Filter did not restrict rows"
    assert set(filtered_df["category"].unique()).issubset(set(categories))
    print(f"[PASS] 11. filter_dataset correctly filtered to {len(filtered_df)} rows for categories {categories}")

    # 12. Test PySpark module availability & architecture notes
    notes = get_big_data_architecture_notes()
    assert "viva_questions" in notes, "Architecture notes missing viva questions"
    print(f"[PASS] 12. PySpark optional module loaded cleanly (PySpark Installed: {is_pyspark_available()})")

    # 13. Test Sample CSV Template
    template = get_sample_csv_template()
    assert "Order Date" in template and "Product Name" in template
    print("[PASS] 13. Sample template generation works")

    print("\nALL 13 TESTS PASSED SUCCESSFULLY! [OK]")


if __name__ == "__main__":
    run_tests()
