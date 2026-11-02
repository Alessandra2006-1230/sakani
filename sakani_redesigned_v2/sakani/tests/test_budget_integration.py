"""Integration tests for budget overlap validation using real database."""

import unittest
import os
import sys

# Ensure the database password is set
if "SAKANI_DB_PASSWORD" not in os.environ:
    raise unittest.SkipTest("SAKANI_DB_PASSWORD not set, skipping integration tests")

from models import budget
from database import queries
from datetime import date
from decimal import Decimal


class TestBudgetOverlapIntegration(unittest.TestCase):
    """Test budget overlap validation with real database."""

    @classmethod
    def setUpClass(cls):
        cls.user_id = 2  # Test user
        cls.category_id = 5  # Seeds category
        # Clean up any existing test budgets
        cls._cleanup_test_budgets()

    @classmethod
    def tearDownClass(cls):
        cls._cleanup_test_budgets()

    @classmethod
    def _cleanup_test_budgets(cls):
        """Remove test budgets created during testing."""
        try:
            budgets = queries.get_budgets(cls.user_id)
            for b in budgets:
                if b["name"].startswith("Test ") or b["name"].startswith("Overlap ") or b["name"].startswith("Adj ") or b["name"].startswith("Cat ") or b["name"].startswith("Wide ") or b["name"].startswith("User ") or b["name"].startswith("Original "):
                    queries.delete_budget(b["id"], cls.user_id)
        except Exception:
            pass

    def setUp(self):
        self._cleanup_test_budgets()

    def test_overlapping_budget_same_category_same_dates(self):
        """Two budgets for same category and same dates should be rejected."""
        # First create a budget in the database
        bid1 = queries.add_budget(self.user_id, "Overlap Test 1", self.category_id,
                                  Decimal("500.00"), "monthly",
                                  date(2026, 10, 1), date(2026, 10, 31), "Test")

        # Now try to validate a second budget with same category and dates
        data2 = {"name": "Overlap Test 2", "amount": "300.00", "period_type": "monthly",
                 "start_date": "2026-10-01", "end_date": "2026-10-31", "category_id": self.category_id}
        ok, message, _values = budget.validate_budget(data2, user_id=self.user_id, exclude_id=None)
        self.assertFalse(ok, "Second budget with same category and dates should be rejected")
        self.assertIn("overlapping", message.lower())

        queries.delete_budget(bid1, self.user_id)

    def test_overlapping_budget_partial_overlap(self):
        """Budget with partially overlapping dates should be rejected."""
        # First create a budget in the database
        bid1 = queries.add_budget(self.user_id, "Overlap Test 1", self.category_id,
                                  Decimal("500.00"), "monthly",
                                  date(2026, 10, 1), date(2026, 10, 31), "Test")

        # Second budget overlaps at the end of the first
        data2 = {"name": "Overlap Test 2", "amount": "300.00", "period_type": "monthly",
                 "start_date": "2026-10-15", "end_date": "2026-11-15", "category_id": self.category_id}
        ok, message, _values = budget.validate_budget(data2, user_id=self.user_id, exclude_id=None)
        self.assertFalse(ok, "Partially overlapping budget should be rejected")
        self.assertIn("overlapping", message.lower())

        queries.delete_budget(bid1, self.user_id)

    def test_adjacent_budgets_allowed(self):
        """Budgets with adjacent dates should be allowed."""
        # First create a budget in the database
        bid1 = queries.add_budget(self.user_id, "Adj Test 1", self.category_id,
                                  Decimal("500.00"), "monthly",
                                  date(2026, 10, 1), date(2026, 10, 31), "Test")

        # Adjacent budget starts right after first ends
        data2 = {"name": "Adj Test 2", "amount": "300.00", "period_type": "monthly",
                 "start_date": "2026-11-01", "end_date": "2026-11-30", "category_id": self.category_id}
        ok, message, _values = budget.validate_budget(data2, user_id=self.user_id, exclude_id=None)
        self.assertTrue(ok, "Adjacent non-overlapping budgets should be allowed")

        queries.delete_budget(bid1, self.user_id)

    def test_different_categories_allowed(self):
        """Budgets for different categories with same dates should be allowed."""
        # First create a budget in the database
        bid1 = queries.add_budget(self.user_id, "Cat Test 1", self.category_id,
                                  Decimal("500.00"), "monthly",
                                  date(2026, 10, 1), date(2026, 10, 31), "Test")

        # Different category, same dates
        data2 = {"name": "Cat Test 2", "amount": "300.00", "period_type": "monthly",
                 "start_date": "2026-10-01", "end_date": "2026-10-31", "category_id": 6}  # Fertilizer
        ok, message, _values = budget.validate_budget(data2, user_id=self.user_id, exclude_id=None)
        self.assertTrue(ok, "Different categories with same dates should be allowed")

        queries.delete_budget(bid1, self.user_id)

    def test_different_users_allowed(self):
        """Same category and dates for different users should be allowed."""
        # First create a budget for user 2
        bid1 = queries.add_budget(2, "User Test 1", self.category_id,
                                  Decimal("500.00"), "monthly",
                                  date(2026, 10, 1), date(2026, 10, 31), "Test")

        # Same for different user (user 1)
        data2 = {"name": "User Test 2", "amount": "300.00", "period_type": "monthly",
                 "start_date": "2026-10-01", "end_date": "2026-10-31", "category_id": self.category_id}
        ok, message, _values = budget.validate_budget(data2, user_id=1, exclude_id=None)
        self.assertTrue(ok, "Different users with same category/dates should be allowed")

        queries.delete_budget(bid1, 2)

    def test_category_wide_budget_overlap(self):
        """Category-wide budgets (NULL category) should not overlap with each other."""
        # First create a category-wide budget in the database
        bid1 = queries.add_budget(self.user_id, "Wide Test 1", None,
                                  Decimal("500.00"), "monthly",
                                  date(2026, 10, 1), date(2026, 10, 31), "Test")

        # Second category-wide budget with same dates
        data2 = {"name": "Wide Test 2", "amount": "300.00", "period_type": "monthly",
                 "start_date": "2026-10-01", "end_date": "2026-10-31", "category_id": None}
        ok, message, _values = budget.validate_budget(data2, user_id=self.user_id, exclude_id=None)
        self.assertFalse(ok, "Overlapping category-wide budgets should be rejected")
        self.assertIn("overlapping", message.lower())

        queries.delete_budget(bid1, self.user_id)

    def test_category_specific_vs_category_wide(self):
        """Category-specific and category-wide budgets are separate - both can exist."""
        # First create a category-specific budget in the database
        bid1 = queries.add_budget(self.user_id, "Cat Specific", self.category_id,
                                  Decimal("500.00"), "monthly",
                                  date(2026, 10, 1), date(2026, 10, 31), "Test")

        # Category-wide budget with same dates - should be allowed since they're different category_id
        data2 = {"name": "Wide Budget", "amount": "300.00", "period_type": "monthly",
                 "start_date": "2026-10-01", "end_date": "2026-10-31", "category_id": None}
        ok, message, _values = budget.validate_budget(data2, user_id=self.user_id, exclude_id=None)
        self.assertTrue(ok, "Category-specific and category-wide budgets should both be allowed")

        queries.delete_budget(bid1, self.user_id)

    def test_edit_budget_excludes_self(self):
        """Editing a budget should not flag itself as an overlap."""
        # First create a budget
        bid = queries.add_budget(self.user_id, "Original Budget", self.category_id,
                                 Decimal("500.00"), "monthly",
                                 date(2026, 10, 1), date(2026, 10, 31), "Test")
        self.assertIsNotNone(bid)

        # Now edit with same dates - should be allowed since exclude_id matches
        data2 = {"name": "Updated Budget", "amount": "600.00", "period_type": "monthly",
                 "start_date": "2026-10-01", "end_date": "2026-10-31", "category_id": self.category_id}
        ok, message, _values = budget.validate_budget(data2, user_id=self.user_id, exclude_id=bid)
        self.assertTrue(ok, "Editing budget with same dates should be allowed when exclude_id is set")
        queries.delete_budget(bid, self.user_id)


if __name__ == "__main__":
    unittest.main()
