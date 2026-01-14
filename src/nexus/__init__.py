"""Kailash Nexus - Zero-configuration workflow orchestration.

The simplest way to expose workflows across API, CLI, and MCP channels.

Usage:
    from nexus import Nexus

    app = Nexus()  # Simple case
    app.start()

    # Or with enterprise features
    app = Nexus(enable_auth=True, enable_monitoring=True)
    app.start()
"""

from .core import Nexus, create_nexus

__version__ = "1.1.3"
__all__ = ["Nexus", "create_nexus"]
