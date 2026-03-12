import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from datetime import datetime, timezone
from handlers.user_handlers import UserCommandHandler, ParsedExpense

class TestDateParsing:
    def test_basic_expense(self):
        res = UserCommandHandler.parse_expense("15 USD Lunch")
        assert res.amount == 15.0
        assert res.currency == "USD"
        assert res.description == "Lunch"
        assert res.date is None

    def test_simple_date_fallback(self):
        res = UserCommandHandler.parse_expense("12 Grab ride yesterday")
        assert res.amount == 12.0
        assert res.description == "Grab ride"
        assert res.date is not None
        assert res.date.tzinfo == timezone.utc
        assert res.date.hour == 0
        assert res.date.minute == 0
        
    def test_comma_delimited_yesterday(self):
        res = UserCommandHandler.parse_expense("15 USD Lunch, yesterday")
        assert res.amount == 15.0
        assert res.description == "Lunch"
        assert res.date is not None

    def test_comma_delimited_days_ago(self):
        res = UserCommandHandler.parse_expense("25.50 Movie tickets, 2 days ago")
        assert res.amount == 25.50
        assert res.description == "Movie tickets"
        assert res.date is not None

    def test_comma_delimited_last_friday(self):
        res = UserCommandHandler.parse_expense("30 JPY Beer, last friday")
        assert res is not None
        assert res.amount == 30.0
        assert res.currency == "JPY"
        assert res.description == "Beer"
        assert res.date is not None

    def test_comma_delimited_invalid_date(self):
        # Fallback to appending comma to description
        res = UserCommandHandler.parse_expense("15 Lunch, with friends")
        assert res.amount == 15.0
        assert res.description == "Lunch, with friends"
        assert res.date is None


    def test_non_delimited_last_saturday(self):
        res = UserCommandHandler.parse_expense("500 dinner last saturday")
        assert res.amount == 500.0
        assert res.description == "dinner"
        assert res.date is not None
