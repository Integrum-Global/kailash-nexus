"""Validation test for Real Project Pattern: agentic-os Session Management.

Tests the handler patterns from the real project catalog:
- Pattern 1: Session Management (4 handlers replace 4 workflows)

NO MOCKING - real workflow execution.
"""

import os
import sys
import uuid
from datetime import datetime
from typing import Dict, Optional

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../../src"))

from kailash.nodes.handler import make_handler_workflow
from kailash.runtime import AsyncLocalRuntime

# --- In-memory session store (from agentic-os pattern) ---

_sessions: Dict[str, dict] = {}


def _reset_sessions():
    _sessions.clear()


# --- Pattern 1: Session Management handlers ---


async def create_session(
    user_id: str,
    agent_id: str,
    context: dict = None,
) -> dict:
    """Create a new session for user-agent interaction."""
    session_id = str(uuid.uuid4())
    session = {
        "session_id": session_id,
        "user_id": user_id,
        "agent_id": agent_id,
        "context": context or {},
        "status": "active",
        "created_at": datetime.now().isoformat(),
        "messages": [],
    }
    _sessions[session_id] = session
    return {"session": session}


async def get_session(session_id: str) -> dict:
    """Get session details."""
    session = _sessions.get(session_id)
    if not session:
        raise ValueError(f"Session not found: {session_id}")
    return {"session": session}


async def update_session(
    session_id: str,
    context: dict = None,
    add_message: dict = None,
) -> dict:
    """Update session context or add message."""
    session = _sessions.get(session_id)
    if not session:
        raise ValueError(f"Session not found: {session_id}")

    if context:
        session["context"].update(context)
    if add_message:
        add_message["timestamp"] = datetime.now().isoformat()
        session["messages"].append(add_message)

    return {"session": session}


async def close_session(session_id: str) -> dict:
    """Close a session."""
    session = _sessions.get(session_id)
    if not session:
        raise ValueError(f"Session not found: {session_id}")

    session["status"] = "closed"
    session["closed_at"] = datetime.now().isoformat()
    return {"session": session}


# --- Tests ---


class TestAgenticOSSessions:
    """Validate agentic-os session management patterns."""

    def setup_method(self):
        _reset_sessions()

    @pytest.mark.asyncio
    async def test_create_session(self):
        """Create a new session with user and agent IDs."""
        workflow = make_handler_workflow(create_session, "handler")
        runtime = AsyncLocalRuntime()

        results, run_id = await runtime.execute_workflow_async(
            workflow,
            inputs={
                "user_id": "user-1",
                "agent_id": "agent-gpt4",
                "context": {"topic": "code review"},
            },
        )

        assert run_id is not None
        handler_result = next(iter(results.values()), {})
        session = handler_result["session"]

        assert session["user_id"] == "user-1"
        assert session["agent_id"] == "agent-gpt4"
        assert session["status"] == "active"
        assert session["context"] == {"topic": "code review"}
        assert session["messages"] == []
        uuid.UUID(session["session_id"])  # Valid UUID

    @pytest.mark.asyncio
    async def test_create_session_default_context(self):
        """Create session with empty default context."""
        workflow = make_handler_workflow(create_session, "handler")
        runtime = AsyncLocalRuntime()

        results, _ = await runtime.execute_workflow_async(
            workflow, inputs={"user_id": "user-2", "agent_id": "agent-basic"}
        )

        handler_result = next(iter(results.values()), {})
        assert handler_result["session"]["context"] == {}

    @pytest.mark.asyncio
    async def test_get_session(self):
        """Get an existing session by ID."""
        # Pre-create session
        sid = str(uuid.uuid4())
        _sessions[sid] = {
            "session_id": sid,
            "user_id": "user-1",
            "agent_id": "agent-1",
            "status": "active",
        }

        workflow = make_handler_workflow(get_session, "handler")
        runtime = AsyncLocalRuntime()

        results, _ = await runtime.execute_workflow_async(
            workflow, inputs={"session_id": sid}
        )

        handler_result = next(iter(results.values()), {})
        assert handler_result["session"]["session_id"] == sid

    @pytest.mark.asyncio
    async def test_get_session_not_found(self):
        """Get raises error for non-existent session."""
        workflow = make_handler_workflow(get_session, "handler")
        runtime = AsyncLocalRuntime()

        with pytest.raises(Exception, match="Session not found"):
            await runtime.execute_workflow_async(
                workflow, inputs={"session_id": "nonexistent"}
            )

    @pytest.mark.asyncio
    async def test_update_session_context(self):
        """Update session context."""
        sid = str(uuid.uuid4())
        _sessions[sid] = {
            "session_id": sid,
            "context": {"initial": True},
            "messages": [],
        }

        workflow = make_handler_workflow(update_session, "handler")
        runtime = AsyncLocalRuntime()

        results, _ = await runtime.execute_workflow_async(
            workflow,
            inputs={"session_id": sid, "context": {"topic": "debugging"}},
        )

        handler_result = next(iter(results.values()), {})
        session = handler_result["session"]
        assert session["context"]["initial"] is True
        assert session["context"]["topic"] == "debugging"

    @pytest.mark.asyncio
    async def test_update_session_add_message(self):
        """Add message to session."""
        sid = str(uuid.uuid4())
        _sessions[sid] = {
            "session_id": sid,
            "context": {},
            "messages": [],
        }

        workflow = make_handler_workflow(update_session, "handler")
        runtime = AsyncLocalRuntime()

        results, _ = await runtime.execute_workflow_async(
            workflow,
            inputs={
                "session_id": sid,
                "add_message": {"role": "user", "content": "Hello"},
            },
        )

        handler_result = next(iter(results.values()), {})
        session = handler_result["session"]
        assert len(session["messages"]) == 1
        assert session["messages"][0]["role"] == "user"
        assert session["messages"][0]["content"] == "Hello"
        assert "timestamp" in session["messages"][0]

    @pytest.mark.asyncio
    async def test_close_session(self):
        """Close an active session."""
        sid = str(uuid.uuid4())
        _sessions[sid] = {
            "session_id": sid,
            "status": "active",
        }

        workflow = make_handler_workflow(close_session, "handler")
        runtime = AsyncLocalRuntime()

        results, _ = await runtime.execute_workflow_async(
            workflow, inputs={"session_id": sid}
        )

        handler_result = next(iter(results.values()), {})
        session = handler_result["session"]
        assert session["status"] == "closed"
        assert "closed_at" in session

    @pytest.mark.asyncio
    async def test_full_session_lifecycle(self):
        """Test complete session lifecycle: create -> update -> close."""
        runtime = AsyncLocalRuntime()

        # 1. Create
        create_wf = make_handler_workflow(create_session, "create")
        results, _ = await runtime.execute_workflow_async(
            create_wf, inputs={"user_id": "u1", "agent_id": "a1"}
        )
        sid = next(iter(results.values()), {})["session"]["session_id"]

        # 2. Update with message
        update_wf = make_handler_workflow(update_session, "update")
        await runtime.execute_workflow_async(
            update_wf,
            inputs={
                "session_id": sid,
                "add_message": {"role": "user", "content": "Help me debug"},
            },
        )

        # 3. Close
        close_wf = make_handler_workflow(close_session, "close")
        results, _ = await runtime.execute_workflow_async(
            close_wf, inputs={"session_id": sid}
        )

        session = next(iter(results.values()), {})["session"]
        assert session["status"] == "closed"
        assert len(session["messages"]) == 1
