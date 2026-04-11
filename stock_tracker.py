import os
import yfinance as yf
from openai import OpenAI
import requests
import json
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_BASE_URL="https://api.minimax.io/v1"
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

openai = OpenAI(
    base_url=ANTHROPIC_BASE_URL,
      api_key=ANTHROPIC_API_KEY,
)
MODEL = "MiniMax-M2.7"
# MODEL = "MiniMax-M2.7-highspeed"
dat = yf.Ticker("AAPL")

# print(dat.calendar)
# print(dat.analyst_price_targets)
# print(dat.quarterly_income_stmt)
# print(dat.history(period='1mo'))
# print(dat.option_chain(dat.options[0]).calls)
# print(json.dumps(dat.info,indent=4) )

# exit()


response= openai.chat.completions.create(
    model=MODEL,
  
    messages = [
        {"role":"system","content":"You are the hottest stock analyst in the world."},
        # {"role":"user","content":f"Summarize this message about stock news in 5 bullets and give a bottom line of if its a good buy or sell: {dat.info}"},
        {"role":"user","content":f"Summarize this quarterly income statement about stock news in 5 bullets and give a bottom line of if its a good buy or sell: {dat.quarterly_income_stmt}, Heres some news about the company: {dat.info}"}
    ]
)

summary = response.choices[0].message.content.split("</think>")[1]



x = requests.post(WEBHOOK_URL, json={"content": summary})

print(x.text)