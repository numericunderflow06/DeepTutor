"""
Test script for Claude Code CLI integration with DeepTutor.
Run this to verify the integration works before starting the full application.
"""

import asyncio
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Load environment variables from .env
from pathlib import Path
env_file = Path(__file__).parent / '.env'
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()


async def test_claude_code_provider():
    """Test the Claude Code provider directly."""
    print("=" * 60)
    print("Testing Claude Code CLI Provider")
    print("=" * 60)

    from src.services.llm import claude_code_provider

    # Test 1: Check if CLI is available
    print("\n[Test 1] Checking Claude Code CLI availability...")
    is_avail = claude_code_provider.is_available()
    print(f"  CLI available: {is_avail}")
    if not is_avail:
        print("  ERROR: Claude Code CLI not found!")
        print("  Install with: npm install -g @anthropic-ai/claude-code")
        print("  Then authenticate: claude login")
        return False

    # Test 2: Test a simple completion
    print("\n[Test 2] Testing simple completion...")
    try:
        response = await claude_code_provider.complete(
            prompt="Say 'Hello from DeepTutor!' and nothing else.",
            system_prompt="You are a helpful assistant. Be very brief.",
            model=os.getenv("LLM_MODEL", "claude-sonnet-4-20250514"),
            timeout=60
        )
        print(f"  Response: {response[:200]}...")
        print("  SUCCESS!")
    except Exception as e:
        print(f"  ERROR: {e}")
        return False

    # Test 3: Test streaming
    print("\n[Test 3] Testing streaming completion...")
    try:
        chunks = []
        async for chunk in claude_code_provider.stream(
            prompt="Count from 1 to 5, one number per line.",
            system_prompt="You are a helpful assistant. Be very brief.",
            model=os.getenv("LLM_MODEL", "claude-sonnet-4-20250514"),
            timeout=60
        ):
            chunks.append(chunk)
            print(f"  Chunk: {repr(chunk)}")
        full_response = "".join(chunks)
        print(f"  Full response: {full_response[:200]}")
        print("  SUCCESS!")
    except Exception as e:
        print(f"  ERROR: {e}")
        return False

    print("\n" + "=" * 60)
    print("All tests passed! Claude Code integration is working.")
    print("=" * 60)
    return True


async def test_factory_routing():
    """Test that the factory correctly routes to Claude Code provider."""
    print("\n" + "=" * 60)
    print("Testing Factory Routing")
    print("=" * 60)

    from src.services.llm import factory

    # Check mode
    mode = factory.get_llm_mode()
    print(f"\n[Info] Current LLM mode: {mode}")
    print(f"[Info] LLM_BINDING env: {os.getenv('LLM_BINDING', 'not set')}")
    print(f"[Info] LLM_MODEL env: {os.getenv('LLM_MODEL', 'not set')}")

    if mode != factory.LLMMode.CLAUDE_CODE:
        print("\n  WARNING: Not in claude_code mode!")
        print("  Set LLM_BINDING=claude_code in .env file")
        return False

    # Test factory complete
    print("\n[Test] Testing factory.complete()...")
    try:
        response = await factory.complete(
            prompt="What is 2 + 2? Answer with just the number.",
            system_prompt="You are a math assistant. Be extremely brief.",
        )
        print(f"  Response: {response[:100]}")
        print("  SUCCESS!")
    except Exception as e:
        print(f"  ERROR: {e}")
        return False

    return True


async def main():
    print("\nDeepTutor Claude Code Integration Test")
    print("=" * 60)
    print(f"Working directory: {os.getcwd()}")
    print(f"Python version: {sys.version}")
    print()

    # Run tests
    provider_ok = await test_claude_code_provider()
    if not provider_ok:
        print("\nProvider test failed. Fix the issues above and try again.")
        return

    factory_ok = await test_factory_routing()
    if not factory_ok:
        print("\nFactory routing test failed. Check your .env configuration.")
        return

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED!")
    print("=" * 60)
    print("\nYou can now start DeepTutor with:")
    print("  cd D:\\DeepTutor")
    print("  python scripts/start_web.py")
    print("\nOr start backend only:")
    print("  python src/api/run_server.py")


if __name__ == "__main__":
    asyncio.run(main())
