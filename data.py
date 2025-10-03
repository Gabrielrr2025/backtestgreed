import pandas as pd
import requests
import yfinance as yf
from datetime import datetime, date

def get_fgi_history() -> pd.DataFrame:
    url = "https://api.alternative.me/fng/"
    params = {"limit": 0, "format": "json", "date_format": "us"}
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    data = r.json().get("data", [])
    rows = []
    for d in data:
        try:
            ts = int(d["timestamp"])
            day = datetime.utcfromtimestamp(ts).date()
            rows.append({"date": pd.to_datetime(day), "FGI": float(d["value"])})
        except Exception:
            continue
    fgi = pd.DataFrame(rows).drop_duplicates(subset=["date"]).sort_values("date").set_index("date")
    return fgi

def get_btc_history(start: date, end: date) -> pd.DataFrame:
    ticker = yf.Ticker("BTC-USD")
    df = ticker.history(start=start, end=end)
    df = df.rename(columns={"Open": "Open", "Close": "Close"})
    df.index = pd.to_datetime(df.index.date)
    return df[["Open", "Close"]].dropna()

def align_series(fgi: pd.DataFrame, px: pd.DataFrame, start: date, end: date) -> pd.DataFrame:
    df = px.join(fgi, how="inner")
    df = df.loc[(df.index >= pd.to_datetime(start)) & (df.index <= pd.to_datetime(end))]
    return df
