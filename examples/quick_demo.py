#!/usr/bin/env python3
"""
NEXUS QUICK DEMO: Zero FastAPI Coding Required
==============================================

Quick demo showing Nexus workflow-to-API automation works perfectly.

Usage:
    cd apps/kailash-nexus
    python examples/quick_demo.py

Then test:
    curl -X POST http://localhost:8080/workflows/greeter/execute -H "Content-Type: application/json" -d '{"name": "Alice"}'
"""

import os
import sys

# Add src to Python path so we can import nexus
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from kailash.workflow.builder import WorkflowBuilder
from nexus import Nexus


def create_simple_workflow():
    """Create a simple greeting workflow."""
    workflow = WorkflowBuilder()

    greeting_code = """
name = parameters.get('name', 'World')
message = parameters.get('message', 'Hello')
result = {'greeting': f'{message}, {name}!', 'name': name, 'timestamp': '2025-01-15T10:00:00Z'}
"""

    workflow.add_node("PythonCodeNode", "greet", {"code": greeting_code.strip()})

    return workflow


def main():
    """Quick demo of Nexus capabilities."""

    print("🚀 Nexus Quick Demo - Zero FastAPI Coding Required")
    print("=" * 55)

    # STEP 1: Zero-config initialization
    app = Nexus(api_port=8080, mcp_port=3002)  # Use different ports
    print("✅ Nexus initialized (ports: API=8080, MCP=3002)")

    # STEP 2: Register workflow - Single call → API + CLI + MCP
    workflow = create_simple_workflow()
    app.register("greeter", workflow)
    print("✅ Workflow registered → Available on API + CLI + MCP")

    # STEP 3: Start platform
    try:
        print("\n🌐 Starting platform...")
        app.start()

        # Check health
        health = app.health_check()
        print(f"📊 Status: {health.get('status', 'unknown')}")

        print("\n" + "=" * 55)
        print("🎉 SUCCESS! Platform running with ZERO FastAPI coding!")
        print("=" * 55)

        print("\n📡 Available Endpoints:")
        print("  🌐 API: http://localhost:8080")
        print("     POST /workflows/greeter/execute")
        print("     GET  /workflows")
        print("     GET  /health")
        print("  🤖 MCP: ws://localhost:3002 (for AI agents)")

        print("\n🧪 Test Command:")
        print("  curl -X POST http://localhost:8080/workflows/greeter/execute \\")
        print("    -H 'Content-Type: application/json' \\")
        print('    -d \'{"name": "Alice", "message": "Welcome"}\'')

        print("\n💡 PROOF: This required:")
        print("   ❌ 0 lines of FastAPI code")
        print("   ❌ 0 route definitions")
        print("   ❌ 0 middleware setup")
        print("   ✅ Just workflow + app.register()!")

        print("\n⏹️  Press Ctrl+C to stop...")

        # Run for 30 seconds to allow testing
        import time

        start_time = time.time()
        while time.time() - start_time < 30:
            time.sleep(1)

        print("\n⏰ Demo timeout reached - stopping platform...")
        app.stop()
        print("✅ Platform stopped gracefully")

        return True

    except KeyboardInterrupt:
        print("\n\n🛑 Demo stopped by user")
        app.stop()
        print("✅ Platform stopped gracefully")
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        print("🔍 Possible causes:")
        print("  • Ports 8080/3002 in use")
        print("  • Missing dependencies")

        return False


if __name__ == "__main__":
    success = main()
    if success:
        print("\n🏆 Demo completed successfully!")
        print("✅ Nexus provides complete workflow-to-API automation")
        print("✅ Zero FastAPI coding required")
        print("✅ Multi-channel platform (API + CLI + MCP)")
    else:
        print("\n❌ Demo failed - check error messages above")
        exit(1)
