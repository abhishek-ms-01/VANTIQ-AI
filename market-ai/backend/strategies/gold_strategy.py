import datetime as dt
from dataclasses import dataclass, field
from typing import Optional, Literal, Dict, Any, Tuple
import pandas as pd
import numpy as np

# Existing indicator functions from indicators.py
from indicators import (
    calculate_ema, calculate_rsi, calculate_macd,
    calculate_adx, calculate_atr, calculate_vwap
)


@dataclass
class RiskConfig:
    account_size: float = 1000.0
    max_daily_loss_pct: float = 0.03
    max_risk_per_trade_pct: float = 0.008
    max_trades_per_day: int = 4
    reward_risk_ratio: float = 1.8
    pip_value_per_lot: float = 10.0
    min_lot: float = 0.01
    max_lot: float = 0.10

    @property
    def max_daily_loss_usd(self) -> float:
        return round(self.account_size * self.max_daily_loss_pct, 2)

    @property
    def max_risk_per_trade_usd(self) -> float:
        return round(self.account_size * self.max_risk_per_trade_pct, 2)


@dataclass
class SessionConfig:
    """
    All sessions are tradeable now -- nothing is hard-blocked. Instead each
    GMT hour maps to a volatility TIER, which adjusts (a) the signal
    confidence score and (b) the pullback/stop tolerance, since thin
    sessions have wider effective spreads and choppier moves for the same
    ATR reading.

    Tiers (GMT):
      OVERLAP     13:00-16:00  -> highest liquidity, tightest spreads
      LONDON      08:00-13:00  -> high liquidity
      NEW_YORK    16:00-21:00  -> moderate, can be choppy into the close
      ASIAN       00:00-08:00  -> low liquidity, wider spreads, slower moves
      OFF_HOURS   21:00-24:00  -> lowest liquidity of the day
    """
    overlap: Tuple[int, int] = (13, 16)
    london: Tuple[int, int] = (8, 13)
    new_york: Tuple[int, int] = (16, 21)
    asian: Tuple[int, int] = (0, 8)
    off_hours: Tuple[int, int] = (21, 24)

    # confidence multiplier + ATR multiplier applied per tier
    tier_settings: Dict[str, Dict[str, float]] = field(default_factory=lambda: {
        "OVERLAP":   {"confidence_mult": 1.00, "atr_mult": 1.0, "score_bonus": 10},
        "LONDON":    {"confidence_mult": 0.95, "atr_mult": 1.0, "score_bonus": 5},
        "NEW_YORK":  {"confidence_mult": 0.90, "atr_mult": 1.1, "score_bonus": 0},
        "ASIAN":     {"confidence_mult": 0.75, "atr_mult": 1.3, "score_bonus": -15},
        "OFF_HOURS": {"confidence_mult": 0.70, "atr_mult": 1.4, "score_bonus": -20},
    })

    def get_tier(self, hour_gmt: int) -> str:
        if self.overlap[0] <= hour_gmt < self.overlap[1]:
            return "OVERLAP"
        if self.london[0] <= hour_gmt < self.london[1]:
            return "LONDON"
        if self.new_york[0] <= hour_gmt < self.new_york[1]:
            return "NEW_YORK"
        if self.asian[0] <= hour_gmt < self.asian[1]:
            return "ASIAN"
        return "OFF_HOURS"

    def get_tier_settings(self, hour_gmt: int) -> Dict[str, float]:
        return self.tier_settings[self.get_tier(hour_gmt)]

    # Kept for backwards compatibility with any code that still calls this --
    # now always True since every session is tradeable. Quality is handled
    # via tiers, not a yes/no gate.
    def is_tradeable(self, hour_gmt: int) -> bool:
        return True


@dataclass
class DailyState:
    date: dt.date
    realized_pnl: float = 0.0
    trades_taken: int = 0
    locked_out: bool = False

    def register_trade_result(self, pnl: float, risk_cfg: RiskConfig) -> None:
        self.realized_pnl += pnl
        self.trades_taken += 1
        if self.realized_pnl <= -risk_cfg.max_daily_loss_usd:
            self.locked_out = True

    def can_trade(self, risk_cfg: RiskConfig) -> bool:
        # NOTE: this is a real money-management guardrail, not a
        # "prediction filter" -- it stays regardless of session settings.
        if self.locked_out:
            return False
        if self.trades_taken >= risk_cfg.max_trades_per_day:
            return False
        if self.realized_pnl <= -risk_cfg.max_daily_loss_usd:
            return False
        return True


