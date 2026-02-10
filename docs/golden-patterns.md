# Golden Patterns for Codegen

Production-validated patterns for AI codegen agents building Kailash applications.

## Overview

10 ranked patterns derived from analysis of three production projects (382K LOC total):

- **agentic-os** (218K LOC): 97 service handlers, 96 models, 23 Kaizen agents
- **impact-verse** (89K LOC): 21 Nexus gateways, 34 models, 13 custom nodes
- **journeymate-backend** (75K LOC): 7 DataFlow instances, 45 models, 17 custom nodes

## Pattern Quick Reference

| #   | Pattern               | When to Use                                  | Key Import                                             |
| --- | --------------------- | -------------------------------------------- | ------------------------------------------------------ |
| 1   | **Nexus Handler**     | API endpoints with full Python access        | `from nexus import Nexus`                              |
| 2   | **DataFlow Model**    | Database entities (auto-generates 11 nodes)  | `from dataflow import DataFlow`                        |
| 3   | **Nexus+DataFlow**    | API with database (CRITICAL config required) | Both above                                             |
| 4   | **Auth Middleware**   | JWT + RBAC + tenant isolation                | `from nexus.auth.plugin import NexusAuthPlugin`        |
| 5   | **Multi-DataFlow**    | Multiple databases per concern               | `from dataflow import DataFlow`                        |
| 6   | **Custom Node**       | Reusable logic across workflows              | `from kailash.nodes.base import Node`                  |
| 7   | **Kaizen Agent**      | LLM-powered features                         | `from kaizen.core.base_agent import BaseAgent`         |
| 8   | **Workflow Builder**  | Multi-step orchestration                     | `from kailash.workflow.builder import WorkflowBuilder` |
| 9   | **AsyncLocalRuntime** | Docker/FastAPI async execution               | `from kailash.runtime import AsyncLocalRuntime`        |
| 10  | **MCP Integration**   | AI agent tool exposure                       | `from nexus import Nexus`                              |

## Decision Tree

```
What are you building?
├── API with database?
│   ├── Simple CRUD → Pattern 1 + 2 (SaaS Template)
│   ├── Multi-model → Pattern 3 + 5 (Multi-Tenant Template)
│   ├── Complex validation → Pattern 8 + 6
│   └── Needs auth → Add Pattern 4
├── AI-powered feature?
│   ├── Single LLM call → Pattern 1 + Kaizen inside
│   ├── Multi-step agent → Pattern 7 + 1
│   ├── RAG/search → Pattern 7 + 10 + DataFlow pgvector
│   └── AI agent integration → Pattern 10
└── Background/batch?
    ├── Event-driven → Pattern 8 + 9
    ├── Scheduled → Pattern 8 + external scheduler
    └── Bulk import → Pattern 2 with BulkCreateNode
```

## Authentication (NexusAuthPlugin)

**CRITICAL**: Use correct WS02 imports and parameter names.

```python
from nexus.auth.plugin import NexusAuthPlugin
from nexus.auth import JWTConfig, TenantConfig
from nexus.auth.dependencies import RequireRole, RequirePermission, get_current_user

auth = NexusAuthPlugin(
    jwt=JWTConfig(
        secret=os.environ["JWT_SECRET"],       # 'secret', NOT 'secret_key'
        algorithm="HS256",
        exempt_paths=["/health"],               # 'exempt_paths', NOT 'exclude_paths'
    ),
    rbac={                                      # Plain dict, NOT RBACConfig
        "admin": ["*"],
        "member": ["contacts:read", "contacts:create"],
    },
    tenant_isolation=TenantConfig(              # TenantConfig object, NOT True
        jwt_claim="tenant_id",
        admin_role="admin",                     # Singular string, NOT 'admin_roles'
    ),
)
```

### Common Auth Mistakes

| Wrong                                | Correct                                         |
| ------------------------------------ | ----------------------------------------------- |
| `JWTConfig(secret_key=...)`          | `JWTConfig(secret=...)`                         |
| `JWTConfig(secret="short")`          | `JWTConfig(secret=...)` (min 32 chars required) |
| `JWTConfig(exclude_paths=[...])`     | `JWTConfig(exempt_paths=[...])`                 |
| `RBACConfig(roles={...})`            | `rbac={"admin": ["*"], ...}` (plain dict)       |
| `tenant_isolation=True`              | `tenant_isolation=TenantConfig(...)`            |
| `TenantConfig(admin_roles=[...])`    | `TenantConfig(admin_role="admin")` (singular)   |
| `from nexus.plugins.auth import ...` | `from nexus.auth.plugin import NexusAuthPlugin` |

## Critical Configuration

```python
# ALWAYS use these settings
app = Nexus(auto_discovery=False)              # Prevents blocking with DataFlow

db = DataFlow(
    database_url="...",
    enable_model_persistence=False,            # Fast startup
    auto_migrate=False,                        # Docker-safe
)

runtime = AsyncLocalRuntime()                  # For async contexts
results, run_id = await runtime.execute_workflow_async(workflow.build(), inputs={})
```

## Anti-Patterns

1. **PythonCodeNode for business logic** - Use `@app.handler()` instead (sandbox blocks imports)
2. **Raw FastAPI alongside Nexus** - Use Nexus public APIs (handler, include_router, endpoint)
3. **Building auth from scratch** - Use NexusAuthPlugin
4. **DataFlow instance per request** - Create at module level, reuse
5. **WorkflowBuilder for simple CRUD** - Use handler for single-step operations
6. **Mocking in integration tests** - Use real `sqlite:///:memory:` database
7. **Accessing `app._gateway.app`** - Use public middleware API

## Scaffolding Templates

Three production-ready templates available:

1. **SaaS API Backend** - REST API + auth + DataFlow + multi-channel
2. **AI Agent Backend** - Kaizen agents + MCP tools + Nexus exposure
3. **Multi-Tenant Enterprise** - Multiple databases + tenant isolation + audit

## Detailed References

- **Skill files** (for AI codegen agents):
  - `.claude/skills/03-nexus/golden-patterns-catalog.md` - Full 10 patterns with examples
  - `.claude/skills/03-nexus/codegen-decision-tree.md` - Decision tree + anti-patterns + templates
- **Validation tests**: `tests/docs/golden_patterns/` (53 tests) + `tests/docs/templates/` (19 tests)
- **Specs**: `instructions/upgrade-frameworks/04-golden-patterns/`
