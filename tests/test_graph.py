"""Tests for LangGraph routing functions."""

from agents.graph import after_guard, should_retry
from langgraph.graph import END


class TestAfterGuard:
    """Test prompt guard routing logic."""

    def test_blocked_returns_end(self):
        state = {"control": {"blocked": True}}
        assert after_guard(state) == END

    def test_safe_returns_query_understanding(self):
        state = {"control": {"blocked": False}}
        assert after_guard(state) == "query_understanding"

    def test_missing_blocked_defaults_to_safe(self):
        state = {"control": {}}
        assert after_guard(state) == "query_understanding"


class TestShouldRetry:
    """Test validation retry routing logic."""

    def test_needs_retry_returns_data_extraction(self):
        state = {"control": {"needs_retry": True}}
        assert should_retry(state) == "data_extraction"

    def test_no_retry_returns_end(self):
        state = {"control": {"needs_retry": False}}
        assert should_retry(state) == END

    def test_missing_needs_retry_defaults_to_end(self):
        state = {"control": {}}
        assert should_retry(state) == END
