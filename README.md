import os
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from stock_screening import compute_indicators, load_data, screen_stocks


st.set_page_config(page_title="Vietnam Stock Screener", page_icon="📈", layout="wide")


@st.cache_data

def fetch_dataset(csv_file=None):
    if csv_file is not None:
        return load_data(csv_file)
    return load_data(str(Path(__file__).parent / "data" / "sample_vn_stocks.csv"))


st.title("📈 Vietnam Stock Screener")
st.caption("Bộ lọc cổ phiếu theo xu hướng, MACD, Fibonacci, khối lượng và xác nhận")

with st.sidebar:
    st.header("Tùy chọn")
    uploaded = st.file_uploader("Tải file CSV cổ phiếu", type=["csv"])
    min_score = st.slider("Điểm tối thiểu", min_value=0, max_value=6, value=4)
    show_only_pass = st.checkbox("Chỉ hiển thị PASS", value=True)

    if uploaded is not None:
        data = pd.read_csv(uploaded, parse_dates=["date"])
    else:
        demo_path = Path(__file__).parent / "data" / "sample_vn_stocks.csv"
        data = load_data(str(demo_path))

screened = screen_stocks(data)
if screened.empty:
    st.warning("Không có mã nào đạt tiêu chuẩn hiện tại.")
    st.stop()

filtered = screened[screened["score"] >= min_score]
if show_only_pass:
    filtered = filtered[filtered["decision"] == "PASS"]

st.subheader("Kết quả lọc")
st.dataframe(filtered, use_container_width=True)

if not filtered.empty:
    fig = go.Figure(
        go.Bar(
            x=filtered["ticker"],
            y=filtered["score"],
            marker_color="rgba(56, 118, 220, 0.8)",
        )
    )
    fig.update_layout(title="Điểm lọc theo mã", xaxis_title="Ticker", yaxis_title="Score")
    st.plotly_chart(fig, use_container_width=True)

    ticker = st.selectbox("Chọn mã để xem biểu đồ", filtered["ticker"].tolist())
    grouped = data[data["ticker"] == ticker].sort_values("date")
    grouped = compute_indicators(grouped)

    chart = go.Figure()
    chart.add_trace(go.Candlestick(
        x=grouped["date"],
        open=grouped["open"],
        high=grouped["high"],
        low=grouped["low"],
        close=grouped["close"],
        name=ticker,
    ))
    chart.add_trace(go.Scatter(x=grouped["date"], y=grouped["ema_20"], mode="lines", name="EMA20"))
    chart.add_trace(go.Scatter(x=grouped["date"], y=grouped["ema_50"], mode="lines", name="EMA50"))
    chart.update_layout(title=f"Biểu đồ {ticker}", xaxis_title="Ngày", yaxis_title="Giá")
    st.plotly_chart(chart, use_container_width=True)

st.markdown("""
### Hướng dẫn
- Tải file CSV từ nguồn dữ liệu thật hoặc dùng CSV mẫu.
- Bộ lọc đánh giá theo: xu hướng, MACD, RSI, khối lượng, Fibonacci, hỗ trợ.
- Chọn mã có `PASS` để phân tích sâu hơn.
""")

