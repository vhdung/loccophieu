import argparse
import numpy as np
import pandas as pd


def generate_demo_data() -> pd.DataFrame:
    tickers = ["FPT", "VNM", "MWG", "VCB", "HPG", "MSN", "TCB", "GVR"]
    rows = []
    start_date = pd.Timestamp("2024-01-01")

    for idx, ticker in enumerate(tickers):
        base = 100 + idx * 15
        price = base
        for day in range(120):
            date = start_date + pd.Timedelta(days=day)
            drift = 0.9 + (day / 200) + (idx * 0.15)
            change = np.sin(day / 7 + idx) * 1.8 + np.cos(day / 11 + idx) * 1.3
            close = max(20, price + change * drift)
            open_ = close * (1 + np.sin(day / 9 + idx) * 0.012)
            high = max(open_, close) * (1 + 0.015 + abs(np.sin(day / 5 + idx)) * 0.025)
            low = min(open_, close) * (1 - 0.015 - abs(np.cos(day / 6 + idx)) * 0.025)
            volume = int(500000 + (day * 12000) + (idx * 70000) + abs(np.sin(day + idx)) * 300000)
            rows.append({
                "date": date,
                "ticker": ticker,
                "open": round(float(open_), 2),
                "high": round(float(high), 2),
                "low": round(float(low), 2),
                "close": round(float(close), 2),
                "volume": volume,
            })
            price = close

    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"])
    return df


def load_data(csv_path: str | None = None) -> pd.DataFrame:
    if csv_path:
        df = pd.read_csv(csv_path, parse_dates=["date"])
        if "ticker" not in df.columns:
            raise ValueError("CSV phải có cột 'ticker'.")
        return df
    return generate_demo_data()


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = (-delta).clip(lower=0)
    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values(["ticker", "date"]).copy()
    df["ema_20"] = df.groupby("ticker")["close"].transform(lambda s: s.ewm(span=20, adjust=False).mean())
    df["ema_50"] = df.groupby("ticker")["close"].transform(lambda s: s.ewm(span=50, adjust=False).mean())
    df["vol_20"] = df.groupby("ticker")["volume"].transform(lambda s: s.rolling(20).mean())
    df["rsi_14"] = df.groupby("ticker")["close"].transform(rsi)

    macd = df.groupby("ticker")["close"].transform(lambda s: s.ewm(span=12, adjust=False).mean() - s.ewm(span=26, adjust=False).mean())
    signal = macd.groupby(df["ticker"]).transform(lambda s: s.ewm(span=9, adjust=False).mean())
    df["macd"] = macd
    df["macd_signal"] = signal
    df["macd_histogram"] = df["macd"] - df["macd_signal"]
    return df


def fib_levels(high: float, low: float) -> dict[str, float]:
    span = high - low
    return {
        "0.382": high - span * 0.382,
        "0.5": high - span * 0.5,
        "0.618": high - span * 0.618,
        "0.786": high - span * 0.786,
    }


def evaluate_stock(group: pd.DataFrame) -> pd.Series | None:
    if group.empty:
        return None

    recent = group.iloc[-1]
    prev = group.iloc[-2] if len(group) > 1 else recent
    close = float(recent["close"])
    ema20 = float(recent["ema_20"])
    ema50 = float(recent["ema_50"])
    rsi = float(recent["rsi_14"])
    volume = float(recent["volume"])
    volume_avg = float(recent["vol_20"])
    macd = float(recent["macd"])
    signal = float(recent["macd_signal"])

    trend_up = (close > ema20) and (ema20 > ema50) and (recent["close"] > prev["close"])
    macd_up = macd > signal
    rsi_ok = 50 <= rsi <= 70
    volume_ok = volume > volume_avg * 1.1

    swing_high = float(group["high"].max())
    swing_low = float(group["low"].min())
    levels = fib_levels(swing_high, swing_low)
    fib_ok = any((levels[k] * 0.98 <= close <= levels[k] * 1.02) for k in levels)

    support = float(group["low"].rolling(20, min_periods=5).min().iloc[-1])
    support_ok = close >= support * 0.96

    score = sum([
        bool(trend_up),
        bool(macd_up),
        bool(rsi_ok),
        bool(volume_ok),
        bool(fib_ok),
        bool(support_ok),
    ])

    return pd.Series({
        "ticker": str(recent["ticker"]),
        "score": float(score),
        "trend": trend_up,
        "macd": macd_up,
        "rsi": rsi_ok,
        "volume": volume_ok,
        "fib": fib_ok,
        "support": support_ok,
        "decision": "PASS" if score >= 5 else "WATCH",
        "last_price": close,
    })


def screen_stocks(df: pd.DataFrame) -> pd.DataFrame:
    df = compute_indicators(df)
    results = []
    for _, group in df.groupby("ticker"):
        row = evaluate_stock(group)
        if row is not None:
            results.append(row)

    if not results:
        return pd.DataFrame(columns=["ticker", "score", "trend", "macd", "rsi", "volume", "fib", "support", "decision", "last_price"])

    out = pd.DataFrame(results)
    out = out.sort_values("score", ascending=False).reset_index(drop=True)
    return out


def main():
    parser = argparse.ArgumentParser(description="Vietnam stock screener")
    parser.add_argument("--csv", type=str, default=None, help="CSV file with columns: date,ticker,open,high,low,close,volume")
    parser.add_argument("--demo", action="store_true", help="Use demo data")
    args = parser.parse_args()

    df = load_data(args.csv if args.csv and not args.demo else None)
    results = screen_stocks(df)

    if results.empty:
        print("Không có mã nào đủ tiêu chuẩn.")
        return

    print(f"{'ticker':<8} {'score':>5} {'trend':>6} {'macd':>6} {'rsi':>6} {'vol':>6} {'fib':>6} {'support':>8} {'decision':>8}")
    for _, row in results.iterrows():
        print(
            f"{row['ticker']:<8} "
            f"{row['score']:>5.1f} "
            f"{str(row['trend']):>6} "
            f"{str(row['macd']):>6} "
            f"{str(row['rsi']):>6} "
            f"{str(row['volume']):>6} "
            f"{str(row['fib']):>6} "
            f"{str(row['support']):>8} "
            f"{row['decision']:>8}"
        )


if __name__ == "__main__":
    main()


