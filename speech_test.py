#!/usr/bin/env python3
"""
Isolated test script for TTS service
Tests the tts_service.py with different argument formats
"""

import subprocess
import sys
import os
from pathlib import Path

# Add the src directory to Python path
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

# Test configurations
tests = [
    {
        "name": "Test 1: Simple message with Spanish (default)",
        "args": ["Hello world"],
        "expected": "Message: Hello world, Language: es (default)"
    },
    {
        "name": "Test 2: Message with explicit English",
        "args": ["Hello world", "en"],
        "expected": "Message: Hello world, Language: en"
    },
    {
        "name": "Test 3: Spanish message",
        "args": ["Hola mundo", "es"],
        "expected": "Message: Hola mundo, Language: es"
    },
    {
        "name": "Test 4: Message with special characters",
        "args": ["¡Cocina! ¿Hola?", "es"],
        "expected": "Message: ¡Cocina! ¿Hola?, Language: es"
    },
    {
        "name": "Test 5: Welcome message (simulating Electron call)",
        "args": ["Bienvenido a Kitchen Tabs", "es"],
        "expected": "Message: Bienvenido a Kitchen Tabs, Language: es"
    }
]

def run_test(test_name, args):
    """Run a single test of the TTS service"""
    print(f"\n{'='*60}")
    print(f"Running: {test_name}")
    print(f"Args: {args}")
    print(f"{'='*60}")

    # Build the command
    tts_script = str(src_path / 'tts_service.py')
    cmd = [sys.executable, tts_script] + args

    print(f"Command: {' '.join(cmd)}")
    print(f"\nOutput:")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

        # Print stdout and stderr
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)

        return_code = result.returncode
        print(f"\nReturn code: {return_code}")
        return return_code == 0

    except subprocess.TimeoutExpired:
        print("ERROR: Test timed out (>10 seconds)")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def main():
    print("=" * 60)
    print("TTS Service Test Suite")
    print("=" * 60)

    results = []

    for test in tests:
        success = run_test(test["name"], test["args"])
        results.append({
            "name": test["name"],
            "passed": success
        })

    # Print summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")

    passed = sum(1 for r in results if r["passed"])
    total = len(results)

    for result in results:
        status = "✅ PASS" if result["passed"] else "❌ FAIL"
        print(f"{status}: {result['name']}")

    print(f"\n{passed}/{total} tests passed")

    if passed == total:
        print("\n✅ All tests passed!")
        return 0
    else:
        print(f"\n❌ {total - passed} test(s) failed")
        return 1

if __name__ == '__main__':
    sys.exit(main())
