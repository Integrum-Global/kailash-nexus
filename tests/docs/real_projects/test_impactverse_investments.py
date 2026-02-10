"""Validation test for Real Project Pattern: impact-verse Investment Tracking.

Tests the handler patterns from the real project catalog:
- Pattern 2: Investment Tracking Gateway

NO MOCKING - real workflow execution.
"""

import os
import sys
import uuid
from datetime import datetime
from typing import Optional

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../../src"))

from kailash.nodes.handler import make_handler_workflow
from kailash.runtime import AsyncLocalRuntime

# --- In-memory store simulating DataFlow ---

_investments = {}


def _reset_investments():
    _investments.clear()


# --- Pattern 2: Investment Tracking handlers ---


async def investment_create(
    contact_id: str,
    fund_id: str,
    amount: float,
    currency: str = "USD",
) -> dict:
    """Create a new investment record."""
    if amount <= 0:
        raise ValueError("Amount must be positive")

    now = datetime.now().isoformat()
    inv_id = str(uuid.uuid4())
    investment = {
        "id": inv_id,
        "contact_id": contact_id,
        "fund_id": fund_id,
        "amount": float(amount),
        "currency": currency,
        "status": "pending",
        "invested_at": now,
        "created_at": now,
    }
    _investments[inv_id] = investment
    return {"investment": investment}


async def investment_confirm(investment_id: str) -> dict:
    """Confirm a pending investment."""
    investment = _investments.get(investment_id)
    if not investment:
        raise ValueError(f"Investment not found: {investment_id}")
    investment["status"] = "confirmed"
    return {"investment": investment}


async def investment_by_contact(contact_id: str) -> dict:
    """Get all investments for a contact."""
    investments = [
        inv for inv in _investments.values() if inv["contact_id"] == contact_id
    ]
    total = sum(inv.get("amount", 0) for inv in investments)
    return {"investments": investments, "total_invested": total}


# --- Tests ---


class TestImpactverseInvestments:
    """Validate impact-verse Investment Tracking handler patterns."""

    def setup_method(self):
        _reset_investments()

    @pytest.mark.asyncio
    async def test_create_investment(self):
        """Create an investment with all fields."""
        workflow = make_handler_workflow(investment_create, "handler")
        runtime = AsyncLocalRuntime()

        results, _ = await runtime.execute_workflow_async(
            workflow,
            inputs={
                "contact_id": "contact-1",
                "fund_id": "fund-growth",
                "amount": 50000.00,
                "currency": "USD",
            },
        )

        handler_result = next(iter(results.values()), {})
        inv = handler_result["investment"]

        assert inv["contact_id"] == "contact-1"
        assert inv["fund_id"] == "fund-growth"
        assert inv["amount"] == 50000.00
        assert inv["currency"] == "USD"
        assert inv["status"] == "pending"

    @pytest.mark.asyncio
    async def test_create_investment_validates_amount(self):
        """Create rejects non-positive amount."""
        workflow = make_handler_workflow(investment_create, "handler")
        runtime = AsyncLocalRuntime()

        with pytest.raises(Exception, match="Amount must be positive"):
            await runtime.execute_workflow_async(
                workflow,
                inputs={
                    "contact_id": "c1",
                    "fund_id": "f1",
                    "amount": -100,
                },
            )

    @pytest.mark.asyncio
    async def test_confirm_investment(self):
        """Confirm a pending investment."""
        inv_id = str(uuid.uuid4())
        _investments[inv_id] = {
            "id": inv_id,
            "contact_id": "c1",
            "status": "pending",
        }

        workflow = make_handler_workflow(investment_confirm, "handler")
        runtime = AsyncLocalRuntime()

        results, _ = await runtime.execute_workflow_async(
            workflow, inputs={"investment_id": inv_id}
        )

        handler_result = next(iter(results.values()), {})
        assert handler_result["investment"]["status"] == "confirmed"

    @pytest.mark.asyncio
    async def test_investment_by_contact(self):
        """List investments for a contact with total."""
        _investments["i1"] = {"id": "i1", "contact_id": "c1", "amount": 10000}
        _investments["i2"] = {"id": "i2", "contact_id": "c1", "amount": 25000}
        _investments["i3"] = {"id": "i3", "contact_id": "c2", "amount": 5000}

        workflow = make_handler_workflow(investment_by_contact, "handler")
        runtime = AsyncLocalRuntime()

        results, _ = await runtime.execute_workflow_async(
            workflow, inputs={"contact_id": "c1"}
        )

        handler_result = next(iter(results.values()), {})
        assert len(handler_result["investments"]) == 2
        assert handler_result["total_invested"] == 35000

    @pytest.mark.asyncio
    async def test_investment_by_contact_empty(self):
        """Returns empty for contact with no investments."""
        workflow = make_handler_workflow(investment_by_contact, "handler")
        runtime = AsyncLocalRuntime()

        results, _ = await runtime.execute_workflow_async(
            workflow, inputs={"contact_id": "no-investments"}
        )

        handler_result = next(iter(results.values()), {})
        assert handler_result["investments"] == []
        assert handler_result["total_invested"] == 0
