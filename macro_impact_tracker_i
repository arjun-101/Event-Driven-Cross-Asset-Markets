import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
from datetime import timedelta, datetime, timezone

ASSETS = {
    "Equities": "SPY",
    "Rates": "TLT",
    "FX": "UUP",
    "Volatility": "VIXY"
}

now_utc = datetime.now(timezone.utc).replace(second=0, microsecond=0)

def weekday_adjust(dt):
    while dt.weekday() > 4:
        dt -= timedelta(days=1)
    return dt

cpi_time = weekday_adjust((now_utc - timedelta(days=2)).replace(hour=13, minute=30))
nfp_time = weekday_adjust((now_utc - timedelta(days=3)).replace(hour=13, minute=30))

events = [
    {"event": "CPI Release", "time": cpi_time, "actual": 3.1, "forecast": 3.2},
    {"event": "Employment (NFP)", "time": nfp_time, "actual": 199000, "forecast": 180000}
]

def run_macro_project():
    results = []

    for e in events:
        event_time = e["time"]
        surprise = e["actual"] - e["forecast"]

        start = event_time - timedelta(days=1)
        end = event_time + timedelta(days=1)

        plt.figure(figsize=(12, 7))
        plotted = False

        for label, ticker in ASSETS.items():
            data = yf.download(
                ticker,
                start=start,
                end=end,
                interval="5m",
                auto_adjust=True,
                progress=False
            )

            if data.empty:
                continue

            data.index = data.index.tz_localize("UTC") if data.index.tz is None else data.index.tz_convert("UTC")
            data["ret"] = data["Close"].pct_change()

            window = data.loc[event_time - timedelta(minutes=30): event_time + timedelta(minutes=120)]
            if window.empty:
                continue

            base = window["Close"].iloc[0]
            window["cum_ret"] = (window["Close"] / base - 1) * 100 if base != 0 else 0

            t0 = window.index.asof(event_time)
            t15 = window.index.asof(event_time + timedelta(minutes=15))
            t60 = window.index.asof(event_time + timedelta(minutes=60))

            r15 = window.loc[t0:t15]["ret"].sum() * 100 if t0 and t15 else 0
            r60 = window.loc[t0:t60]["ret"].sum() * 100 if t0 and t60 else 0

            results.append({
                "Event": e["event"],
                "Asset": label,
                "Surprise": surprise,
                "15m_Impact_%": round(r15, 3),
                "60m_Impact_%": round(r60, 3)
            })

            plt.plot(window.index, window["cum_ret"], label=f"{label} ({ticker})")
            plotted = True

        if plotted:
            plt.axvline(event_time, color="red", linestyle="--")
            plt.title(f"Market Reaction: {e['event']} (Surprise: {surprise})")
            plt.ylabel("Cumulative Return (%)")
            plt.xlabel("Time (UTC)")
            plt.legend()
            plt.grid(alpha=0.3)

            fname = f"market_reaction_{e['event'].replace(' ', '')}{event_time.strftime('%Y%m%d_%H%M')}.png"
            plt.savefig(fname)
        plt.close()

    print(pd.DataFrame(results))

if _name_ == "_main_":
    run_macro_project()
