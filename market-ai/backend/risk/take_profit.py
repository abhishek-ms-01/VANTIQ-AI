import pandas as pd
from typing import Tuple, Optional
from indicators import calculate_swing_high, calculate_swing_low

def calculate_targets(
    direction: str,
    entry_price: float,
    data_df: pd.DataFrame,
    swing_window: int = 20
) -> Tuple[Optional[float], Optional[float]]:
    """
    Calculates TP1 and TP2 based on market structure.
    Target 1: Nearest meaningful resistance/support.
    Target 2: Next major structure level.
    """
    if data_df.empty:
        return None, None
        
    if direction == "LONG":
        # Find swing highs above entry
        if 'swing_high' not in data_df.columns:
            swing_highs = calculate_swing_high(data_df, window=swing_window)
        else:
            swing_highs = data_df['swing_high']
            
        recent_highs = swing_highs.dropna()
        valid_highs = recent_highs[recent_highs > entry_price].sort_values(ascending=True).unique()
        
        if len(valid_highs) >= 2:
            return valid_highs[0], valid_highs[1]
        elif len(valid_highs) == 1:
            return valid_highs[0], None
        else:
            return None, None
            
    elif direction == "SHORT":
        # Find swing lows below entry
        if 'swing_low' not in data_df.columns:
            swing_lows = calculate_swing_low(data_df, window=swing_window)
        else:
            swing_lows = data_df['swing_low']
            
        recent_lows = swing_lows.dropna()
        valid_lows = recent_lows[recent_lows < entry_price].sort_values(ascending=False).unique()
        
        if len(valid_lows) >= 2:
            return valid_lows[0], valid_lows[1]
        elif len(valid_lows) == 1:
            return valid_lows[0], None
        else:
            return None, None
            
    return None, None
