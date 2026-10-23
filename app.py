"""
SalesSight – Sales Data Analytics Dashboard
A modern, beginner-friendly Streamlit web application for interactive
sales analytics, automated data cleaning, and executive reporting.
College Mini Project with PySpark Big Data Architecture Support.
"""

import os
from io import BytesIO
from typing import Optional
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Import core analytics & data loader modules
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

# ---------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------
st.set_page_config(
    page_title="SalesSight – Sales Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------
# Custom Styling (CSS)
# ---------------------------------------------------------
st.markdown("""
<style>
    /* Global layout enhancements */
    .main .block-container {
        padding-top: 1.5rem;
        padding-bottom: 3rem;
        max-width: 95%;
    }
    
    /* Header branding */
    .brand-title {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .brand-sub {
        color: #64748B;
        font-size: 1.05rem;
        margin-bottom: 1.2rem;
    }

    /* KPI Card styling */
    .kpi-card {
        background: #ffffff;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 18px 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .kpi-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.08);
    }
    .kpi-label {
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #64748B;
        margin-bottom: 4px;
    }
    .kpi-value {
        font-size: 1.85rem;
        font-weight: 700;
        color: #0F172A;
    }
    .kpi-sub {
        font-size: 0.8rem;
        color: #10B981;
        margin-top: 4px;
        font-weight: 500;
    }

    /* Insights Box */
    .insight-box {
        background: #F8FAFC;
        border-left: 4px solid #3B82F6;
        padding: 14px 18px;
        border-radius: 0 8px 8px 0;
        margin-bottom: 10px;
    }
    .insight-title {
        font-weight: 700;
        color: #1E293B;
        font-size: 0.95rem;
    }
    .insight-text {
        color: #475569;
        font-size: 0.9rem;
        margin-top: 2px;
    }

    /* Empty state card */
    .empty-state {
        text-align: center;
        padding: 50px 20px;
        background: #F8FAFC;
        border: 2px dashed #CBD5E1;
        border-radius: 16px;
        margin-top: 20px;
    }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------
# Helper: Load Sample or Uploaded Dataset
# ---------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_and_prepare_dataset(file_source: str, file_bytes: Optional[bytes] = None, file_name: Optional[str] = None):
    """
    Cached wrapper to load, standardize, validate, and clean dataset.
    Never caches hardcoded analytics; processes real data safely.
    """
    if file_source == "sample":
        sample_path = os.path.join(os.path.dirname(__file__), "data", "sample_sales.csv")
        df_raw, err = load_file(sample_path)
    else:
        if file_bytes is None:
            return None, None, ["No file uploaded"], [], {}, {}
        bio = BytesIO(file_bytes)
        bio.name = file_name or "uploaded_data.csv"
        df_raw, err = load_file(bio)

    if err:
        return None, None, [err], [], {}, {}

    # Standardize column naming
    std_df, col_map = standardize_columns(df_raw)

    # Validate schema
    is_valid, errors, warnings, detected_features = validate_dataset(std_df)
    if not is_valid:
        return df_raw, None, errors, warnings, detected_features, col_map

    # Clean & enrich dataset
    clean_df, summary = clean_dataset(std_df)

    return df_raw, clean_df, errors, warnings, detected_features, summary


# ---------------------------------------------------------
# Sidebar Controls
# ---------------------------------------------------------
with st.sidebar:
    st.markdown("## 📊 **SalesSight**")
    st.markdown("*Sales Data Analytics Web App*")
    st.divider()

    st.subheader("1. Data Source")
    data_source = st.radio(
        "Select Data Source:",
        options=["Built-in Sample Dataset", "Upload CSV / Excel"],
        index=0,
        help="Explore immediately using the realistic built-in store dataset or upload your own store records."
    )

    uploaded_file = None
    if data_source == "Upload CSV / Excel":
        uploaded_file = st.file_uploader(
            "Upload Sales File (.csv or .xlsx)",
            type=["csv", "xlsx", "xls"],
            help="Upload sales transactions. Required: Date, Product/Category, and Revenue (or Quantity + Price)."
        )

    # Download Sample Template
    st.markdown("---")
    st.markdown("**Need a format template?**")
    template_str = get_sample_csv_template()
    st.download_button(
        label="📥 Download CSV Template",
        data=template_str,
        file_name="sales_data_template.csv",
        mime="text/csv",
        help="Download a clean CSV template showing accepted columns and sample rows."
    )

# ---------------------------------------------------------
# Dataset Loading & Preprocessing
# ---------------------------------------------------------
df_raw = None
df_clean = None
load_errors = []
load_warnings = []
detected_features = {}
cleaning_summary = {}

if data_source == "Built-in Sample Dataset":
    df_raw, df_clean, load_errors, load_warnings, detected_features, cleaning_summary = (
        load_and_prepare_dataset(file_source="sample")
    )
elif uploaded_file is not None:
    bytes_data = uploaded_file.getvalue()
    df_raw, df_clean, load_errors, load_warnings, detected_features, cleaning_summary = (
        load_and_prepare_dataset(
            file_source="upload",
            file_bytes=bytes_data,
            file_name=uploaded_file.name
        )
    )

# ---------------------------------------------------------
# Empty State Check
# ---------------------------------------------------------
if df_clean is None:
    st.markdown('<div class="brand-title">SalesSight – Sales Data Analytics Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="brand-sub">Modern sales intelligence, trend forecasting, and executive reporting.</div>', unsafe_allow_html=True)

    if load_errors:
        st.error("### ⚠️ Dataset Validation Error")
        for err in load_errors:
            st.error(f"• {err}")
        if df_raw is not None:
            with st.expander("Preview of Raw Uploaded Data", expanded=True):
                st.write(f"Detected columns: `{list(df_raw.columns)}`")
                st.dataframe(df_raw.head(10), use_container_width=True)
        st.info("💡 Please review the required format or download the CSV template from the sidebar.")
    else:
        st.markdown("""
        <div class="empty-state">
            <h2 style="color: #1E3A8A; font-weight: 700;">No Sales Dataset Loaded Yet</h2>
            <p style="color: #64748B; font-size: 1.05rem; max-width: 650px; margin: 10px auto 25px auto;">
                Welcome to <b>SalesSight</b>! Upload a sales CSV or Excel spreadsheet using the sidebar,
                or switch to the <b>Built-in Sample Dataset</b> to instantly test the interactive dashboard.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        col_c1, col_c2, col_c3 = st.columns([1, 2, 1])
        with col_c2:
            st.markdown("#### 📋 Supported Columns")
            st.markdown("""
            SalesSight supports flexible column headers:
            - **Date**: `Order Date`, `Date`, `InvoiceDate`
            - **Product**: `Product Name`, `Product`, `Item`, `Description`
            - **Category**: `Category`, `Product Category`, `Department`
            - **Revenue**: `Sales`, `Revenue`, `Total Amount` OR `Quantity` & `Unit Price`
            - **Geographic (Optional)**: `Region`, `Country`
            - **Order Identifier (Optional)**: `Order ID`, `InvoiceNo`
            """)
    st.stop()


# ---------------------------------------------------------
# Sidebar Interactive Filters (Only when data is loaded)
# ---------------------------------------------------------
with st.sidebar:
    st.subheader("2. Interactive Filters")
    
    # 1. Date Range Filter
    date_filter = None
    if "order_date" in df_clean.columns and not df_clean["order_date"].empty:
        min_date = df_clean["order_date"].min().date()
        max_date = df_clean["order_date"].max().date()
        
        if min_date == max_date:
            st.info(f"Dataset contains transactions for a single date: {min_date}")
            date_filter = (min_date, max_date)
        else:
            selected_dates = st.date_input(
                "Filter by Order Date Range:",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date,
            )
            if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
                date_filter = selected_dates

    # 2. Category Filter
    selected_categories = []
    if "category" in df_clean.columns:
        all_categories = sorted(df_clean["category"].dropna().unique().tolist())
        selected_categories = st.multiselect(
            "Filter by Category:",
            options=all_categories,
            default=all_categories,
            help="Select one or more categories to filter the charts."
        )

    # 3. Region Filter (if available)
    selected_regions = []
    if "region" in df_clean.columns and df_clean["region"].nunique() > 1:
        all_regions = sorted(df_clean["region"].dropna().unique().tolist())
        selected_regions = st.multiselect(
            "Filter by Region:",
            options=all_regions,
            default=all_regions,
        )

    # 4. Country Filter (if available)
    selected_countries = []
    if "country" in df_clean.columns and df_clean["country"].nunique() > 1:
        all_countries = sorted(df_clean["country"].dropna().unique().tolist())
        selected_countries = st.multiselect(
            "Filter by Country:",
            options=all_countries,
            default=all_countries,
        )

    # Reset Filters Note
    st.caption("Filters dynamically update all KPIs, charts, and downloadable reports.")


# ---------------------------------------------------------
# Apply Filters
# ---------------------------------------------------------
filtered_df = filter_dataset(
    df=df_clean,
    date_range=date_filter,
    categories=selected_categories if selected_categories else None,
    regions=selected_regions if selected_regions else None,
    countries=selected_countries if selected_countries else None,
)

if filtered_df.empty:
    st.warning("⚠️ No transactions match the selected filters. Please adjust the sidebar filter options.")
    st.stop()


# ---------------------------------------------------------
# Header & Active Filter Badges
# ---------------------------------------------------------
st.markdown('<div class="brand-title">SalesSight – Sales Data Analytics Dashboard</div>', unsafe_allow_html=True)
st.markdown(
    f'<div class="brand-sub">Displaying analytics for <b>{len(filtered_df):,}</b> transactions '
    f'({(len(filtered_df)/len(df_clean)*100):.1f}% of loaded dataset).</div>',
    unsafe_allow_html=True
)

# Display warnings if optional fields are missing
if load_warnings:
    with st.expander("ℹ️ Data Processing Notices", expanded=False):
        for w in load_warnings:
            st.info(f"• {w}")


# ---------------------------------------------------------
# Navigation Tabs
# ---------------------------------------------------------
tab_dashboard, tab_deepdive, tab_data_quality, tab_big_data, tab_export = st.tabs([
    "📊 Executive Dashboard",
    "🔍 Deep-Dive Analytics",
    "📋 Data Explorer & Audit",
    "⚡ Big Data Extension (PySpark)",
    "📥 Export Reports"
])


# =========================================================
# TAB 1: EXECUTIVE DASHBOARD
# =========================================================
with tab_dashboard:
    # 1. Compute KPIs
    kpi_data = compute_kpis(filtered_df)

    # KPI Metric Cards
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Total Revenue</div>
            <div class="kpi-value">${kpi_data['total_revenue']:,.2f}</div>
            <div class="kpi-sub">Across {kpi_data['total_orders']} orders</div>
        </div>
        """, unsafe_allow_html=True)

    with kpi2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Total Orders</div>
            <div class="kpi-value">{kpi_data['total_orders']:,}</div>
            <div class="kpi-sub">Distinct transactions</div>
        </div>
        """, unsafe_allow_html=True)

    with kpi3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Total Units Sold</div>
            <div class="kpi-value">{kpi_data['total_units']:,}</div>
            <div class="kpi-sub">{kpi_data['avg_units_per_order']:.1f} items / order avg</div>
        </div>
        """, unsafe_allow_html=True)

    with kpi4:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Average Order Value (AOV)</div>
            <div class="kpi-value">${kpi_data['aov']:,.2f}</div>
            <div class="kpi-sub">{kpi_data['total_products']} unique products</div>
        </div>
        """, unsafe_allow_html=True)

    st.write("")
    st.write("")

    # 2. Charts Row 1: Monthly Sales Trend & Sales by Product Category
    c_trend, c_category = st.columns([1.6, 1.1])

    with c_trend:
        monthly_df = get_monthly_sales_trend(filtered_df)
        if not monthly_df.empty:
            fig_trend = go.Figure()

            # Area / Line for Monthly Revenue
            fig_trend.add_trace(go.Scatter(
                x=monthly_df["month_label"],
                y=monthly_df["revenue"],
                mode="lines+markers",
                name="Revenue ($)",
                line=dict(color="#2563EB", width=3, shape="spline"),
                marker=dict(size=8, color="#1E40AF"),
                fill="tozeroy",
                fillcolor="rgba(37, 99, 235, 0.12)",
                hovertemplate="<b>%{x}</b><br>Revenue: $%{y:,.2f}<extra></extra>"
            ))

            fig_trend.update_layout(
                title=dict(text="<b>Monthly Revenue Trend</b>", font=dict(size=16, color="#0F172A")),
                xaxis=dict(title="Month", showgrid=False),
                yaxis=dict(title="Revenue ($)", showgrid=True, gridcolor="#E2E8F0"),
                plot_bgcolor="white",
                paper_bgcolor="white",
                margin=dict(l=20, r=20, t=45, b=20),
                height=380,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_trend, use_container_width=True)
        else:
            st.info("Monthly trend unavailable (single period or missing order date).")

    with c_category:
        category_df = get_sales_by_category(filtered_df)
        if not category_df.empty:
            fig_cat = px.pie(
                category_df,
                names="category",
                values="total_revenue",
                hole=0.45,
                color_discrete_sequence=px.colors.qualitative.Bold,
            )
            fig_cat.update_traces(
                textposition="inside",
                textinfo="percent+label",
                hovertemplate="<b>%{label}</b><br>Sales: $%{value:,.2f}<br>Share: %{percent}<extra></extra>"
            )
            fig_cat.update_layout(
                title=dict(text="<b>Sales by Product Category</b>", font=dict(size=16, color="#0F172A")),
                showlegend=False,
                margin=dict(l=10, r=10, t=45, b=20),
                height=380,
                paper_bgcolor="white",
            )
            st.plotly_chart(fig_cat, use_container_width=True)
        else:
            st.info("Category breakdown not available.")

    # 3. Charts Row 2: Top 10 Selling Products & Geographic Sales
    c_products, c_geo = st.columns([1.4, 1.3])

    with c_products:
        top_prods_df = get_top_selling_products(filtered_df, top_n=10)
        if not top_prods_df.empty:
            # Sort ascending so highest appears at top of horizontal bar chart
            top_prods_sorted = top_prods_df.sort_values(by="total_revenue", ascending=True)

            fig_prod = px.bar(
                top_prods_sorted,
                x="total_revenue",
                y="product",
                orientation="h",
                text="total_revenue",
                color="total_revenue",
                color_continuous_scale="Blues",
            )
            fig_prod.update_traces(
                texttemplate="$%{text:,.0f}",
                textposition="outside",
                hovertemplate="<b>%{y}</b><br>Revenue: $%{x:,.2f}<extra></extra>"
            )
            fig_prod.update_layout(
                title=dict(text="<b>Top 10 Selling Products</b> (by Revenue)", font=dict(size=16, color="#0F172A")),
                xaxis=dict(title="Revenue ($)", showgrid=True, gridcolor="#E2E8F0"),
                yaxis=dict(title="", showgrid=False),
                plot_bgcolor="white",
                paper_bgcolor="white",
                coloraxis_showscale=False,
                margin=dict(l=10, r=40, t=45, b=20),
                height=420,
            )
            st.plotly_chart(fig_prod, use_container_width=True)
        else:
            st.info("Product breakdown not available.")

    with c_geo:
        # Check if country or region columns exist
        has_region_data = "region" in filtered_df.columns and filtered_df["region"].nunique() > 1
        has_country_data = "country" in filtered_df.columns and filtered_df["country"].nunique() > 1

        if has_region_data or has_country_data:
            geo_mode = "Region" if has_region_data else "Country"
            if has_region_data and has_country_data:
                geo_mode = st.radio("Geographic Dimension:", ["Region", "Country"], horizontal=True, key="geo_toggle")

            if geo_mode == "Region":
                geo_df = get_sales_by_region(filtered_df)
                geo_col_name = "region"
                geo_title = "<b>Sales by Region</b>"
            else:
                geo_df = get_sales_by_country(filtered_df)
                geo_col_name = "country"
                geo_title = "<b>Sales by Country</b>"

            fig_geo = px.bar(
                geo_df,
                x=geo_col_name,
                y="total_revenue",
                color=geo_col_name,
                color_discrete_sequence=px.colors.qualitative.Safe,
                text="total_revenue",
            )
            fig_geo.update_traces(
                texttemplate="$%{text:,.0f}",
                textposition="outside",
                hovertemplate="<b>%{x}</b><br>Revenue: $%{y:,.2f}<extra></extra>"
            )
            fig_geo.update_layout(
                title=dict(text=geo_title, font=dict(size=16, color="#0F172A")),
                xaxis=dict(title="", showgrid=False),
                yaxis=dict(title="Revenue ($)", showgrid=True, gridcolor="#E2E8F0"),
                showlegend=False,
                plot_bgcolor="white",
                paper_bgcolor="white",
                margin=dict(l=10, r=10, t=45, b=20),
                height=380,
            )
            st.plotly_chart(fig_geo, use_container_width=True)
        else:
            st.info("Regional/Geographic data not present in this dataset.")

    # 4. Automated Insights Section (Strictly from real data)
    st.markdown("### 💡 Automated Data Insights & Key Findings")
    insights_list = generate_automated_insights(filtered_df)
    
    col_ins1, col_ins2 = st.columns(2)
    for idx, item in enumerate(insights_list):
        target_col = col_ins1 if idx % 2 == 0 else col_ins2
        with target_col:
            st.markdown(f"""
            <div class="insight-box">
                <div class="insight-title">{item['title']}</div>
                <div class="insight-text">{item['text']}</div>
            </div>
            """, unsafe_allow_html=True)


