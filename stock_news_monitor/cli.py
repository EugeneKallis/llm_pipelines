"""
Example CLI — fetch news and pipe to a local Ollama model.

Usage:
    python -m stock_news_monitor.cli NVDA
    python -m stock_news_monitor.cli CRWD --hours 24 --model qwen2.5:7b
"""

import argparse
import json
import sys

from stock_news_monitor import build_llm_prompt, get_stock_news


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch stock news and summarize with local LLM")
    parser.add_argument("ticker", help="Stock symbol, e.g. NVDA, CRWD, VOO")
    parser.add_argument("--hours", type=int, default=24, help="Lookback window in hours (default: 24)")
    parser.add_argument("--model", default="qwen2.5:7b", help="Ollama model name (default: qwen2.5:7b)")
    parser.add_argument("--json", action="store_true", help="Output raw prompt as JSON instead of calling LLM")
    args = parser.parse_args()

    try:
        if args.json:
            prompt = build_llm_prompt(args.ticker, hours=args.hours)
            print(json.dumps(prompt, indent=2))
            return
    except Exception as e:
        print(f"[stock_news_monitor] Error: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        import ollama
    except ImportError:
        print("ollama not installed. Run: pip install ollama", file=sys.stderr)
        sys.exit(1)

    try:
        prompt = build_llm_prompt(args.ticker, hours=args.hours)
        response = ollama.chat(
            model=args.model,
            messages=[
                {"role": "system", "content": prompt["system"]},
                {"role": "user",   "content": prompt["user"]},
            ],
        )
        print(response["message"]["content"])
    except Exception as e:
        print(f"[stock_news_monitor] Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
