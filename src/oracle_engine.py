#!/usr/bin/env python3
"""
ORACLE Engine - Strategic Decision Simulation Platform
Gemini AI powered hypothesis testing and scenario analysis

Usage:
    export GEMINI_API_KEY="your-api-key"
    python -m src.oracle_engine --domain business --count 50

Author: Mustafa Sarac / NeuraByte Labs
License: MIT
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any
import argparse
import aiohttp
from dataclasses import dataclass, asdict, field
import importlib

# Configuration
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
MAX_CONCURRENT = int(os.getenv("MAX_CONCURRENT", "5"))
RETRY_ATTEMPTS = 3
DELAY_BETWEEN_CALLS = float(os.getenv("DELAY_BETWEEN_CALLS", "1.0"))


@dataclass
class SimulationResult:
    """Result of a single simulation run"""
    simulation_id: str
    domain: str
    category: str
    hypothesis: str
    scenario: str
    outcome: str  # positive, negative, neutral
    confidence: float
    insights: List[str]
    recommendations: List[str]
    risks: List[str]
    dependencies: List[str]
    priority_score: int
    raw_response: str
    timestamp: str
    duration_ms: int
    metadata: Dict[str, Any] = field(default_factory=dict)


class GeminiClient:
    """Async client for Gemini API"""

    def __init__(self, api_key: str, model: str = None):
        self.api_key = api_key
        self.model = model or GEMINI_MODEL
        self.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        self.session: Optional[aiohttp.ClientSession] = None
        self.total_tokens = 0
        self.total_cost = 0.0

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, *args):
        if self.session:
            await self.session.close()

    async def generate(self, prompt: str, temperature: float = 0.7) -> str:
        """Generate response from Gemini"""
        url = f"{self.api_url}?key={self.api_key}"

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "topP": 0.95,
                "maxOutputTokens": 4096,
            }
        }

        # Add thinking config for Gemini 3 Pro models
        if "gemini-3" in self.model or "thinking" in self.model:
            payload["generationConfig"]["thinkingConfig"] = {"thinkingLevel": "low"}

        for attempt in range(RETRY_ATTEMPTS):
            try:
                async with self.session.post(url, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])

                        # Extract text from response
                        text_response = ""
                        for part in parts:
                            if "text" in part:
                                text_response = part["text"]

                        # Track usage if available
                        usage = data.get("usageMetadata", {})
                        if usage:
                            self.total_tokens += usage.get("totalTokenCount", 0)

                        return text_response if text_response else '{"error": "No text in response"}'

                    elif response.status == 429:
                        wait_time = (attempt + 1) * 5
                        print(f"  Rate limited, waiting {wait_time}s...")
                        await asyncio.sleep(wait_time)
                    else:
                        text = await response.text()
                        print(f"  API error {response.status}: {text[:200]}")

            except Exception as e:
                print(f"  Request error: {e}")
                await asyncio.sleep(2)

        return '{"error": "Failed after retries"}'


class OracleEngine:
    """Main simulation engine"""

    def __init__(self, domain: str, api_key: str):
        self.domain = domain
        self.api_key = api_key
        self.results: List[SimulationResult] = []
        self.config = self._load_domain_config(domain)

    def _load_domain_config(self, domain: str) -> Dict:
        """Load domain-specific configuration"""
        template_path = Path(__file__).parent.parent / "templates" / f"{domain}.json"

        if template_path.exists():
            with open(template_path) as f:
                return json.load(f)
        else:
            # Return default config
            return {
                "name": domain,
                "master_prompt": self._default_master_prompt(),
                "categories": {},
                "hypotheses": {}
            }

    def _default_master_prompt(self) -> str:
        return """Sen dünyanın en deneyimli stratejik danışmanısın. 20+ yıl boyunca
Fortune 500 şirketlerinin kritik kararlarında danışmanlık yaptın.

## GÖREV
Verilen hipotezi stratejik açıdan analiz et ve değerlendir.

## ANALİZ KRİTERLERİ
1. **Desirability** - Hedef kitle bunu gerçekten istiyor mu?
2. **Feasibility** - Teknik/operasyonel olarak mümkün mü?
3. **Viability** - İş modeli sürdürülebilir mi?
4. **Differentiation** - Rakiplerden nasıl ayrışıyor?
5. **Scalability** - Ölçeklenebilir mi?
6. **Risk** - Ana riskler neler?