# =========================================================
# TAB 2: DEEP-DIVE ANALYTICS
# =========================================================
with tab_deepdive:
    st.markdown("### 🔍 Granular Product & Category Breakdown")
    
    col_tab_p, col_tab_c = st.columns(2)

    with col_tab_p:
        st.markdown("#### Top Products Performance Table")
        top_prods_all = get_top_selling_products(filtered_df, top_n=20)
        if not top_prods_all.empty:
            display_prods = top_prods_all.copy()
            display_prods["total_revenue"] = display_prods["total_revenue"].apply(lambda v: f"${v:,.2f}")
            display_prods["avg_unit_price"] = display_prods["avg_unit_price"].apply(lambda v: f"${v:,.2f}")
            display_prods["revenue_share_%"] = display_prods["revenue_share_%"].apply(lambda v: f"{v:.1f}%")
            st.dataframe(display_prods, use_container_width=True)

    with col_tab_c:
        st.markdown("#### Category Contribution Table")
        cat_all = get_sales_by_category(filtered_df)
        if not cat_all.empty:
            display_cats = cat_all.copy()
            display_cats["total_revenue"] = display_cats["total_revenue"].apply(lambda v: f"${v:,.2f}")
            display_cats["revenue_share_%"] = display_cats["revenue_share_%"].apply(lambda v: f"{v:.1f}%")
            st.dataframe(display_cats, use_container_width=True)

    st.divider()

    # Monthly breakdown table
    st.markdown("#### 📅 Monthly Performance Summary")
    monthly_full = get_monthly_sales_trend(filtered_df)
    if not monthly_full.empty:
        display_m = monthly_full[["year_month", "month_label", "revenue", "orders", "units_sold", "aov", "revenue_growth_%"]].copy()
        display_m["revenue"] = display_m["revenue"].apply(lambda v: f"${v:,.2f}")
        display_m["aov"] = display_m["aov"].apply(lambda v: f"${v:,.2f}")
        display_m["revenue_growth_%"] = display_m["revenue_growth_%"].apply(
            lambda v: f"{v:+.1f}%" if pd.notna(v) else "-"
        )
        st.dataframe(display_m, use_container_width=True)