class GoldStrategy:
    """
    Gold Strategy (XAUUSD)
    Timeframes: 15M, 1H, 4H, 1D
    Strategy: PULLBACK TO EMA50 + VWAP CONFIRMATION + SESSION-TIERED SCORING

    All 24 hours can produce a signal. Session quality is expressed through
    `session_tier` and an adjusted `signal_strength`, not through blocking
    trades outright. Asian/off-hours setups will typically score lower and
    carry a wider stop (since the same ATR reading represents choppier,
    lower-conviction movement in thin liquidity) -- that's reflected in the
    numbers so you can decide per-signal whether to act on it, rather than
    the strategy silently deciding for you.
    """

    def __init__(self):
        self.timeframes = ['15M', '1H', '4H', '1D']
        self.risk_cfg = RiskConfig()
        self.session_cfg = SessionConfig()
        self._daily_state = None

    def _get_daily_state(self, timestamp: pd.Timestamp) -> DailyState:
        current_date = timestamp.date()
        if self._daily_state is None or self._daily_state.date != current_date:
            self._daily_state = DailyState(date=current_date)
        return self._daily_state

    def calculate_indicators(self, data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        for tf in self.timeframes:
            if tf not in data or data[tf].empty:
                continue
            df = data[tf].copy()
            df['ema21'] = calculate_ema(df['close'], 21)  # Kept for UI backwards compatibility
            df['ema50'] = calculate_ema(df['close'], 50)
            df['ema200'] = calculate_ema(df['close'], 200)
            df['rsi14'] = calculate_rsi(df['close'], 14)
            df['atr14'] = calculate_atr(df, 14)

            macd_line, signal_line, hist = calculate_macd(df['close'])
            df['macd'] = macd_line
            df['macd_signal'] = signal_line
            df['adx14'] = calculate_adx(df, 14)

            df['candle_size'] = abs(df['close'] - df['open'])

            if isinstance(df.index, pd.DatetimeIndex):
                df['vwap'] = calculate_vwap(df)
            else:
                df['vwap'] = df['close']

            data[tf] = df
        return data

    def detect_market_regime(self, data: Dict[str, pd.DataFrame]) -> str:
        if '1D' not in data or data['1D'].empty:
            return "UNKNOWN"
        last = data['1D'].iloc[-1]
        if last['close'] > last['ema200'] and last['ema50'] > last['ema200']:
            return "BULL"
        if last['close'] < last['ema200'] and last['ema50'] < last['ema200']:
            return "BEAR"
        return "RANGING"

    def _is_pullback_toward(self, current_price: float, ma_value: float, atr: float, atr_mult: float) -> bool:
        return abs(current_price - ma_value) <= (0.6 * atr * atr_mult)

    def generate_signal(self, data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        data = self.calculate_indicators(data)

        if any(tf not in data or data[tf].empty for tf in self.timeframes):
            return self._build_no_trade("Missing timeframe data")

        df15 = data['15M']
        if len(df15) < 2:
            return self._build_no_trade("Not enough 15M data")

        last15 = df15.iloc[-1]
        prev15 = df15.iloc[-2]

        ts = df15.index[-1]
        hour_gmt = ts.tz_convert("UTC").hour if ts.tzinfo else ts.hour

        session_tier = self.session_cfg.get_tier(hour_gmt)
        tier_settings = self.session_cfg.get_tier_settings(hour_gmt)

        regime = self.detect_market_regime(data)

        if regime == "RANGING" or regime == "UNKNOWN":
            return self._build_no_trade(
                "Regime is Ranging/Unknown. Waiting for clear trend to establish.",
                session_tier=session_tier,
            )

        current_atr = last15["atr14"]
        if pd.isna(current_atr) or current_atr <= 0:
            return self._build_no_trade("Invalid ATR", session_tier=session_tier)

        daily_state = self._get_daily_state(ts)
        if not daily_state.can_trade(self.risk_cfg):
            return self._build_no_trade(
                "Daily risk limit reached or max trades taken",
                session_tier=session_tier,
            )

        pullback_zone = self._is_pullback_toward(
            last15["close"], last15["ema50"], current_atr, tier_settings["atr_mult"]
        )

        direction = "NO_TRADE"
        reasons = []
        warnings = []
        base_score = 0

        if regime == "BULL" and pullback_zone:
            momentum_resumed = prev15["rsi14"] < 50 <= last15["rsi14"]
            above_vwap = last15["close"] >= last15["vwap"]
            if momentum_resumed and above_vwap:
                direction = "LONG"
                base_score = 85
                reasons = ["Bull regime pullback to EMA50", "RSI reclaimed 50", "Above VWAP"]
            else:
                if not momentum_resumed:
                    warnings.append("RSI hasn't reclaimed 50")
                if not above_vwap:
                    warnings.append("Price below VWAP")

        elif regime == "BEAR" and pullback_zone:
            momentum_resumed = prev15["rsi14"] > 50 >= last15["rsi14"]
            below_vwap = last15["close"] <= last15["vwap"]
            if momentum_resumed and below_vwap:
                direction = "SHORT"
                base_score = 85
                reasons = ["Bear regime pullback to EMA50", "RSI lost 50", "Below VWAP"]
            else:
                if not momentum_resumed:
                    warnings.append("RSI hasn't lost 50")
                if not below_vwap:
                    warnings.append("Price above VWAP")

        if direction == "NO_TRADE":
            if not pullback_zone:
                warnings.append("Not in EMA50 pullback zone")
            return self._build_no_trade(
                "Setup criteria not met. Waiting for next valid EMA50 pullback.",
                warnings=warnings, regime=regime, session_tier=session_tier,
            )

        # Session-adjusted score and confidence
        score = max(0, min(100, round(base_score * tier_settings["confidence_mult"] + tier_settings["score_bonus"])))
        if session_tier in ("ASIAN", "OFF_HOURS"):
            warnings.append(f"{session_tier} session: lower liquidity, wider effective spread -- size down / confirm before entry")

        trade_quality = "HIGH" if score >= 75 else "MEDIUM" if score >= 55 else "LOW"

        # Build trade setup -- stop distance widened for thinner sessions via atr_mult
        stop_distance = max(current_atr * tier_settings["atr_mult"], 1e-6)
        target_distance = stop_distance * self.risk_cfg.reward_risk_ratio
        entry = last15["close"]

        stop_loss = round(entry - stop_distance if direction == "LONG" else entry + stop_distance, 2)
        target_1 = round(entry + target_distance if direction == "LONG" else entry - target_distance, 2)

        stop_pips = abs(entry - stop_loss) * 10
        lots = 0
        if stop_pips > 0:
            remaining_daily_budget = self.risk_cfg.max_daily_loss_usd + daily_state.realized_pnl
            risk_budget = min(self.risk_cfg.max_risk_per_trade_usd, max(remaining_daily_budget, 0))
            if risk_budget > 0:
                raw_lots = risk_budget / (stop_pips * self.risk_cfg.pip_value_per_lot)
                lots = max(self.risk_cfg.min_lot, min(self.risk_cfg.max_lot, round(raw_lots, 2)))

        signal_data = {
            "direction": direction,
            "signal_strength": score,
            "trade_quality": trade_quality,
            "market_regime": regime,
            "session_tier": session_tier,
            "session_hour_gmt": hour_gmt,
            "reasons": reasons,
            "warnings": warnings,
            "timeframes": self.timeframes,
            "entry": entry,
            "stop_loss": stop_loss,
            "target_1": target_1,
            "target_2": target_1,
            "risk_reward": self.risk_cfg.reward_risk_ratio,
            "invalidation": f"15M Close past {stop_loss}",
            "lots": lots,
        }

        signal_data['explanation'] = self.explain_signal(signal_data)
        return signal_data

    def _build_no_trade(self, reason: str, warnings: list = None, regime: str = "UNKNOWN",
                         session_tier: str = "UNKNOWN") -> Dict[str, Any]:
        return {
            "direction": "NO_TRADE",
            "signal_strength": 0,
            "trade_quality": "NONE",
            "market_regime": regime,
            "session_tier": session_tier,
            "reasons": [reason],
            "warnings": warnings or [],
            "timeframes": self.timeframes,
            "entry": 0, "stop_loss": 0, "target_1": 0, "target_2": 0,
            "risk_reward": 0, "invalidation": "", "explanation": reason,
            "lots": 0
        }

    def explain_signal(self, result: dict) -> str:
        if result['direction'] == "NO_TRADE":
            return f"No Trade: {', '.join(result.get('reasons', []))}"

        explanation = f"Gold {result['direction']} Setup ({result['session_tier']} session, {result['risk_reward']} R:R). "
        explanation += f"Regime: {result['market_regime']}. Quality: {result['trade_quality']} ({result['signal_strength']}/100). "
        explanation += f"Entry: {result['entry']:.2f}, SL: {result['stop_loss']:.2f}, TP: {result['target_1']:.2f}. "
        explanation += f"Rec. Lots: {result.get('lots', 0.01)}. "
        explanation += f"Reasons: {', '.join(result['reasons'])}."
        if result.get('warnings'):
            explanation += f" Notes: {', '.join(result['warnings'])}."

        return explanation 
