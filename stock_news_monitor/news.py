"""
Google News RSS → Bing RSS → Yahoo Finance HTML, with LLM prompt builder.

No API keys required. Pure stdlib + regex.
"""

import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from typing import Optional

# ──────────────────────────────────────────────────────────────────────────────
# Ticker → search term expansions (ticker alone can miss results)
# ──────────────────────────────────────────────────────────────────────────────

TICKER_ALTERNATIVES: dict[str, list[str]] = {
    "VOO":    ["VOO", "Vanguard S&P 500 ETF"],
    "IVV":    ["IVV", "iShares Core S&P 500 ETF"],
    "FSELX":  ["FSELX", "Fidelity Semiconductor ETF"],
    "SLV":    ["SLV", "iShares Silver Trust", "silver ETF"],
    "MJ":     ["MJ", "cannabis ETF", "cannabis stocks"],
    "USAR":   ["USAR", "USAR battery", "lithium stocks"],
    "CRWD":   ["CrowdStrike"],
    "NVDA":   ["NVIDIA"],
    "RCKT":   ["Rocket Pharmaceuticals"],
}

# ──────────────────────────────────────────────────────────────────────────────
# RSS / HTML fetchers
# ──────────────────────────────────────────────────────────────────────────────

_NEWS_SOURCES = [
    # (name, url_fn)  — url_fn(term, hours) returns a URL string
    (
        "Google News RSS",
        lambda q, h: (
            f"https://news.google.com/rss/search?"
            f"q={urllib.parse.quote(q)}%20when:{h}h"
            f"&hl=en-US&gl=US&ceid=US:en"
        ),
    ),
    (
        "Bing News RSS",
        lambda q, h: (
            f"https://www.bing.com/news/search?"
            f"q={urllib.parse.quote(q)}+when:{h}h&format=rss"
        ),
    ),
    (
        "Yahoo Finance",
        lambda q, h: (
            f"https://finance.yahoo.com/quote/{urllib.parse.quote(q.upper())}/news"
            # Yahoo doesn't support a when: param — we rely on the caller
            # to set a sensible lookback and filter dates client-side
        ),
    ),
]

_RSS_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; NewsBot/1.0)",
}

_HTML_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36",
}


