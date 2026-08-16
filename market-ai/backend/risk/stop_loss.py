import pandas as pd
from typing import Dict, Any, Optional
from indicators import calculate_swing_low, calculate_swing_high

def calculate_stop_loss(
    direction: str,
    entry_price: float,
    data_df: pd.DataFrame,
    atr: float,
    atr_multiplier: float = 1.0,
    swing_window: int = 5
) -> Optional[float]:
    """
    Calculates Stop Loss using market structure and ATR buffer.
    LONG: Stop below valid structural swing low + ATR buffer.
    SHORT: Stop above valid structural swing high + ATR buffer.
    """
    if data_df.empty:
        return None

    # Calculate recent swings if not already present
    if 'swing_low' not in data_df.columns:
        swing_lows = calculate_swing_low(data_df, window=swing_window)
    else:
        swing_lows = data_df['swing_low']
        
    if 'swing_high' not in data_df.columns:
        swing_highs = calculate_swing_high(data_df, window=swing_window)
    else:
        swing_highs = data_df['swing_high']
        
    if direction == "LONG":
        # Find the most recent valid swing low below the entry price
        recent_lows = swing_lows.dropna()
        valid_lows = recent_lows[recent_lows < entry_price]
        if not valid_lows.empty:
            structure_low = valid_lows.iloc[-1]
        else:
            # Fallback to rolling minimum if no valid swing low found
            structure_low = data_df['low'].rolling(window=20).min().iloc[-1]
            
        return structure_low - (atr * atr_multiplier)
        
    elif direction == "SHORT":
        # Find the most recent valid swing high above the entry price
        recent_highs = swing_highs.dropna()
        valid_highs = recent_highs[recent_highs > entry_price]
        if not valid_highs.empty:
            structure_high = valid_highs.iloc[-1]
        else:
            # Fallback to rolling maximum if no valid swing high found
            structure_high = data_df['high'].rolling(window=20).max().iloc[-1]
            
        return structure_high + (atr * atr_multiplier)
        
    return None
