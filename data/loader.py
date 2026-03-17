"""
Loads CSV files into DuckDB in-memory database and performs cleaning.

HOW IT WORKS:
1. Creates an in-memory DuckDB connection
2. Uses DuckDB's read_csv_auto to load each CSV (auto-detects types)
3. Runs cleaning SQL to fix column names, drop junk columns, parse dates
4. Returns the connection for querying

WHY DuckDB?
- Reads CSVs directly with zero setup (no server, no config)
- SQL interface — same language the LLM will generate
- Extremely fast for analytical queries (columnar engine)
- In-memory mode perfect for datasets under 1GB
"""

import re
import duckdb
import os
import pandas as pd
import logging

logger = logging.getLogger(__name__)


def load_all_data(data_dir: str = "Sales Dataset") -> duckdb.DuckDBPyConnection:
    """Load all CSV files into DuckDB tables and clean them."""
    con = duckdb.connect(":memory:")

    # --- 1. Amazon Sales (128K rows) - Core transaction data ---
    con.execute(f"""
        CREATE TABLE amazon_sales AS
        SELECT * FROM read_csv_auto('{data_dir}/Amazon Sale Report.csv')
    """)
    # Drop junk columns
    con.execute('ALTER TABLE amazon_sales DROP COLUMN IF EXISTS "Unnamed: 22"')
    con.execute("ALTER TABLE amazon_sales DROP COLUMN IF EXISTS index")
    # Rename hyphenated columns to underscored (DuckDB requires quotes for hyphens)
    con.execute('ALTER TABLE amazon_sales RENAME COLUMN "ship-service-level" TO ship_service_level')
    con.execute('ALTER TABLE amazon_sales RENAME COLUMN "ship-city" TO ship_city')
    con.execute('ALTER TABLE amazon_sales RENAME COLUMN "ship-state" TO ship_state')
    con.execute('ALTER TABLE amazon_sales RENAME COLUMN "ship-postal-code" TO ship_postal_code')
    con.execute('ALTER TABLE amazon_sales RENAME COLUMN "ship-country" TO ship_country')
    con.execute('ALTER TABLE amazon_sales RENAME COLUMN "promotion-ids" TO promotion_ids')
    # Column name may have trailing space or not depending on CSV parsing
    try:
        con.execute('ALTER TABLE amazon_sales RENAME COLUMN "Sales Channel " TO sales_channel')
    except Exception:
        con.execute('ALTER TABLE amazon_sales RENAME COLUMN "Sales Channel" TO sales_channel')
    con.execute('ALTER TABLE amazon_sales RENAME COLUMN "Order ID" TO order_id')
    con.execute('ALTER TABLE amazon_sales RENAME COLUMN "Courier Status" TO courier_status')
    con.execute('ALTER TABLE amazon_sales RENAME COLUMN "fulfilled-by" TO fulfilled_by')
    # Standardize city names to uppercase
    con.execute("UPDATE amazon_sales SET ship_city = UPPER(ship_city)")
    # Fix postal code: DOUBLE -> VARCHAR (preserve leading zeros, drop .0)
    con.execute("""
        ALTER TABLE amazon_sales ALTER COLUMN ship_postal_code
        SET DATA TYPE VARCHAR USING CAST(CAST(ship_postal_code AS BIGINT) AS VARCHAR)
    """)

    # --- 2. International Sales - B2B sales with customers ---
    _load_international_sales(con, data_dir)

    # --- 3. Inventory / Stock (9K rows) - Stock levels by SKU ---
    con.execute(f"""
        CREATE TABLE inventory AS
        SELECT * FROM read_csv_auto('{data_dir}/Sale Report.csv')
    """)
    con.execute("ALTER TABLE inventory DROP COLUMN IF EXISTS index")
    con.execute('ALTER TABLE inventory RENAME COLUMN "SKU Code" TO sku_code')
    con.execute('ALTER TABLE inventory RENAME COLUMN "Design No." TO design_no')

    # --- 4. Product Pricing March 2021 (1.3K rows) ---
    con.execute(f"""
        CREATE TABLE product_pricing_2021 AS
        SELECT * FROM read_csv_auto('{data_dir}/P  L March 2021.csv')
    """)
    con.execute("ALTER TABLE product_pricing_2021 DROP COLUMN IF EXISTS index")
    con.execute('ALTER TABLE product_pricing_2021 RENAME COLUMN "Style Id" TO style_id')
    con.execute('ALTER TABLE product_pricing_2021 RENAME COLUMN "MRP Old" TO mrp_old')
    con.execute('ALTER TABLE product_pricing_2021 RENAME COLUMN "Final MRP Old" TO final_mrp_old')
    con.execute('ALTER TABLE product_pricing_2021 RENAME COLUMN "Ajio MRP" TO ajio_mrp')
    con.execute('ALTER TABLE product_pricing_2021 RENAME COLUMN "Amazon MRP" TO amazon_mrp')
    con.execute('ALTER TABLE product_pricing_2021 RENAME COLUMN "Amazon FBA MRP" TO amazon_fba_mrp')
    con.execute('ALTER TABLE product_pricing_2021 RENAME COLUMN "Flipkart MRP" TO flipkart_mrp')
    con.execute('ALTER TABLE product_pricing_2021 RENAME COLUMN "Limeroad MRP" TO limeroad_mrp')
    con.execute('ALTER TABLE product_pricing_2021 RENAME COLUMN "Myntra MRP" TO myntra_mrp')
    con.execute('ALTER TABLE product_pricing_2021 RENAME COLUMN "Paytm MRP" TO paytm_mrp')
    con.execute('ALTER TABLE product_pricing_2021 RENAME COLUMN "Snapdeal MRP" TO snapdeal_mrp')
    con.execute('ALTER TABLE product_pricing_2021 RENAME COLUMN "TP 1" TO tp_1')
    con.execute('ALTER TABLE product_pricing_2021 RENAME COLUMN "TP 2" TO tp_2')
    _clean_pricing_table(con, 'product_pricing_2021',
                         ['Weight', 'tp_1', 'tp_2', 'mrp_old', 'final_mrp_old',
                          'ajio_mrp', 'amazon_mrp', 'amazon_fba_mrp', 'flipkart_mrp',
                          'limeroad_mrp', 'myntra_mrp', 'paytm_mrp', 'snapdeal_mrp'])

    # --- 5. Product Pricing May 2022 (1.3K rows) ---
    con.execute(f"""
        CREATE TABLE product_pricing_2022 AS
        SELECT * FROM read_csv_auto('{data_dir}/May-2022.csv')
    """)
    con.execute("ALTER TABLE product_pricing_2022 DROP COLUMN IF EXISTS index")
    con.execute('ALTER TABLE product_pricing_2022 RENAME COLUMN "Style Id" TO style_id')
    con.execute('ALTER TABLE product_pricing_2022 RENAME COLUMN "MRP Old" TO mrp_old')
    con.execute('ALTER TABLE product_pricing_2022 RENAME COLUMN "Final MRP Old" TO final_mrp_old')
    con.execute('ALTER TABLE product_pricing_2022 RENAME COLUMN "Ajio MRP" TO ajio_mrp')
    con.execute('ALTER TABLE product_pricing_2022 RENAME COLUMN "Amazon MRP" TO amazon_mrp')
    con.execute('ALTER TABLE product_pricing_2022 RENAME COLUMN "Amazon FBA MRP" TO amazon_fba_mrp')
    con.execute('ALTER TABLE product_pricing_2022 RENAME COLUMN "Flipkart MRP" TO flipkart_mrp')
    con.execute('ALTER TABLE product_pricing_2022 RENAME COLUMN "Limeroad MRP" TO limeroad_mrp')
    con.execute('ALTER TABLE product_pricing_2022 RENAME COLUMN "Myntra MRP" TO myntra_mrp')
    con.execute('ALTER TABLE product_pricing_2022 RENAME COLUMN "Paytm MRP" TO paytm_mrp')
    con.execute('ALTER TABLE product_pricing_2022 RENAME COLUMN "Snapdeal MRP" TO snapdeal_mrp')
    _clean_pricing_table(con, 'product_pricing_2022',
                         ['Weight', 'TP', 'mrp_old', 'final_mrp_old',
                          'ajio_mrp', 'amazon_mrp', 'amazon_fba_mrp', 'flipkart_mrp',
                          'limeroad_mrp', 'myntra_mrp', 'paytm_mrp', 'snapdeal_mrp'])

    return con


