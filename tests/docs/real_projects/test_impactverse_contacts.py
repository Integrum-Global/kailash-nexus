"""Validation test for Real Project Pattern: impact-verse Contact CRUD.

Tests the handler patterns from the real project catalog:
- Pattern 1: Contact CRUD Gateway (75% reduction: ~400 lines -> ~100 lines)

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

_contacts = {}


def _reset_contacts():
    _contacts.clear()


# --- Pattern 1: Contact CRUD handlers (from impact-verse) ---


async def contact_create(
    name: str,
    email: str,
    phone: str = None,
    company: str = None,
) -> dict:
    """Create a new contact."""
    if not name or not name.strip():
        raise ValueError("Name is required")
    if not email or "@" not in email:
        raise ValueError("Valid email is required")

    now = datetime.now().isoformat()
    contact_id = str(uuid.uuid4())
    contact = {
        "id": contact_id,
        "name": name.strip(),
        "email": email.strip().lower(),
        "phone": phone.strip() if phone else None,
        "company": company.strip() if company else None,
        "created_at": now,
        "updated_at": now,
    }
    _contacts[contact_id] = contact
    return {"contact": contact}


async def contact_read(contact_id: str) -> dict:
    """Retrieve a contact by ID."""
    contact = _contacts.get(contact_id)
    if not contact:
        raise ValueError(f"Contact not found: {contact_id}")
    return {"contact": contact}


async def contact_update(
    contact_id: str,
    name: str = None,
    email: str = None,
    phone: str = None,
    company: str = None,
) -> dict:
    """Update contact fields."""
    contact = _contacts.get(contact_id)
    if not contact:
        raise ValueError(f"Contact not found: {contact_id}")

    if name is not None:
        contact["name"] = name.strip()
    if email is not None:
        contact["email"] = email.strip().lower()
    if phone is not None:
        contact["phone"] = phone.strip() or None
    if company is not None:
        contact["company"] = company.strip() or None

    contact["updated_at"] = datetime.now().isoformat()
    return {"contact": contact}


async def contact_delete(contact_id: str) -> dict:
    """Delete a contact by ID."""
    if contact_id not in _contacts:
        raise ValueError(f"Contact not found: {contact_id}")
    del _contacts[contact_id]
    return {"deleted": True, "contact_id": contact_id}


async def contact_list(
    page: int = 1,
    page_size: int = 20,
    company: str = None,
) -> dict:
    """List contacts with optional company filter."""
    all_contacts = list(_contacts.values())

    if company:
        all_contacts = [c for c in all_contacts if c.get("company") == company]

    total = len(all_contacts)
    offset = (page - 1) * page_size
    page_results = all_contacts[offset : offset + page_size]

    return {
        "contacts": page_results,
        "pagination": {"page": page, "page_size": page_size, "total": total},
    }


async def contact_search(
    query: str,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    """Search contacts by name, email, or company."""
    all_contacts = list(_contacts.values())
    query_lower = query.lower()

    filtered = [
        c
        for c in all_contacts
        if query_lower in c["name"].lower()
        or query_lower in c["email"].lower()
        or query_lower in (c.get("company") or "").lower()
    ]

    offset = (page - 1) * page_size
    return {"contacts": filtered[offset : offset + page_size], "query": query}


# --- Tests ---


class TestImpactverseContacts:
    """Validate impact-verse Contact CRUD handler patterns."""

    def setup_method(self):
        _reset_contacts()

    @pytest.mark.asyncio
    async def test_create_contact(self):
        """Create a contact with all fields."""
        workflow = make_handler_workflow(contact_create, "handler")
        runtime = AsyncLocalRuntime()

        results, _ = await runtime.execute_workflow_async(
            workflow,
            inputs={
                "name": "Alice Smith",
                "email": "Alice@Example.com",
                "phone": " 555-1234 ",
                "company": " Acme Corp ",
            },
        )

        handler_result = next(iter(results.values()), {})
        contact = handler_result["contact"]

        assert contact["name"] == "Alice Smith"
        assert contact["email"] == "alice@example.com"  # lowercased
        assert contact["phone"] == "555-1234"  # stripped
        assert contact["company"] == "Acme Corp"  # stripped
        assert "id" in contact
        assert "created_at" in contact

    @pytest.mark.asyncio
    async def test_create_contact_validates_name(self):
        """Create rejects empty name."""
        workflow = make_handler_workflow(contact_create, "handler")
        runtime = AsyncLocalRuntime()

        with pytest.raises(Exception, match="Name is required"):
            await runtime.execute_workflow_async(
                workflow, inputs={"name": "  ", "email": "a@b.com"}
            )

    @pytest.mark.asyncio
    async def test_create_contact_validates_email(self):
        """Create rejects invalid email."""
        workflow = make_handler_workflow(contact_create, "handler")
        runtime = AsyncLocalRuntime()

        with pytest.raises(Exception, match="Valid email is required"):
            await runtime.execute_workflow_async(
                workflow, inputs={"name": "Test", "email": "invalid"}
            )

    @pytest.mark.asyncio
    async def test_read_contact(self):
        """Read returns contact by ID."""
        # Pre-create a contact
        contact_id = str(uuid.uuid4())
        _contacts[contact_id] = {
            "id": contact_id,
            "name": "Bob",
            "email": "bob@test.com",
        }

        workflow = make_handler_workflow(contact_read, "handler")
        runtime = AsyncLocalRuntime()

        results, _ = await runtime.execute_workflow_async(
            workflow, inputs={"contact_id": contact_id}
        )

        handler_result = next(iter(results.values()), {})
        assert handler_result["contact"]["name"] == "Bob"

    @pytest.mark.asyncio
    async def test_read_contact_not_found(self):
        """Read raises error for non-existent contact."""
        workflow = make_handler_workflow(contact_read, "handler")
        runtime = AsyncLocalRuntime()

        with pytest.raises(Exception, match="Contact not found"):
            await runtime.execute_workflow_async(
                workflow, inputs={"contact_id": "nonexistent"}
            )

    @pytest.mark.asyncio
    async def test_update_contact(self):
        """Update modifies contact fields."""
        contact_id = str(uuid.uuid4())
        _contacts[contact_id] = {
            "id": contact_id,
            "name": "Carol",
            "email": "carol@test.com",
            "phone": None,
            "company": None,
            "updated_at": "old",
        }

        workflow = make_handler_workflow(contact_update, "handler")
        runtime = AsyncLocalRuntime()

        results, _ = await runtime.execute_workflow_async(
            workflow,
            inputs={
                "contact_id": contact_id,
                "name": "Carol Updated",
                "company": "NewCo",
            },
        )

        handler_result = next(iter(results.values()), {})
        contact = handler_result["contact"]
        assert contact["name"] == "Carol Updated"
        assert contact["company"] == "NewCo"
        assert contact["updated_at"] != "old"

    @pytest.mark.asyncio
    async def test_delete_contact(self):
        """Delete removes contact."""
        contact_id = str(uuid.uuid4())
        _contacts[contact_id] = {"id": contact_id, "name": "To Delete"}

        workflow = make_handler_workflow(contact_delete, "handler")
        runtime = AsyncLocalRuntime()

        results, _ = await runtime.execute_workflow_async(
            workflow, inputs={"contact_id": contact_id}
        )

        handler_result = next(iter(results.values()), {})
        assert handler_result["deleted"] is True
        assert contact_id not in _contacts

    @pytest.mark.asyncio
    async def test_list_contacts(self):
        """List returns contacts with pagination."""
        for i in range(3):
            cid = str(uuid.uuid4())
            _contacts[cid] = {
                "id": cid,
                "name": f"Contact {i}",
                "email": f"c{i}@test.com",
                "company": "Acme" if i < 2 else "Beta",
            }

        workflow = make_handler_workflow(contact_list, "handler")
        runtime = AsyncLocalRuntime()

        results, _ = await runtime.execute_workflow_async(
            workflow, inputs={"page": 1, "page_size": 10}
        )

        handler_result = next(iter(results.values()), {})
        assert handler_result["pagination"]["total"] == 3

    @pytest.mark.asyncio
    async def test_list_contacts_filter_company(self):
        """List filters by company."""
        _contacts["c1"] = {
            "id": "c1",
            "name": "A",
            "email": "a@t.com",
            "company": "Acme",
        }
        _contacts["c2"] = {
            "id": "c2",
            "name": "B",
            "email": "b@t.com",
            "company": "Beta",
        }

        workflow = make_handler_workflow(contact_list, "handler")
        runtime = AsyncLocalRuntime()

        results, _ = await runtime.execute_workflow_async(
            workflow, inputs={"company": "Acme"}
        )

        handler_result = next(iter(results.values()), {})
        assert handler_result["pagination"]["total"] == 1

    @pytest.mark.asyncio
    async def test_search_contacts(self):
        """Search finds contacts by name/email/company."""
        _contacts["c1"] = {
            "id": "c1",
            "name": "Alice",
            "email": "alice@acme.com",
            "company": "Acme",
        }
        _contacts["c2"] = {
            "id": "c2",
            "name": "Bob",
            "email": "bob@beta.com",
            "company": "Beta",
        }

        workflow = make_handler_workflow(contact_search, "handler")
        runtime = AsyncLocalRuntime()

        results, _ = await runtime.execute_workflow_async(
            workflow, inputs={"query": "alice"}
        )

        handler_result = next(iter(results.values()), {})
        assert len(handler_result["contacts"]) == 1
        assert handler_result["query"] == "alice"
