import pandas as pd
import numpy as np
from typing import Dict, Any
from indicators import (
    calculate_ema, calculate_vwap, calculate_rsi, 
    calculate_adx, calculate_atr, calculate_volume_average
)

class BankNiftyStrategy:
    """
    Bank Nifty Strategy
    Timeframes: 5M entry, 15M confirmation, 1H direction
    """
    
    def __init__(self):
        self.timeframes = ['5M', '15M', '1H']
    
    def calculate_indicators(self, data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        for tf in self.timeframes:
            if tf not in data or data[tf].empty:
                continue
            df = data[tf].copy()
            df['ema9'] = calculate_ema(df['close'], 9)
            df['ema21'] = calculate_ema(df['close'], 21)
            df['ema50'] = calculate_ema(df['close'], 50)
            df['vwap'] = calculate_vwap(df)
            df['rsi14'] = calculate_rsi(df['close'], 14)
            df['adx14'] = calculate_adx(df, 14)
            df['atr14'] = calculate_atr(df, 14)
            df['vol_ma'] = calculate_volume_average(df['volume'], 20)
            data[tf] = df
        return data

    def detect_market_regime(self, data: Dict[str, pd.DataFrame]) -> str:
        if '1H' not in data or data['1H'].empty:
            return "UNKNOWN"
        
        df = data['1H']
        last_row = df.iloc[-1]
        
        if last_row['ema9'] > last_row['ema21'] and last_row['ema21'] > last_row['ema50']:
            return "BULLISH_TREND"
        elif last_row['ema9'] < last_row['ema21'] and last_row['ema21'] < last_row['ema50']:
            return "BEARISH_TREND"
        else:
            return "RANGING"

    def _is_15m_bullish(self, df: pd.DataFrame) -> bool:
        if df.empty: return False
        last = df.iloc[-1]
        return last['close'] > last['ema21'] and last['ema9'] > last['ema21']

    def _is_15m_bearish(self, df: pd.DataFrame) -> bool:
        if df.empty: return False
        last = df.iloc[-1]
        return last['close'] < last['ema21'] and last['ema9'] < last['ema21']

    def _is_1h_bullish(self, df: pd.DataFrame) -> bool:
        if df.empty: return False
        last = df.iloc[-1]
        return last['close'] > last['ema50']

    def _is_1h_bearish(self, df: pd.DataFrame) -> bool:
        if df.empty: return False
        last = df.iloc[-1]
        return last['close'] < last['ema50']

    def generate_signal(self, data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        data = self.calculate_indicators(data)
        
        if any(tf not in data or data[tf].empty for tf in self.timeframes):
            return {"direction": "NO_TRADE", "reason": "Missing timeframe data"}
            
        df5 = data['5M']
        df15 = data['15M']
        df1h = data['1H']
        
        last5 = df5.iloc[-1]
        
        # Check Long conditions
        long_cond = {
            'vwap': last5['close'] > last5['vwap'],
            'ema': last5['ema9'] > last5['ema21'] and last5['ema21'] > last5['ema50'],
            'rsi': last5['rsi14'] > 52,
            'adx': last5['adx14'] > 20,
            '15m': self._is_15m_bullish(df15),
            '1h': self._is_1h_bullish(df1h),
            'vol': last5['volume'] > last5['vol_ma']
        }
        
        # Check Short conditions
        short_cond = {
            'vwap': last5['close'] < last5['vwap'],
            'ema': last5['ema9'] < last5['ema21'] and last5['ema21'] < last5['ema50'],
            'rsi': last5['rsi14'] < 48,
            'adx': last5['adx14'] > 20,
            '15m': self._is_15m_bearish(df15),
            '1h': self._is_1h_bearish(df1h),
            'vol': last5['volume'] > last5['vol_ma']
        }
        
        score_weights = {
            'vwap': 20, 'ema': 20, 'rsi': 15, 'adx': 15, 
            '15m': 10, '1h': 10, 'vol': 10
        }
        
        long_score = sum(score_weights[k] for k, v in long_cond.items() if v)
        short_score = sum(score_weights[k] for k, v in short_cond.items() if v)
        
        # Conflict detection on critical conditions
        if (long_cond['ema'] and short_cond['1h']) or (short_cond['ema'] and long_cond['1h']):
            return self._build_no_trade("Conflicting timeframes")
            
        direction = "NO_TRADE"
        score = 0
        reasons = []
        
        if long_cond['ema'] and long_cond['vwap']:
            if long_score >= 60:
                direction = "LONG"
                score = long_score
                reasons = [k for k, v in long_cond.items() if v]
        elif short_cond['ema'] and short_cond['vwap']:
            if short_score >= 60:
                direction = "SHORT"
                score = short_score
                reasons = [k for k, v in short_cond.items() if v]
                
        if direction == "NO_TRADE":
            return self._build_no_trade("Conditions not met")
            
        signal_data = {
            "direction": direction,
            "signal_strength": score,
            "trade_quality": "HIGH" if score >= 80 else "MEDIUM",
            "market_regime": self.detect_market_regime(data),
            "reasons": reasons,
            "warnings": [k for k, v in (long_cond if direction == "LONG" else short_cond).items() if not v],
            "timeframes": self.timeframes
        }
        
        setup = self.generate_trade_setup(data, direction)
        signal_data.update(setup)
        signal_data['explanation'] = self.explain_signal(signal_data)
        
        return signal_data

    def _build_no_trade(self, reason: str) -> Dict[str, Any]:
        return {
            "direction": "NO_TRADE",
            "signal_strength": 0,
            "trade_quality": "NONE",
            "market_regime": "UNKNOWN",
            "reasons": [reason],
            "warnings": [],
            "timeframes": self.timeframes,
            "entry": 0, "stop_loss": 0, "target_1": 0, "target_2": 0,
            "risk_reward": 0, "invalidation": "", "explanation": reason
        }

    def calculate_score(self, signal_data: dict) -> int:
        return signal_data.get('signal_strength', 0)

    def generate_trade_setup(self, data: Dict[str, pd.DataFrame], direction: str) -> Dict[str, Any]:
        last5 = data['5M'].iloc[-1]
        entry = last5['close']
        atr = last5['atr14']
        
        if direction == "LONG":
            stop_loss = entry - (atr * 1.5)
            target_1 = entry + (atr * 1.5)
            target_2 = entry + (atr * 3.0)
            invalidation = "Price closes below 5M EMA50"
        else:
            stop_loss = entry + (atr * 1.5)
            target_1 = entry - (atr * 1.5)
            target_2 = entry - (atr * 3.0)
            invalidation = "Price closes above 5M EMA50"
            
        risk = abs(entry - stop_loss)
        reward = abs(target_2 - entry)
        rr = reward / risk if risk > 0 else 0
        
        return {
            "entry": entry,
            "stop_loss": stop_loss,
            "target_1": target_1,
            "target_2": target_2,
            "risk_reward": round(rr, 2),
            "invalidation": invalidation
        }

    def explain_signal(self, result: dict) -> str:
        if result['direction'] == "NO_TRADE":
            return f"No Trade: {', '.join(result.get('reasons', []))}"
            
        explanation = f"{result['direction']} Signal detected. Strength: {result['signal_strength']}/100. "
        explanation += f"Regime: {result['market_regime']}. "
        explanation += f"Entry at {result['entry']:.2f}, SL: {result['stop_loss']:.2f}. "
        explanation += f"Key reasons: {', '.join(result['reasons'])}. "
        if result['warnings']:
            explanation += f"Warnings (conditions not met): {', '.join(result['warnings'])}."
            
        return explanation
