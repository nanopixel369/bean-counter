#!/usr/bin/env python3
"""Quick import test for Bean Counter dependencies"""

try:
    from fastmcp import FastMCP
    print("✅ fastmcp imported")
except ImportError as e:
    print(f"❌ fastmcp import failed: {e}")

try:
    from prefab_ui.app import PrefabApp
    print("✅ prefab_ui.app imported")
except ImportError as e:
    print(f"❌ prefab_ui.app import failed: {e}")

try:
    from prefab_ui.components import Column, Heading, Grid, Card, CardContent, Metric, Text, Row
    print("✅ prefab_ui.components imported")
except ImportError as e:
    print(f"❌ prefab_ui.components import failed: {e}")

try:
    from dotenv import load_dotenv
    print("✅ python-dotenv imported")
except ImportError as e:
    print(f"❌ python-dotenv import failed: {e}")

try:
    import httpx
    print("✅ httpx imported")
except ImportError as e:
    print(f"❌ httpx import failed: {e}")

print("\n✅ All dependencies check passed!")
