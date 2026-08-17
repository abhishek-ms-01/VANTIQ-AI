import datetime as dt
from dataclasses import dataclass, field
from typing import Optional, Literal, Dict, Any
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
    london: tuple[int, int] = (8, 17)
    new_york: tuple[int, int] = (13, 22)
    tokyo: tuple[int, int] = (0, 9)
    sydney: tuple[int, int] = (22, 7)
    
    # Gold is best traded during London and NY sessions for sufficient volume/volatility
    tradeable_sessions: tuple[str, ...] = ("london", "new_york")

    def is_tradeable(self, hour_gmt: int) -> bool:
        is_london = self.london[0] <= hour_gmt < self.london[1]
        is_ny = self.new_york[0] <= hour_gmt < self.new_york[1]
        
        return is_london or is_ny

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
        if self.locked_out: return False
        if self.trades_taken >= risk_cfg.max_trades_per_day: return False
        if self.realized_pnl <= -risk_cfg.max_daily_loss_usd: return False
        return True

class GoldStrategy:
    """
    Gold Strategy (XAUUSD)
    Timeframes: 15M, 1H, 4H, 1D
    Strategy: PULLBACK TO EMA50 + VWAP CONFIRMATION + STRICT RISK CONTROL
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
            df['ema21'] = calculate_ema(df['close'], 21) # Kept for UI backwards compatibility
            df['ema50'] = calculate_ema(df['close'], 50)
            df['ema200'] = calculate_ema(df['close'], 200)
            df['rsi14'] = calculate_rsi(df['close'], 14)
            df['atr14'] = calculate_atr(df, 14)
            
            # Keep MACD/ADX so frontend TechnicalPanel doesn't break
            macd_line, signal_line, hist = calculate_macd(df['close'])
            df['macd'] = macd_line
            df['macd_signal'] = signal_line
            df['adx14'] = calculate_adx(df, 14)

            # Volatility filter (detect extended candles)
            df['candle_size'] = abs(df['close'] - df['open'])
            
            # VWAP
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

    def _is_pullback_toward(self, current_price: float, ma_value: float, atr: float) -> bool:
        # User defined pullback zone as 0.6 * ATR
        return abs(current_price - ma_value) <= (0.6 * atr)

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

        regime = self.detect_market_regime(data)
        
        if regime == "RANGING" or regime == "UNKNOWN":
            return self._build_no_trade("Regime is Ranging/Unknown (No Edge)")

        if not self.session_cfg.is_tradeable(hour_gmt):
            return self._build_no_trade(f"Outside session hours (Hour {hour_gmt} GMT)")

        current_atr = last15["atr14"]
        if pd.isna(current_atr) or current_atr <= 0:
            return self._build_no_trade("Invalid ATR")

        daily_state = self._get_daily_state(ts)
        if not daily_state.can_trade(self.risk_cfg):
            return self._build_no_trade("Daily risk limit reached or max trades taken")

        pullback_zone = self._is_pullback_toward(last15["close"], last15["ema50"], current_atr)

        direction = "NO_TRADE"
        reasons = []
        warnings = []
        score = 0
        
        if regime == "BULL" and pullback_zone:
            momentum_resumed = prev15["rsi14"] < 50 <= last15["rsi14"]
            above_vwap = last15["close"] >= last15["vwap"]
            if momentum_resumed and above_vwap:
                direction = "LONG"
                score = 85
                reasons = ["Bull regime pullback to EMA50", "RSI reclaimed 50", "Above VWAP"]
            else:
                if not momentum_resumed: warnings.append("RSI hasn't reclaimed 50")
                if not above_vwap: warnings.append("Price below VWAP")

        elif regime == "BEAR" and pullback_zone:
            momentum_resumed = prev15["rsi14"] > 50 >= last15["rsi14"]
            below_vwap = last15["close"] <= last15["vwap"]
            if momentum_resumed and below_vwap:
                direction = "SHORT"
                score = 85
                reasons = ["Bear regime pullback to EMA50", "RSI lost 50", "Below VWAP"]
            else:
                if not momentum_resumed: warnings.append("RSI hasn't lost 50")
                if not below_vwap: warnings.append("Price above VWAP")

        if direction == "NO_TRADE":
            if not pullback_zone:
                warnings.append("Not in EMA50 pullback zone")
            return self._build_no_trade("Setup criteria not met", warnings=warnings, regime=regime)

        # Build trade setup
        stop_distance = max(current_atr * 1.0, 1e-6)
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
            "trade_quality": "HIGH",
            "market_regime": regime,
            "reasons": reasons,
            "warnings": warnings,
            "timeframes": self.timeframes,
            "entry": entry,
            "stop_loss": stop_loss,
            "target_1": target_1,
            "target_2": target_1, # Unused target 2 in this rigid 1.8 R:R model
            "risk_reward": self.risk_cfg.reward_risk_ratio,
            "invalidation": f"15M Close past {stop_loss}",
            "lots": lots
        }
        
        signal_data['explanation'] = self.explain_signal(signal_data)
        return signal_data

    def _build_no_trade(self, reason: str, warnings: list = None, regime: str = "UNKNOWN") -> Dict[str, Any]:
        return {
            "direction": "NO_TRADE",
            "signal_strength": 0,
            "trade_quality": "NONE",
            "market_regime": regime,
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
            
        explanation = f"Gold {result['direction']} Setup (1.8 R:R). "
        explanation += f"Regime: {result['market_regime']}. "
        explanation += f"Entry: {result['entry']:.2f}, SL: {result['stop_loss']:.2f}. "
        explanation += f"Rec. Lots: {result.get('lots', 0.01)}. "
        explanation += f"Reasons: {', '.join(result['reasons'])}."
            
        return explanation
