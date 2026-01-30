#!/usr/bin/env python3
"""
Simple test script to verify Python installation and basic imports
"""

import sys
import os

print(f"Python version: {sys.version}")
print(f"Current directory: {os.getcwd()}")

# Test basic imports
try:
    import asyncio
    print("✅ asyncio imported successfully")
except ImportError as e:
    print(f"❌ asyncio import failed: {e}")

try:
    import aiohttp
    print("✅ aiohttp imported successfully")
except ImportError as e:
    print(f"❌ aiohttp import failed: {e}")

try:
    import aiogram
    print("✅ aiogram imported successfully")
except ImportError as e:
    print(f"❌ aiogram import failed: {e}")

try:
    import pandas
    print("✅ pandas imported successfully")
except ImportError as e:
    print(f"❌ pandas import failed: {e}")

try:
    import numpy
    print("✅ numpy imported successfully")
except ImportError as e:
    print(f"❌ numpy import failed: {e}")

print("\n🔧 Testing basic functionality...")

# Test async functionality
async def test_async():
    print("✅ Async function works")
    return "async test complete"

# Run the test
if __name__ == "__main__":
    result = asyncio.run(test_async())
    print(f"✅ Result: {result}")
    print("\n🎉 Basic Python test completed successfully!")
