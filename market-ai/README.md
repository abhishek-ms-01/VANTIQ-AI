<div align="center">
  <h1>VANTIQ AI : Autonomous Institutional Market Terminal</h1>
  <p><strong>A production-ready, quantitative trading engine and visual dashboard engineered for Gold (XAU/USD).</strong></p>
</div>

---

## ⚡ Overview

**VANTIQ AI** is a fully automated, institutional-grade market intelligence platform. Designed to operate 24/7 without human intervention, it continuously monitors the Gold (XAU/USD) market, runs complex multi-timeframe quantitative analysis, enforces strict daily risk management protocols, and dispatches high-conviction trade setups directly to your Telegram. 

It is coupled with a sleek, premium React/Vite terminal dashboard that allows you to inspect the AI's real-time reasoning, live market data, and active risk guardrails.

## 🧠 How It Works (The Engine)

At its core, VANTIQ AI operates on a highly robust data-to-execution pipeline:

1. **Live Ingestion:** The FastAPI backend autonomously pulls real-time candlestick and quote data using the **TwelveData API**.
2. **Multi-Timeframe Analysis:** The `GoldStrategy` engine calculates core institutional indicators (EMA21, EMA50, EMA200, RSI, MACD, VWAP, ATR) simultaneously across **15M, 1H, 4H, and 1D** timeframes.
3. **Macro Regime Detection:** It evaluates the 1D chart to determine the overarching market regime (`BULL`, `BEAR`, or `RANGING`). If the market is chopping sideways, the AI holds cash.
4. **Precision Entry (EMA50 + VWAP):** If the regime is trending, the AI hunts for high-probability pullbacks to the 15M EMA50, confirming momentum resumption with RSI and institutional volume weighting (VWAP).
5. **Session Volatility Tiering:** Rather than hard-blocking sessions, the AI applies a **Tiered Volatility Score** (OVERLAP, LONDON, NEW_YORK, ASIAN, OFF_HOURS). It intelligently widens stops and lowers confidence scores during thin, illiquid Asian sessions, while tightening parameters during heavy overlap hours.
6. **Risk Management Guardrails:** Before authorizing a trade, the `DailyState` manager ensures the setup won't violate your strictly defined account rules (e.g., max 3% daily loss, max 4 trades per day, strict 1.8 Risk:Reward ratio).
7. **Telegram Dispatch:** Once a valid setup is green-lit, the system instantly fires a formatted trade execution plan straight to your phone via Telegram.

## 🛠️ Technology Stack

**Frontend (The Terminal):**
- React 19 / Vite
- Tailwind CSS (Premium Dark/Light Glassmorphism UI)
- Recharts (Data Visualization)
- Fully responsive, mobile-first design

**Backend (The Brain):**
- FastAPI (High-performance Python framework)
- Pandas & NumPy (Quantitative data manipulation)
- Uvicorn (ASGI server)
- TwelveData (Market data provider)
- Telegram Bot API (Asynchronous notifications)

## 🚀 Quick Start

### 1. Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
*Configure your `.env` file with your `TWELVE_DATA_API_KEY` and Telegram credentials.*
```bash
uvicorn main:app --reload
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
*Access the terminal at `http://localhost:5173`.*

## 📈 The Dashboard
The frontend acts as your mission control:
- **Live Price Feed:** Ticking market data updated continuously.
- **Technical Panel:** Live readout of all moving averages, oscillators, and volatility metrics.
- **AI Strategy Console:** Real-time visibility into *what* the AI is thinking, including its current regime classification, trade quality score, and rejection reasons.

---
<div align="center">
  <i>Engineered for Alpha. Built with precision.</i>
</div>
