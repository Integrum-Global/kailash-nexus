#!/usr/bin/env python3
"""
NEXUS COMPREHENSIVE DEMO: Zero FastAPI Coding Required
=====================================================

This example demonstrates that Nexus requires ZERO FastAPI coding and provides
complete high-level workflow-to-API automation through SDK integration.

Key Findings:
- Single workflow registration → API + CLI + MCP exposure automatically
- Zero-config setup with enterprise defaults
- Uses SDK's enterprise gateway (no custom FastAPI needed)
- Production-ready features enabled by default
- Progressive enhancement for complex scenarios

Usage:
    cd apps/kailash-nexus
    python examples/comprehensive_demo.py

Then test:
- API: curl http://localhost:8000/workflows/data-processor/execute -X POST -H "Content-Type: application/json" -d '{"data": [1,2,3,4,5]}'
- MCP: AI agents can call the workflow directly
- CLI: nexus run data-processor --data '[1,2,3,4,5]'
"""

import os
import sys

# Add src to Python path so we can import nexus
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import json

from kailash.runtime.local import LocalRuntime
from kailash.workflow.builder import WorkflowBuilder
from nexus import Nexus

# ==============================================================================
# EXAMPLE 1: ZERO-CONFIG DATA PROCESSING WORKFLOW
# ==============================================================================


def create_data_processing_workflow():
    """Create a data processing workflow with multiple nodes."""
    workflow = WorkflowBuilder()

    # Input validation node
    validation_code = """
def validate_input(data):
    if not isinstance(data, list):
        raise ValueError("Data must be a list")
    if len(data) == 0:
        raise ValueError("Data cannot be empty")
    if not all(isinstance(x, (int, float)) for x in data):
        raise ValueError("All data items must be numbers")
    return {"validated_data": data}

result = validate_input(parameters.get('data', []))
"""
    workflow.add_node("PythonCodeNode", "validator", {"code": validation_code.strip()})

    # Data processing node
    processing_code = """
def process_data(validated_data):
    data = validated_data
    result = {
        "original": data,
        "count": len(data),
        "sum": sum(data),
        "average": sum(data) / len(data),
        "min": min(data),
        "max": max(data),
        "processed": [x * 2 for x in data]  # Double each value
    }
    return {"result": result}

result = process_data(parameters.get('validated_data', []))
"""
    workflow.add_node("PythonCodeNode", "processor", {"code": processing_code.strip()})

    # Results formatting node
    formatting_code = """
def format_results(result):
    data_result = result
    formatted = {
        "status": "success",
        "summary": f"Processed {data_result['count']} numbers",
        "statistics": {
            "sum": data_result["sum"],
            "average": round(data_result["average"], 2),
            "range": f"{data_result['min']} - {data_result['max']}"
        },
        "original_data": data_result["original"],
        "processed_data": data_result["processed"]
    }
    return {"formatted_result": formatted}

result = format_results(parameters.get('result', {}))
"""
    workflow.add_node("PythonCodeNode", "formatter", {"code": formatting_code.strip()})

    # Connect the workflow pipeline
    workflow.add_connection(
        "validator", "validated_data", "processor", "validated_data"
    )
    workflow.add_connection("processor", "result", "formatter", "result")

    return workflow


# ==============================================================================
# EXAMPLE 2: SIMPLE GREETING WORKFLOW (like basic_usage.py)
# ==============================================================================


def create_greeting_workflow():
    """Create a simple greeting workflow similar to basic_usage.py."""
    workflow = WorkflowBuilder()

    greeting_code = """
name = parameters.get('name', 'World')
message = parameters.get('message', 'Hello')
result = {'greeting': f'{message}, {name}!', 'name': name, 'message': message}
"""

    workflow.add_node("PythonCodeNode", "greet", {"code": greeting_code.strip()})

    return workflow


# ==============================================================================
# EXAMPLE 3: DATABASE SIMULATION WORKFLOW
# ==============================================================================


