"""Tests for data loader utilities."""

from data.loader import _sanitize_table_name


class TestSanitizeTableName:
    """Test filename to table name conversion."""

    def test_simple_csv(self):
        assert _sanitize_table_name("sales.csv") == "sales"

    def test_spaces_replaced(self):
        assert _sanitize_table_name("Amazon Sale Report.csv") == "amazon_sale_report"

    def test_special_chars_replaced(self):
        assert _sanitize_table_name("P  L March 2021.csv") == "p_l_march_2021"

    def test_xlsx_extension_removed(self):
        assert _sanitize_table_name("report.xlsx") == "report"

    def test_json_extension_removed(self):
        assert _sanitize_table_name("data.json") == "data"

    def test_multiple_underscores_collapsed(self):
        assert _sanitize_table_name("my---file.csv") == "my_file"

    def test_leading_trailing_underscores_stripped(self):
        assert _sanitize_table_name("-file-.csv") == "file"
