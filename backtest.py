import numpy as np
import pandas as pd

from utils import annualized_return, max_drawdown

def run_backtest(df: pd.DataFrame,
                 buy_th: int = 30,
                 sell_th: int = 70,
                 initial_capital: float = 10000.0,
                 trade_on_close: bool = True,
                 reinvest: bool = True,
                 fee_bps: int = 10):
    """
    Regras:
      - Compra quando FGI < buy_th
      - Vende quando FGI > sell_th
      - trade_on_close: se True, executa na própria barra (close); senão, na abertura do dia seguinte (Open_next)
      - fee_bps: taxa única aplicada a toda operação (compra e venda), em basis points (1 bps = 0.01%)
    """
    data = df.copy().dropna(subset=["FGI", "Close"])
    data["signal_buy"] = data["FGI"] < buy_th
    data["signal_sell"] = data["FGI"] > sell_th
    data["Open_next"] = data["Open"].shift(-1)

    # Estado da carteira
    cash = initial_capital
    btc = 0.0
    position = 0  # 0 em caixa, 1 comprado
    trades = []   # lista de dicts
    equity = []   # valor de carteira diário

    for i, row in data.iterrows():
        price_exec = row["Close"] if trade_on_close else row["Open_next"]
        if pd.isna(price_exec):
            portfolio_value = cash + btc * row["Close"]
            equity.append((i, portfolio_value))
            continue

        fee_mult = 1.0 - (fee_bps / 10000.0)

        if position == 0 and row["signal_buy"]:
            if cash > 0:
                btc = (cash * fee_mult) / price_exec
                cash = 0.0
                position = 1
                trades.append({"date": i, "side": "buy", "price": price_exec, "fgi": row["FGI"]})

        elif position == 1 and row["signal_sell"]:
            if btc > 0:
                cash = btc * price_exec * fee_mult
                btc = 0.0
                position = 0
                trades.append({"date": i, "side": "sell", "price": price_exec, "fgi": row["FGI"]})

        portfolio_value = cash + btc * row["Close"]
        equity.append((i, portfolio_value))

    portfolio = pd.DataFrame(equity, columns=["date", "equity"]).set_index("date")
    trades_df = pd.DataFrame(trades)
    return trades_df, portfolio


def summary_metrics(portfolio: pd.DataFrame, close_prices: pd.Series, initial_capital: float):
    strat_return = portfolio["equity"].iloc[-1] / initial_capital - 1.0
    strat_cagr = annualized_return(portfolio["equity"], periods_per_year=365.25)
    strat_mdd = max_drawdown(portfolio["equity"])

    first_close = close_prices.iloc[0]
    last_close = close_prices.iloc[-1]
    bh_equity = (close_prices / first_close) * initial_capital
    bh_return = last_close / first_close - 1.0
    bh_cagr = annualized_return(bh_equity, periods_per_year=365.25)

    return {
        "strategy_return": strat_return,
        "strategy_cagr": strat_cagr,
        "strategy_mdd": strat_mdd,
        "bh_return": bh_return,
        "bh_cagr": bh_cagr,
        "n_trades": 0  # substituído no app pelo len(trades)
    }


def equity_curves(portfolio: pd.DataFrame, close_prices: pd.Series, initial_capital: float):
    bh_equity = (close_prices / close_prices.iloc[0]) * initial_capital
    curves = pd.concat([portfolio["equity"].rename("Strategy"), bh_equity.rename("Buy&Hold")], axis=1).dropna()
    return curves
