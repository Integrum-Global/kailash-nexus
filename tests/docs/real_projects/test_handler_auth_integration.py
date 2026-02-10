"""Validation test for Handler + Auth Integration pattern.

Tests that handler functions work correctly with the auth middleware stack.
Uses real NexusAuthPlugin with JWT, RBAC, and tenant isolation.

NO MOCKING - real middleware stack with real JWT tokens.
"""

import os
import sys
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt as pyjwt
import pytest
from fastapi import Depends, Request
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../../src"))

from nexus.auth.dependencies import get_current_user, require_permission, require_role
from nexus.auth.jwt import JWTConfig
from nexus.auth.plugin import NexusAuthPlugin
from nexus.auth.tenant.config import TenantConfig
from nexus.auth.tenant.context import get_current_tenant_id

# Test secret
TEST_SECRET = "handler-auth-integration-test-secret-32chars"


@pytest.fixture
def create_token():
    """Factory to create JWT tokens."""

    def _create(
        user_id: str = "user-1",
        email: str = "user@test.com",
        roles: list = None,
        tenant_id: str = None,
        expired: bool = False,
    ) -> str:
        now = datetime.now(timezone.utc)
        exp = now - timedelta(hours=1) if expired else now + timedelta(hours=1)

        payload = {
            "sub": user_id,
            "email": email,
            "iat": int(now.timestamp()),
            "exp": int(exp.timestamp()),
            "token_type": "access",
        }
        if roles:
            payload["roles"] = roles
        if tenant_id:
            payload["tenant_id"] = tenant_id

        return pyjwt.encode(payload, TEST_SECRET, algorithm="HS256")

    return _create


@pytest.fixture
def handler_auth_app():
    """FastAPI app with handler endpoints and auth middleware.

    Simulates how handlers work with the NexusAuthPlugin in production.
    """
    from fastapi import FastAPI

    app = FastAPI()

    plugin = NexusAuthPlugin(
        jwt=JWTConfig(
            secret=TEST_SECRET,
            exempt_paths=["/health"],
        ),
        rbac={
            "admin": ["*"],
            "user": ["read:profile", "write:profile", "read:data"],
            "viewer": ["read:data"],
        },
        tenant_isolation=TenantConfig(
            jwt_claim="tenant_id",
            validate_tenant_exists=False,
            validate_tenant_active=False,
            allow_admin_override=True,
            admin_role="admin",
            exclude_paths=["/health"],
        ),
    )
    plugin.install(app)

    # --- Handler-style endpoints (simulating @app.handler behavior) ---
    # In production, @app.handler() auto-registers at /workflows/<name>/execute
    # Here we simulate that by creating FastAPI endpoints with the same logic

    @app.get("/health")
    async def health():
        return {"status": "healthy"}

    @app.get("/api/users")
    async def list_users(request: Request, user=Depends(require_role("admin"))):
        """List users - admin only (simulates handler with admin requirement)."""
        tenant = get_current_tenant_id() or getattr(request.state, "tenant_id", None)
        return {
            "users": [{"id": "u1", "name": "User 1"}],
            "requested_by": user.user_id,
            "tenant": tenant,
        }

    @app.get("/api/profile")
    async def get_profile(request: Request, user=Depends(get_current_user)):
        """Get current user profile (any authenticated user)."""
        return {
            "user_id": user.user_id,
            "email": user.email,
        }

    @app.get("/api/data")
    async def get_data(request: Request, user=Depends(require_permission("read:data"))):
        """Get data - requires read:data permission."""
        tenant = get_current_tenant_id() or getattr(request.state, "tenant_id", None)
        return {
            "data": [1, 2, 3],
            "user_id": user.user_id,
            "tenant": tenant,
        }

    return app


@pytest.fixture
def client(handler_auth_app):
    return TestClient(handler_auth_app)


# --- Tests ---


class TestHandlerAuthIntegration:
    """Validate handler + auth integration patterns."""

    def test_public_endpoint_no_auth(self, client):
        """Health endpoint accessible without auth."""
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"

    def test_admin_handler_with_admin_token(self, client, create_token):
        """Admin handler accessible with admin role."""
        token = create_token(user_id="admin-1", roles=["admin"], tenant_id="tenant-a")
        resp = client.get(
            "/api/users",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["requested_by"] == "admin-1"
        assert len(data["users"]) > 0

    def test_admin_handler_rejected_for_user(self, client, create_token):
        """Admin handler rejects non-admin users."""
        token = create_token(user_id="user-1", roles=["user"], tenant_id="tenant-a")
        resp = client.get(
            "/api/users",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403

    def test_profile_handler_any_authenticated(self, client, create_token):
        """Profile handler works for any authenticated user."""
        token = create_token(
            user_id="user-42", email="test@example.com", roles=["user"]
        )
        resp = client.get(
            "/api/profile",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["user_id"] == "user-42"
        assert data["email"] == "test@example.com"

    def test_profile_handler_rejected_without_auth(self, client):
        """Profile handler rejects unauthenticated requests."""
        resp = client.get("/api/profile")
        assert resp.status_code == 401

    def test_data_handler_with_permission(self, client, create_token):
        """Data handler accessible with read:data permission (via RBAC)."""
        token = create_token(user_id="user-1", roles=["user"], tenant_id="tenant-a")
        resp = client.get(
            "/api/data",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"] == [1, 2, 3]
        assert data["user_id"] == "user-1"

    def test_data_handler_rejected_no_permission(self, client, create_token):
        """Data handler rejects users without read:data permission."""
        # Create token with no roles (no permissions)
        token = create_token(user_id="anon-1")
        resp = client.get(
            "/api/data",
            headers={"Authorization": f"Bearer {token}"},
        )
        # No roles means no permissions from RBAC, should get 403
        assert resp.status_code == 403

    def test_tenant_isolation_in_handler(self, client, create_token):
        """Handler receives correct tenant context."""
        token = create_token(user_id="admin-1", roles=["admin"], tenant_id="org-acme")
        resp = client.get(
            "/api/users",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["tenant"] == "org-acme"

    def test_expired_token_rejected(self, client, create_token):
        """Expired JWT rejected by middleware."""
        token = create_token(user_id="user-1", expired=True)
        resp = client.get(
            "/api/profile",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code in (401, 403)

    def test_invalid_token_rejected(self, client):
        """Invalid JWT rejected by middleware."""
        resp = client.get(
            "/api/profile",
            headers={"Authorization": "Bearer invalid-token-here"},
        )
        assert resp.status_code == 401