## ÇIKTI FORMATI (STRICT JSON)
Sadece JSON döndür:
{
  "outcome": "positive|negative|neutral",
  "confidence": 0.0-1.0,
  "insights": ["insight1", "insight2", "insight3"],
  "recommendations": ["rec1", "rec2"],
  "risks": ["risk1", "risk2"],
  "priority_score": 1-100,
  "summary": "Tek paragraf özet"
}"""

    async def run_simulation(
        self,
        client: GeminiClient,
        category: str,
        hypothesis: str,
        sim_number: int
    ) -> SimulationResult:
        """Run a single simulation"""
        sim_id = f"ORC-{self.domain[:3].upper()}-{category[:3].upper()}-{sim_number:04d}"

        # Build prompt
        master_prompt = self.config.get("master_prompt", self._default_master_prompt())
        category_prompt = self.config.get("categories", {}).get(category, {}).get("prompt", "")

        full_prompt = f"""{master_prompt}

## DOMAIN: {self.domain.upper()}
## CATEGORY: {category}

{category_prompt}

## HİPOTEZ
{hypothesis}

Analiz et ve JSON formatında cevap ver."""

        start = datetime.now()
        raw_response = await client.generate(full_prompt)
        duration = (datetime.now() - start).total_seconds() * 1000

        # Parse response
        try:
            json_start = raw_response.find('{')
            json_end = raw_response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                data = json.loads(raw_response[json_start:json_end])
            else:
                data = {"error": "No JSON found", "outcome": "neutral"}
        except json.JSONDecodeError:
            data = {"error": "Invalid JSON", "outcome": "neutral"}

        return SimulationResult(
            simulation_id=sim_id,
            domain=self.domain,
            category=category,
            hypothesis=hypothesis,
            scenario=hypothesis[:200],
            outcome=data.get("outcome", "neutral"),
            confidence=float(data.get("confidence", 0.5)),
            insights=data.get("insights", []),
            recommendations=data.get("recommendations", []),
            risks=data.get("risks", []),
            dependencies=data.get("dependencies", []),
            priority_score=int(data.get("priority_score", 50)),
            raw_response=raw_response,
            timestamp=datetime.now().isoformat(),
            duration_ms=int(duration),
            metadata={"summary": data.get("summary", "")}
        )

    async def run_category(
        self,
        client: GeminiClient,
        category: str,
        hypotheses: List[str],
        semaphore: asyncio.Semaphore
    ) -> List[SimulationResult]:
        """Run all simulations for a category"""
        results = []
        total = len(hypotheses)

        for i, hypothesis in enumerate(hypotheses):
            async with semaphore:
                result = await self.run_simulation(client, category, hypothesis, i + 1)
                results.append(result)
                self.results.append(result)

                # Progress
                pct = ((i + 1) / total) * 100
                outcome_icon = "+" if result.outcome == "positive" else "-" if result.outcome == "negative" else "o"
                print(f"\r  [{category:12}] {i+1:3}/{total:3} ({pct:5.1f}%) [{outcome_icon}]", end="", flush=True)

                await asyncio.sleep(DELAY_BETWEEN_CALLS)

        print()  # newline
        return results

    async def run_all(self, categories: Dict[str, List[str]], output_dir: Path):
        """Run all simulations"""
        semaphore = asyncio.Semaphore(MAX_CONCURRENT)

        async with GeminiClient(self.api_key) as client:
            for category, hypotheses in categories.items():
                print(f"\n{'='*60}")
                print(f"  CATEGORY: {category.upper()} ({len(hypotheses)} simulations)")
                print(f"{'='*60}")

                await self.run_category(client, category, hypotheses, semaphore)

                # Save intermediate results
                self._save_results(output_dir, category)

            print(f"\n  Total tokens used: {client.total_tokens:,}")

        # Generate summary
        self._generate_summary(output_dir)

        return self.results

    def _save_results(self, output_dir: Path, category: str):
        """Save results for a category"""
        category_results = [r for r in self.results if r.category == category]
        output_file = output_dir / f"{self.domain}_{category}_results.json"

        with open(output_file, "w") as f:
            json.dump([asdict(r) for r in category_results], f, indent=2, ensure_ascii=False)

        print(f"  Saved {len(category_results)} results to {output_file.name}")

    def _generate_summary(self, output_dir: Path):
        """Generate markdown summary"""
        lines = [
            f"# ORACLE Engine - {self.domain.upper()} Simulation Summary",
            f"\nGenerated: {datetime.now().isoformat()}",
            f"\nTotal Simulations: {len(self.results)}",
            "\n---\n",
            "## Overview\n",
        ]

        # Group by category
        categories = {}
        for r in self.results:
            if r.category not in categories:
                categories[r.category] = []
            categories[r.category].append(r)

        for category, sims in categories.items():
            positive = sum(1 for s in sims if s.outcome == "positive")
            negative = sum(1 for s in sims if s.outcome == "negative")
            neutral = len(sims) - positive - negative
            avg_conf = sum(s.confidence for s in sims) / len(sims) if sims else 0
            avg_prio = sum(s.priority_score for s in sims) / len(sims) if sims else 0

            lines.append(f"### {category.upper()}")
            lines.append(f"| Metric | Value |")
            lines.append(f"|--------|-------|")
            lines.append(f"| Total | {len(sims)} |")
            lines.append(f"| Positive | {positive} ({positive/len(sims)*100:.0f}%) |")
            lines.append(f"| Negative | {negative} ({negative/len(sims)*100:.0f}%) |")
            lines.append(f"| Neutral | {neutral} ({neutral/len(sims)*100:.0f}%) |")
            lines.append(f"| Avg Confidence | {avg_conf:.2f} |")
            lines.append(f"| Avg Priority | {avg_prio:.1f}/100 |")
            lines.append("")

            # Top 5 by priority
            top_5 = sorted(sims, key=lambda x: x.priority_score, reverse=True)[:5]
            if top_5:
                lines.append("**Top 5 by Priority:**")
                for i, s in enumerate(top_5, 1):
                    icon = "+" if s.outcome == "positive" else "-" if s.outcome == "negative" else "o"
                    lines.append(f"{i}. [{icon}] (P:{s.priority_score}) {s.hypothesis[:80]}...")
                lines.append("")

        # Save summary
        summary_file = output_dir / f"{self.domain}_summary.md"
        with open(summary_file, "w") as f:
            f.write("\n".join(lines))

        print(f"\n  Summary saved to {summary_file.name}")

        # Save all results
        all_file = output_dir / f"{self.domain}_all_results.json"
        with open(all_file, "w") as f:
            json.dump([asdict(r) for r in self.results], f, indent=2, ensure_ascii=False)

        print(f"  All results saved to {all_file.name}")


def print_banner():
    print("""
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
║   Powered by Gemini AI | NeuraByte Labs                                     ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")


