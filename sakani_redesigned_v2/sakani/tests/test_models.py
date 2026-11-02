"""Unit tests for Sakani authentication helpers and validators."""

import unittest

from models import auth, budget, breakeven, cycle, validators


class TestPasswordHashing(unittest.TestCase):
    def test_hash_and_verify_roundtrip(self):
        password_hash, salt = auth.hash_password("correct horse battery")
        self.assertTrue(auth.verify_password("correct horse battery", password_hash, salt))

    def test_wrong_password_fails(self):
        password_hash, salt = auth.hash_password("correct horse battery")
        self.assertFalse(auth.verify_password("wrong horse battery", password_hash, salt))

    def test_salt_is_random_per_hash(self):
        first_hash, first_salt = auth.hash_password("same-password")
        second_hash, second_salt = auth.hash_password("same-password")
        self.assertNotEqual(first_salt, second_salt)
        self.assertNotEqual(first_hash, second_hash)

    def test_verify_with_stored_salt_format(self):
        digest, salt = auth.hash_password("mypassword")
        self.assertTrue(auth.verify_password("mypassword", digest, salt))


class TestSignupValidation(unittest.TestCase):
    def test_valid_signup(self):
        ok, message = auth.validate_signup("Juan Dela Cruz", "juan@example.com", "password123", "password123")
        self.assertTrue(ok, message)

    def test_mismatched_passwords(self):
        ok, _message = auth.validate_signup("Juan", "juan@example.com", "password123", "password456")
        self.assertFalse(ok)

    def test_short_password_rejected(self):
        ok, _message = auth.validate_signup("Juan", "juan@example.com", "short", "short")
        self.assertFalse(ok)

    def test_missing_name_rejected(self):
        ok, _message = auth.validate_signup("  ", "juan@example.com", "password123", "password123")
        self.assertFalse(ok)


class TestLoginValidation(unittest.TestCase):
    def test_valid_login_fields(self):
        ok, _message = auth.validate_login("juan@example.com", "password123")
        self.assertTrue(ok)

    def test_invalid_email_rejected(self):
        ok, _message = auth.validate_login("not-an-email", "password123")
        self.assertFalse(ok)

    def test_empty_password_rejected(self):
        ok, _message = auth.validate_login("juan@example.com", "")
        self.assertFalse(ok)


class TestAmountValidation(unittest.TestCase):
    def test_valid_amount(self):
        ok, value, amount = validators.validate_amount("123.50")
        self.assertTrue(ok)
        self.assertEqual(float(amount), 123.50)

    def test_zero_amount_rejected(self):
        ok, message, _amount = validators.validate_amount("0")
        self.assertFalse(ok)

    def test_negative_amount_rejected(self):
        ok, _message, _amount = validators.validate_amount("-5")
        self.assertFalse(ok)

    def test_non_numeric_amount_rejected(self):
        ok, _message, _amount = validators.validate_amount("abc")
        self.assertFalse(ok)

    def test_nan_amount_rejected(self):
        ok, _message, _amount = validators.validate_amount("nan")
        self.assertFalse(ok)

    def test_infinite_amount_rejected(self):
        ok, _message, _amount = validators.validate_amount("inf")
        self.assertFalse(ok)

    def test_max_decimal_amount_allowed(self):
        ok, _message, _amount = validators.validate_amount("9999999999.99")
        self.assertTrue(ok)

    def test_amount_above_decimal_range_rejected(self):
        ok, _message, _amount = validators.validate_amount("10000000000")
        self.assertFalse(ok)


class TestTransactionDateValidation(unittest.TestCase):
    def test_valid_date(self):
        ok, value = validators.validate_transaction_date("2026-10-28")
        self.assertTrue(ok)
        self.assertEqual(str(value), "2026-10-28")

    def test_invalid_format_rejected(self):
        ok, _message = validators.validate_transaction_date("28-10-2026")
        self.assertFalse(ok)

    def test_impossible_date_rejected(self):
        ok, _message = validators.validate_transaction_date("2026-02-30")
        self.assertFalse(ok)


class TestDescriptionValidation(unittest.TestCase):
    def test_valid_description(self):
        ok, cleaned = validators.validate_description("  Seeds for Q1  ")
        self.assertTrue(ok)
        self.assertEqual(cleaned, "Seeds for Q1")

    def test_too_long_description_rejected(self):
        ok, _message = validators.validate_description("x" * 256)
        self.assertFalse(ok)


