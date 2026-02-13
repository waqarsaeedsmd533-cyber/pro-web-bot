from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import threading
import time
import yfinance as yf
import pandas as pd

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

bot_running = False
signals = []

symbols = ["EURUSD=X", "GBPUSD=X", "GC=F"]

EMA_FAST = 50
EMA_SLOW = 200
RSI_PERIOD = 14


def fetch_data(symbol):
    data = yf.download(
        tickers=symbol,
        period="1d",
        interval="5m",
        progress=False
    )
    return data


def calculate_signal(df):
    df['EMA_FAST'] = df['Close'].ewm(span=EMA_FAST).mean()
    df['EMA_SLOW'] = df['Close'].ewm(span=EMA_SLOW).mean()

    delta = df['Close'].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(RSI_PERIOD).mean()
    avg_loss = loss.rolling(RSI_PERIOD).mean()
    rs = avg_gain / avg_loss
    df['RSI'] = 100 - (100 / (1 + rs))

    last = df.iloc[-1]

    uptrend = last['EMA_FAST'] > last['EMA_SLOW']
    downtrend = last['EMA_FAST'] < last['EMA_SLOW']

    if uptrend and 35 < last['RSI'] < 55:
        return "CALL"
    elif downtrend and 45 < last['RSI'] < 65:
        return "PUT"
    else:
        return "NONE"


def bot_loop():
    global signals

    while bot_running:
        temp_signals = []

        for symbol in symbols:
            try:
                df = fetch_data(symbol)
                signal = calculate_signal(df)

                temp_signals.append({
                    "symbol": symbol,
                    "signal": signal,
                    "time": time.strftime("%H:%M:%S")
                })

            except:
                temp_signals.append({
                    "symbol": symbol,
                    "signal": "ERROR",
                    "time": time.strftime("%H:%M:%S")
                })

        signals = temp_signals
        time.sleep(10)


@app.get("/")
def home():
    return {"message": "PRO WEB BOT RUNNING"}


@app.get("/signals")
def get_signals():
    return {
        "bot_running": bot_running,
        "signals": signals
    }


@app.post("/start
