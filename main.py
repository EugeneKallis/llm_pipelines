from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from stock_tracker import get_stock_summary
from stock_news_monitor import build_llm_prompt, get_stock_news
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="llm_pipelines")


@app.get("/")
def root():
    return {"message": "Hello World"}


@app.get("/stocks_pipeline/{ticker}")
def stocks_pipeline(ticker: str):
    return get_stock_summary(ticker)


@app.get("/stock-news/{ticker}")
def stock_news(ticker: str, hours: int = 24):
    """
    Fetch news for a ticker and return the LLM-ready prompt dict.

    Query params:
        ticker: Stock symbol, e.g. NVDA, CRWD, VOO
        hours:  Lookback window in hours (default 24)

    Returns:
        {"system": "...", "user": "..."}
    """
    try:
        prompt = build_llm_prompt(ticker.upper(), hours=hours)
        return prompt
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.get("/stock-news/{ticker}/summary")
def stock_news_summary(ticker: str, hours: int = 24):
    """
    Fetch news for a ticker, run it through the LLM, and return the analysis.

    Uses OpenAI if OPENAI_API_KEY is set, otherwise Ollama at localhost:11434.

    Query params:
        ticker: Stock symbol, e.g. NVDA, CRWD, VOO
        hours:  Lookback window in hours (default 24)
        model:  Override model name (default: gpt-4o-mini for OpenAI, qwen2.5:7b for Ollama)
    """
    openai_key = os.getenv("OPENAI_API_KEY")
    model_override = os.getenv("LLM_MODEL")

    try:
        prompt = build_llm_prompt(ticker.upper(), hours=hours)
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))

    if openai_key:
        from openai import OpenAI
        client = OpenAI(api_key=openai_key)
        model = model_override or "gpt-4o-mini"
        try:
            res = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": prompt["system"]},
                    {"role": "user",   "content": prompt["user"]},
                ],
            )
            return {"ticker": ticker.upper(), "model": model, "summary": res.choices[0].message.content}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"OpenAI error: {e}")

    # Ollama fallback
    try:
        import ollama
    except ImportError:
        raise HTTPException(status_code=500, detail="ollama not installed. Run: pip install ollama")

    model = model_override or "qwen2.5:7b"
    try:
        res = ollama.chat(
            model=model,
            messages=[
                {"role": "system", "content": prompt["system"]},
                {"role": "user",   "content": prompt["user"]},
            ],
        )
        return {"ticker": ticker.upper(), "model": model, "summary": res["message"]["content"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ollama error: {e}")