class TestCycleStatus(unittest.TestCase):
    def test_planned_can_go_active(self):
        self.assertTrue(cycle.is_valid_transition("planned", "active"))

    def test_planned_cannot_jump_to_harvested(self):
        self.assertFalse(cycle.is_valid_transition("planned", "harvested"))

    def test_active_can_go_harvested(self):
        self.assertTrue(cycle.is_valid_transition("active", "harvested"))

    def test_harvested_can_go_archived(self):
        self.assertTrue(cycle.is_valid_transition("harvested", "archived"))

    def test_archived_is_terminal(self):
        self.assertFalse(cycle.is_valid_transition("archived", "active"))

    def test_unknown_statuses_rejected(self):
        self.assertFalse(cycle.is_valid_cycle_status("growing"))
        self.assertTrue(cycle.is_valid_cycle_status("planned"))

    def test_cycle_fields_validate_crop_name(self):
        ok, message, values = cycle.validate_cycle_fields({
            "crop_name": "", "start_date": "2026-10-01", "status": "planned",
        })
        self.assertFalse(ok)

    def test_cycle_fields_validate_dates(self):
        ok, _message, values = cycle.validate_cycle_fields({
            "crop_name": "Rice", "start_date": "2026-13-45", "status": "planned",
        })
        self.assertFalse(ok)


class TestBudgetValidation(unittest.TestCase):
    def test_valid_budget(self):
        ok, message, values = budget.validate_budget({
            "name": "Monthly Seeds",
            "amount": "500.00",
            "period_type": "monthly",
            "start_date": "2026-10-01",
            "end_date": "2026-10-31",
        })
        self.assertTrue(ok, message)
        self.assertEqual(values["name"], "Monthly Seeds")

    def test_missing_name_rejected(self):
        ok, _message, _values = budget.validate_budget({
            "name": "  ",
            "amount": "500.00",
            "period_type": "monthly",
            "start_date": "2026-10-01",
            "end_date": "2026-10-31",
        })
        self.assertFalse(ok)

    def test_invalid_amount_rejected(self):
        ok, _message, _values = budget.validate_budget({
            "name": "Test",
            "amount": "not-a-number",
            "period_type": "monthly",
            "start_date": "2026-10-01",
            "end_date": "2026-10-31",
        })
        self.assertFalse(ok)

    def test_zero_amount_rejected(self):
        ok, _message, _values = budget.validate_budget({
            "name": "Test",
            "amount": "0",
            "period_type": "monthly",
            "start_date": "2026-10-01",
            "end_date": "2026-10-31",
        })
        self.assertFalse(ok)

    def test_start_after_end_rejected(self):
        ok, _message, _values = budget.validate_budget({
            "name": "Test",
            "amount": "500.00",
            "period_type": "monthly",
            "start_date": "2026-10-15",
            "end_date": "2026-10-01",
        })
        self.assertFalse(ok)

    def test_invalid_period_rejected(self):
        ok, _message, _values = budget.validate_budget({
            "name": "Test",
            "amount": "500.00",
            "period_type": "weekly",
            "start_date": "2026-10-01",
            "end_date": "2026-10-31",
        })
        self.assertFalse(ok)

    def test_long_name_rejected(self):
        ok, _message, _values = budget.validate_budget({
            "name": "x" * 101,
            "amount": "500.00",
            "period_type": "monthly",
            "start_date": "2026-10-01",
            "end_date": "2026-10-31",
        })
        self.assertFalse(ok)

    def test_budget_amount_returns_decimal(self):
        ok, _message, values = budget.validate_budget({
            "name": "Test",
            "amount": "123.45",
            "period_type": "monthly",
            "start_date": "2026-10-01",
            "end_date": "2026-10-31",
        })
        self.assertTrue(ok)
        from decimal import Decimal
        self.assertIsInstance(values["amount"], Decimal)
        self.assertEqual(values["amount"], Decimal("123.45"))

    # Overlap validation tests are in test_budget_integration.py (requires database)


class TestBreakeven(unittest.TestCase):
    def test_valid_breakeven_quantity(self):
        ok, message, qty = breakeven.calculate_break_even_quantity(1000, 25)
        self.assertTrue(ok, message)
        self.assertEqual(qty, 40)

    def test_zero_price_rejected(self):
        ok, _message, _qty = breakeven.calculate_break_even_quantity(1000, 0)
        self.assertFalse(ok)

    def test_negative_price_rejected(self):
        ok, _message, _qty = breakeven.calculate_break_even_quantity(1000, -5)
        self.assertFalse(ok)

    def test_negative_costs_rejected(self):
        ok, _message, _qty = breakeven.calculate_break_even_quantity(-100, 25)
        self.assertFalse(ok)

    def test_expected_revenue(self):
        ok, message, rev = breakeven.calculate_expected_revenue(100, 25.50)
        self.assertTrue(ok, message)
        self.assertEqual(rev, 2550.00)

    def test_estimated_net(self):
        ok, message, net = breakeven.calculate_estimated_net(5000, 3000)
        self.assertTrue(ok, message)
        self.assertEqual(net, 2000.00)


if __name__ == "__main__":
    unittest.main()