# =========================================================
# TAB 3: DATA EXPLORER & AUDIT
# =========================================================
with tab_data_quality:
    st.markdown("### 📋 Data Quality, Cleaning & Raw Records")
    
    # Cleaning metrics cards
    dq1, dq2, dq3, dq4 = st.columns(4)
    dq1.metric("Raw Rows Loaded", f"{cleaning_summary.get('original_rows', len(filtered_df)):,}")
    dq2.metric("Duplicates Removed", f"{cleaning_summary.get('duplicates_removed', 0):,}")
    dq3.metric("Invalid Dates Dropped", f"{cleaning_summary.get('invalid_dates_dropped', 0):,}")
    dq4.metric("Clean Records Active", f"{len(filtered_df):,}")

    if cleaning_summary.get("revenue_calculated_from_qty_price", False):
        st.success("✅ **Revenue Column Formula**: Revenue was computed on the fly using `Quantity * Unit Price`.")

    st.markdown("#### 🔍 Filtered Dataset Records")
    search_term = st.text_input("Quick Search (Filter rows by product, category, customer, etc.):")
    
    table_to_show = filtered_df.copy()
    if search_term:
        mask = table_to_show.astype(str).apply(lambda row: row.str.contains(search_term, case=False).any(), axis=1)
        table_to_show = table_to_show[mask]

    st.dataframe(
        table_to_show.head(100),
        use_container_width=True
    )
    st.caption(f"Showing up to 100 of {len(table_to_show):,} matching records.")