def _load_international_sales(con: duckdb.DuckDBPyConnection, data_dir: str):
    """Load international sales CSV which contains 3 embedded sections.

    Section 1 (rows 0-18633): Clean sales data.
    Section 2 (rows 18634-19675): Junk (embedded SKU/Stock lists).
    Section 3 (rows 19676+): Sales data with shifted columns (CUSTOMER before DATE).
    """
    filepath = os.path.join(data_dir, "International sale Report.csv")

    # Section 1: first 18634 data rows with correct column order
    section1 = pd.read_csv(filepath, nrows=18634)
    section1 = section1.drop(columns=["index"], errors="ignore")

    # Section 3: skip header + section1 + section2 + section3 header (19677 lines)
    # Section 3 columns: index, CUSTOMER, DATE, Months, Style, SKU, PCS, RATE, GROSS AMT, Stock
    section3 = pd.read_csv(filepath, skiprows=19677, header=None,
                           names=["index", "CUSTOMER", "DATE", "Months", "Style", "SKU",
                                  "PCS", "RATE", "GROSS AMT", "Stock"])
    section3 = section3.drop(columns=["index", "Stock"], errors="ignore")
    section3["Size"] = None
    # Reorder to match section 1 columns
    section3 = section3[["DATE", "Months", "CUSTOMER", "Style", "SKU", "Size",
                         "PCS", "RATE", "GROSS AMT"]]

    # Combine both sections
    df = pd.concat([section1, section3], ignore_index=True)

    # Clean and cast types
    df["CUSTOMER"] = df["CUSTOMER"].str.strip()
    df["DATE"] = pd.to_datetime(df["DATE"], format="%m-%d-%y", errors="coerce")
    for col in ["PCS", "RATE", "GROSS AMT"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Rename for cleaner column names
    df = df.rename(columns={"GROSS AMT": "gross_amt"})

    # Register in DuckDB
    con.register("_intl_df", df)
    con.execute("CREATE TABLE international_sales AS SELECT * FROM _intl_df")
    con.unregister("_intl_df")
    logger.info("Loaded international_sales: %d rows", len(df))


def _clean_pricing_table(con: duckdb.DuckDBPyConnection, table_name: str,
                         price_cols: list[str]):
    """Replace non-numeric values with NULL and cast price/weight columns to DOUBLE."""
    # Null out non-numeric values (Nill, #VALUE!, etc.) in price columns
    for col in price_cols:
        con.execute(f"""
            UPDATE {table_name} SET "{col}" = NULL
            WHERE TRY_CAST("{col}" AS DOUBLE) IS NULL AND "{col}" IS NOT NULL
        """)
        con.execute(f"""
            ALTER TABLE {table_name} ALTER COLUMN "{col}"
            SET DATA TYPE DOUBLE USING CAST("{col}" AS DOUBLE)
        """)
    # Also null out 'Nill' in text columns like Catalog, Category
    columns = con.execute(f"DESCRIBE {table_name}").fetchall()
    for col_name, col_type, *_ in columns:
        if "VARCHAR" in col_type:
            con.execute(f'UPDATE {table_name} SET "{col_name}" = NULL '
                        f"WHERE \"{col_name}\" = 'Nill'")


def _sanitize_table_name(filename: str) -> str:
    """Convert a filename into a valid DuckDB table name."""
    name = os.path.splitext(filename)[0]
    name = re.sub(r"[^a-zA-Z0-9]", "_", name)
    name = re.sub(r"_+", "_", name).strip("_").lower()
    return name


def load_uploaded_file(con: duckdb.DuckDBPyConnection, uploaded_file) -> str:
    """Load an uploaded file (CSV, Excel, JSON, or text) into DuckDB.

    Returns the table name created.
    """
    filename = uploaded_file.name
    table_name = _sanitize_table_name(filename)
    ext = os.path.splitext(filename)[1].lower()

    if ext == ".csv":
        df = pd.read_csv(uploaded_file)
    elif ext == ".xlsx":
        df = pd.read_excel(uploaded_file, engine="openpyxl")
    elif ext == ".json":
        df = pd.read_json(uploaded_file)
    elif ext == ".txt":
        # Try tab-delimited first, fall back to comma-delimited
        content = uploaded_file.read().decode("utf-8")
        uploaded_file.seek(0)
        if "\t" in content[:1000]:
            df = pd.read_csv(uploaded_file, sep="\t")
        else:
            df = pd.read_csv(uploaded_file, sep=",")
    else:
        raise ValueError(f"Unsupported file type: {ext}")

    # Clean column names: replace spaces and special chars with underscores
    df.columns = [re.sub(r"[^a-zA-Z0-9]", "_", c).strip("_") for c in df.columns]

    con.register(f"{table_name}_df", df)
    con.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM {table_name}_df")
    con.unregister(f"{table_name}_df")

    row_count = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
    logger.info("Loaded uploaded file '%s' as table '%s' (%d rows)", filename, table_name, row_count)
    return table_name
