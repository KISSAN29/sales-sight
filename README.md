# SalesSight – Sales Data Analytics Dashboard

> **A Modern, Full-Featured Sales Analytics Web Application & College Mini Project**  
> Built with **Python, Streamlit, Pandas, Plotly, and OpenPyXL**, featuring an optional **PySpark Big-Data Extension**.

---

## 📌 Project Overview

**SalesSight** is a comprehensive, interactive business intelligence and sales analytics dashboard designed to help businesses, retail managers, and analysts monitor key performance indicators (KPIs), identify revenue drivers, uncover trends, and make data-driven decisions.

This project was built to balance **real-world software engineering practices** (modular architecture, data validation, automated insights, export reporting) with **beginner-friendly college viva readiness**, ensuring every function and design decision can be effortlessly explained during academic reviews.

---

## 🌟 Key Features

### 1. Executive Analytics Dashboard
- **Real-Time KPIs**: Total Revenue, Total Orders, Total Units Sold, Average Order Value (AOV), and Items per Order.
- **Monthly Revenue Trend**: Interactive Plotly area/line chart with smoothing, tooltips, and chronological sorting.
- **Top 10 Selling Products**: Dynamic horizontal ranking by revenue.
- **Sales by Category**: Interactive donut chart with percentage breakdown.
- **Geographic Breakdown**: Visualizes sales by Region and Country whenever available in the dataset.
- **Automated Insights**: Generates real, computed takeaways (top product share, dominant category, peak month, order ticket size). *Never uses hardcoded mock numbers.*

### 2. Robust Data Ingestion & Validation
- **Multi-Format Support**: Upload `.csv` or Excel (`.xlsx`, `.xls`) files.
- **Built-in Sample Dataset**: Instant one-click exploration using realistic transaction records (`data/sample_sales.csv`).
- **Flexible Column Mapping**: Intelligently identifies various common column aliases (e.g. `InvoiceDate` / `Order Date`, `Item` / `Product Name`, `Sales` / `Revenue`).
- **Intelligent Revenue Calculation**:
  - Automatically calculates `Sales = Quantity * Unit Price` when those columns are present.
  - Automatically verifies and prioritizes existing revenue/sales columns.
- **Data Cleaning & Auditing**:
  - Safely drops duplicate records and logs the count.
  - Coerces dates and drops invalid date rows.
  - Cleans currency symbols (`$`, `€`, `£`, commas) from numeric fields.
  - Fills missing category/product values with clean defaults.

### 3. Deep-Dive Analytics & Search
- Filtered tabular breakdown of product rankings and category shares.
- Real-time search filter for rapid transaction discovery.

### 4. Report Exports
- **CSV Export for Filtered Transactions**
- **CSV Export for Top Selling Products**
- **CSV Export for Monthly Performance Trends**
- **Downloadable CSV Sample Template** directly from the sidebar.

### 5. Big Data & PySpark Extension
- **Modular Decoupling**: Business logic in `src/analytics.py` is written to match the exact contracts of `src/pyspark_extension.py`.
- **Zero-Dependency Core**: PySpark is **completely optional**; the application runs fast on pure Pandas without requiring Java/Spark for normal datasets.
- **Viva-Ready Viva Guide**: Dedicated dashboard tab with architectural comparisons, code mappings, and frequently asked college viva questions.

---

## 🗂️ Project Directory Structure

```text
sales-sight/
│
├── app.py                      # Main Streamlit web application & user interface
├── requirements.txt            # Python dependencies (Streamlit, Pandas, Plotly, OpenPyXL)
├── README.md                   # Comprehensive documentation & college viva guide
├── test_sales_sight.py         # Automated test suite (13 unit & integration tests)
│
├── data/
│   └── sample_sales.csv        # Realistic multi-month retail sales dataset
│
└── src/
    ├── __init__.py             # Package marker
    ├── data_loader.py          # File ingestion, flexible schema standardization, cleaning
    ├── analytics.py            # KPI calculation, trend aggregation, dynamic insights
    └── pyspark_extension.py    # Optional Apache Spark distributed analytics module & notes
```

---

## 🛠️ Technology Stack

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Frontend & UI** | Streamlit | Responsive, modern web dashboard with sidebar filters and tabs |
| **Data Manipulation** | Pandas | High-performance in-memory DataFrame transformations and cleaning |
| **Data Visualizations** | Plotly & Plotly Express | Interactive charts (hover tooltips, zooming, responsive layouts) |
| **File Formats** | OpenPyXL | Excel (`.xlsx`) parsing and reading |
| **Big Data (Optional)** | PySpark | Distributed cluster processing adapter for large-scale datasets |
| **Language** | Python 3.10+ | Core implementation |