# =========================================================
# TAB 4: BIG DATA EXTENSION (PYSPARK)
# =========================================================
with tab_big_data:
    st.markdown("### ⚡ Big Data Architecture & PySpark Extension")
    st.markdown(
        "SalesSight is built with an enterprise-ready modular design. "
        "The application separates data computation from visual presentation, allowing seamless scaling from **Pandas** to **Apache Spark (PySpark)**."
    )

    pyspark_status = is_pyspark_available()
    if pyspark_status:
        st.success("✅ **PySpark Environment**: PySpark is installed and ready for distributed execution.")
    else:
        st.info("ℹ️ **PySpark Status**: PySpark is optional. The application is running in high-speed Pandas mode. PySpark can be plugged in when analyzing massive cluster-scale datasets.")

    notes = get_big_data_architecture_notes()

    st.markdown(f"#### 🏛️ {notes['title']}")
    st.write(notes["concept"])

    # Comparison Table
    st.markdown("#### ⚖️ Computational Architecture Comparison")
    comp_df = pd.DataFrame(notes["comparison_table"])
    st.table(comp_df)

    # PySpark Code Sample
    st.markdown("#### 💻 Modular Code Implementation (`src/pyspark_extension.py`)")
    with st.expander("View Equivalent PySpark Distributed Aggregations", expanded=False):
        st.code("""
# PySpark Distributed Single-Pass Aggregation
def compute_kpis_spark(spark_df):
    kpi_row = spark_df.agg(
        F.sum("sales").alias("total_revenue"),
        F.countDistinct("order_id").alias("total_orders"),
        F.sum("quantity").alias("total_units"),
    ).collect()[0]

    return {
        "total_revenue": float(kpi_row["total_revenue"] or 0.0),
        "total_orders": int(kpi_row["total_orders"] or 0),
        "total_units": int(kpi_row["total_units"] or 0),
        "aov": float(kpi_row["total_revenue"] / kpi_row["total_orders"]),
    }
        """, language="python")

    # Viva Questions and Answers
    st.markdown("#### 🎓 College Viva & Interview Guide")
    for q_item in notes["viva_questions"]:
        with st.expander(f"❓ {q_item['question']}", expanded=False):
            st.markdown(f"**Answer**: {q_item['answer']}")


