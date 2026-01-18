import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import griddata
from mpl_toolkits.mplot3d import Axes3D

# -----------------------------
# CONFIG
# -----------------------------
TICKER = "SPY"
RISK_FREE_RATE = 0.045

# -----------------------------
# FETCH OPTION DATA
# -----------------------------
ticker = yf.Ticker(TICKER)
spot = ticker.info["regularMarketPrice"]

options_data = []
for expiry in ticker.options:
    chain = ticker.option_chain(expiry)
    for df, opt_type in [(chain.calls, "call"), (chain.puts, "put")]:
        if not df.empty:
            df = df.copy()
            df["option_type"] = opt_type
            df["expiration_date"] = expiry
            options_data.append(df)

df = pd.concat(options_data, ignore_index=True)

# -----------------------------
# TIME TO EXPIRY & IV
# -----------------------------
df["expiration_date"] = pd.to_datetime(df["expiration_date"]).dt.tz_localize(None)
df["lastTradeDate"] = pd.to_datetime(df["lastTradeDate"]).dt.tz_localize(None)

df["T"] = (df["expiration_date"] - df["lastTradeDate"]).dt.days / 365.25
df.rename(columns={"impliedVolatility": "IV"}, inplace=True)

df = df[(df["T"] > 0) & (df["IV"] > 0)]

# -----------------------------
# DATA CLEANING
# -----------------------------
df = df[(df["bid"] > 0) & (df["ask"] > 0)]
df = df[(df["volume"] > 0) | (df["openInterest"] > 0)]

df["spread_pct"] = (df["ask"] - df["bid"]) / df["lastPrice"]
df = df[(df["lastPrice"] > 0) & (df["spread_pct"] <= 1.0)]

df["moneyness"] = df["strike"] / spot
df = df[(df["moneyness"] >= 0.7) & (df["moneyness"] <= 1.3)]

df = df[df["bid"] <= df["ask"]]

# -----------------------------
# INTERPOLATION GRID
# -----------------------------
m = df["moneyness"].values
t = df["T"].values
iv = df["IV"].values

m_grid = np.linspace(m.min(), m.max(), 100)
t_grid = np.linspace(t.min(), t.max(), 100)
M, T = np.meshgrid(m_grid, t_grid)

points = np.column_stack([m, t])
IV_surface = griddata(points, iv, (M, T), method="cubic")
IV_linear = griddata(points, iv, (M, T), method="linear")

IV_surface = np.where(np.isnan(IV_surface), IV_linear, IV_surface)
IV_surface = np.nan_to_num(IV_surface, nan=np.nanmean(IV_surface))

# -----------------------------
# PLOT & SAVE
# -----------------------------
fig = plt.figure(figsize=(10, 7))
ax = fig.add_subplot(111, projection="3d")

ax.plot_surface(M, T, IV_surface, cmap="viridis")
ax.set_xlabel("Moneyness (K/S)")
ax.set_ylabel("Time to Expiry (Years)")
ax.set_zlabel("Implied Volatility")
ax.set_title("Implied Volatility Surface")

plt.savefig("volatility_surface.png")
plt.close()