def create_user_management_workflow():
    """Create a user management workflow with database simulation."""
    workflow = WorkflowBuilder()

    # User data preparation
    prep_code = """
def prepare_user_data(name, email, age=None):
    if not name or not name.strip():
        raise ValueError("Name is required")
    if not email or "@" not in email:
        raise ValueError("Valid email is required")

    user_data = {
        "name": name.strip(),
        "email": email.strip().lower(),
        "age": int(age) if age else None,
        "created_at": "2025-01-15T10:00:00Z"  # Simulated timestamp
    }

    return {"user_data": user_data}

name = parameters.get('name', '')
email = parameters.get('email', '')
age = parameters.get('age')

result = prepare_user_data(name, email, age)
"""
    workflow.add_node("PythonCodeNode", "data_prep", {"code": prep_code.strip()})

    # Simulate database operation
    db_code = """
def simulate_database_insert(user_data):
    # In production, this would be AsyncSQLDatabaseNode with real database
    user = user_data

    # Simulate database insertion
    user["user_id"] = f"user_{hash(user['email']) % 10000}"

    return {
        "operation": "user_created",
        "user": user,
        "database": "users_db",
        "table": "users"
    }

user_data = parameters.get('user_data', {})
result = simulate_database_insert(user_data)
"""
    workflow.add_node("PythonCodeNode", "database", {"code": db_code.strip()})

    # Response formatting
    response_code = """
def format_response(operation, user, database, table):
    return {
        "status": "success",
        "operation": operation,
        "user_created": {
            "user_id": user["user_id"],
            "name": user["name"],
            "email": user["email"],
            "age": user["age"]
        },
        "database_info": {
            "database": database,
            "table": table,
            "timestamp": user["created_at"]
        }
    }

operation = parameters.get('operation', '')
user = parameters.get('user', {})
database = parameters.get('database', '')
table = parameters.get('table', '')

result = format_response(operation, user, database, table)
"""
    workflow.add_node("PythonCodeNode", "formatter", {"code": response_code.strip()})

    # Connect database workflow
    workflow.add_connection("data_prep", "user_data", "database", "user_data")
    workflow.add_connection("database", "operation", "formatter", "operation")
    workflow.add_connection("database", "user", "formatter", "user")
    workflow.add_connection("database", "database", "formatter", "database")
    workflow.add_connection("database", "table", "formatter", "table")

    return workflow


# ==============================================================================
# MAIN NEXUS APPLICATION - ZERO FASTAPI CODING REQUIRED!
# ==============================================================================


