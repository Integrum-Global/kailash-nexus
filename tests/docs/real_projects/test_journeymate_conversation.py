"""Validation test for Real Project Pattern: journeymate-backend conversations.

Tests the handler patterns from the real project catalog:
- Pattern 1: Create Conversation (55% reduction)
- Pattern 2: List Conversations (33% reduction)

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

# --- Pattern 1: Create Conversation (from journeymate-backend) ---


async def create_conversation(
    user_id: str,
    title: str = "New Conversation",
    model: str = "gpt-4",
    system_prompt: str = "You are a helpful assistant.",
) -> dict:
    """Create a new conversation for a user."""
    conv_id = str(uuid.uuid4())
    created_at = datetime.now().isoformat()

    conversation = {
        "id": conv_id,
        "title": title,
        "user_id": user_id,
        "model": model,
        "system_prompt": system_prompt,
        "created_at": created_at,
        "messages": [
            {
                "role": "system",
                "content": system_prompt,
                "timestamp": created_at,
            }
        ],
        "message_count": 1,
    }

    return {"conversation": conversation}


# --- Pattern 2: List Conversations (simplified without DataFlow) ---

# In-memory store for testing
_test_conversations = []


async def list_conversations(
    user_id: str,
    page: int = 1,
    page_size: int = 20,
    sort_by: str = "created_at",
    sort_order: str = "desc",
) -> dict:
    """List conversations for a user with pagination."""
    offset = (page - 1) * page_size

    # Simulated DataFlow query
    user_convs = [c for c in _test_conversations if c["user_id"] == user_id]

    # Sort
    reverse = sort_order == "desc"
    user_convs.sort(key=lambda c: c.get(sort_by, ""), reverse=reverse)

    total = len(user_convs)
    page_results = user_convs[offset : offset + page_size]

    return {
        "conversations": page_results,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": (total + page_size - 1) // page_size if total > 0 else 0,
        },
    }


# --- Tests ---


class TestJourneymateConversation:
    """Validate journeymate-backend conversation patterns."""

    @pytest.mark.asyncio
    async def test_create_conversation(self):
        """Pattern 1: Create conversation with all fields."""
        workflow = make_handler_workflow(create_conversation, "handler")
        runtime = AsyncLocalRuntime()

        results, run_id = await runtime.execute_workflow_async(
            workflow,
            inputs={
                "user_id": "user-123",
                "title": "My Chat",
                "model": "gpt-4o",
                "system_prompt": "You are a coding assistant.",
            },
        )

        assert run_id is not None
        handler_result = next(iter(results.values()), {})
        conv = handler_result["conversation"]

        assert conv["title"] == "My Chat"
        assert conv["user_id"] == "user-123"
        assert conv["model"] == "gpt-4o"
        assert conv["system_prompt"] == "You are a coding assistant."
        assert conv["message_count"] == 1
        assert len(conv["messages"]) == 1
        assert conv["messages"][0]["role"] == "system"
        assert conv["messages"][0]["content"] == "You are a coding assistant."
        # Verify UUID format
        uuid.UUID(conv["id"])  # Raises if invalid

    @pytest.mark.asyncio
    async def test_create_conversation_defaults(self):
        """Pattern 1: Create conversation with defaults."""
        workflow = make_handler_workflow(create_conversation, "handler")
        runtime = AsyncLocalRuntime()

        results, _ = await runtime.execute_workflow_async(
            workflow, inputs={"user_id": "user-456"}
        )

        handler_result = next(iter(results.values()), {})
        conv = handler_result["conversation"]

        assert conv["title"] == "New Conversation"
        assert conv["model"] == "gpt-4"
        assert conv["system_prompt"] == "You are a helpful assistant."

    @pytest.mark.asyncio
    async def test_list_conversations_empty(self):
        """Pattern 2: List returns empty for user with no conversations."""
        _test_conversations.clear()

        workflow = make_handler_workflow(list_conversations, "handler")
        runtime = AsyncLocalRuntime()

        results, _ = await runtime.execute_workflow_async(
            workflow, inputs={"user_id": "user-999"}
        )

        handler_result = next(iter(results.values()), {})
        assert handler_result["conversations"] == []
        assert handler_result["pagination"]["total"] == 0

    @pytest.mark.asyncio
    async def test_list_conversations_with_data(self):
        """Pattern 2: List returns conversations for correct user."""
        _test_conversations.clear()
        _test_conversations.extend(
            [
                {
                    "id": "c1",
                    "user_id": "user-A",
                    "title": "Chat 1",
                    "created_at": "2026-01-01",
                },
                {
                    "id": "c2",
                    "user_id": "user-A",
                    "title": "Chat 2",
                    "created_at": "2026-01-02",
                },
                {
                    "id": "c3",
                    "user_id": "user-B",
                    "title": "Chat 3",
                    "created_at": "2026-01-01",
                },
            ]
        )

        workflow = make_handler_workflow(list_conversations, "handler")
        runtime = AsyncLocalRuntime()

        results, _ = await runtime.execute_workflow_async(
            workflow, inputs={"user_id": "user-A"}
        )

        handler_result = next(iter(results.values()), {})
        assert len(handler_result["conversations"]) == 2
        assert handler_result["pagination"]["total"] == 2

    @pytest.mark.asyncio
    async def test_list_conversations_pagination(self):
        """Pattern 2: Pagination works correctly."""
        _test_conversations.clear()
        for i in range(5):
            _test_conversations.append(
                {
                    "id": f"c{i}",
                    "user_id": "user-A",
                    "title": f"Chat {i}",
                    "created_at": f"2026-01-0{i + 1}",
                }
            )

        workflow = make_handler_workflow(list_conversations, "handler")
        runtime = AsyncLocalRuntime()

        results, _ = await runtime.execute_workflow_async(
            workflow, inputs={"user_id": "user-A", "page": 1, "page_size": 2}
        )

        handler_result = next(iter(results.values()), {})
        assert len(handler_result["conversations"]) == 2
        assert handler_result["pagination"]["total"] == 5
        assert handler_result["pagination"]["total_pages"] == 3
