"""
Bean Counter - MCP Token Count & Analysis Server with Interactive Dashboard
Provides token counting, character analysis, and cost estimation for Claude models.
"""

import os
import httpx
import json
from typing import Any
from dotenv import load_dotenv
from fastmcp import FastMCP, Resource
from fastmcp.server.apps import AppConfig

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


@mcp.tool(app=AppConfig())
async def count_tokens(text: str, model: str = "claude-sonnet-4-6") -> Any:
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
        return {
            "type": "error",
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

    # Return structured data for the dashboard to render
    result_data = {
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
    
    # Return with embedded HTML dashboard that will render the results
    return {
        "type": "text",
        "text": format_dashboard_html(result_data)
    }


def format_dashboard_html(data: dict) -> str:
    """Generate the HTML dashboard with the results data embedded."""
    html = f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 12px;">
        <div style="background: white; border-radius: 12px; box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3); overflow: hidden;">
            
            <!-- Header -->
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 24px; text-align: center;">
                <h1 style="font-size: 28px; font-weight: 700; margin-bottom: 8px; margin-top: 0;">🫘 Bean Counter</h1>
                <p style="font-size: 14px; opacity: 0.9; margin: 0;">Token Analysis & Cost Estimation</p>
            </div>
            
            <!-- Content -->
            <div style="padding: 24px;">
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 24px;">
                    <!-- Tokens -->
                    <div style="background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); border-radius: 8px; padding: 16px; border-left: 4px solid #667eea;">
                        <div style="font-size: 12px; color: #666; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600; margin-bottom: 8px;">Tokens</div>
                        <div style="font-size: 24px; font-weight: 700; color: #333; font-family: 'Monaco', monospace;">{data['tokens']:,}</div>
                    </div>
                    
                    <!-- Characters -->
                    <div style="background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); border-radius: 8px; padding: 16px; border-left: 4px solid #667eea;">
                        <div style="font-size: 12px; color: #666; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600; margin-bottom: 8px;">Characters</div>
                        <div style="font-size: 24px; font-weight: 700; color: #333; font-family: 'Monaco', monospace;">{data['char_count']:,}</div>
                    </div>
                    
                    <!-- Words -->
                    <div style="background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); border-radius: 8px; padding: 16px; border-left: 4px solid #667eea;">
                        <div style="font-size: 12px; color: #666; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600; margin-bottom: 8px;">Words</div>
                        <div style="font-size: 24px; font-weight: 700; color: #333; font-family: 'Monaco', monospace;">{data['word_count']:,}</div>
                    </div>
                    
                    <!-- Ratio -->
                    <div style="background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); border-radius: 8px; padding: 16px; border-left: 4px solid #667eea;">
                        <div style="font-size: 12px; color: #666; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600; margin-bottom: 8px;">Tokens/Char</div>
                        <div style="font-size: 24px; font-weight: 700; color: #333; font-family: 'Monaco', monospace;">{data['tokens_per_char']}</div>
                    </div>
                    
                    <!-- Input Cost -->
                    <div style="background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); border-radius: 8px; padding: 16px; border-left: 4px solid #667eea; grid-column: 1 / -1;">
                        <div style="font-size: 12px; color: #666; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600; margin-bottom: 8px;">Est. Input Cost</div>
                        <div style="font-size: 24px; font-weight: 700; color: #333; font-family: 'Monaco', monospace;">${data['input_cost_usd']:.6f}</div>
                    </div>
                </div>
                
                <!-- Cost Breakdown -->
                <div style="background: #fff8f0; border-radius: 8px; padding: 16px; border-left: 4px solid #f093fb; margin-top: 20px;">
                    <h3 style="font-size: 14px; color: #666; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600; margin-bottom: 12px; margin-top: 0;">💰 Cost Breakdown</h3>
                    
                    <div style="display: flex; justify-content: space-between; align-items: center; padding: 8px 0; font-size: 14px; border-bottom: 1px solid rgba(240, 147, 251, 0.2);">
                        <span style="color: #666;">Input Tokens:</span>
                        <span style="font-weight: 600; color: #333; font-family: 'Monaco', monospace;">{data['tokens']:,}</span>
                    </div>
                    
                    <div style="display: flex; justify-content: space-between; align-items: center; padding: 8px 0; font-size: 14px; border-bottom: 1px solid rgba(240, 147, 251, 0.2);">
                        <span style="color: #666;">Output Est.:</span>
                        <span style="font-weight: 600; color: #333; font-family: 'Monaco', monospace;">{data['output_tokens_estimate']:,}</span>
                    </div>
                    
                    <div style="display: flex; justify-content: space-between; align-items: center; padding: 8px 0; font-size: 14px; border-bottom: 1px solid rgba(240, 147, 251, 0.2);">
                        <span style="color: #666;">Output Cost Est.:</span>
                        <span style="font-weight: 600; color: #333; font-family: 'Monaco', monospace;">${data['output_cost_estimate_usd']:.6f}</span>
                    </div>
                    
                    <div style="display: flex; justify-content: space-between; align-items: center; padding: 12px 0; margin-top: 8px; border-top: 2px solid #f093fb; font-size: 16px; font-weight: 700;">
                        <span>Total Est. Cost:</span>
                        <span style="color: #f093fb; font-size: 20px; font-family: 'Monaco', monospace;">${data['total_cost_estimate_usd']:.6f}</span>
                    </div>
                </div>
                
                <div style="display: inline-block; background: #667eea; color: white; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; margin-top: 16px;">Model: {data['model']}</div>
            </div>
            
            <!-- Footer -->
            <div style="background: #f5f7fa; padding: 16px 24px; text-align: center; font-size: 12px; color: #999; border-top: 1px solid #e0e0e0;">
                Powered by Anthropic Token Counting API
            </div>
        </div>
    </div>
    """
    return html


if __name__ == "__main__":
    mcp.run(transport="stdio")
