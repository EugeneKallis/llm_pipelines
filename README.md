# llm_pipelines

Group of LLM scripts I can call.

## Packages

### `stock_news_monitor` — Stock news fetcher + LLM prompt builder

No API keys required. Fetches news via Google News RSS → Bing RSS → Yahoo Finance HTML, builds a structured `{"system", "user"}` prompt ready for any LLM.

```bash
# Fetch + summarize with local Ollama model
python -m stock_news_monitor.cli NVDA
python -m stock_news_monitor.cli CRWD --hours 24 --model qwen2.5:7b

# Just print the raw prompt (no LLM call)
python -m stock_news_monitor.cli NVDA --json
```

**Python API:**
```python
from stock_news_monitor import build_llm_prompt, get_stock_news

# Raw articles dict
news = get_stock_news("NVDA", hours=24)
# {"Google News RSS": [{"title": "...", "link": "...", "pub_date": "..."}]}

# LLM prompt dict — pass directly to your chat endpoint
prompt = build_llm_prompt("NVDA", hours=24)
# {"system": "...", "user": "..."}

import ollama
response = ollama.chat(
    model="qwen2.5:7b",
    messages=[
        {"role": "system", "content": prompt["system"]},
        {"role": "user",   "content": prompt["user"]},
    ],
)
print(response["message"]["content"])
```

### `stock_tracker` — Financial data + analyst summary (requires NewsAPI key)

```bash
pip install ollama  # optional, for CLI use
```

Set `NEWS_API_KEY` and `NEWS_API_URL` in `.env` (see `.env.example`).