def main():
    parser = argparse.ArgumentParser(description="ORACLE Engine - Strategic Simulation Platform")
    parser.add_argument("--domain", required=True, help="Simulation domain (e.g., business, product, tech)")
    parser.add_argument("--template", help="Path to custom template JSON file")
    parser.add_argument("--output", default="results", help="Output directory")
    parser.add_argument("--model", default=None, help="Gemini model to use")
    parser.add_argument("--category", help="Run specific category only")
    parser.add_argument("--count", type=int, help="Limit hypotheses per category")
    args = parser.parse_args()

    # Check API key
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set")
        print("Get your key at: https://aistudio.google.com/apikey")
        sys.exit(1)

    print_banner()

    # Setup
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.model:
        global GEMINI_MODEL
        GEMINI_MODEL = args.model

    # Load template
    engine = OracleEngine(args.domain, api_key)

    if args.template:
        with open(args.template) as f:
            engine.config = json.load(f)

    # Get hypotheses
    hypotheses = engine.config.get("hypotheses", {})

    if not hypotheses:
        print(f"No hypotheses found for domain '{args.domain}'")
        print(f"Create a template at: templates/{args.domain}.json")
        sys.exit(1)

    if args.category:
        hypotheses = {args.category: hypotheses.get(args.category, [])}

    if args.count:
        hypotheses = {k: v[:args.count] for k, v in hypotheses.items()}

    total_sims = sum(len(v) for v in hypotheses.values())

    print(f"  Domain: {args.domain}")
    print(f"  Model: {GEMINI_MODEL}")
    print(f"  Categories: {', '.join(hypotheses.keys())}")
    print(f"  Total Simulations: {total_sims}")
    print(f"  Output: {output_dir}")

    # Run
    asyncio.run(engine.run_all(hypotheses, output_dir))

    print("\n" + "="*60)
    print("  SIMULATION COMPLETE")
    print("="*60)


if __name__ == "__main__":
    main()
