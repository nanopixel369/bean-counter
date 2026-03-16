# 🫘 Bean Counter - MCP Token Counter with Interactive Dashboard

A Model Context Protocol (MCP) server that counts tokens in text and returns detailed analysis with cost estimation for Claude models.

## Features

- **Accurate Token Counting** - Uses Anthropic's official token counting API
- **Cost Estimation** - Calculates estimated input/output costs for various Claude models
- **Multiple Models** - Supports Claude Opus 4.6, Sonnet 4.6, and Haiku 4.5
- **Detailed Metrics**:
  - Token count
  - Character count
  - Word count
  - Tokens per character ratio
  - Input cost estimation
  - Output cost estimation
  - Total cost estimate

## Supported Models

- `claude-opus-4-6` - Most capable, highest cost
- `claude-sonnet-4-6` - Balanced performance and cost (recommended)
- `claude-haiku-4-5` - Fastest and cheapest

## Setup

### Prerequisites

- Python 3.9+
- Anthropic API Key ([get one here](https://console.anthropic.com/))

### Installation

1. **Create your .env file**:
   Copy `.env.example` to `.env` and add your API key

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Local Testing

```bash
python server.py
```

### Deploy to Prefect Horizon

1. Push to GitHub: `nanopixel369/bean-counter`
2. Go to [horizon.prefect.io](https://horizon.prefect.io)
3. Sign in with GitHub and connect your repo
4. Set Entrypoint: `server.py:mcp`
5. Add Secret: `ANTHROPIC_API_KEY`
6. Deploy and get your live URL

### Add to Claude.ai

Settings → Connectors → Add custom connector → Paste Horizon URL

## Tool: count_tokens

```
count_tokens(text: str, model: str = "claude-sonnet-4-6") -> dict
```

Returns token count, character count, word count, and cost estimation.

## Security

✅ API Key Protection:
- `.env` is in `.gitignore` - never committed
- Local: loaded from `.env` via `python-dotenv`
- Horizon: stored in encrypted secrets vault

## Files

```
bean-counter/
├── server.py           # FastMCP server
├── requirements.txt    # Dependencies
├── .env.example        # Template
├── .env                # Local (not committed)
├── .gitignore          # Protects secrets
└── README.md           # This file
```

## License

MIT
