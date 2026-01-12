"""
Claude Code CLI Provider
========================

Wraps Claude Code CLI to leverage Max subscription authentication.
This allows DeepTutor to use Claude via the CLI instead of direct API calls.

Usage:
    Set LLM_BINDING=claude_code in your .env file
    Ensure Claude Code CLI is installed and authenticated with Max subscription
"""

import subprocess
import json
import os
import time
import asyncio
from typing import AsyncGenerator, Dict, List, Optional, Any
from pathlib import Path


# Default configuration
DEFAULT_TIMEOUT = 900  # 15 minutes
DEFAULT_MODEL = "claude-sonnet-4-20250514"


def get_claude_cmd() -> str:
    """Get the path to claude CLI executable."""
    # Check for custom path in environment
    custom_path = os.getenv("CLAUDE_CODE_PATH")
    if custom_path and Path(custom_path).exists():
        return custom_path

    # Default Windows path
    windows_path = Path.home() / "AppData" / "Roaming" / "npm" / "claude.cmd"
    if windows_path.exists():
        return str(windows_path)

    # Default Unix path (assume it's in PATH)
    return "claude"


async def complete(
    prompt: str,
    system_prompt: str = "You are a helpful assistant.",
    model: Optional[str] = None,
    messages: Optional[List[Dict[str, str]]] = None,
    **kwargs,
) -> str:
    """
    Complete a prompt using Claude Code CLI.

    Args:
        prompt: The user prompt
        system_prompt: System prompt for context
        model: Model name (e.g., claude-sonnet-4-20250514)
        messages: Pre-built messages array (will be converted to prompt)
        **kwargs: Additional parameters (temperature, max_tokens - note: CLI has limited support)

    Returns:
        str: The LLM response text
    """
    model = model or os.getenv("LLM_MODEL", DEFAULT_MODEL)
    timeout = kwargs.get("timeout", DEFAULT_TIMEOUT)

    # Build the full prompt
    full_prompt = _build_prompt(prompt, system_prompt, messages)

    # Build command
    cmd = [
        get_claude_cmd(),
        "-p", "-",  # Read prompt from stdin
        "--output-format", "json",
        "--model", model,
        "--dangerously-skip-permissions"  # Required for non-interactive use
    ]

    # Run in thread pool to not block async loop
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,
        lambda: _run_cli_sync(cmd, full_prompt, timeout)
    )

    return result


async def stream(
    prompt: str,
    system_prompt: str = "You are a helpful assistant.",
    model: Optional[str] = None,
    messages: Optional[List[Dict[str, str]]] = None,
    **kwargs,
) -> AsyncGenerator[str, None]:
    """
    Stream a response using Claude Code CLI with stream-json output.

    Args:
        prompt: The user prompt
        system_prompt: System prompt for context
        model: Model name
        messages: Pre-built messages array
        **kwargs: Additional parameters

    Yields:
        str: Response text chunks
    """
    model = model or os.getenv("LLM_MODEL", DEFAULT_MODEL)
    timeout = kwargs.get("timeout", DEFAULT_TIMEOUT)

    # Build the full prompt
    full_prompt = _build_prompt(prompt, system_prompt, messages)

    # Build command with stream-json format
    cmd = [
        get_claude_cmd(),
        "-p", "-",
        "--output-format", "stream-json",
        "--model", model,
        "--dangerously-skip-permissions"
    ]

    # Use async subprocess for streaming
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    # Send prompt
    process.stdin.write(full_prompt.encode('utf-8'))
    await process.stdin.drain()
    process.stdin.close()

    accumulated_text = ""
    start_time = time.time()

    try:
        async for line in process.stdout:
            # Check timeout
            if time.time() - start_time > timeout:
                process.kill()
                break

            line_str = line.decode('utf-8', errors='replace').strip()
            if not line_str:
                continue

            try:
                event = json.loads(line_str)
                event_type = event.get("type", "")

                # Handle text delta events
                if event_type == "content_block_delta":
                    delta = event.get("delta", {})
                    if delta.get("type") == "text_delta":
                        text = delta.get("text", "")
                        if text:
                            accumulated_text += text
                            yield text

                # Handle assistant message with direct text
                elif event_type == "assistant":
                    message = event.get("message", {})
                    content_list = message.get("content", [])
                    for content in content_list:
                        if content.get("type") == "text":
                            text = content.get("text", "")
                            if text and text not in accumulated_text:
                                yield text

                # Handle final result
                elif event_type == "result":
                    result_text = event.get("result", "")
                    if result_text and not accumulated_text:
                        yield result_text

            except json.JSONDecodeError:
                # Not JSON, might be raw output
                continue

    except Exception as e:
        # Log error but don't crash
        print(f"[Claude Code Provider] Stream error: {e}")
    finally:
        await process.wait()


def _build_prompt(
    prompt: str,
    system_prompt: str,
    messages: Optional[List[Dict[str, str]]] = None
) -> str:
    """
    Build a full prompt string from components.

    Claude Code CLI expects a single prompt, so we need to combine
    system prompt and messages into one string.
    """
    parts = []

    # Add system prompt as context
    if system_prompt and system_prompt != "You are a helpful assistant.":
        parts.append(f"<system>\n{system_prompt}\n</system>\n")

    # Add messages if provided
    if messages:
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                parts.append(f"<system>\n{content}\n</system>\n")
            elif role == "assistant":
                parts.append(f"<assistant>\n{content}\n</assistant>\n")
            else:  # user
                parts.append(f"{content}\n")
    else:
        # Just use the direct prompt
        parts.append(prompt)

    return "\n".join(parts)


def _run_cli_sync(cmd: List[str], prompt: str, timeout: int) -> str:
    """
    Run Claude Code CLI synchronously.

    Args:
        cmd: Command and arguments
        prompt: The prompt to send via stdin
        timeout: Timeout in seconds

    Returns:
        str: Response text
    """
    try:
        result = subprocess.run(
            cmd,
            input=prompt,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=timeout
        )

        if result.returncode != 0:
            error_msg = result.stderr or f"CLI returned code {result.returncode}"
            raise Exception(f"Claude Code CLI error: {error_msg}")

        stdout = result.stdout.strip()
        if not stdout:
            return ""

        # Try to parse as JSON
        try:
            response = json.loads(stdout)
            return response.get("result", stdout)
        except json.JSONDecodeError:
            # Plain text response
            return stdout

    except subprocess.TimeoutExpired:
        raise Exception(f"Claude Code CLI timed out after {timeout} seconds")
    except FileNotFoundError:
        raise Exception(
            "Claude Code CLI not found. Install with: npm install -g @anthropic-ai/claude-code\n"
            "Or set CLAUDE_CODE_PATH environment variable to the executable path."
        )


async def fetch_models(base_url: str = None, api_key: str = None) -> List[str]:
    """
    Return available models for Claude Code CLI.

    The CLI supports these models via Max subscription.
    """
    return [
        "claude-sonnet-4-20250514",
        "claude-opus-4-5-20251101",
        "claude-3-5-sonnet-20241022",
        "claude-3-5-haiku-20241022",
    ]


def is_available() -> bool:
    """Check if Claude Code CLI is available and authenticated."""
    try:
        cmd = [get_claude_cmd(), "--version"]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0
    except Exception:
        return False


__all__ = [
    "complete",
    "stream",
    "fetch_models",
    "is_available",
    "get_claude_cmd",
]
