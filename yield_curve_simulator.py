import numpy as np
import matplotlib.pyplot as plt

# -----------------------------
# TENORS (Years)
# -----------------------------
tenors = np.array([0.5, 1, 2, 5, 7, 10, 20, 30])

# -----------------------------
# BASE YIELD CURVE
# -----------------------------
def generate_base_yield_curve(tenors):
    rates = 0.015 + 0.002 * tenors - 0.00002 * tenors**2
    rates[rates < 0] = 0.001
    return rates

base_curve = generate_base_yield_curve(tenors)

# -----------------------------
# CURVE MOVEMENTS
# -----------------------------
def parallel_shift(curve, shift_bps):
    return curve + shift_bps / 10000

def steepener(curve, tenors, short_bps, long_bps):
    shift = np.interp(tenors, [tenors[0], tenors[-1]],
                      [short_bps/10000, long_bps/10000])
    return curve + shift

def flattener(curve, tenors, short_bps, long_bps):
    shift = np.interp(tenors, [tenors[0], tenors[-1]],
                      [short_bps/10000, long_bps/10000])
    return curve + shift

def twist(curve, tenors, short_bps, mid_bps, long_bps):
    mid = len(tenors) // 2
    shift = np.interp(
        tenors,
        [tenors[0], tenors[mid], tenors[-1]],
        [short_bps/10000, mid_bps/10000, long_bps/10000]
    )
    return curve + shift

def butterfly(curve, tenors, wing_bps, belly_bps):
    mid = len(tenors) // 2
    shift = np.interp(
        tenors,
        [tenors[0], tenors[mid], tenors[-1]],
        [wing_bps/10000, belly_bps/10000, wing_bps/10000]
    )
    return curve + shift

# -----------------------------
# BOND PRICING & RISK
# -----------------------------
def bond_price(y, maturity, coupon=0.05, freq=1, face=100):
    times = np.arange(1, maturity + 1)
    cashflows = np.full(len(times), coupon * face)
    cashflows[-1] += face
    return np.sum(cashflows / (1 + y)**times)

def dv01(price_up, price_down):
    return (price_down - price_up) / 2

def duration(price, price_up, price_down, y):
    return (price_down - price_up) / (2 * price * y)

def convexity(price, price_up, price_down, y):
    return (price_up + price_down - 2 * price) / (price * y**2)

# -----------------------------
# SAMPLE PORTFOLIO
# -----------------------------
portfolio = [
    {"maturity": 2, "weight": 0.3},
    {"maturity": 5, "weight": 0.4},
    {"maturity": 10, "weight": 0.3}
]

def portfolio_value(curve):
    total = 0
    for bond in portfolio:
        y = np.interp(bond["maturity"], tenors, curve)
        total += bond["weight"] * bond_price(y, bond["maturity"])
    return total

# -----------------------------
# SCENARIO ANALYSIS
# -----------------------------
scenarios = {
    "Parallel +50bp": parallel_shift(base_curve, 50),
    "Steepener": steepener(base_curve, tenors, -20, 30),
    "Flattener": flattener(base_curve, tenors, 20, -30),
    "Twist": twist(base_curve, tenors, 20, -10, 30),
    "Butterfly": butterfly(base_curve, tenors, -20, 40)
}

base_value = portfolio_value(base_curve)

print("\nPORTFOLIO VALUE IMPACT\n")
for name, curve in scenarios.items():
    value = portfolio_value(curve)
    print(f"{name}: {round(value - base_value, 2)}")

# -----------------------------
# PLOT
# -----------------------------
plt.plot(tenors, base_curve, label="Base Curve", lw=2)
for name, curve in scenarios.items():
    plt.plot(tenors, curve, label=name, linestyle="--")

plt.xlabel("Tenor (Years)")
plt.ylabel("Yield")
plt.title("Yield Curve Movement Simulator")
plt.legend()
plt.grid(alpha=0.3)
plt.savefig("yield_curve_scenarios.png")
plt.close()
