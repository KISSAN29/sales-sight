"""
SalesSight - Big Data & PySpark Extension Module
Demonstrates modular design pattern for scaling from Pandas to Apache Spark.
PySpark is completely OPTIONAL and not required for the basic dashboard.
"""

from typing import Any, Dict, Optional, Tuple

# Safe optional import of PySpark
try:
    import pyspark
    from pyspark.sql import SparkSession
    from pyspark.sql import functions as F
    PYSPARK_AVAILABLE = True
    PYSPARK_ERROR = None
except ImportError as e:
    PYSPARK_AVAILABLE = False
    PYSPARK_ERROR = str(e)


def is_pyspark_available() -> bool:
    """Return True if PySpark is installed and available in the environment."""
    return PYSPARK_AVAILABLE


class PySparkSalesAnalytics:
    """
    Modular PySpark implementation of the analytics engine.
    Mirrors the aggregation contracts used in src/analytics.py,
    enabling distributed processing on multi-gigabyte or terabyte sales logs.
    """

    def __init__(self, app_name: str = "SalesSight-BigData"):
        if not PYSPARK_AVAILABLE:
            raise RuntimeError(
                f"PySpark is not installed in this environment ({PYSPARK_ERROR}). "
                "Install using: pip install pyspark"
            )
        self.spark = (
            SparkSession.builder
            .appName(app_name)
            .config("spark.sql.execution.arrow.pyspark.enabled", "true")
            .getOrCreate()
        )

    def load_dataset(self, file_path: str):
        """Loads a large CSV or Parquet dataset into a distributed DataFrame."""
        if file_path.endswith(".parquet"):
            return self.spark.read.parquet(file_path)
        return self.spark.read.option("header", "true").option("inferSchema", "true").csv(file_path)

    def compute_kpis(self, df) -> Dict[str, Any]:
        """
        Calculates KPIs using distributed Spark aggregations.
        Uses single-pass aggregation for performance on clusters.
        """
        kpi_row = df.agg(
            F.sum("sales").alias("total_revenue"),
            F.countDistinct("order_id").alias("total_orders"),
            F.sum("quantity").alias("total_units"),
        ).collect()[0]

        revenue = float(kpi_row["total_revenue"] or 0.0)
        orders = int(kpi_row["total_orders"] or 0)
        units = int(kpi_row["total_units"] or 0)
        aov = (revenue / orders) if orders > 0 else 0.0

        return {
            "total_revenue": revenue,
            "total_orders": orders,
            "total_units": units,
            "aov": aov,
            "engine": "Apache Spark (Distributed)",
        }

    def monthly_trend(self, df):
        """Computes monthly sales trend using Spark SQL functions."""
        return (
            df.withColumn("year_month", F.date_format("order_date", "yyyy-MM"))
            .groupBy("year_month")
            .agg(
                F.sum("sales").alias("revenue"),
                F.countDistinct("order_id").alias("orders"),
                F.sum("quantity").alias("units_sold"),
            )
            .orderBy("year_month")
        )

    def top_products(self, df, top_n: int = 10):
        """Computes top products using Spark DataFrame groupBy and orderBy."""
        return (
            df.groupBy("product", "category")
            .agg(
                F.sum("sales").alias("total_revenue"),
                F.sum("quantity").alias("units_sold"),
                F.countDistinct("order_id").alias("total_orders"),
            )
            .orderBy(F.col("total_revenue").desc())
            .limit(top_n)
        )


def get_big_data_architecture_notes() -> Dict[str, Any]:
    """
    Returns structured viva / technical explanation details about the
    big data architecture and how SalesSight bridges Pandas and PySpark.
    """
    return {
        "title": "Scalability Architecture: Pandas vs. PySpark",
        "concept": (
            "SalesSight is architected with a decoupled analytics layer. "
            "For small to medium datasets (<5GB), it uses Pandas for immediate in-memory analysis. "
            "For enterprise datasets (10GB - Terabytes), the identical business logic plugs into PySpark."
        ),
        "comparison_table": [
            {
                "Attribute": "Dataset Size Limit",
                "Pandas (Current Default)": "Single-node RAM bound (typically < 4-8 GB)",
                "PySpark (Big Data Extension)": "Distributed cluster memory / disk (Terabytes+)"
            },
            {
                "Attribute": "Execution Model",
                "Pandas (Current Default)": "Eager execution (immediate calculation in Python)",
                "PySpark (Big Data Extension)": "Lazy evaluation (DAG build, Catalyst Optimizer)"
            },
            {
                "Attribute": "Compute Architecture",
                "Pandas (Current Default)": "Single CPU core / thread by default",
                "PySpark (Big Data Extension)": "Master-Worker cluster with distributed partitions"
            },
            {
                "Attribute": "Deployment Footprint",
                "Pandas (Current Default)": "Zero-overhead, pure Python library",
                "PySpark (Big Data Extension)": "Requires Java JVM & Spark cluster manager"
            },
        ],
        "viva_questions": [
            {
                "question": "Why didn't we make PySpark mandatory for this dashboard?",
                "answer": "PySpark requires a Java Runtime Environment (JRE/JDK) and cluster configuration. Making it mandatory would complicate basic installation for college evaluation while adding unnecessary memory overhead for typical department datasets (< 100MB)."
            },
            {
                "question": "How did you design the code to allow swapping PySpark without rewriting the UI?",
                "answer": "We implemented a modular Service/Adapter architecture. Both src/analytics.py and src/pyspark_extension.py expose the same aggregation interfaces (compute_kpis, monthly_trend, top_products). The Streamlit frontend consumes plain tabular dictionaries, regardless of the compute engine underneath."
            },
            {
                "question": "What is PySpark Lazy Evaluation?",
                "answer": "In PySpark, transformations like groupBy() or filter() do not execute immediately. Instead, Spark builds a Directed Acyclic Graph (DAG) and optimizes the query execution plan using the Catalyst Optimizer. Execution only occurs when an action like collect(), show(), or count() is invoked."
            }
        ]
    }
