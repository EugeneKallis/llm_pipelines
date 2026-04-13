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

Set `NEWS_API_KEY` and `NEWS_API_URL` in `.env` (see `.env.example`).

---

## FastAPI Endpoints

Start with: `uv run fastapi dev main.py`

| Endpoint | Description |
|---|---|
| `GET /` | Health check |
| `GET /stocks_pipeline/{ticker}` | Full financial pipeline (yfinance + NewsAPI) |
| `GET /stock-news/{ticker}` | Fetch news, return `{"system": "...", "user": "..."}` |
| `GET /stock-news/{ticker}/summary` | Fetch news + run through LLM, return analysis |

**Query params:**
- `hours` — lookback window in hours (default 24)

**`/stock-news/{ticker}/summary` LLM selection:**
- Uses OpenAI if `OPENAI_API_KEY` is set
- Falls back to Ollama at `localhost:11434` using `qwen2.5:7b`
- Override with `LLM_MODEL` env var

```bash
# Preview the LLM prompt
curl "http://localhost:8000/stock-news/NVDA?hours=24"

# Full analysis (Ollama or OpenAI)
curl "http://localhost:8000/stock-news/NVDA/summary?hours=24"
```
