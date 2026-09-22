from datetime import date
from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from .models import Expense


class ExpenseAPITests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.expenses_url = reverse("expense-list-create")
        self.summary_url = reverse("spend-summary")

        # Create sample seed data across months
        self.exp1 = Expense.objects.create(
            amount=Decimal("150.00"),
            category="Food",
            note="Groceries",
            date=date(2026, 8, 10)  # Previous month sample
        )
        self.exp2 = Expense.objects.create(
            amount=Decimal("50.00"),
            category="Transport",
            note="Uber",
            date=date(2026, 8, 15)  # Previous month sample
        )
        self.exp3 = Expense.objects.create(
            amount=Decimal("250.00"),
            category="Food",
            note="Fine Dining",
            date=date(2026, 9, 5)   # Current month sample (>20% increase for Food: 250 vs 150 -> +66.67%)
        )
        self.exp4 = Expense.objects.create(
            amount=Decimal("100.00"),
            category="Utilities",
            note="Electricity",
            date=date(2026, 9, 12)  # Current month sample
        )

    # 1. Create expense successfully
    def test_create_expense_successfully(self):
        payload = {
            "amount": "45.50",
            "category": "Entertainment",
            "note": "Movie ticket",
            "date": "2026-09-20"
        }
        response = self.client.post(self.expenses_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["category"], "Entertainment")
        self.assertEqual(float(response.data["amount"]), 45.50)
        self.assertTrue(Expense.objects.filter(category="Entertainment").exists())

    # 2. Reject negative amount
    def test_reject_negative_amount(self):
        payload = {
            "amount": "-20.00",
            "category": "Food",
            "note": "Invalid negative expense",
            "date": "2026-09-20"
        }
        response = self.client.post(self.expenses_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("amount", response.data)
        self.assertEqual(response.data["amount"][0], "Amount must be greater than 0.")

    # 3. Reject zero amount
    def test_reject_zero_amount(self):
        payload = {
            "amount": "0.00",
            "category": "Food",
            "note": "Invalid zero expense",
            "date": "2026-09-20"
        }
        response = self.client.post(self.expenses_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("amount", response.data)
        self.assertEqual(response.data["amount"][0], "Amount must be greater than 0.")

    # 4. Reject empty category
    def test_reject_empty_category(self):
        payload = {
            "amount": "100.00",
            "category": "   ",
            "note": "No category",
            "date": "2026-09-20"
        }
        response = self.client.post(self.expenses_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("category", response.data)
        self.assertEqual(response.data["category"][0], "Category cannot be empty.")

    # 5. Get expenses
    def test_get_expenses(self):
        response = self.client.get(self.expenses_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)

    # 6. Filter by category
    def test_filter_by_category(self):
        response = self.client.get(self.expenses_url, {"category": "Food"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        for item in response.data:
            self.assertEqual(item["category"], "Food")

    # 7. Filter by start date
    def test_filter_by_start_date(self):
        response = self.client.get(self.expenses_url, {"start_date": "2026-09-01"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        for item in response.data:
            self.assertTrue(item["date"] >= "2026-09-01")

    # 8. Filter by end date
    def test_filter_by_end_date(self):
        response = self.client.get(self.expenses_url, {"end_date": "2026-08-31"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        for item in response.data:
            self.assertTrue(item["date"] <= "2026-08-31")

    # 9. Filter by date range
    def test_filter_by_date_range(self):
        response = self.client.get(self.expenses_url, {
            "start_date": "2026-08-12",
            "end_date": "2026-09-08"
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        dates = [item["date"] for item in response.data]
        self.assertIn("2026-08-15", dates)
        self.assertIn("2026-09-05", dates)

    # 10. Summary total calculation
    def test_summary_total_calculation(self):
        response = self.client.get(self.summary_url, {"year": 2026, "month": 9})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total_spend"], 550.00)

    # 11. Summary category calculation
    def test_summary_category_calculation(self):
        response = self.client.get(self.summary_url, {"year": 2026, "month": 9})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        spend_by_cat = response.data["spend_by_category"]
        self.assertEqual(spend_by_cat["Food"], 400.00)
        self.assertEqual(spend_by_cat["Transport"], 50.00)
        self.assertEqual(spend_by_cat["Utilities"], 100.00)

    # 12. Month-over-month calculation
    def test_month_over_month_calculation(self):
        response = self.client.get(self.summary_url, {"year": 2026, "month": 9})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["current_month"]["total_spend"], 350.00)
        self.assertEqual(response.data["previous_month"]["total_spend"], 200.00)
        self.assertEqual(response.data["mom_change"]["difference"], 150.00)
        self.assertEqual(response.data["mom_change"]["percentage"], 75.0)

    # 13. January previous-month calculation
    def test_january_previous_month_calculation(self):
        Expense.objects.create(amount=Decimal("300.00"), category="Shopping", date=date(2025, 12, 20))
        Expense.objects.create(amount=Decimal("450.00"), category="Shopping", date=date(2026, 1, 10))

        response = self.client.get(self.summary_url, {"year": 2026, "month": 1})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["current_month"]["year"], 2026)
        self.assertEqual(response.data["current_month"]["month"], 1)
        self.assertEqual(response.data["current_month"]["total_spend"], 450.00)

        self.assertEqual(response.data["previous_month"]["year"], 2025)
        self.assertEqual(response.data["previous_month"]["month"], 12)
        self.assertEqual(response.data["previous_month"]["total_spend"], 300.00)

        self.assertEqual(response.data["mom_change"]["difference"], 150.00)
        self.assertEqual(response.data["mom_change"]["percentage"], 50.0)

    # 14. >20% category insight
    def test_greater_than_20_percent_category_insight(self):
        response = self.client.get(self.summary_url, {"year": 2026, "month": 9})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        insights = response.data["insights"]
        self.assertEqual(len(insights), 1)
        self.assertEqual(insights[0]["category"], "Food")
        self.assertEqual(insights[0]["previous_month_spend"], 150.00)
        self.assertEqual(insights[0]["current_month_spend"], 250.00)
        self.assertEqual(insights[0]["increase_percentage"], 66.67)
        self.assertIn("Food spend increased by 66.67% compared to previous month.", insights[0]["message"])

    # 15. No previous-month spending / division by zero case
    def test_no_previous_month_spending_division_by_zero(self):
        Expense.objects.all().delete()
        Expense.objects.create(amount=Decimal("500.00"), category="Rent", date=date(2026, 10, 1))

        # October 2026: prev month (Sept 2026) has 0 spend -> percentage is 100.0%
        response = self.client.get(self.summary_url, {"year": 2026, "month": 10})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["current_month"]["total_spend"], 500.00)
        self.assertEqual(response.data["previous_month"]["total_spend"], 0.00)
        self.assertEqual(response.data["mom_change"]["difference"], 500.00)
        self.assertEqual(response.data["mom_change"]["percentage"], 100.0)

        # December 2026: both Dec 2026 and Nov 2026 have 0 spend -> percentage is 0.0%
        response_empty = self.client.get(self.summary_url, {"year": 2026, "month": 12})
        self.assertEqual(response_empty.status_code, status.HTTP_200_OK)
        self.assertEqual(response_empty.data["current_month"]["total_spend"], 0.00)
        self.assertEqual(response_empty.data["previous_month"]["total_spend"], 0.00)
        self.assertEqual(response_empty.data["mom_change"]["difference"], 0.00)
        self.assertEqual(response_empty.data["mom_change"]["percentage"], 0.0)
