import os
import yfinance as yf
from openai import OpenAI
import requests

NEWS_API_KEY = os.getenv("NEWS_API_KEY")
NEWS_API_URL = os.getenv("NEWS_API_URL")


def fetch_newsapi_articles(ticker):
    if not NEWS_API_KEY:
        return "NewsAPI key not configured"

    try:
        company_name = yf.Ticker(ticker).info.get("shortName", ticker)
        params = {
            "apiKey": NEWS_API_KEY,
            "q": company_name,
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": 10,
        }
        resp = requests.get(NEWS_API_URL, params=params)
        data = resp.json()
        if data.get("status") == "ok":
            articles = data.get("articles", [])
            return "\n".join(
                f"- {a['title']}: {a.get('description', '')}" for a in articles[:5]
            )
        return f"NewsAPI error: {data.get('message', 'Unknown error')}"
    except Exception as e:
        return f"Failed to fetch news: {str(e)}"


def get_stock_summary(ticker):
    dat = yf.Ticker(ticker)
    newsapi_articles = fetch_newsapi_articles(ticker)

    message={
                "system": "You are the hottest stock analyst in the world.",
                "user": f"""
                        Summarize the following stock data for {ticker} in 5 bullets and give a bottom line of if its a good buy or sell:
                        
                        Quarterly Income Statement:
                        {dat.quarterly_income_stmt}

                        Annual Income Statement:
                        {dat.income_stmt}

                        Balance Sheet:
                        {dat.balance_sheet}

                        Cashflow:
                        {dat.cashflow}

                        News:
                        {dat.news}

                        External News (NewsAPI):
                        {newsapi_articles}

                        Analyst Price Targets:
                        {dat.analyst_price_targets}

                        Recommendations:
                        {dat.recommendations}

                        Company Info:
                        {dat.info}
            """,
        }
    
    return message
