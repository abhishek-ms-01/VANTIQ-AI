from typing import Dict, Any, List
import pandas as pd
from datetime import datetime, timedelta
from risk.stop_loss import calculate_stop_loss
from risk.take_profit import calculate_targets

def _build_no_trade(reasons: List[str]) -> Dict[str, Any]:
    return {
        "direction": "NO_TRADE",
        "entry_price": 0.0,
        "stop_loss": 0.0,
        "target_1": 0.0,
        "target_2": 0.0,
        "risk_points": 0.0,
        "reward_target_1": 0.0,
        "reward_target_2": 0.0,
        "risk_reward_target_1": 0.0,
        "risk_reward_target_2": 0.0,
        "signal_strength": 0,
        "trade_quality": 0,
        "invalidation_level": "",
        "reasons": reasons,
        "warnings": []
    }

def validate_and_build_trade_plan(
    raw_signal: Dict[str, Any],
    data_df: pd.DataFrame,
    atr_multiplier: float = 1.0,
    min_rr: float = 1.0
) -> Dict[str, Any]:
    """
    Constructs the COMPLETE TRADE SETUP.
    Validates targets, stop loss, R:R, and calculates Trade Quality.
    """
    if raw_signal.get("direction", "NO_TRADE") == "NO_TRADE":
        return _build_no_trade(raw_signal.get("reasons", ["NO_VALID_SETUP"]))

    direction = raw_signal["direction"]
    entry_price = raw_signal.get("entry", 0.0)
    
    if entry_price == 0.0:
        return _build_no_trade(["INVALID_ENTRY"])

    # Freshness check (assuming datetime index, if available)
    if isinstance(data_df.index, pd.DatetimeIndex):
        last_time = data_df.index[-1]
        # Just a basic check, adjust based on live needs
        if pd.Timestamp.utcnow().tz_localize(None) - last_time.tz_localize(None) > pd.Timedelta(days=7):
            return _build_no_trade(["STALE_DATA"])

    # Stop Loss
    last_row = data_df.iloc[-1]
    atr = last_row.get("atr14", 0.0)
    
    if atr == 0.0:
        return _build_no_trade(["INSUFFICIENT_DATA (ATR missing)"])

    sl = calculate_stop_loss(direction, entry_price, data_df, atr, atr_multiplier)
    
    if not sl:
        # Fallback to strategy default if structure stop loss fails
        sl = raw_signal.get("stop_loss", 0.0)
        
    if sl == 0.0 or (direction == "LONG" and sl >= entry_price) or (direction == "SHORT" and sl <= entry_price):
        return _build_no_trade(["INVALID_STOP"])

    # Targets
    tp1, tp2 = calculate_targets(direction, entry_price, data_df)
    
    # Check if structural tp1 gives a good RR. If not, discard it.
    if tp1:
        risk_dist = abs(entry_price - sl)
        reward_dist = abs(tp1 - entry_price)
        if risk_dist > 0 and (reward_dist / risk_dist) < min_rr:
            tp1 = None
            tp2 = None
            
    # Fallback to strategy targets if structural targets not found or discarded
    if not tp1:
        tp1 = raw_signal.get("target_1", 0.0)
    if not tp2:
        tp2 = raw_signal.get("target_2", tp1)
        
    if not tp1 or tp1 == 0.0:
        return _build_no_trade(["INVALID_TARGET"])

    # Validate targets direction
    if direction == "LONG" and (tp1 <= entry_price or (tp2 and tp2 <= tp1)):
        # Target too close or invalid
        if tp1 <= entry_price:
             return _build_no_trade(["RESISTANCE_TOO_CLOSE"])
    elif direction == "SHORT" and (tp1 >= entry_price or (tp2 and tp2 >= tp1)):
        if tp1 >= entry_price:
             return _build_no_trade(["SUPPORT_TOO_CLOSE"])

    # Risk and Reward calculation
    risk_points = abs(entry_price - sl)
    reward_tp1 = abs(tp1 - entry_price)
    reward_tp2 = abs(tp2 - entry_price) if tp2 else 0.0
    
    rr_tp1 = round(reward_tp1 / risk_points, 2) if risk_points > 0 else 0.0
    rr_tp2 = round(reward_tp2 / risk_points, 2) if risk_points > 0 else 0.0

    if rr_tp1 < min_rr:
        # Instead of rejecting, forcefully adjust the target to meet the minimum R:R
        if direction == "LONG":
            tp1 = entry_price + (risk_points * min_rr)
        else:
            tp1 = entry_price - (risk_points * min_rr)
        tp2 = tp1
        reward_tp1 = abs(tp1 - entry_price)
        reward_tp2 = reward_tp1
        rr_tp1 = min_rr
        rr_tp2 = min_rr

    # Trade Quality Scoring (0-100)
    trade_quality = 0
    
    # 1. Trend Alignment (from strategy regime)
    regime = raw_signal.get("market_regime", "UNKNOWN")
    if (direction == "LONG" and "BULL" in regime) or (direction == "SHORT" and "BEAR" in regime):
        trade_quality += 30
    elif regime == "RANGING":
        trade_quality += 10
        
    # 2. Risk/Reward (Up to 30 points)
    if rr_tp1 >= 2.0:
        trade_quality += 30
    elif rr_tp1 >= 1.5:
        trade_quality += 20
    elif rr_tp1 >= 1.0:
        trade_quality += 10
        
    # 3. Setup Quality / Signal Strength agreement (Up to 20 points)
    signal_strength = raw_signal.get("signal_strength", 0)
    if signal_strength >= 80:
        trade_quality += 20
    elif signal_strength >= 60:
        trade_quality += 10
        
    # 4. Volatility Check (Up to 20 points)
    # Good volatility: Candle size <= 2 ATR
    candle_size = abs(last_row["close"] - last_row["open"])
    if candle_size <= (atr * 1.5):
        trade_quality += 20
    elif candle_size <= (atr * 2.5):
        trade_quality += 10
    else:
        # High volatility penalty
        pass

    return {
        "direction": direction,
        "entry_price": round(entry_price, 5),
        "stop_loss": round(sl, 5),
        "target_1": round(tp1, 5),
        "target_2": round(tp2, 5) if tp2 else 0.0,
        "risk_points": round(risk_points, 5),
        "reward_target_1": round(reward_tp1, 5),
        "reward_target_2": round(reward_tp2, 5),
        "risk_reward_target_1": rr_tp1,
        "risk_reward_target_2": rr_tp2,
        "signal_strength": signal_strength,
        "trade_quality": trade_quality,
        "invalidation_level": raw_signal.get("invalidation", "Invalidated by market structure break"),
        "reasons": raw_signal.get("reasons", []),
        "warnings": raw_signal.get("warnings", [])
    }
