import numpy as np
import pandas as pd

def annualized_return(equity: pd.Series, periods_per_year=365.25):
    equity = equity.dropna()
    if len(equity) < 2:
        return 0.0
    start = equity.iloc[0]
    end = equity.iloc[-1]
    n_periods = len(equity)
    years = n_periods / periods_per_year
    if start <= 0 or years <= 0:
        return 0.0
    return (end / start) ** (1 / years) - 1

def max_drawdown(equity: pd.Series):
    s = equity.dropna().astype(float)
    roll_max = s.cummax()
    drawdown = s / roll_max - 1.0
    return drawdown.min()

def fmt_money(x, prefix="$"):
    try:
        return f"{prefix}{x:,.2f}"
    except Exception:
        return str(x)

def fmt_pct(x, suffix=""):
    try:
        return f"{x*100:,.2f}%{(' ' + suffix) if suffix else ''}"
    except Exception:
        return str(x)
