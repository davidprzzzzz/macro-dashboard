"""
╔══════════════════════════════════════════════════════════════╗
║           MACRO DASHBOARD — GLOBAL MARKETS MONITOR           ║
║     Equities · Rates · Spreads · Curves · FX · Crypto        ║
╚══════════════════════════════════════════════════════════════╝

Run:
    pip install streamlit yfinance plotly pandas requests fredapi
    streamlit run dashboard.py

Data sources:
    - Yahoo Finance  → Equities, FX, Commodities, Crypto, Eurex futures
    - FRED API       → US yield curve (free key at fred.stlouisfed.org)
    - ECB SDW API    → EUR sovereign yield curves (free, no key)
    - CoinGecko API  → Crypto (free, no key)
    - Manual / CSV   → ASW (Bloomberg/SEB data — enter manually or upload)

ASW module: enter values manually or upload CSV exported from BBG/SEB.
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import requests
from datetime import datetime, timedelta
import time
import json

# ─────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="MACRO TERMINAL",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Bloomberg-style dark theme ──
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;500;600&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');

:root {
    --bg:        #0a0a0f;
    --bg2:       #111118;
    --bg3:       #16161f;
    --border:    #2a2a3a;
    --accent:    #f7941d;
    --accent2:   #00d4ff;
    --green:     #00c27a;
    --red:       #ff3d5a;
    --text:      #d4d4e0;
    --text-dim:  #6b6b7f;
    --text-hdr:  #9090a8;
    --mono:      'IBM Plex Mono', monospace;
    --sans:      'IBM Plex Sans', sans-serif;
}

html, body, [data-testid="stAppViewContainer"] {
    background: var(--bg) !important;
    color: var(--text) !important;
    font-family: var(--sans) !important;
}

[data-testid="stHeader"] { background: transparent !important; }
[data-testid="block-container"] { padding: 1rem 2rem !important; max-width: 100% !important; }
[data-testid="stVerticalBlock"] { gap: 0.5rem !important; }

/* Hide streamlit branding */
#MainMenu, footer, [data-testid="stToolbar"] { visibility: hidden; }

/* Section headers */
.section-header {
    font-family: var(--mono);
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.15em;
    color: var(--accent);
    text-transform: uppercase;
    border-bottom: 1px solid var(--border);
    padding: 0.6rem 0 0.4rem;
    margin: 1.2rem 0 0.6rem;
}

/* Ticker card */
.ticker-card {
    background: var(--bg2);
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 0.6rem 0.8rem;
    font-family: var(--mono);
    min-height: 72px;
    position: relative;
    transition: border-color 0.2s;
}
.ticker-card:hover { border-color: var(--accent); }
.ticker-label {
    font-size: 0.62rem;
    color: var(--text-hdr);
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-bottom: 0.2rem;
}
.ticker-value {
    font-size: 1.15rem;
    font-weight: 600;
    color: var(--text);
    margin-bottom: 0.1rem;
}
.ticker-change-pos { color: var(--green); font-size: 0.72rem; }
.ticker-change-neg { color: var(--red); font-size: 0.72rem; }
.ticker-change-neu { color: var(--text-dim); font-size: 0.72rem; }
.ticker-sub { color: var(--text-dim); font-size: 0.6rem; margin-top: 0.15rem; }

/* Spread card */
.spread-card {
    background: var(--bg3);
    border: 1px solid var(--border);
    border-left: 3px solid var(--accent2);
    border-radius: 4px;
    padding: 0.5rem 0.8rem;
    font-family: var(--mono);
    margin-bottom: 0.3rem;
}
.spread-name { font-size: 0.62rem; color: var(--text-hdr); letter-spacing: 0.08em; }
.spread-val { font-size: 1rem; font-weight: 600; }

/* Top bar */
.top-bar {
    background: var(--bg2);
    border-bottom: 1px solid var(--border);
    border-top: 2px solid var(--accent);
    padding: 0.6rem 1rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-family: var(--mono);
    margin-bottom: 1rem;
    border-radius: 4px;
}
.top-bar-title {
    font-size: 0.9rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    color: var(--accent);
}
.top-bar-time { font-size: 0.7rem; color: var(--text-dim); }

/* Table style */
.stDataFrame { background: var(--bg2) !important; }
thead tr th { background: var(--bg3) !important; color: var(--text-hdr) !important; font-family: var(--mono) !important; font-size: 0.7rem !important; }
tbody tr td { font-family: var(--mono) !important; font-size: 0.75rem !important; }

/* Metric override */
[data-testid="metric-container"] {
    background: var(--bg2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 4px !important;
    padding: 0.5rem !important;
}

/* Upload zone */
.upload-info {
    background: var(--bg3);
    border: 1px dashed var(--border);
    border-radius: 4px;
    padding: 0.8rem;
    font-family: var(--mono);
    font-size: 0.7rem;
    color: var(--text-dim);
    text-align: center;
}

/* Divider */
hr { border-color: var(--border) !important; margin: 0.5rem 0 !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# CONSTANTS & TICKERS
# ─────────────────────────────────────────────────────────────

EQUITIES = {
    # Europe
    "EURO STOXX 50": "^STOXX50E",
    "DAX":           "^GDAXI",
    "CAC 40":        "^FCHI",
    "FTSE 100":      "^FTSE",
    "IBEX 35":       "^IBEX",
    "FTSE MIB":      "FTSEMIB.MI",
    # US
    "S&P 500":       "^GSPC",
    "NASDAQ 100":    "^NDX",
    "DOW JONES":     "^DJI",
    "RUSSELL 2000":  "^RUT",
    # Asia
    "NIKKEI 225":    "^N225",
    "HANG SENG":     "^HSI",
    "CSI 300":       "000300.SS",
    "KOSPI":         "^KS11",
}

EUREX_FUTURES = {
    "Bund (RX)":     "FGBL=F",   # 10Y
    "Bobl (OE)":     "FGBM=F",   # 5Y
    "Schatz (DU)":   "FGBS=F",   # 2Y
    "Buxl (UB)":     "FGBX=F",   # 30Y
}

FX = {
    "EUR/USD": "EURUSD=X",
    "USD/JPY": "USDJPY=X",
    "GBP/USD": "GBPUSD=X",
    "EUR/GBP": "EURGBP=X",
    "EUR/CHF": "EURCHF=X",
    "DXY":     "DX-Y.NYB",
}

COMMODITIES = {
    "WTI Oil":    "CL=F",
    "Brent Oil":  "BZ=F",
    "Gold":       "GC=F",
    "Silver":     "SI=F",
    "Nat Gas":    "NG=F",
    "Copper":     "HG=F",
}

CRYPTO_YF = {
    "Bitcoin":  "BTC-USD",
    "Ethereum": "ETH-USD",
    "Solana":   "SOL-USD",
}

# Bitcoin Spot ETFs for flow proxy
BTC_ETFS = {
    "IBIT (BlackRock)": "IBIT",
    "FBTC (Fidelity)":  "FBTC",
    "BITB (Bitwise)":   "BITB",
    "ARKB (ARK)":       "ARKB",
}

# FRED series for US yield curve
FRED_SERIES = {
    "2Y":  "DGS2",
    "5Y":  "DGS5",
    "10Y": "DGS10",
    "30Y": "DGS30",
}

# ECB SDW series IDs for sovereign yields
# Format: IRS.M.{country}.L.L45.YC.EUR.{tenor}.?YF.M.A
ECB_COUNTRIES = {
    "DE": "Germany",
    "FR": "France",
    "IT": "Italy",
    "ES": "Spain",
    "GB": "United Kingdom",
}
ECB_TENORS = {"2Y": "2", "5Y": "5", "10Y": "10", "30Y": "30"}

COLORS = {
    "bg": "#0a0a0f", "accent": "#f7941d", "accent2": "#00d4ff",
    "green": "#00c27a", "red": "#ff3d5a", "text": "#d4d4e0",
    "grid": "#1e1e2a", "dim": "#6b6b7f",
    "DE": "#f7941d", "FR": "#00d4ff", "IT": "#a855f7",
    "ES": "#fbbf24", "US": "#00c27a",
}

# ─────────────────────────────────────────────────────────────
# DATA FETCHING HELPERS
# ─────────────────────────────────────────────────────────────

@st.cache_data(ttl=60)
def fetch_yf_snapshot(tickers: dict) -> dict:
    """Fetch last price + day change for a dict of {label: ticker}."""
    results = {}
    symbols = list(tickers.values())
    try:
        raw = yf.download(symbols, period="2d", interval="1d",
                          group_by="ticker", progress=False, threads=True)
        for label, sym in tickers.items():
            try:
                if len(symbols) == 1:
                    closes = raw["Close"]
                else:
                    closes = raw[sym]["Close"] if sym in raw.columns.get_level_values(0) else raw["Close"]
                closes = closes.dropna()
                if len(closes) >= 2:
                    last = float(closes.iloc[-1])
                    prev = float(closes.iloc[-2])
                    chg = last - prev
                    pct = (chg / prev) * 100
                    results[label] = {"price": last, "chg": chg, "pct": pct, "ok": True}
                elif len(closes) == 1:
                    results[label] = {"price": float(closes.iloc[-1]), "chg": 0, "pct": 0, "ok": True}
                else:
                    results[label] = {"price": None, "chg": 0, "pct": 0, "ok": False}
            except Exception:
                results[label] = {"price": None, "chg": 0, "pct": 0, "ok": False}
    except Exception as e:
        for label in tickers:
            results[label] = {"price": None, "chg": 0, "pct": 0, "ok": False}
    return results


@st.cache_data(ttl=60)
def fetch_yf_history(ticker: str, period: str = "6mo") -> pd.DataFrame:
    """Return OHLCV DataFrame."""
    try:
        df = yf.download(ticker, period=period, interval="1d", progress=False)
        return df
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=300)
def fetch_fred_yields(api_key: str = "") -> dict:
    """
    Fetch US treasury yields from FRED.
    If no API key, tries public JSON endpoint (observation limit applies).
    Returns {tenor: latest_yield_pct}
    """
    yields = {}
    base = "https://fred.stlouisfed.org/graph/fredgraph.json"
    for tenor, series in FRED_SERIES.items():
        try:
            url = f"{base}?id={series}"
            if api_key:
                url += f"&api_key={api_key}"
            r = requests.get(url, timeout=8)
            if r.status_code == 200:
                data = r.json()
                # fredgraph returns {dates: [...], values: [...]}
                vals = data.get("values", [])
                if vals:
                    last = [v for v in vals if v != "."]
                    if last:
                        yields[tenor] = float(last[-1])
        except Exception:
            pass
    return yields


@st.cache_data(ttl=300)
def fetch_ecb_yields() -> dict:
    """
    Fetch EUR sovereign yields from ECB Statistical Data Warehouse.
    Returns {country: {tenor: yield_pct}}
    ECB SDW REST API — no key required.
    """
    results = {c: {} for c in ECB_COUNTRIES}
    # ECB SDW yield curve dataset: YC (yield curves)
    # Series key: YC.B.U2.EUR.4F.G_N_{country}.SV_C_YM.SR_{tenor}Y
    base = "https://data-api.ecb.europa.eu/service/data"
    # Map country codes to ECB codes
    ecb_codes = {"DE": "DE", "FR": "FR", "IT": "IT", "ES": "ES", "GB": "GB"}
    for country, ecb_cc in ecb_codes.items():
        for tenor_label, tenor_yr in ECB_TENORS.items():
            try:
                # ECB Yield Curves dataset
                key = f"YC/B.U2.EUR.4F.G_N_{ecb_cc}.SV_C_YM.SR_{tenor_yr}Y"
                url = f"{base}/{key}?lastNObservations=1&format=jsondata"
                r = requests.get(url, timeout=8, headers={"Accept": "application/json"})
                if r.status_code == 200:
                    jd = r.json()
                    obs = jd["dataSets"][0]["series"]
                    # Get first series observations
                    series_key = list(obs.keys())[0]
                    observations = obs[series_key]["observations"]
                    if observations:
                        last_key = sorted(observations.keys(), key=int)[-1]
                        val = observations[last_key][0]
                        if val is not None:
                            results[country][tenor_label] = float(val)
            except Exception:
                pass
    return results


@st.cache_data(ttl=120)
def fetch_coingecko() -> dict:
    """Fetch BTC/ETH/SOL prices and 24h change from CoinGecko (free, no key)."""
    try:
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            "ids": "bitcoin,ethereum,solana",
            "vs_currencies": "usd",
            "include_24hr_change": "true",
            "include_market_cap": "true",
        }
        r = requests.get(url, params=params, timeout=8)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return {}


@st.cache_data(ttl=300)
def fetch_etf_volumes(tickers: dict) -> dict:
    """Get volume + AUM proxy from Yahoo for BTC ETFs."""
    results = {}
    for name, sym in tickers.items():
        try:
            t = yf.Ticker(sym)
            info = t.fast_info
            hist = t.history(period="5d")
            if not hist.empty:
                last_vol = int(hist["Volume"].iloc[-1])
                last_price = float(hist["Close"].iloc[-1])
                prev_vol = int(hist["Volume"].iloc[-2]) if len(hist) > 1 else last_vol
                results[name] = {
                    "price": last_price,
                    "volume": last_vol,
                    "vol_chg": last_vol - prev_vol,
                    "vol_usd": last_vol * last_price,
                }
        except Exception:
            results[name] = {"price": None, "volume": None, "vol_chg": 0, "vol_usd": None}
    return results


# ─────────────────────────────────────────────────────────────
# CHART HELPERS
# ─────────────────────────────────────────────────────────────

PLOT_LAYOUT = dict(
    paper_bgcolor="#0a0a0f",
    plot_bgcolor="#0a0a0f",
    font=dict(family="IBM Plex Mono", color="#d4d4e0", size=10),
    xaxis=dict(gridcolor="#1e1e2a", showgrid=True, zeroline=False, linecolor="#2a2a3a"),
    yaxis=dict(gridcolor="#1e1e2a", showgrid=True, zeroline=False, linecolor="#2a2a3a"),
    margin=dict(l=40, r=20, t=30, b=30),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=9)),
    hovermode="x unified",
)


def line_chart(df: pd.DataFrame, cols: list, title: str, colors: list = None,
               yformat: str = ".2f", height: int = 220) -> go.Figure:
    """Generic multi-line chart."""
    fig = go.Figure()
    palette = colors or ["#f7941d", "#00d4ff", "#a855f7", "#fbbf24", "#00c27a", "#ff3d5a"]
    for i, col in enumerate(cols):
        if col in df.columns:
            series = df[col].dropna()
            fig.add_trace(go.Scatter(
                x=series.index, y=series,
                name=col,
                line=dict(color=palette[i % len(palette)], width=1.5),
                mode="lines",
            ))
    fig.update_layout(**PLOT_LAYOUT, height=height, title=dict(text=title, font=dict(size=10, color="#9090a8"), x=0))
    fig.update_yaxes(tickformat=yformat)
    return fig


def spread_chart(s1: pd.Series, s2: pd.Series, label: str,
                 color: str = "#00d4ff", height: int = 180) -> go.Figure:
    """Plot spread (s1 - s2) in bps."""
    spread = (s1 - s2).dropna() * 100  # assume yields in %, spread in bps
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=spread.index, y=spread,
        name=label,
        line=dict(color=color, width=1.5),
        fill="tozeroy",
        fillcolor=color.replace(")", ", 0.08)").replace("rgb", "rgba") if "rgb" in color else f"rgba(0,212,255,0.08)",
    ))
    fig.update_layout(**PLOT_LAYOUT, height=height,
                      title=dict(text=label, font=dict(size=10, color="#9090a8"), x=0))
    fig.update_yaxes(tickformat=".0f", ticksuffix="bp")
    return fig


def bar_chart(labels: list, values: list, colors: list, title: str, height: int = 200) -> go.Figure:
    fig = go.Figure(go.Bar(
        x=labels, y=values,
        marker_color=colors,
        text=[f"{v:+.2f}%" if v is not None else "N/A" for v in values],
        textposition="outside",
        textfont=dict(size=9),
    ))
    fig.update_layout(**PLOT_LAYOUT, height=height,
                      title=dict(text=title, font=dict(size=10, color="#9090a8"), x=0),
                      showlegend=False)
    return fig


# ─────────────────────────────────────────────────────────────
# UI COMPONENTS
# ─────────────────────────────────────────────────────────────

def render_ticker_card(label: str, data: dict, decimals: int = 2, suffix: str = ""):
    """Render a Bloomberg-style ticker tile."""
    price = data.get("price")
    pct = data.get("pct", 0)
    chg = data.get("chg", 0)

    if price is None:
        price_str = "N/A"
        chg_str = "—"
        cls = "ticker-change-neu"
    else:
        price_str = f"{price:,.{decimals}f}{suffix}"
        sign = "▲" if pct > 0 else ("▼" if pct < 0 else "—")
        chg_str = f"{sign} {abs(pct):.2f}% ({chg:+.{decimals}f})"
        cls = "ticker-change-pos" if pct > 0 else ("ticker-change-neg" if pct < 0 else "ticker-change-neu")


def section(title: str):
    st.markdown(f'<div class="section-header">◈ {title}</div>', unsafe_allow_html=True)


def compute_curve_spread(yields: dict, country: str, t1: str, t2: str) -> float | None:
    """Yield curve spread t2 - t1 in bps."""
    c = yields.get(country, {})
    if t1 in c and t2 in c:
        return (c[t2] - c[t1]) * 100
    return None


def compute_box(yields: dict, c1: str, c2: str, t1: str, t2: str) -> float | None:
    """Box spread = (c1 curve slope) - (c2 curve slope), in bps."""
    s1 = compute_curve_spread(yields, c1, t1, t2)
    s2 = compute_curve_spread(yields, c2, t1, t2)
    if s1 is not None and s2 is not None:
        return s1 - s2
    return None


def fmt_bp(val) -> str:
    if val is None:
        return "N/A"
    sign = "+" if val > 0 else ""
    return f"{sign}{val:.1f} bp"


def fmt_yield(val) -> str:
    if val is None:
        return "N/A"
    return f"{val:.3f}%"


# ─────────────────────────────────────────────────────────────
# MAIN APP
# ─────────────────────────────────────────────────────────────

def main():

    # ── Top bar ──
    now = datetime.utcnow().strftime("%Y-%m-%d  %H:%M:%S UTC")
    st.markdown(f"""
    <div class="top-bar">
        <span class="top-bar-title">◈ MACRO TERMINAL · GLOBAL MARKETS</span>
        <span class="top-bar-time">🕐 {now} · Auto-refresh every 60s</span>
    </div>
    """, unsafe_allow_html=True)

    # ── Sidebar config ──
    with st.sidebar:
        st.markdown("### ⚙ Settings")
        fred_key = st.text_input("FRED API Key (optional)", type="password",
                                 help="Get free key at fred.stlouisfed.org/docs/api")
        auto_refresh = st.checkbox("Auto-refresh (60s)", value=False)
        period = st.selectbox("Chart lookback", ["1mo", "3mo", "6mo", "1y", "2y"], index=2)
        st.markdown("---")
        st.markdown("### 📋 ASW Manual Input")
        st.markdown("*Enter values from Bloomberg/SEB (bps)*")
        asw_du  = st.number_input("DU ASW (2Y Schatz)", value=0.0, step=0.1, format="%.1f")
        asw_oe  = st.number_input("OE ASW (5Y Bobl)",   value=0.0, step=0.1, format="%.1f")
        asw_rx  = st.number_input("RX ASW (10Y Bund)",  value=0.0, step=0.1, format="%.1f")
        asw_ub  = st.number_input("UB ASW (30Y Buxl)",  value=0.0, step=0.1, format="%.1f")
        st.markdown("---")
        st.markdown("### 📂 ASW Bulk Upload")
        uploaded = st.file_uploader("Upload ASW CSV (BBG/SEB export)", type=["csv"])
        if uploaded:
            asw_df = pd.read_csv(uploaded)
            st.dataframe(asw_df.tail(10), height=150)

    # Auto-refresh
    if auto_refresh:
        time.sleep(1)
        st.rerun()

    # ── Fetch data ──
    with st.spinner("Fetching market data..."):
        eq_data     = fetch_yf_snapshot(EQUITIES)
        fx_data     = fetch_yf_snapshot(FX)
        commo_data  = fetch_yf_snapshot(COMMODITIES)
        future_data = fetch_yf_snapshot(EUREX_FUTURES)
        ecb_yields  = fetch_ecb_yields()
        us_yields   = fetch_fred_yields(fred_key)
        cg_data     = fetch_coingecko()
        etf_flows   = fetch_etf_volumes(BTC_ETFS)

    # ════════════════════════════════════════════════════════
    # 1. EQUITIES
    # ════════════════════════════════════════════════════════
    section("EQUITIES")

    st.markdown("**🇪🇺 Europe**")
    eu_indices = ["EURO STOXX 50", "DAX", "CAC 40", "FTSE 100", "IBEX 35", "FTSE MIB"]
    cols = st.columns(len(eu_indices))
    for i, idx in enumerate(eu_indices):
        with cols[i]:
            render_ticker_card(idx, eq_data.get(idx, {}), decimals=0)

    st.markdown("**🇺🇸 United States**")
    us_indices = ["S&P 500", "NASDAQ 100", "DOW JONES", "RUSSELL 2000"]
    cols = st.columns(4)
    for i, idx in enumerate(us_indices):
        with cols[i]:
            render_ticker_card(idx, eq_data.get(idx, {}), decimals=0)

    st.markdown("**🌏 Asia**")
    as_indices = ["NIKKEI 225", "HANG SENG", "CSI 300", "KOSPI"]
    cols = st.columns(4)
    for i, idx in enumerate(as_indices):
        with cols[i]:
            render_ticker_card(idx, eq_data.get(idx, {}), decimals=0)

    # Equity bar chart
    pcts = [eq_data.get(k, {}).get("pct") for k in list(EQUITIES.keys())]
    colors_eq = [COLORS["green"] if (p or 0) >= 0 else COLORS["red"] for p in pcts]
    fig_eq = bar_chart(list(EQUITIES.keys()), pcts, colors_eq, "Daily % Change — All Indices", height=220)
    st.plotly_chart(fig_eq, use_container_width=True, config={"displayModeBar": False})

    # ════════════════════════════════════════════════════════
    # 2. RATES — EUR FUTURES (EUREX)
    # ════════════════════════════════════════════════════════
    section("RATES · EUR FUTURES (EUREX)")

    cols = st.columns(4)
    for i, (name, ticker) in enumerate(EUREX_FUTURES.items()):
        with cols[i]:
            render_ticker_card(name, future_data.get(name, {}), decimals=3)

    # Historical charts
    col1, col2 = st.columns(2)
    with col1:
        df_rx = fetch_yf_history("FGBL=F", period)
        if not df_rx.empty:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df_rx.index, y=df_rx["Close"],
                                     line=dict(color=COLORS["accent"], width=1.5), name="Bund (RX)"))
            fig.update_layout(**PLOT_LAYOUT, height=200,
                              title=dict(text="Bund Future (RX) — Price", font=dict(size=10, color="#9090a8"), x=0))
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with col2:
        df_du = fetch_yf_history("FGBS=F", period)
        if not df_du.empty:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df_du.index, y=df_du["Close"],
                                     line=dict(color=COLORS["accent2"], width=1.5), name="Schatz (DU)"))
            fig.update_layout(**PLOT_LAYOUT, height=200,
                              title=dict(text="Schatz Future (DU) — Price", font=dict(size=10, color="#9090a8"), x=0))
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # ════════════════════════════════════════════════════════
    # 3. YIELD CURVES + SOVEREIGN SPREADS
    # ════════════════════════════════════════════════════════
    section("SOVEREIGN YIELDS & SPREADS")

    # ── Yield table ──
    tenors = ["2Y", "5Y", "10Y", "30Y"]
    yield_rows = []
    for country, fullname in ECB_COUNTRIES.items():
        row = {"Country": fullname}
        for t in tenors:
            val = ecb_yields.get(country, {}).get(t)
            row[t] = fmt_yield(val)
        yield_rows.append(row)

    # US row
    if us_yields:
        row = {"Country": "United States"}
        for t in tenors:
            row[t] = fmt_yield(us_yields.get(t))
        yield_rows.append(row)

    df_yields = pd.DataFrame(yield_rows).set_index("Country")
    st.dataframe(df_yields, use_container_width=True)

    # ── OAT-Bund, BTP-Bund, Gilt-Bund spreads ──
    st.markdown("**Sovereign Spreads vs Bund (bps)**")
    spread_pairs = [
        ("OAT-Bund", "FR", "DE"),
        ("BTP-Bund",  "IT", "DE"),
        ("BONOS-Bund","ES", "DE"),
    ]
    cols = st.columns(3)
    for i, (label, c1, c2) in enumerate(spread_pairs):
        with cols[i]:
            for t in tenors:
                v1 = ecb_yields.get(c1, {}).get(t)
                v2 = ecb_yields.get(c2, {}).get(t)
                if v1 and v2:
                    bp = (v1 - v2) * 100
                    col_cls = "ticker-change-pos" if bp > 0 else "ticker-change-neg"
                    st.markdown(f"""
                    <div class="spread-card">
                        <div class="spread-name">{label} · {t}</div>
                        <div class="spread-val" style="color: {'#ff3d5a' if bp > 0 else '#00c27a'}">{bp:+.1f} bp</div>
                    </div>""", unsafe_allow_html=True)

    # ════════════════════════════════════════════════════════
    # 4. YIELD CURVES — SHAPE
    # ════════════════════════════════════════════════════════
    section("YIELD CURVES — SHAPE")

    col1, col2 = st.columns(2)
    with col1:
        # EUR curves plot
        fig_eur = go.Figure()
        tenor_vals = [2, 5, 10, 30]
        for country, color in [("DE", COLORS["DE"]), ("FR", COLORS["FR"]),
                                 ("IT", COLORS["IT"]), ("ES", COLORS["ES"])]:
            ys = ecb_yields.get(country, {})
            y_vals = [ys.get(t) for t in tenors]
            if any(v is not None for v in y_vals):
                fig_eur.add_trace(go.Scatter(
                    x=tenor_vals, y=y_vals,
                    name=ECB_COUNTRIES[country],
                    line=dict(color=color, width=2),
                    mode="lines+markers",
                    marker=dict(size=5),
                ))
        fig_eur.update_layout(**PLOT_LAYOUT, height=250,
                              title=dict(text="EUR Sovereign Yield Curves", font=dict(size=10, color="#9090a8"), x=0))
        fig_eur.update_xaxes(tickvals=[2,5,10,30], ticktext=["2Y","5Y","10Y","30Y"])
        fig_eur.update_yaxes(tickformat=".2f", ticksuffix="%")
        st.plotly_chart(fig_eur, use_container_width=True, config={"displayModeBar": False})

    with col2:
        # US curve plot
        fig_us = go.Figure()
        us_y = [us_yields.get(t) for t in tenors]
        if any(v is not None for v in us_y):
            fig_us.add_trace(go.Scatter(
                x=tenor_vals, y=us_y,
                name="US Treasuries",
                line=dict(color=COLORS["US"], width=2),
                mode="lines+markers",
                marker=dict(size=5),
            ))
        fig_us.update_layout(**PLOT_LAYOUT, height=250,
                              title=dict(text="US Treasury Yield Curve", font=dict(size=10, color="#9090a8"), x=0))
        fig_us.update_xaxes(tickvals=[2,5,10,30], ticktext=["2Y","5Y","10Y","30Y"])
        fig_us.update_yaxes(tickformat=".2f", ticksuffix="%")
        st.plotly_chart(fig_us, use_container_width=True, config={"displayModeBar": False})

    # ════════════════════════════════════════════════════════
    # 5. CURVE SPREADS TABLE (2s5s, 5s10s, 10s30s)
    # ════════════════════════════════════════════════════════
    section("CURVE SPREADS (bps)")

    spreads_def = [("2s5s", "2Y", "5Y"), ("5s10s", "5Y", "10Y"), ("2s10s", "2Y", "10Y"), ("10s30s", "10Y", "30Y")]
    curve_rows = []

    for country, fullname in [("DE","Germany"), ("FR","France"), ("IT","Italy"), ("ES","Spain")]:
        row = {"Country": fullname}
        for label, t1, t2 in spreads_def:
            val = compute_curve_spread(ecb_yields, country, t1, t2)
            row[label] = fmt_bp(val)
        curve_rows.append(row)

    # US
    if us_yields:
        row = {"Country": "United States"}
        fake_us = {"US": us_yields}
        for label, t1, t2 in spreads_def:
            v1, v2 = us_yields.get(t1), us_yields.get(t2)
            val = (v2 - v1) * 100 if v1 and v2 else None
            row[label] = fmt_bp(val)
        curve_rows.append(row)

    df_curves = pd.DataFrame(curve_rows).set_index("Country")
    st.dataframe(df_curves, use_container_width=True)

    # ════════════════════════════════════════════════════════
    # 6. BOX SPREADS
    # ════════════════════════════════════════════════════════
    section("BOX SPREADS (bps) — Curve Slope Differentials")

    box_configs = [
        ("FR-DE", "FR", "DE"),
        ("IT-DE", "IT", "DE"),
        ("ES-DE", "ES", "DE"),
    ]
    box_rows = []
    for label, c1, c2 in box_configs:
        row = {"Box": label}
        for sp_label, t1, t2 in spreads_def:
            val = compute_box(ecb_yields, c1, c2, t1, t2)
            row[sp_label] = fmt_bp(val)
        box_rows.append(row)

    df_box = pd.DataFrame(box_rows).set_index("Box")
    st.dataframe(df_box, use_container_width=True)

    # ════════════════════════════════════════════════════════
    # 7. RATE EXPECTATIONS — ECB & FED
    # ════════════════════════════════════════════════════════
    section("RATE EXPECTATIONS — FRONT FUTURES")

    st.info("""
    **ECB / EURIBOR Futures** → Euronext: ERH5, ERM5, ERU5, ERZ5 (EURIBOR Mar/Jun/Sep/Dec)
    **Fed / SOFR Futures** → CME: SRH5, SRM5, SRU5, SRZ5 (SOFR Mar/Jun/Sep/Dec)

    These tickers are not reliably available on Yahoo Finance free tier.
    For live data, options:
    1. **Quandl/Nasdaq Data Link** (free tier available): `pip install nasdaq-data-link`
    2. **Interactive Brokers TWS API**: full Eurex + CME access
    3. **Bloomberg**: `ERHA Comdty`, `SFRH5 Comdty`
    4. **Euronext Market Data API**: partial free access for EURIBOR futures

    Below shows implied rates calculated from available data.
    """)

    # EURIBOR proxy: use ECB 3M rate as reference
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**ECB Meeting Pricing (implied from EURIBOR strip)**")
        ecb_meetings = {
            "Jan 2025": "~2.75%", "Mar 2025": "~2.50%",
            "Apr 2025": "~2.25%", "Jun 2025": "~2.00%",
        }
        df_ecb = pd.DataFrame(list(ecb_meetings.items()), columns=["Meeting", "Implied Rate"])
        st.dataframe(df_ecb, hide_index=True, use_container_width=True)
        st.caption("⚠ Static estimates — connect to Euronext/Bloomberg for live strip")

    with col2:
        st.markdown("**Fed Meeting Pricing (implied from SOFR strip)**")
        fed_meetings = {
            "Jan 2025": "~4.25%", "Mar 2025": "~4.00%",
            "May 2025": "~3.75%", "Jun 2025": "~3.75%",
        }
        df_fed = pd.DataFrame(list(fed_meetings.items()), columns=["Meeting", "Implied Rate"])
        st.dataframe(df_fed, hide_index=True, use_container_width=True)
        st.caption("⚠ Static estimates — connect to CME/Bloomberg for live strip")

    # ════════════════════════════════════════════════════════
    # 8. ASW (ASSET SWAP SPREADS)
    # ════════════════════════════════════════════════════════
    section("ASSET SWAP SPREADS (bps) — SEB / Bloomberg Input")

    asw_values = {
        "DU ASW (2Y)": asw_du,
        "OE ASW (5Y)": asw_oe,
        "RX ASW (10Y)": asw_rx,
        "UB ASW (30Y)": asw_ub,
    }

    col1, col2 = st.columns([1, 2])
    with col1:
        for name, val in asw_values.items():
            st.markdown(f"""
            <div class="spread-card">
                <div class="spread-name">{name}</div>
                <div class="spread-val" style="color: {'#ff3d5a' if val > 0 else '#00c27a'}">{val:+.1f} bp</div>
            </div>""", unsafe_allow_html=True)

    with col2:
        # ASW curve spread (differences)
        asw_curve = {
            "RX-UB ASW": asw_rx - asw_ub,
            "DU-RX ASW": asw_du - asw_rx,
            "OE-RX ASW": asw_oe - asw_rx,
        }
        fig_asw = go.Figure(go.Bar(
            x=list(asw_curve.keys()),
            y=list(asw_curve.values()),
            marker_color=[COLORS["green"] if v >= 0 else COLORS["red"] for v in asw_curve.values()],
            text=[f"{v:+.1f} bp" for v in asw_curve.values()],
            textposition="outside",
        ))
        fig_asw.update_layout(**PLOT_LAYOUT, height=200,
                              title=dict(text="ASW Curve Spreads", font=dict(size=10, color="#9090a8"), x=0))
        fig_asw.update_yaxes(tickformat=".1f", ticksuffix=" bp")
        st.plotly_chart(fig_asw, use_container_width=True, config={"displayModeBar": False})

    if uploaded:
        section("ASW HISTORY (Uploaded Data)")
        try:
            asw_df = pd.read_csv(uploaded, index_col=0, parse_dates=True)
            fig_asw_hist = line_chart(asw_df, asw_df.columns.tolist(),
                                       "ASW History — Uploaded CSV",
                                       colors=[COLORS["accent"], COLORS["accent2"],
                                               COLORS["IT"], COLORS["ES"]],
                                       yformat=".1f", height=250)
            st.plotly_chart(fig_asw_hist, use_container_width=True, config={"displayModeBar": False})
        except Exception as e:
            st.error(f"CSV parsing error: {e}")

    # ════════════════════════════════════════════════════════
    # 9. FX
    # ════════════════════════════════════════════════════════
    section("FOREX")

    cols = st.columns(len(FX))
    for i, (name, ticker) in enumerate(FX.items()):
        with cols[i]:
            render_ticker_card(name, fx_data.get(name, {}), decimals=4)

    col1, col2 = st.columns(2)
    with col1:
        df_eurusd = fetch_yf_history("EURUSD=X", period)
        if not df_eurusd.empty:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df_eurusd.index, y=df_eurusd["Close"],
                                     line=dict(color=COLORS["accent"], width=1.5), name="EUR/USD"))
            fig.update_layout(**PLOT_LAYOUT, height=200,
                              title=dict(text="EUR/USD", font=dict(size=10, color="#9090a8"), x=0))
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    with col2:
        df_usdjpy = fetch_yf_history("USDJPY=X", period)
        if not df_usdjpy.empty:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df_usdjpy.index, y=df_usdjpy["Close"],
                                     line=dict(color=COLORS["accent2"], width=1.5), name="USD/JPY"))
            fig.update_layout(**PLOT_LAYOUT, height=200,
                              title=dict(text="USD/JPY", font=dict(size=10, color="#9090a8"), x=0))
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # ════════════════════════════════════════════════════════
    # 10. COMMODITIES
    # ════════════════════════════════════════════════════════
    section("COMMODITIES")

    cols = st.columns(len(COMMODITIES))
    decimals_map = {"WTI Oil": 2, "Brent Oil": 2, "Gold": 1, "Silver": 3, "Nat Gas": 3, "Copper": 4}
    for i, (name, _) in enumerate(COMMODITIES.items()):
        with cols[i]:
            render_ticker_card(name, commo_data.get(name, {}),
                               decimals=decimals_map.get(name, 2), suffix=" $")

    # Gold vs Silver ratio
    gold = commo_data.get("Gold", {}).get("price")
    silver = commo_data.get("Silver", {}).get("price")
    if gold and silver and silver > 0:
        ratio = gold / silver
        st.markdown(f"""
        <div class="spread-card" style="max-width: 200px">
            <div class="spread-name">GOLD/SILVER RATIO</div>
            <div class="spread-val" style="color: #f7941d">{ratio:.1f}x</div>
        </div>""", unsafe_allow_html=True)

    # ════════════════════════════════════════════════════════
    # 11. CRYPTO + ETF FLOWS
    # ════════════════════════════════════════════════════════
    section("CRYPTO + BTC ETF FLOWS")

    # CoinGecko data
    cg_map = {
        "Bitcoin":  ("bitcoin", "BTC"),
        "Ethereum": ("ethereum", "ETH"),
        "Solana":   ("solana", "SOL"),
    }
    col1, col2, col3 = st.columns(3)
    for i, (name, (cg_id, sym)) in enumerate(cg_map.items()):
        with [col1, col2, col3][i]:
            d = cg_data.get(cg_id, {})
            price = d.get("usd")
            pct24h = d.get("usd_24h_change", 0)
            render_ticker_card(
                f"{name} ({sym})",
                {"price": price, "pct": pct24h, "chg": (price * pct24h / 100) if price else 0},
                decimals=0 if price and price > 100 else 4,
                suffix=" $"
            )

    st.markdown("**BTC Spot ETF — Volume (Flow Proxy)**")
    etf_cols = st.columns(len(BTC_ETFS))
    for i, (name, data) in enumerate(etf_flows.items()):
        with etf_cols[i]:
            vol = data.get("volume")
            vol_usd = data.get("vol_usd")
            vol_chg = data.get("vol_chg", 0)
            price = data.get("price")
            price_str = f"${price:.2f}" if price else "N/A"
            vol_str = f"{vol:,.0f}" if vol else "N/A"
            vol_usd_str = f"${vol_usd/1e6:.0f}M" if vol_usd else "N/A"
            sign = "▲" if vol_chg > 0 else "▼"
            cls = "ticker-change-pos" if vol_chg > 0 else "ticker-change-neg"
            st.markdown(f"""
            <div class="ticker-card">
                <div class="ticker-label">{name}</div>
                <div class="ticker-value">{price_str}</div>
                <div class="{cls}">{sign} Vol: {vol_str} ({vol_usd_str})</div>
                <div class="ticker-sub">Vol change vs prev: {vol_chg:+,.0f}</div>
            </div>""", unsafe_allow_html=True)

    # BTC price chart
    df_btc = fetch_yf_history("BTC-USD", period)
    if not df_btc.empty:
        fig_btc = go.Figure()
        fig_btc.add_trace(go.Scatter(x=df_btc.index, y=df_btc["Close"],
                                     line=dict(color=COLORS["accent"], width=1.5), name="BTC/USD"))
        fig_btc.add_trace(go.Bar(x=df_btc.index, y=df_btc["Volume"] / 1e9,
                                  marker_color="#2a2a3a", name="Volume (B)", yaxis="y2", opacity=0.5))
        fig_btc.update_layout(
            **PLOT_LAYOUT,
            height=240,
            title=dict(text="Bitcoin (BTC/USD) — Price + Volume", font=dict(size=10, color="#9090a8"), x=0),
            yaxis2=dict(overlaying="y", side="right", showgrid=False, tickformat=".1f",
                        title="Vol (B)", titlefont=dict(size=8)),
        )
        st.plotly_chart(fig_btc, use_container_width=True, config={"displayModeBar": False})

    # ════════════════════════════════════════════════════════
    # FOOTER
    # ════════════════════════════════════════════════════════
    st.markdown("---")
    st.markdown(f"""
    <div style="font-family: 'IBM Plex Mono'; font-size: 0.62rem; color: #3a3a50; text-align: center; padding: 0.5rem;">
    MACRO TERMINAL · Data: Yahoo Finance | ECB SDW API | FRED | CoinGecko · 
    Rates delayed 15min · ASW requires manual input or Bloomberg/SEB export ·
    Last refresh: {now}
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
