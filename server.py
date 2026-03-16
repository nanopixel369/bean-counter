"""
Bean Counter - MCP Token Count & Analysis Server with Interactive Dashboard
Provides token counting, character analysis, and cost estimation for Claude models.
"""

import os
import httpx
from typing import Any
from dotenv import load_dotenv
from fastmcp import FastMCP

# Load environment variables
load_dotenv()

# Initialize FastMCP server
mcp = FastMCP("Bean Counter")

# Constants
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages/count_tokens"

# Pricing per 1M tokens (as of March 2025)
PRICING = {
    "claude-opus-4-6": {"input": 15.00, "output": 75.00},
    "claude-sonnet-4-6": {"input": 3.00, "output": 15.00},
    "claude-haiku-4-5": {"input": 0.80, "output": 4.00},
}


async def count_tokens_api(text: str, model: str) -> dict:
    """Call Anthropic token counting API."""
    if not ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY not set in environment")

    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "content-type": "application/json",
        "anthropic-version": "2023-06-01",
    }

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": text}],
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            ANTHROPIC_API_URL, json=payload, headers=headers, timeout=10.0
        )
        response.raise_for_status()
        data = response.json()
        return {"tokens": data.get("input_tokens", 0)}


def calculate_metrics(text: str, tokens: int) -> dict:
    """Calculate additional metrics."""
    char_count = len(text)
    word_count = len(text.split())
    tokens_per_char = tokens / char_count if char_count > 0 else 0

    return {
        "char_count": char_count,
        "word_count": word_count,
        "tokens_per_char": tokens_per_char,
    }


def get_cost(tokens: int, model: str, is_output: bool = False) -> float:
    """Calculate estimated cost in USD."""
    if model not in PRICING:
        return 0.0

    key = "output" if is_output else "input"
    price_per_million = PRICING[model].get(key, 0)
    cost = (tokens / 1_000_000) * price_per_million
    return cost


@mcp.tool()
async def count_tokens(text: str, model: str = "claude-sonnet-4-6") -> dict[str, Any]:
    """
    Count tokens in text and return analysis with cost estimation.

    Args:
        text: The text content to analyze
        model: Claude model name (claude-opus-4-6, claude-sonnet-4-6, claude-haiku-4-5)

    Returns:
        Dictionary with token count, metrics, and cost estimation
    """
    # Validate model
    available_models = list(PRICING.keys())
    if model not in available_models:
        return {
            "error": f"Model '{model}' not supported. Available: {available_models}"
        }

    # Call Anthropic API to get token count
    token_result = await count_tokens_api(text, model)
    tokens = token_result["tokens"]

    # Calculate metrics
    metrics = calculate_metrics(text, tokens)

    # Calculate costs
    input_cost = get_cost(tokens, model, is_output=False)
    output_tokens_estimate = tokens // 2
    output_cost = get_cost(output_tokens_estimate, model, is_output=True)
    total_cost = input_cost + output_cost

    return {
        "model": model,
        "tokens": tokens,
        "char_count": metrics["char_count"],
        "word_count": metrics["word_count"],
        "tokens_per_char": round(metrics["tokens_per_char"], 4),
        "input_cost_usd": round(input_cost, 6),
        "output_cost_estimate_usd": round(output_cost, 6),
        "total_cost_estimate_usd": round(total_cost, 6),
        "output_tokens_estimate": output_tokens_estimate,
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")
