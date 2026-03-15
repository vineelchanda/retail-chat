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

import duckdb
import os


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

    # --- 2. International Sales (37K rows) - B2B sales with customers ---
    con.execute(f"""
        CREATE TABLE international_sales AS
        SELECT * FROM read_csv_auto('{data_dir}/International sale Report.csv')
    """)
    con.execute("ALTER TABLE international_sales DROP COLUMN IF EXISTS index")
    con.execute('ALTER TABLE international_sales RENAME COLUMN "GROSS AMT" TO gross_amt')

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

    return con
