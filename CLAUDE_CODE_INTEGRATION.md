# Claude Code CLI Integration for DeepTutor

This document describes the modifications made to DeepTutor to support Claude Code CLI as an LLM provider, allowing the use of Anthropic Max subscriptions instead of direct API keys.

## Overview

DeepTutor was modified to route LLM calls through the Claude Code CLI (`claude.cmd`), which authenticates using your Max subscription's OAuth token. This eliminates the need for a separate Anthropic API key.

## What Was Changed

### New Files Created

| File | Purpose |
|------|---------|
| `src/services/llm/claude_code_provider.py` | New provider that wraps Claude Code CLI for LLM calls |
| `test_claude_code_integration.py` | Test script to verify the integration works |
| `.env` | Configuration file for Claude Code mode |

### Modified Files

#### `src/services/llm/factory.py`

- Added import for `claude_code_provider`
- Added `CLAUDE_CODE = "claude_code"` to `LLMMode` enum
- Updated `get_llm_mode()` to detect `LLM_BINDING=claude_code`
- Modified `complete()` to route to `claude_code_provider` when in Claude Code mode
- Modified `stream()` to route to `claude_code_provider` when in Claude Code mode
- Added `claude_code` to `API_PROVIDER_PRESETS` with available models

#### `.env.example`

- Added documentation section for Claude Code CLI configuration
- Added examples for `LLM_BINDING=claude_code` and `CLAUDE_CODE_PATH`

## How It Works

```
DeepTutor Agent
      |
      v
factory.complete() / factory.stream()
      |
      v
[LLM_BINDING == "claude_code"?]
      |
      +-- Yes --> claude_code_provider.py
      |                  |
      |                  v
      |           subprocess.run("claude.cmd -p - --output-format json ...")
      |                  |
      |                  v
      |           Claude Code CLI (uses Max subscription OAuth)
      |                  |
      |                  v
      |           Anthropic API (via your subscription)
      |
      +-- No --> cloud_provider.py or local_provider.py (original behavior)
```

### claude_code_provider.py Details

The provider:

1. **Builds prompts** - Combines system prompt and messages into a single prompt string
2. **Executes CLI** - Runs `claude.cmd` with:
   - `-p -` (read prompt from stdin)
   - `--output-format json` or `--output-format stream-json`
   - `--model <model-name>`
   - `--dangerously-skip-permissions` (required for non-interactive use)
3. **Parses response** - Extracts result from JSON output
4. **Supports streaming** - Uses `stream-json` format for real-time responses

### Supported Models

- `claude-sonnet-4-20250514` (default)
- `claude-opus-4-5-20251101`
- `claude-3-5-sonnet-20241022`
- `claude-3-5-haiku-20241022`

## Configuration

### Environment Variables

```bash
# Required for Claude Code mode
LLM_BINDING=claude_code
LLM_MODEL=claude-sonnet-4-20250514

# Optional: Custom path to claude CLI
CLAUDE_CODE_PATH=C:\Users\YourUser\AppData\Roaming\npm\claude.cmd
```

### Prerequisites

1. **Claude Code CLI installed**:
   ```bash
   npm install -g @anthropic-ai/claude-code
   ```

2. **Authenticated with Max subscription**:
   ```bash
   claude login
   ```

3. **Embeddings provider** (Claude doesn't provide embeddings):
   - Option A: Ollama with `nomic-embed-text` (free, local)
   - Option B: OpenAI API key for embeddings only
   - Option C: Jina AI free tier

## Limitations

1. **No direct API control** - Temperature/max_tokens are handled by Claude Code defaults
2. **Subprocess overhead** - Each call spawns a new process (slower than direct API)
3. **No tool use passthrough** - Claude Code's tools are not exposed to DeepTutor
4. **Session management** - Each call is independent (no multi-turn context at CLI level)

## Testing

Run the test script to verify integration:

```bash
cd D:\DeepTutor
python test_claude_code_integration.py
```

Expected output:
```
[Test 1] Checking Claude Code CLI availability...
  CLI available: True
[Test 2] Testing simple completion...
  SUCCESS!
[Test 3] Testing streaming completion...
  SUCCESS!
ALL TESTS PASSED!
```

## Reverting to Standard API

To use the standard Anthropic API instead:

```bash
# In .env
LLM_BINDING=anthropic
LLM_MODEL=claude-3-5-sonnet-20241022
LLM_API_KEY=sk-ant-api03-your-key-here
LLM_HOST=https://api.anthropic.com/v1
```
