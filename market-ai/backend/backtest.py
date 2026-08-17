"""
backtest.py
===========

Bar-by-bar backtester for gold_strategy.py. Feed it real historical
OHLCV data (from TwelveData, your broker, or any source) -- this script
does not fetch data itself, because backtest data quality/source is
something you should choose and verify deliberately.

Usage:
    from backtest import run_backtest
    results = run_backtest(intraday_df, daily_df, GoldStrategy())
    print(results["summary"])

Expected DataFrame format for both intraday_df and daily_df:
    - Index: pandas DatetimeIndex (UTC, tz-aware recommended)
    - Columns: open, high, low, close, volume
"""

from __future__ import annotations

import pandas as pd
from strategies.gold_strategy import GoldStrategy


def _simulate_exit(
    intraday_df: pd.DataFrame,
    entry_idx: int,
    direction: str,
    stop: float,
    target: float,
    max_bars_forward: int = 96,  # e.g. 96 x 15m bars = 24h cap on a trade
) -> tuple[float, pd.Timestamp, str]:
    """
    Walks forward from entry_idx and checks each subsequent bar's high/low
    to see whether stop or target was hit first. If both could plausibly
    hit within the same bar, this assumes the WORSE outcome (stop) hits
    first -- a conservative assumption, since intrabar order is unknown.
    """
    end_idx = min(entry_idx + max_bars_forward, len(intraday_df) - 1)
    for i in range(entry_idx + 1, end_idx + 1):
        bar = intraday_df.iloc[i]
        if direction == "LONG":
            hit_stop = bar["low"] <= stop
            hit_target = bar["high"] >= target
        else:
            hit_stop = bar["high"] >= stop
            hit_target = bar["low"] <= target

        if hit_stop and hit_target:
            return stop, intraday_df.index[i], "stop_and_target_same_bar_assumed_stop"
        if hit_stop:
            return stop, intraday_df.index[i], "stop"
        if hit_target:
            return target, intraday_df.index[i], "target"

    # Timed out -- close at last available price
    last_bar = intraday_df.iloc[end_idx]
    return last_bar["close"], intraday_df.index[end_idx], "timeout"


def run_backtest(
    intraday_df: pd.DataFrame,
    daily_df: pd.DataFrame,
    strategy: GoldStrategy,
    lookback_bars: int = 210,
) -> dict:
    trades = []
    equity = strategy.risk_cfg.account_size

    # We need to construct the resampled 1H and 4H DataFrames up front for performance
    # Since gold_strategy requires all 4 timeframes to determine the regime.
    print("Resampling 1H and 4H data for strategy...")
    resampled_1h = intraday_df.resample('1h', label='right', closed='right').agg(
        {'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'}
    ).dropna()
    
    resampled_4h = intraday_df.resample('4h', label='right', closed='right').agg(
        {'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'}
    ).dropna()

    for i in range(lookback_bars, len(intraday_df)):
        window = intraday_df.iloc[: i + 1]
        current_ts = window.index[-1]
        
        daily_window = daily_df[daily_df.index <= current_ts]
        window_1h = resampled_1h[resampled_1h.index <= current_ts]
        window_4h = resampled_4h[resampled_4h.index <= current_ts]
        
        if len(daily_window) < 200 or len(window_1h) < 50 or len(window_4h) < 50:
            continue
            
        data_dict = {
            '15M': window,
            '1H': window_1h,
            '4H': window_4h,
            '1D': daily_window
        }

        result = strategy.generate_signal(data_dict)
        if result is None or result.get("direction", "NO_TRADE") == "NO_TRADE":
            continue

        exit_price, exit_ts, exit_reason = _simulate_exit(
            intraday_df, i, result["direction"], result["stop_loss"], result["target_1"]
        )

        pip_move = abs(exit_price - result["entry"]) * 10
        won = (
            (result["direction"] == "LONG" and exit_price > result["entry"])
            or (result["direction"] == "SHORT" and exit_price < result["entry"])
        )
        pnl_usd = pip_move * strategy.risk_cfg.pip_value_per_lot * result["lots"]
        pnl_usd = pnl_usd if won else -pnl_usd
        
        # Register the result with the strategy's daily state
        daily_state = strategy._get_daily_state(current_ts)
        daily_state.register_trade_result(pnl_usd, strategy.risk_cfg)
        
        equity += pnl_usd

        trades.append(
            {
                "entry_time": current_ts,
                "exit_time": exit_ts,
                "direction": result["direction"],
                "entry": result["entry"],
                "stop": result["stop_loss"],
                "target": result["target_1"],
                "exit_price": exit_price,
                "exit_reason": exit_reason,
                "lots": result["lots"],
                "pnl_usd": round(pnl_usd, 2),
                "won": won,
                "equity_after": round(equity, 2),
            }
        )

    trades_df = pd.DataFrame(trades)
    if trades_df.empty:
        return {"trades": trades_df, "summary": "No trades were generated -- check data range/filters."}

    win_rate = trades_df["won"].mean()
    total_pnl = trades_df["pnl_usd"].sum()
    avg_win = trades_df.loc[trades_df["won"], "pnl_usd"].mean() if trades_df["won"].any() else 0
    avg_loss = trades_df.loc[~trades_df["won"], "pnl_usd"].mean() if (~trades_df["won"]).any() else 0
    max_drawdown = (trades_df["equity_after"].cummax() - trades_df["equity_after"]).max()

    summary = (
        f"Trades: {len(trades_df)}\n"
        f"Win rate: {win_rate:.1%}\n"
        f"Total PnL: ${total_pnl:.2f}\n"
        f"Avg win: ${avg_win:.2f} | Avg loss: ${avg_loss:.2f}\n"
        f"Max drawdown: ${max_drawdown:.2f}\n"
        f"Ending equity: ${trades_df['equity_after'].iloc[-1]:.2f}"
    )

    return {"trades": trades_df, "summary": summary, "win_rate": win_rate, "total_pnl": total_pnl}


if __name__ == "__main__":
    print(__doc__)
    print("Import run_backtest() and pass in real historical OHLCV DataFrames to use this.")