def _fetch_rss(url: str, timeout: int = 10) -> list[dict]:
    """Fetch + parse an RSS feed. Returns [{title, link, pub_date}, ...]."""
    req = urllib.request.Request(url, headers=_RSS_HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        tree = ET.parse(resp)

    items = tree.findall(".//item")
    results = []
    for item in items:
        raw = (item.findtext("title") or "").replace("<![CDATA[", "").replace("]]>", "")
        results.append({
            "title":   raw.strip(),
            "link":    item.findtext("link") or "",
            "pub_date": item.findtext("pubDate") or item.findtext("dc:date") or "",
        })
    return results


def _fetch_yahoo_finance(url: str, timeout: int = 10) -> list[dict]:
    """
    Fetch Yahoo Finance news page and extract headlines via regex.
    Returns [{title, link, pub_date}, ...].  pub_date is empty for Yahoo — filter
    by the caller's lookback window instead.
    """
    req = urllib.request.Request(url, headers=_HTML_HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        html = resp.read().decode("utf-8", errors="ignore")

    results: list[dict] = []

    # Strategy 1: data-testid="news-article" containers
    article_blocks = re.findall(
        r'<article[^>]*data-testid="news-article"[^>]*>(.*?)</article>',
        html,
        re.DOTALL,
    )
    for block in article_blocks:
        # Pull headline from h3 inside block
        m = re.search(r'<h3[^>]*>([^<]+)</h3>', block)
        if m:
            title = m.group(1).strip()
            if len(title) > 15:
                results.append({"title": title, "link": url, "pub_date": ""})

    if results:
        return results

    # Strategy 2: JSON data embedded in page
    json_headlines = re.findall(r'"headline":\s*"([^"]{20,200})"', html)
    for h in json_headlines:
        results.append({"title": h.strip(), "link": url, "pub_date": ""})

    return results


# ──────────────────────────────────────────────────────────────────────────────
# Core news fetcher with fallback chain
# ──────────────────────────────────────────────────────────────────────────────

def get_stock_news(
    ticker: str,
    hours: int = 24,
    timeout: int = 10,
) -> dict[str, list[dict]]:
    """
    Fetch recent news for a ticker using multiple sources with automatic fallback.

    Tries: Google News RSS → Bing News RSS → Yahoo Finance HTML

    Args:
        ticker: Stock symbol e.g. 'NVDA', 'CRWD'
        hours:  Lookback window in hours (default 24).
               Yahoo Finance ignores this — filter by date client-side.
        timeout: HTTP request timeout in seconds (default 10).

    Returns:
        Dict mapping source name → list of article dicts.
        Only sources that returned results are included.
        e.g. {"Google News RSS": [{"title": "...", "link": "...", "pub_date": "..."}]}

    Raises:
        RuntimeError: if no sources return any results.
    """
    search_terms = TICKER_ALTERNATIVES.get(ticker.upper(), [ticker.upper()])
    all_results: dict[str, list[dict]] = {}

    for source_name, url_fn in _NEWS_SOURCES:
        for term in search_terms:
            url = url_fn(term, hours)
            try:
                if "yahoo.com" in url:
                    items = _fetch_yahoo_finance(url, timeout=timeout)
                else:
                    items = _fetch_rss(url, timeout=timeout)

                if items:
                    all_results[source_name] = items
                    break  # Got results — move to next source
            except Exception:
                continue  # Try next term, then next source

    if not all_results:
        raise RuntimeError(
            f"Failed to fetch news for '{ticker}' from all configured sources. "
            "Check network connectivity."
        )

    return all_results


# ──────────────────────────────────────────────────────────────────────────────
# LLM prompt builder
# ──────────────────────────────────────────────────────────────────────────────

def build_llm_prompt(
    ticker: str,
    hours: int = 24,
    timeout: int = 10,
) -> dict[str, str]:
    """
    Fetch news for a ticker and build a structured system + user message pair
    ready to pass directly to an LLM chat endpoint.

    Args:
        ticker: Stock symbol e.g. 'NVDA', 'CRWD'
        hours:  Lookback window in hours (default 24)
        timeout: HTTP request timeout in seconds (default 10)

    Returns:
        {"system": "<system message>", "user": "<user message>"}

    Raises:
        RuntimeError: if news fetch fails from all sources.
    """
    news_by_source = get_stock_news(ticker, hours=hours, timeout=timeout)

    # Deduplicate by title (case-insensitive), preserve insertion order
    seen: set[str] = set()
    articles: list[dict] = []
    for source, items in news_by_source.items():
        for item in items:
            key = item["title"].lower()
            if key not in seen:
                seen.add(key)
                articles.append({**item, "source": source})

    system = f"""You are a sharp, no-nonsense financial analyst. Your job is to synthesize recent news about {ticker} into a concise summary for an investor.

Rules:
- Return exactly 3 sections: **Overview**, **Key Developments**, **Signal vs Noise**
- **Overview**: 1-2 sentence framing of the overall news theme right now
- **Key Developments**: 2-5 bullets, one per material item. Each bullet: what happened + why it matters in one sentence
- **Signal vs Noise**: Flag 1-2 items as "overrated noise" if they are opinion/prediction/clickbait
- If there is genuinely no material news, say "No material developments for {ticker} in this window."
- Be direct. No disclaimers, no "it's important to note", no generic market recap format."""

    if not articles:
        user = (
            f"No news articles found for {ticker} in the last {hours} hours. "
            "Note this in your response."
        )
    else:
        lines = [f"Recent news for {ticker} (last {hours} hours):\n"]
        for i, a in enumerate(articles, 1):
            pub = f" ({a['pub_date'][:16]})" if a["pub_date"] else ""
            lines.append(f"[{i}] {a['title']}{pub}")
            lines.append(f"    Source: {a['source']} | Link: {a['link']}")
            lines.append("")
        user = "\n".join(lines)

    return {"system": system, "user": user}
