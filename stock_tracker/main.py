import os
import yfinance as yf
from openai import OpenAI
import requests

MODEL = "MiniMax-M2.7"
MODEL = "llama3.2:1b"

def get_stock_summary(openai, model, webhook_url,ticker):
    dat = yf.Ticker(ticker)
    response = openai.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "You are the hottest stock analyst in the world.",
            },
            # {"role":"user","content":f"Summarize this message about stock news in 5 bullets and give a bottom line of if its a good buy or sell: {dat.info}"},
            {
                "role": "user",
                "content": f"Summarize this quarterly income statement about stock news in 5 bullets and give a bottom line of if its a good buy or sell: {dat.quarterly_income_stmt}, Heres some news about the company: {dat.info}",
            },
        ],
    )
    
    summary = response.choices[0].message.content
    if "</think>" in summary:
        summary = summary.split("</think>")[1]
    r = requests.post(webhook_url, json={"content": summary})
    return {"status_code": r.status_code, "summary": summary}
