import pandas as pd
import numpy as np

def calculate_sma(series: pd.Series, period: int) -> pd.Series:
    """Simple Moving Average"""
    return series.rolling(window=period).mean()

def calculate_ema(series: pd.Series, period: int) -> pd.Series:
    """Exponential Moving Average"""
    return series.ewm(span=period, adjust=False).mean()

def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Relative Strength Index"""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    # Use exponential moving average for smoother RSI as is standard, but simple mean is also common.
    # Standard RSI uses Wilder's smoothing. Let's use Wilder's Smoothing:
    gain = delta.where(delta > 0, 0).ewm(alpha=1/period, adjust=False).mean()
    loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/period, adjust=False).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    """Moving Average Convergence Divergence"""
    ema_fast = calculate_ema(series, fast)
    ema_slow = calculate_ema(series, slow)
    macd_line = ema_fast - ema_slow
    signal_line = calculate_ema(macd_line, signal)
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram

def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Average True Range"""
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = np.max(ranges, axis=1)
    # Wilder's smoothing for ATR
    atr = true_range.ewm(alpha=1/period, adjust=False).mean()
    return atr

def calculate_adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Average Directional Index"""
    high = df['high']
    low = df['low']
    close = df['close']
    
    plus_dm = high.diff()
    minus_dm = low.diff()
    
    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm > 0] = 0
    minus_dm = minus_dm.abs()
    
    # +DM and -DM only if they are the larger movement
    mask = plus_dm < minus_dm
    plus_dm[mask] = 0
    minus_dm[~mask] = 0
    
    tr = np.max(pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low - close.shift()).abs()
    ], axis=1), axis=1)
    
    atr = tr.ewm(alpha=1/period, adjust=False).mean()
    
    plus_di = 100 * (plus_dm.ewm(alpha=1/period, adjust=False).mean() / atr)
    minus_di = 100 * (minus_dm.ewm(alpha=1/period, adjust=False).mean() / atr)
    
    dx = (np.abs(plus_di - minus_di) / (plus_di + minus_di)) * 100
    adx = dx.ewm(alpha=1/period, adjust=False).mean()
    
    return adx

def calculate_vwap(df: pd.DataFrame) -> pd.Series:
    """Volume Weighted Average Price"""
    q = df['volume']
    p = (df['high'] + df['low'] + df['close']) / 3
    
    # Forex pairs often have 0 volume reported from APIs. Fallback to typical price.
    if q.sum() == 0:
        return p
    
    if isinstance(df.index, pd.DatetimeIndex):
        vwap = (p * q).groupby(df.index.date).cumsum() / q.groupby(df.index.date).cumsum()
    else:
        # Fallback to cumulative if no datetime index
        vwap = (p * q).cumsum() / q.cumsum()
        
    # Replace any remaining NaNs (e.g. start of day with 0 volume) with typical price
    vwap = vwap.fillna(p)
    return vwap

def calculate_volume_average(series: pd.Series, period: int = 20) -> pd.Series:
    """Volume Moving Average"""
    return series.rolling(window=period).mean()

def calculate_swing_high(df: pd.DataFrame, window: int = 5) -> pd.Series:
    """Swing High: Highest high in the window around a point.
    Using shift to prevent look-ahead bias: a swing high is formed if the highest point was window days ago.
    """
    # Look back `window` periods
    rolling_max = df['high'].rolling(window=window*2+1, center=False).max()
    # The swing high is confirmed if the high window periods ago is the rolling max
    is_swing_high = df['high'].shift(window) == rolling_max
    return df['high'].shift(window).where(is_swing_high)

def calculate_swing_low(df: pd.DataFrame, window: int = 5) -> pd.Series:
    """Swing Low: Lowest low in the window"""
    rolling_min = df['low'].rolling(window=window*2+1, center=False).min()
    is_swing_low = df['low'].shift(window) == rolling_min
    return df['low'].shift(window).where(is_swing_low)

def calculate_support(df: pd.DataFrame, window: int = 20) -> pd.Series:
    """Support level estimation using recent swing lows or rolling min."""
    return df['low'].rolling(window=window).min()

def calculate_resistance(df: pd.DataFrame, window: int = 20) -> pd.Series:
    """Resistance level estimation using recent swing highs or rolling max."""
    return df['high'].rolling(window=window).max()
