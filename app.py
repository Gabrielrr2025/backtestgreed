#!/usr/bin/env python3
import io
from datetime import date, datetime
import pandas as pd
import streamlit as st

from backtest import run_backtest, summary_metrics, equity_curves
from data import get_fgi_history, get_btc_history, align_series
from utils import fmt_money, fmt_pct

st.set_page_config(page_title="BTC Fear & Greed Backtest", layout="wide")

st.title("📈 Backtest BTC usando Fear & Greed Index")
st.caption("Estratégia: comprar quando FGI < limiar de 'medo' e vender quando FGI > limiar de 'ganância'. Dados diários.")

with st.sidebar:
    st.header("Parâmetros")
    start = st.date_input("Data inicial", value=date(2018, 2, 1), help="O FGI tem histórico a partir de 2018.")
    end = st.date_input("Data final", value=date.today())
    buy_th = st.number_input("Comprar quando FGI < ", value=30, min_value=0, max_value=49, step=1)
    sell_th = st.number_input("Vender quando FGI > ", value=70, min_value=51, max_value=100, step=1)
    initial_capital = st.number_input("Capital inicial (USD)", value=10000.0, min_value=10.0, step=100.0, format="%.2f")
    trade_on_close = st.selectbox("Preço p/ executar ordens", ["Fechamento do dia (close)", "Abertura do dia seguinte (open)"])
    trade_on_close = (trade_on_close == "Fechamento do dia (close)")
    reinvest = st.checkbox("Reinvestir 100% do capital a cada sinal (sem fracionar)", value=True)
    fee_bps = st.number_input("Taxa por trade (bps)", value=10, min_value=0, max_value=2000, help="1 bps = 0,01%. Ex.: 10 bps = 0,10% por operação.")
    st.markdown("---")
    st.caption("Dica: ajuste limiares (ex.: <25 / >75) e compare com Buy&Hold.")

st.info("Buscando dados históricos do Fear & Greed Index e do preço do BTC...")
fgi = get_fgi_history()
px = get_btc_history(start, end)
df = align_series(fgi, px, start, end)

if df.empty:
    st.error("Sem dados no intervalo selecionado.")
    st.stop()

st.subheader("Amostra de dados")
st.dataframe(df.head(10))

st.subheader("Regras da estratégia")
st.write(f"• **Compra** quando FGI < **{buy_th}**  • **Venda** quando FGI > **{sell_th}**  • Execução: {'close' if trade_on_close else 'next open'}  • Taxa: {fee_bps} bps")

# Rodar backtest
trades, portfolio = run_backtest(
    df=df,
    buy_th=buy_th,
    sell_th=sell_th,
    initial_capital=initial_capital,
    trade_on_close=trade_on_close,
    reinvest=reinvest,
    fee_bps=fee_bps
)

# Métricas
metrics = summary_metrics(portfolio, df["Close"], initial_capital)
metrics["n_trades"] = len(trades)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Retorno Estrat.", fmt_pct(metrics['strategy_return']), fmt_pct(metrics['strategy_cagr'], suffix=" a.a."))
col2.metric("Retorno Buy&Hold", fmt_pct(metrics['bh_return']), fmt_pct(metrics['bh_cagr'], suffix=" a.a."))
col3.metric("Máx. Drawdown (Estrat.)", fmt_pct(metrics['strategy_mdd']))
col4.metric("Nº de trades", f"{int(metrics['n_trades'])}")

# Curvas de capital
st.subheader("Curva de capital")
curves = equity_curves(portfolio, df["Close"], initial_capital)
st.line_chart(curves)

with st.expander("Ver operações (trades)"):
    st.dataframe(trades)

# Downloads
st.subheader("Exportar resultados")
def to_excel_bytes(trades_df, portfolio_df, curves_df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        trades_df.to_excel(writer, sheet_name="trades", index=False)
        portfolio_df.to_excel(writer, sheet_name="portfolio", index=True)
        curves_df.to_excel(writer, sheet_name="equity_curves", index=True)
    return output.getvalue()

excel_bytes = to_excel_bytes(trades, portfolio, curves)
st.download_button("Baixar Excel (trades + carteira + curvas)", data=excel_bytes, file_name="fgi_backtest.xlsx")

csv_trades = trades.to_csv(index=False).encode("utf-8")
st.download_button("Baixar Trades (CSV)", data=csv_trades, file_name="trades.csv")

st.caption("Aviso: backtests não garantem resultados futuros. Use como estudo de caso/educacional.")