# =========================================================
# TAB 5: EXPORT REPORTS
# =========================================================
with tab_export:
    st.markdown("### 📥 Download Analytical Reports (CSV)")
    st.write("Export your filtered sales analytics and aggregated summaries for presentation or spreadsheet audits.")

    exp1, exp2, exp3 = st.columns(3)

    with exp1:
        st.markdown("#### 📄 Filtered Transactions")
        st.caption("Full list of transactions matching current date and category filters.")
        csv_full = filtered_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download Filtered Data (CSV)",
            data=csv_full,
            file_name="salessight_filtered_transactions.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with exp2:
        st.markdown("#### 🏆 Top Products Report")
        st.caption("Aggregated rankings, total revenues, and quantities per product.")
        top_prods_export = get_top_selling_products(filtered_df, top_n=50)
        csv_prods = top_prods_export.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download Top Products (CSV)",
            data=csv_prods,
            file_name="salessight_top_products_report.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with exp3:
        st.markdown("#### 📊 Category & Monthly Summary")
        st.caption("Monthly revenue trends and category market shares.")
        monthly_export = get_monthly_sales_trend(filtered_df)
        csv_monthly = monthly_export.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download Monthly Trend (CSV)",
            data=csv_monthly,
            file_name="salessight_monthly_trend_report.csv",
            mime="text/csv",
            use_container_width=True,
        )

st.markdown("---")
st.caption("SalesSight – Sales Data Analytics Dashboard | Built with Streamlit, Pandas, and Plotly")
