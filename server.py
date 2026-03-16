"""
Bean Counter - MCP Token Count & Analysis Server with Interactive Dashboard
Provides token counting, character analysis, and cost estimation for Claude models.
Uses Prefab UI for interactive dashboard rendering in FastMCP.
"""

import os
import httpx
from typing import Any
from dotenv import load_dotenv
from fastmcp import FastMCP
from prefab_ui.app import PrefabApp
from prefab_ui.components import (
    Column,
    Heading,
    Grid,
    Card,
    CardContent,
    Metric,
    Text,
    Row,
)

# Load environment variables
load_dotenv()

# Initialize FastMCP server
mcp = FastMCP("Bean Counter")

# Constants
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages/count_tokens"

# Pricing per 1M tokens (as of March 2026)
PRICING = {
    "claude-opus-4-6": {"input": 5.00, "output": 25.00},
    "claude-sonnet-4-6": {"input": 3.00, "output": 15.00},
    "claude-haiku-4-5": {"input": 1.00, "output": 5.00},
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

@mcp.tool(app=True)
async def count_tokens(text: str, model: str = "claude-sonnet-4-6") -> PrefabApp:
    """
    Count tokens in text and return interactive dashboard with analysis metrics.

    Args:
        text: The text content to analyze
        model: Claude model name (claude-opus-4-6, claude-sonnet-4-6, claude-haiku-4-5)

    Returns:
        Interactive dashboard with token count, metrics, and cost estimation
    """
    # Validate model
    available_models = list(PRICING.keys())
    if model not in available_models:
        # Fallback UI for error case
        with Column(gap=4) as view:
            Heading("🫘 Bean Counter")
            Text(f"Error: Model '{model}' not supported.", css_class="text-red-500")
            Text(f"Available models: {', '.join(available_models)}")
        return PrefabApp(view=view)

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

    # Build the dashboard UI with Prefab components
    with Column(gap=4, css_class="p-6 bg-[#141413] rounded-xl min-h-full") as view:
        # Header
        Heading("🫘 Bean Counter", css_class="text-[#FAF9F5]")
        
        # Main metrics grid
        with Grid(min_column_width="14rem", gap=4):
            with Card(css_class="bg-[#1e1d1b] border border-[#3a3835]"):
                with CardContent():
                    Metric(
                        label="Tokens",
                        value=f"{tokens:,}",
                        description="Input tokens",
                        css_class="text-[#FAF9F5]",
                    )
            
            with Card(css_class="bg-[#1e1d1b] border border-[#3a3835]"):
                with CardContent():
                    Metric(
                        label="Characters",
                        value=f"{metrics['char_count']:,}",
                        description="Total characters",
                        css_class="text-[#FAF9F5]",
                    )
            
            with Card(css_class="bg-[#1e1d1b] border border-[#3a3835]"):
                with CardContent():
                    Metric(
                        label="Words",
                        value=f"{metrics['word_count']:,}",
                        description="Total words",
                        css_class="text-[#FAF9F5]",
                    )
            
            with Card(css_class="bg-[#1e1d1b] border border-[#3a3835]"):
                with CardContent():
                    Metric(
                        label="Tokens/Char",
                        value=f"{metrics['tokens_per_char']:.4f}",
                        description="Compression ratio",
                        css_class="text-[#FAF9F5]",
                    )

        # Cost breakdown section
        with Card(css_class="bg-[#1e1d1b] border border-[#3a3835]"):
            with CardContent():
                Heading("💰 Cost Estimation", css_class="text-lg text-[#FAF9F5]")
                
                with Column(gap=2):
                    with Row(gap=2, css_class="justify-between"):
                        Text("Model:", css_class="text-[#B0AEA5]")
                        Text(model, css_class="font-mono font-semibold text-[#FAF9F5]")
                    
                    with Row(gap=2, css_class="justify-between"):
                        Text("Input Cost:", css_class="text-[#B0AEA5]")
                        Text(
                            f"${input_cost:.6f}",
                            css_class="font-mono font-semibold text-[#D97757]",
                        )
                    
                    with Row(gap=2, css_class="justify-between"):
                        Text("Output Est.:", css_class="text-[#B0AEA5]")
                        Text(
                            f"{output_tokens_estimate:,} tokens",
                            css_class="font-mono font-semibold text-[#FAF9F5]",
                        )
                    
                    with Row(gap=2, css_class="justify-between"):
                        Text("Output Cost Est.:", css_class="text-[#B0AEA5]")
                        Text(
                            f"${output_cost:.6f}",
                            css_class="font-mono font-semibold text-[#D97757]",
                        )
                    
                    # Total cost highlight
                    with Row(
                        gap=2,
                        css_class="justify-between border-t border-[#3a3835] pt-3 mt-3",
                    ):
                        Text("Total Est. Cost:", css_class="font-semibold text-[#FAF9F5]")
                        Text(
                            f"${total_cost:.6f}",
                            css_class="font-mono font-bold text-lg text-[#D97757]",
                        )

    return PrefabApp(view=view)


if __name__ == "__main__":
    mcp.run(transport="stdio")
