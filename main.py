from fastapi import FastAPI
from stock_tracker import get_stock_summary
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

MINIMAX_BASE_URL = "https://api.minimax.io/v1"
MINIMAX_BASE_URL = "http://ollama.lan:11434/v1"
MINIMAX_API_KEY = os.getenv("MINIMAX_API_KEY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
MODEL = "qwen3.5:4b"

openai = OpenAI(
    base_url=MINIMAX_BASE_URL,
    api_key=MINIMAX_API_KEY,
)



app = FastAPI()


@app.get("/")
def root():
    return {"message": "Hello World"}

@app.get("/stocks_pipeline")
def stocks_pipeline():
    get_stock_summary(openai,MODEL,WEBHOOK_URL,"AAPL")