---

## 🚀 Installation & Launch Guide

### Step 1: Open Terminal in the Project Directory
```powershell
cd "C:\Users\ADMIN\.gemini\antigravity\scratch\sales-sight"
```

### Step 2: Install Dependencies
Install all required libraries using `pip`:
```powershell
py -m pip install -r requirements.txt
```

*(Streamlit, Pandas, Plotly, and OpenPyXL are included. PySpark is optional and commented out by default).*

### Step 3: Run the Automated Test Suite
Verify that all data loading, standardization, and analytic aggregations pass:
```powershell
py test_sales_sight.py
```
*Expected Output: `ALL 13 TESTS PASSED SUCCESSFULLY! [OK]`*

### Step 4: Launch the Streamlit Web Application
```powershell
py -m streamlit run app.py
```

The web dashboard will automatically open in your default browser at:
```text
http://localhost:8501
```

---

## 📊 Dataset Schema & Column Aliases

SalesSight accepts any CSV or Excel file containing sales data. It uses smart column mapping so your column headers don't have to match exact names:

| Canonical Field | Recognized Aliases | Required? |
| :--- | :--- | :--- |
| **`order_date`** | `Order Date`, `Date`, `InvoiceDate`, `Transaction_Date` | **Yes** |
| **`product`** | `Product Name`, `Product`, `Item`, `Description`, `Title` | **Yes** (or Category) |
| **`category`** | `Category`, `Product Category`, `Department`, `Type` | Optional |
| **`sales`** | `Sales`, `Revenue`, `Total Amount`, `Total`, `Amount` | **Yes** (or Qty + Price) |
| **`quantity`** | `Quantity`, `Qty`, `Units`, `Units_Sold`, `Count` | Optional (used for revenue fallback) |
| **`unit_price`** | `Unit Price`, `Price`, `Rate`, `Price_Per_Unit` | Optional (used for revenue fallback) |
| **`region`** | `Region`, `Area`, `Territory`, `Zone` | Optional (enables regional chart) |
| **`country`** | `Country`, `Country_Name`, `Nation` | Optional (enables country chart) |
| **`order_id`** | `Order ID`, `OrderID`, `InvoiceNo`, `Transaction_ID` | Optional (auto-generated if missing) |

---

## 🎓 College Viva & Interview Guide

If presenting this project for a college viva or evaluation, here are answers to key questions examiners frequently ask:

### 1. What is the architecture of the project?
> *"SalesSight follows a **Modular 3-Tier Layered Architecture**:*
> 1. ***Ingestion & Cleaning Layer (`src/data_loader.py`)***: *Loads files, normalizes flexible column synonyms, removes duplicates, validates date/numeric datatypes, and computes revenue.*
> 2. ***Analytics & Business Logic Layer (`src/analytics.py`)***: *Pure Python/Pandas functions for KPIs, time-series trends, and automated insight generation. Keeps computation completely separate from presentation.*
> 3. ***Presentation Layer (`app.py`)***: *Streamlit UI with Plotly visualizations, reactive sidebar filtering, and report downloads."*

### 2. How is revenue calculated if the dataset doesn't have a 'Sales' column?
> *"In `src/data_loader.py`, the `clean_dataset()` function detects if a direct sales column is missing. If both `Quantity` and `Unit Price` are present, it computes `Sales = Quantity * Unit Price`. If a sales column already exists, it validates it and only uses the fallback calculation if missing or corrupt values occur."*

### 3. How does this project handle Big Data? Where does PySpark fit in?
> *"Pandas is an in-memory single-node library, which works exceptionally well for datasets under 4–8 GB. For enterprise datasets with millions or billions of rows (hundreds of gigabytes or terabytes), Pandas exceeds available RAM.  
> To demonstrate big-data readiness, we created `src/pyspark_extension.py`. It implements the exact same aggregation contracts (`compute_kpis`, `monthly_trend`, `top_products`) using Apache Spark's distributed DataFrame API. PySpark uses distributed partitions across a cluster and lazy evaluation with the Catalyst Optimizer, so the architecture is future-proof."*

### 4. How did you ensure data integrity?
> *"We implemented automated deduplication (`drop_duplicates()`), date error coercion (`pd.to_datetime(..., errors='coerce')`), string currency stripping (`$`, `€`, commas), and an empty state banner that prevents displaying hardcoded or incorrect metrics."*

---

## 👥 Authors & Academic Credits
- **Project**: SalesSight – Sales Data Analytics Dashboard
- **Purpose**: College Mini Project / Practical Demonstration
- **License**: MIT Open Source