def main():
    """
    Main application demonstrating Nexus capabilities.

    This is the ENTIRE setup required - NO FastAPI coding needed!
    """

    print("🚀 Starting Nexus Comprehensive Demo")
    print("=" * 50)

    # STEP 1: Initialize Nexus with zero configuration
    # This automatically sets up:
    # - Enterprise FastAPI server via create_gateway()
    # - WebSocket MCP server for AI agents
    # - CLI interface preparation
    # - Health monitoring and durability
    app = Nexus()

    print("✅ Nexus initialized with zero configuration")

    # STEP 2: Register workflows - Single call exposes on ALL channels
    print("\n📝 Registering workflows...")

    # Data processing workflow
    data_workflow = create_data_processing_workflow()
    app.register("data-processor", data_workflow)
    print("  ✅ data-processor: Registered → API + CLI + MCP")

    # Greeting workflow (like basic_usage.py)
    greeting_workflow = create_greeting_workflow()
    app.register("greeter", greeting_workflow)
    print("  ✅ greeter: Registered → API + CLI + MCP")

    # Database workflow
    db_workflow = create_user_management_workflow()
    app.register("user-manager", db_workflow)
    print("  ✅ user-manager: Registered → API + CLI + MCP")

    # STEP 3: Optional enterprise features (progressive enhancement)
    print("\n🔒 Configuring enterprise features...")
    app.auth.strategy = "rbac"  # Role-based access control
    app.monitoring.interval = 30  # Performance monitoring
    app.api.cors_enabled = True  # CORS for web clients

    print("  ✅ Enterprise features configured")

    # STEP 4: Start all channels with single command
    print("\n🌐 Starting multi-channel platform...")
    print("This single command starts:")
    print("  • REST API server (enterprise-grade)")
    print("  • WebSocket MCP server (for AI agents)")
    print("  • CLI interface (for command-line use)")
    print("  • Health monitoring and metrics")
    print("  • Auto-discovery and hot-reload")

    try:
        app.start()

        print("\n" + "=" * 60)
        print("🎉 NEXUS PLATFORM RUNNING - ZERO FASTAPI CODING REQUIRED!")
        print("=" * 60)

        # Check platform health
        health = app.health_check()
        print(f"\n📊 Platform Status: {health.get('status', 'unknown')}")

        print("\n📡 Available Interfaces:")
        print("  🌐 REST API: http://localhost:8000")
        print("    • POST /workflows/data-processor/execute")
        print("    • POST /workflows/greeter/execute")
        print("    • POST /workflows/user-manager/execute")
        print("    • GET  /workflows (list all workflows)")
        print("    • GET  /health (health check)")

        print("\n  🤖 MCP Interface: ws://localhost:3001")
        print("    • AI agents can call workflows directly")
        print("    • Real-time WebSocket communication")
        print("    • Tool discovery and execution")

        print("\n  ⌨️  CLI Interface: nexus run <workflow>")
        print("    • nexus run data-processor --data '[1,2,3,4,5]'")
        print("    • nexus run greeter --name 'Alice'")
        print("    • nexus run user-manager --name 'John' --email 'john@example.com'")

        print("\n🧪 Test Commands:")
        print("  # Test data processor")
        print(
            "  curl -X POST http://localhost:8000/workflows/data-processor/execute \\"
        )
        print('    -H "Content-Type: application/json" \\')
        print("    -d '{\"data\": [1, 2, 3, 4, 5]}'")

        print("\n  # Test greeter")
        print("  curl -X POST http://localhost:8000/workflows/greeter/execute \\")
        print('    -H "Content-Type: application/json" \\')
        print('    -d \'{"name": "Alice", "message": "Welcome"}\'')

        print("\n  # Test user manager")
        print("  curl -X POST http://localhost:8000/workflows/user-manager/execute \\")
        print('    -H "Content-Type: application/json" \\')
        print('    -d \'{"name": "Alice", "email": "alice@example.com", "age": 30}\'')

        print("\n" + "=" * 60)
        print("💡 KEY INSIGHT: This entire multi-channel platform required:")
        print("   ❌ ZERO FastAPI route definitions")
        print("   ❌ ZERO custom middleware setup")
        print("   ❌ ZERO API endpoint coding")
        print("   ❌ ZERO WebSocket handling")
        print("   ❌ ZERO CLI command setup")
        print("   ✅ ONLY workflow definitions + app.register() calls!")
        print("=" * 60)

        print("\n⏹️  Press Ctrl+C to stop the platform...")

        # Keep running until interrupted
        import signal
        import time

        def signal_handler(sig, frame):
            print("\n\n🛑 Shutting down Nexus platform...")
            try:
                app.stop()
                print("✅ Platform stopped gracefully")
            except Exception as e:
                print(f"⚠️ Shutdown warning: {e}")
            exit(0)

        signal.signal(signal.SIGINT, signal_handler)

        while True:
            time.sleep(1)

    except Exception as e:
        print(f"❌ Error starting platform: {e}")
        print(f"   Error type: {type(e).__name__}")
        print("\n🔍 This might be due to:")
        print("  • Ports 8000 or 3001 already in use")
        print("  • Missing dependencies")
        print("  • Configuration issues")

        # Let's try to get more specific error info
        import traceback

        print("\n🐛 Full error traceback:")
        traceback.print_exc()

        return False

    return True


if __name__ == "__main__":
    success = main()
    if not success:
        exit(1)
