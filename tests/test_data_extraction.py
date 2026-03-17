"""Tests for the data extraction agent's SQL sanitization."""

from agents.data_extraction import sanitize_sql


class TestSanitizeSQL:
    """Test SQL sanitization blocks dangerous statements."""

    def test_blocks_drop_table(self):
        assert sanitize_sql("DROP TABLE amazon_sales") is not None

    def test_blocks_delete_from(self):
        assert sanitize_sql("DELETE FROM inventory WHERE 1=1") is not None

    def test_blocks_alter_table(self):
        assert sanitize_sql("ALTER TABLE amazon_sales ADD COLUMN x INT") is not None

    def test_blocks_truncate(self):
        assert sanitize_sql("TRUNCATE TABLE amazon_sales") is not None

    def test_blocks_insert_into(self):
        assert sanitize_sql("INSERT INTO amazon_sales VALUES (1,2,3)") is not None

    def test_blocks_update_set(self):
        assert sanitize_sql("UPDATE amazon_sales SET Amount = 0") is not None

    def test_blocks_create_table(self):
        assert sanitize_sql("CREATE TABLE hack AS SELECT * FROM amazon_sales") is not None

    def test_blocks_grant(self):
        assert sanitize_sql("GRANT ALL ON amazon_sales TO public") is not None

    def test_blocks_revoke(self):
        assert sanitize_sql("REVOKE SELECT ON amazon_sales FROM user1") is not None

    def test_allows_select(self):
        assert sanitize_sql("SELECT * FROM amazon_sales LIMIT 10") is None

    def test_allows_select_with_where(self):
        sql = "SELECT Category, COUNT(*) AS cnt FROM amazon_sales WHERE Status = 'Shipped' GROUP BY Category"
        assert sanitize_sql(sql) is None

    def test_allows_select_with_join(self):
        sql = "SELECT a.order_id, b.gross_amt FROM amazon_sales a JOIN international_sales b ON a.order_id = b.order_id"
        assert sanitize_sql(sql) is None

    def test_allows_cte_query(self):
        sql = "WITH revenue AS (SELECT Category, SUM(Amount) AS total FROM amazon_sales GROUP BY Category) SELECT * FROM revenue LIMIT 5"
        assert sanitize_sql(sql) is None

    def test_allows_aggregate_functions(self):
        sql = "SELECT COUNT(*), SUM(Amount), AVG(Amount) FROM amazon_sales"
        assert sanitize_sql(sql) is None

    def test_case_insensitive_block(self):
        assert sanitize_sql("drop table amazon_sales") is not None

    def test_mixed_case_block(self):
        assert sanitize_sql("DrOp TaBlE amazon_sales") is not None
