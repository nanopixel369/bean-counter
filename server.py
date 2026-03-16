"""
Bean Counter - MCP Token Count & Analysis Server with Interactive Dashboard
Uses Prefab UI with a custom dark Theme matching the Claude UI color palette.
"""

import os
import httpx
from dotenv import load_dotenv
from fastmcp import FastMCP
from prefab_ui.app import PrefabApp, Theme
from prefab_ui.components import (
    Column, Heading, Grid, Card, CardContent, Metric, Text, Row,
)

load_dotenv()

mcp = FastMCP("Bean Counter")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages/count_tokens"

PRICING = {
    "claude-opus-4-6":   {"input": 5.00,  "output": 25.00},
    "claude-sonnet-4-6": {"input": 3.00,  "output": 15.00},
    "claude-haiku-4-5":  {"input": 1.00,  "output": 5.00},
}

# Applied to BOTH light and dark — renders correctly regardless of host mode
_PALETTE = {
    "background":           "#262624",
    "foreground":           "#F8F7F1",
    "card":                 "#30302E",
    "card-foreground":      "#F8F7F1",
    "muted":                "#30302E",
    "muted-foreground":     "#C1BFB5",
    "border":               "rgba(255,255,255,0.08)",
    "input":                "rgba(255,255,255,0.08)",
    "primary":              "#D67456",
    "primary-foreground":   "#F8F7F1",
    "secondary":            "#141413",
    "secondary-foreground": "#C1BFB5",
    "accent":               "#141413",
    "accent-foreground":    "#F8F7F1",
    "ring":                 "#D67456",
}

CLAUDE_THEME = Theme(light=_PALETTE, dark=_PALETTE)

# Fills the full iframe background so blank space matches the widget
_BODY_CSS = "body, html { background: #262624 !important; margin: 0; padding: 0; }"


async def count_tokens_api(text: str, model: str) -> dict:
    if not ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY not set")
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "content-type": "application/json",
        "anthropic-version": "2023-06-01",
    }
    payload = {"model": model, "messages": [{"role": "user", "content": text}]}
    async with httpx.AsyncClient() as client:
        response = await client.post(ANTHROPIC_API_URL, json=payload, headers=headers, timeout=10.0)
        response.raise_for_status()
        return {"tokens": response.json().get("input_tokens", 0)}


def calculate_metrics(text: str, tokens: int) -> dict:
    char_count = len(text)
    word_count = len(text.split())
    tokens_per_char = tokens / char_count if char_count > 0 else 0
    return {"char_count": char_count, "word_count": word_count, "tokens_per_char": tokens_per_char}


def get_cost(tokens: int, model: str, is_output: bool = False) -> float:
    if model not in PRICING:
        return 0.0
    key = "output" if is_output else "input"
    return (tokens / 1_000_000) * PRICING[model].get(key, 0)


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
    available_models = list(PRICING.keys())
    if model not in available_models:
        with Column(gap=4) as view:
            Heading("🫘 Bean Counter")
            Text(f"Error: Model '{model}' not supported.")
            Text(f"Available: {', '.join(available_models)}")
        return PrefabApp(view=view, theme=CLAUDE_THEME, stylesheets=[_BODY_CSS])

    token_result = await count_tokens_api(text, model)
    tokens = token_result["tokens"]
    metrics = calculate_metrics(text, tokens)
    input_cost = get_cost(tokens, model, is_output=False)
    output_tokens_estimate = tokens // 2
    output_cost = get_cost(output_tokens_estimate, model, is_output=True)
    total_cost = input_cost + output_cost

    with Column(gap=3, css_class="p-4 max-w-sm") as view:
        Heading("🫘 Bean Counter")

        with Grid(min_column_width="12rem", gap=3):
            with Card():
                with CardContent():
                    Metric(label="Tokens", value=f"{tokens:,}", description="Input tokens")
            with Card():
                with CardContent():
                    Metric(label="Characters", value=f"{metrics['char_count']:,}", description="Total characters")
            with Card(css_class="bg-secondary"):
                with CardContent():
                    Metric(label="Words", value=f"{metrics['word_count']:,}", description="Total words")
            with Card(css_class="bg-secondary"):
                with CardContent():
                    Metric(label="Tokens/Char", value=f"{metrics['tokens_per_char']:.4f}", description="Compression ratio")

        with Card():
            with CardContent():
                Heading("💰 Cost Estimation", css_class="text-base mb-2")
                with Column(gap=1):
                    with Row(css_class="justify-between"):
                        Text("Model", css_class="text-muted-foreground text-sm")
                        Text(model, css_class="font-mono text-sm")
                    with Row(css_class="justify-between"):
                        Text("Input cost", css_class="text-muted-foreground text-sm")
                        Text(f"${input_cost:.6f}", css_class="text-sm")
                    with Row(css_class="justify-between"):
                        Text("Output est.", css_class="text-muted-foreground text-sm")
                        Text(f"{output_tokens_estimate:,} tokens", css_class="text-sm")
                    with Row(css_class="justify-between"):
                        Text("Output cost est.", css_class="text-muted-foreground text-sm")
                        Text(f"${output_cost:.6f}", css_class="text-sm")
                    with Row(css_class="justify-between border-t pt-2 mt-1"):
                        Text("Total est. cost", css_class="font-semibold text-sm")
                        Text(f"${total_cost:.6f}", css_class="font-semibold text-primary text-sm")

    return PrefabApp(view=view, theme=CLAUDE_THEME, stylesheets=[_BODY_CSS])


if __name__ == "__main__":
    mcp.run(transport="stdio")
