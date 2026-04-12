from fastapi import FastAPI
from stock_tracker import get_stock_summary
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()



app = FastAPI()


@app.get("/")
def root():
    return {"message": "Hello World"}


@app.get("/stocks_pipeline/{ticker}")
def stocks_pipeline(ticker:str):
    return get_stock_summary(ticker)
