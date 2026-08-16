import pandas as pd
import numpy as np
from typing import Dict, Any
from indicators import (
    calculate_ema, calculate_rsi, calculate_macd, 
    calculate_adx, calculate_atr
)

class GoldStrategy:
    """
    Gold Strategy (XAUUSD)
    Timeframes: 15M, 1H, 4H, 1D
    Strategy: TREND + PULLBACK + CONFIRMATION
    """
    
    def __init__(self):
        self.timeframes = ['15M', '1H', '4H', '1D']
    
    def calculate_indicators(self, data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        for tf in self.timeframes:
            if tf not in data or data[tf].empty:
                continue
            df = data[tf].copy()
            df['ema21'] = calculate_ema(df['close'], 21)
            df['ema50'] = calculate_ema(df['close'], 50)
            df['ema200'] = calculate_ema(df['close'], 200)
            df['rsi14'] = calculate_rsi(df['close'], 14)
            macd_line, signal_line, hist = calculate_macd(df['close'])
            df['macd'] = macd_line
            df['macd_signal'] = signal_line
            df['macd_hist'] = hist
            df['adx14'] = calculate_adx(df, 14)
            df['atr14'] = calculate_atr(df, 14)
            # Volatility filter (detect extended candles)
            df['candle_size'] = abs(df['close'] - df['open'])
            data[tf] = df
        return data

    def detect_market_regime(self, data: Dict[str, pd.DataFrame]) -> str:
        if '1D' not in data or data['1D'].empty:
            return "UNKNOWN"
        last = data['1D'].iloc[-1]
        if last['close'] > last['ema200'] and last['ema50'] > last['ema200']:
            return "SECULAR_BULL"
        elif last['close'] < last['ema200'] and last['ema50'] < last['ema200']:
            return "SECULAR_BEAR"
        return "RANGING"

    def _is_pullback_toward(self, current_price: float, ma_value: float, atr: float) -> bool:
        # Pullback is within 1 ATR of the moving average
        return abs(current_price - ma_value) <= (1.0 * atr)

    def generate_signal(self, data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        data = self.calculate_indicators(data)
        
        if any(tf not in data or data[tf].empty for tf in self.timeframes):
            return self._build_no_trade("Missing timeframe data")
            
        df15 = data['15M']
        df1h = data['1H']
        df4h = data['4H']
        
        last15 = df15.iloc[-1]
        prev15 = df15.iloc[-2] if len(df15) > 1 else last15
        last1h = df1h.iloc[-1]
        last4h = df4h.iloc[-1]
        
        # Avoid extended candles
        if last15['candle_size'] > last15['atr14'] * 2.5:
            return self._build_no_trade("Recent candle too extended (Volatility filter)")
            
        # Avoid weak trends
        if last1h['adx14'] < 20:
            return self._build_no_trade("Weak trend: 1H ADX < 20")
        
        # Check Long conditions
        long_cond = {
            '4h_trend': last4h['ema50'] > last4h['ema200'],
            '1h_trend': last1h['ema21'] > last1h['ema50'],
            '1h_adx': last1h['adx14'] > 25,
            '15m_pullback': self._is_pullback_toward(last15['low'], last15['ema21'], last15['atr14']),
            '15m_rsi': prev15['rsi14'] < 50 and last15['rsi14'] > 50, # RSI recovery above 50
            '15m_macd': last15['macd'] > 0 # MACD positive
        }
        
        # Check Short conditions
        short_cond = {
            '4h_trend': last4h['ema50'] < last4h['ema200'],
            '1h_trend': last1h['ema21'] < last1h['ema50'],
            '1h_adx': last1h['adx14'] > 25,
            '15m_pullback': self._is_pullback_toward(last15['high'], last15['ema21'], last15['atr14']),
            '15m_rsi': prev15['rsi14'] > 50 and last15['rsi14'] < 50, # RSI dropping below 50
            '15m_macd': last15['macd'] < 0 # MACD negative
        }
        
        score_weights = {
            '4h_trend': 20, '1h_trend': 20, '1h_adx': 15,
            '15m_pullback': 20, '15m_rsi': 15, '15m_macd': 10
        }
        
        long_score = sum(score_weights[k] for k, v in long_cond.items() if v)
        short_score = sum(score_weights[k] for k, v in short_cond.items() if v)
        
        if (long_cond['4h_trend'] and short_cond['1h_trend']) or (short_cond['4h_trend'] and long_cond['1h_trend']):
            return self._build_no_trade("Conflicting timeframes (1H vs 4H)")
            
        direction = "NO_TRADE"
        score = 0
        reasons = []
        
        if long_cond['4h_trend'] and long_cond['1h_trend'] and long_cond['15m_pullback']:
            if long_score >= 60:
                direction = "LONG"
                score = long_score
                reasons = [k for k, v in long_cond.items() if v]
        elif short_cond['4h_trend'] and short_cond['1h_trend'] and short_cond['15m_pullback']:
            if short_score >= 60:
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
            stop_loss = entry - (atr * 1.5)
            target_1 = entry + (atr * 2.0)
            target_2 = entry + (atr * 4.0)
            invalidation = "15M close below EMA50"
        else:
            stop_loss = entry + (atr * 1.5)
            target_1 = entry - (atr * 2.0)
            target_2 = entry - (atr * 4.0)
            invalidation = "15M close above EMA50"
            
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
            
        explanation = f"Gold {result['direction']} Setup. Strength: {result['signal_strength']}. "
        explanation += f"Regime: {result['market_regime']}. "
        explanation += f"Entry: {result['entry']:.2f}, SL: {result['stop_loss']:.2f}. "
        explanation += f"Reasons: {', '.join(result['reasons'])}. "
        if result['warnings']:
            explanation += f"Warnings: {', '.join(result['warnings'])}."
            
        return explanation
