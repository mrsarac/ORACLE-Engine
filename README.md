# ORACLE Engine

> Strategic Decision Simulation Platform powered by Gemini AI

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   ██████╗ ██████╗  █████╗  ██████╗██╗     ███████╗                          ║
║  ██╔═══██╗██╔══██╗██╔══██╗██╔════╝██║     ██╔════╝                          ║
║  ██║   ██║██████╔╝███████║██║     ██║     █████╗                            ║
║  ██║   ██║██╔══██╗██╔══██║██║     ██║     ██╔══╝                            ║
║  ╚██████╔╝██║  ██║██║  ██║╚██████╗███████╗███████╗                          ║
║   ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚══════╝╚══════╝                          ║
║                                                                              ║
║   ENGINE - Strategic Decision Simulation Platform                            ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

## What is ORACLE?

ORACLE Engine runs hundreds of AI-powered simulations to validate business hypotheses, test pricing strategies, analyze competitive scenarios, and de-risk strategic decisions.

**Use Cases:**
- Validate SaaS pricing before launch
- Test go-to-market strategies
- Analyze competitive scenarios
- Evaluate feature prioritization
- Risk assessment and mitigation planning

## Quick Start

### 1. Setup

```bash
# Clone
git clone git@github.com:mrsarac/ORACLE-Engine.git
cd ORACLE-Engine

# Install dependencies
pip install -r requirements.txt

# Set API key
export GEMINI_API_KEY="your-api-key-here"
```

Get your Gemini API key: https://aistudio.google.com/apikey

### 2. Run Simulation

```bash
# Run business strategy simulation
python -m src.oracle_engine --domain business --output results/

# Run SUBSTANCE-specific simulation
python -m src.oracle_engine --domain substance --output results/

# Run specific category only
python -m src.oracle_engine --domain business --category pricing --output results/

# Limit simulations per category
python -m src.oracle_engine --domain business --count 5 --output results/
```

### 3. View Results

Results are saved to the `results/` directory:
- `{domain}_summary.md` - Human-readable summary with insights
- `{domain}_{category}_results.json` - Detailed results per category
- `{domain}_all_results.json` - All simulation results

## Domain Templates

ORACLE uses JSON templates to define simulation domains. Built-in templates:

| Domain | Description | Categories |
|--------|-------------|------------|
| `business` | General SaaS business strategy | pricing, gtm, competitive, risk, growth |
| `substance` | AGI prediction platform | pricing, features, gtm, competitive, growth |

### Create Custom Domain

```json
// templates/my-product.json
{
  "name": "My Product",
  "description": "Product-specific simulation",
  "master_prompt": "You are an expert in...",
  "categories": {
    "pricing": {
      "prompt": "Analyze pricing strategy...",
      "count": 20
    }
  },
  "hypotheses": {
    "pricing": [
      "Free tier + $9.99/mo premium",
      "Usage-based pricing",
      "..."
    ]
  }
}
```

Run with custom template:
```bash
python -m src.oracle_engine --domain my-product --template templates/my-product.json
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GEMINI_API_KEY` | (required) | Your Gemini API key |
| `GEMINI_MODEL` | `gemini-2.0-flash` | Gemini model to use |
| `MAX_CONCURRENT` | `5` | Max parallel API calls |
| `DELAY_BETWEEN_CALLS` | `1.0` | Seconds between calls |

### Supported Models

| Model | Speed | Cost | Best For |
|-------|-------|------|----------|
| `gemini-2.0-flash` | Fast | Low | Quick iterations |
| `gemini-1.5-pro` | Medium | Medium | Balanced |
| `gemini-3-pro-preview` | Slow | High | Deep analysis |

## Output Format

### Simulation Result

```json
{
  "simulation_id": "ORC-BUS-PRI-0001",
  "domain": "business",
  "category": "pricing",
  "hypothesis": "Free tier + $9.99/mo premium",
  "outcome": "positive",
  "confidence": 0.85,
  "priority_score": 78,
  "insights": [
    "Strong value proposition for solo developers",
    "Free tier enables viral growth"
  ],
  "recommendations": [
    "Consider annual discount for retention",
    "Add usage limits to free tier"
  ],
  "risks": [
    "High support burden from free users",
    "Conversion rate may be low"
  ]
}
```

### Summary Report

The summary report includes:
- Overview statistics per category
- Positive/negative/neutral breakdown
- Top 5 hypotheses by priority score
- Key insights aggregated across simulations

## Cost Estimation

| Model | ~Cost per 100 simulations |
|-------|---------------------------|
| gemini-2.0-flash | $0.10 - $0.30 |
| gemini-1.5-pro | $0.50 - $1.50 |
| gemini-3-pro-preview | $2.00 - $5.00 |

## Project Structure

```
ORACLE-Engine/
├── src/
│   ├── __init__.py
│   └── oracle_engine.py      # Main engine
├── templates/
│   ├── business.json         # Business strategy template
│   ├── substance.json        # SUBSTANCE-specific template
│   └── company.json          # Company formation strategy
├── docs/                      # Documentation
├── examples/                  # Example configs
├── requirements.txt
├── .env.example
└── README.md
```

## Private Data Storage

Keep your simulation results private while using the open-source engine:

```bash
# 1. Create a private data repo
mkdir ~/ORACLE-Data
cd ~/ORACLE-Data
git init

# 2. Symlink results folder
cd ~/ORACLE-Engine
rm -rf results
ln -s ~/ORACLE-Data/results results

# 3. Run simulations - data goes to private repo
python -m src.oracle_engine --domain business --output results/
```

This way:
- **ORACLE-Engine** stays open source (public)
- **Your simulation data** stays private (separate repo)

## Examples

### Validate Pricing Strategy

```bash
# Create pricing-focused template
cat > templates/pricing-test.json << 'EOF'
{
  "name": "Pricing Validation",
  "master_prompt": "You are a SaaS pricing expert...",
  "categories": {
    "pricing": {"prompt": "Analyze...", "count": 20}
  },
  "hypotheses": {
    "pricing": [
      "$4.99/mo micro-SaaS",
      "$9.99/mo standard",
      "$19.99/mo premium",
      "$49.99/mo professional",
      "$99/year annual"
    ]
  }
}
EOF

# Run
python -m src.oracle_engine --domain pricing-test --template templates/pricing-test.json
```

### Competitive Analysis

```bash
python -m src.oracle_engine --domain business --category competitive --count 10
```

## Roadmap

- [x] Core simulation engine
- [x] Gemini API integration
- [x] Domain templates
- [x] JSON result output
- [x] Markdown summary generation
- [ ] Web UI dashboard
- [ ] Historical comparison
- [ ] Multi-model support (Claude, GPT)
- [ ] Automated insights extraction
- [ ] Slack/Discord notifications

## License

MIT License - See [LICENSE](LICENSE)

---

**Built by [NeuraByte Labs](https://neurabytelabs.com)**

*"Know the future before you build it."*
