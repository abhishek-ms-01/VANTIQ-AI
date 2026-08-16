import pandas as pd
import numpy as np
from typing import Dict, Any
from indicators import (
    calculate_ema, calculate_vwap, calculate_rsi, 
    calculate_adx, calculate_atr
)

class SensexStrategy:
    """
    Sensex Strategy
    Timeframes: 15M, 1H, 4H
    Slower trend confirmation than Bank Nifty.
    """
    
    def __init__(self):
        self.timeframes = ['15M', '1H', '4H']
    
    def calculate_indicators(self, data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        for tf in self.timeframes:
            if tf not in data or data[tf].empty:
                continue
            df = data[tf].copy()
            df['ema20'] = calculate_ema(df['close'], 20)
            df['ema50'] = calculate_ema(df['close'], 50)
            df['ema200'] = calculate_ema(df['close'], 200)
            df['vwap'] = calculate_vwap(df)
            df['rsi14'] = calculate_rsi(df['close'], 14)
            df['adx14'] = calculate_adx(df, 14)
            df['atr14'] = calculate_atr(df, 14)
            data[tf] = df
        return data

    def detect_market_regime(self, data: Dict[str, pd.DataFrame]) -> str:
        if '1H' not in data or data['1H'].empty:
            return "UNKNOWN"
        
        df = data['1H']
        last = df.iloc[-1]
        
        if last['ema20'] > last['ema50'] and last['close'] > last['ema200']:
            return "BULLISH_TREND"
        elif last['ema20'] < last['ema50'] and last['close'] < last['ema200']:
            return "BEARISH_TREND"
        else:
            return "RANGING"

    def _is_1h_bullish(self, df: pd.DataFrame) -> bool:
        if df.empty: return False
        last = df.iloc[-1]
        return last['close'] > last['ema50'] and last['ema20'] > last['ema50']

    def _is_1h_bearish(self, df: pd.DataFrame) -> bool:
        if df.empty: return False
        last = df.iloc[-1]
        return last['close'] < last['ema50'] and last['ema20'] < last['ema50']

    def _is_4h_bullish(self, df: pd.DataFrame) -> bool:
        if df.empty: return False
        last = df.iloc[-1]
        return last['close'] > last['ema200']

    def _is_4h_bearish(self, df: pd.DataFrame) -> bool:
        if df.empty: return False
        last = df.iloc[-1]
        return last['close'] < last['ema200']

    def generate_signal(self, data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        data = self.calculate_indicators(data)
        
        if any(tf not in data or data[tf].empty for tf in self.timeframes):
            return self._build_no_trade("Missing timeframe data")
            
        df15 = data['15M']
        df1h = data['1H']
        df4h = data['4H']
        
        last15 = df15.iloc[-1]
        
        # Check Long conditions
        long_cond = {
            'ema200': last15['close'] > last15['ema200'],
            'ema_cross': last15['ema20'] > last15['ema50'],
            'vwap': last15['close'] > last15['vwap'],
            'rsi': 50 <= last15['rsi14'] <= 68,
            'adx': last15['adx14'] > 20,
            '1h': self._is_1h_bullish(df1h),
            '4h': self._is_4h_bullish(df4h)
        }
        
        # Check Short conditions
        short_cond = {
            'ema200': last15['close'] < last15['ema200'],
            'ema_cross': last15['ema20'] < last15['ema50'],
            'vwap': last15['close'] < last15['vwap'],
            'rsi': 32 <= last15['rsi14'] <= 50,
            'adx': last15['adx14'] > 20,
            '1h': self._is_1h_bearish(df1h),
            '4h': self._is_4h_bearish(df4h)
        }
        
        score_weights = {
            'ema200': 20, 'ema_cross': 15, 'vwap': 15, 
            'rsi': 10, 'adx': 10, '1h': 15, '4h': 15
        }
        
        long_score = sum(score_weights[k] for k, v in long_cond.items() if v)
        short_score = sum(score_weights[k] for k, v in short_cond.items() if v)
        
        # Conflict detection
        if (long_cond['ema200'] and short_cond['4h']) or (short_cond['ema200'] and long_cond['4h']):
            return self._build_no_trade("Conflicting timeframes (15m vs 4h)")
            
        direction = "NO_TRADE"
        score = 0
        reasons = []
        
        if long_cond['ema200'] and long_cond['ema_cross'] and long_cond['4h']:
            if long_score >= 65:
                direction = "LONG"
                score = long_score
                reasons = [k for k, v in long_cond.items() if v]
        elif short_cond['ema200'] and short_cond['ema_cross'] and short_cond['4h']:
            if short_score >= 65:
                direction = "SHORT"
                score = short_score
                reasons = [k for k, v in short_cond.items() if v]
                
        if direction == "NO_TRADE":
            return self._build_no_trade("Conditions not met")
            
        signal_data = {
            "direction": direction,
            "signal_strength": score,
            "trade_quality": "HIGH" if score >= 85 else "MEDIUM",
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
        last15 = data['15M'].iloc[-1]
        entry = last15['close']
        atr = last15['atr14']
        
        if direction == "LONG":
            stop_loss = entry - (atr * 2.0)
            target_1 = entry + (atr * 2.0)
            target_2 = entry + (atr * 4.0)
            invalidation = "Price closes below 15M EMA50"
        else:
            stop_loss = entry + (atr * 2.0)
            target_1 = entry - (atr * 2.0)
            target_2 = entry - (atr * 4.0)
            invalidation = "Price closes above 15M EMA50"
            
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
            
        explanation = f"Sensex {result['direction']} Signal. Score: {result['signal_strength']}. "
        explanation += f"Regime: {result['market_regime']}. "
        explanation += f"Entry: {result['entry']:.2f}, SL: {result['stop_loss']:.2f}. "
        explanation += f"Reasons: {', '.join(result['reasons'])}. "
        if result['warnings']:
            explanation += f"Missing factors: {', '.join(result['warnings'])}."
            
        return explanation
