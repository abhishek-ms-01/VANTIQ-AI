from config import ASSETS
from market_data.twelve_data import get_twelve_data_live_price, get_twelve_data_historical_candles
from market_data.upstox import get_upstox_live_price, get_upstox_historical_candles
from datetime import datetime
import yfinance as yf
import pandas as pd
import asyncio

# Cache to prevent rate limits
_cache = {}
_cache_ttl = 60 # 60 seconds TTL for candles
_price_cache = {}
_price_cache_ttl = 5 # 5 seconds TTL for live price

async def get_live_price(asset_id: str):
    if asset_id not in ASSETS:
        raise ValueError("invalid symbol")
        
    asset = ASSETS[asset_id]
    symbol = asset["provider_symbol"]
    
    # Check price cache
    now = datetime.now().timestamp()
    if asset_id in _price_cache:
        cached = _price_cache[asset_id]
        if now - cached['time'] < _price_cache_ttl:
            return cached['data']

    # Use yfinance for real data fallback
    try:
        # yfinance symbol mapping
        yf_sym = {
            'BANKNIFTY': '^NSEBANK',
            'SENSEX': '^BSESN',
            'GOLD': 'GC=F',
            'EURUSD': 'EURUSD=X',
            'BTC': 'BTC-USD',
            'ETH': 'ETH-USD'
        }.get(asset_id, symbol)
        
        ticker = yf.Ticker(yf_sym)
        data = ticker.history(period="2d")
        if not data.empty:
            last = data.iloc[-1]
            prev = data.iloc[-2] if len(data) > 1 else last
            
            result = {
                "price": float(last['Close']),
                "previous_close": float(prev['Close']),
                "change": float(last['Close'] - prev['Close']),
                "change_percent": float((last['Close'] - prev['Close']) / prev['Close'] * 100),
                "timestamp": datetime.utcnow().isoformat(),
                "source": "Yahoo Finance",
                "market_status": get_market_status(asset_id)
            }
            _price_cache[asset_id] = {'time': now, 'data': result}
            return result
    except Exception as e:
        pass
        
    return "DATA_UNAVAILABLE"

async def get_historical_candles(asset_id: str, timeframe: str):
    if asset_id not in ASSETS:
        raise ValueError("invalid symbol")
        
    cache_key = f"{asset_id}_{timeframe}"
    now = datetime.now().timestamp()
    
    if cache_key in _cache:
        cached = _cache[cache_key]
        if now - cached['time'] < _cache_ttl:
            return cached['data']

    # Use yfinance
    yf_sym = {
        'BANKNIFTY': '^NSEBANK',
        'SENSEX': '^BSESN',
        'GOLD': 'GC=F',
        'EURUSD': 'EURUSD=X',
        'BTC': 'BTC-USD',
        'ETH': 'ETH-USD'
    }.get(asset_id, ASSETS[asset_id]["provider_symbol"])
    
    intervals = {
        '5M': '5m',
        '15M': '15m',
        '1H': '1h',
        '4H': '1h', # yfinance doesn't do 4h, we resample
        '1D': '1d'
    }
    
    if timeframe not in intervals:
        return "DATA_UNAVAILABLE"
        
    period = "60d" if timeframe in ['5M', '15M'] else "730d"
    
    try:
        df = await asyncio.to_thread(yf.download, yf_sym, interval=intervals[timeframe], period=period, progress=False)
        
        if df.empty:
            return "DATA_UNAVAILABLE"
            
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        df.columns = [col.lower() for col in df.columns]
        if 'volume' not in df.columns:
            df['volume'] = 0
            
        if timeframe == '4H':
            df = df.resample('4h').agg({
                'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'
            }).dropna()
            
        # Keep last 500 candles to save bandwidth
        df = df.tail(500)
        
        candles = []
        for idx, row in df.iterrows():
            candles.append({
                "timestamp": idx.isoformat(),
                "open": float(row['open']),
                "high": float(row['high']),
                "low": float(row['low']),
                "close": float(row['close']),
                "volume": float(row['volume'])
            })
            
        _cache[cache_key] = {'time': now, 'data': candles}
        return candles
        
    except Exception as e:
        print(f"Error fetching candles: {e}")
        return "DATA_UNAVAILABLE"

def get_market_status(asset_id: str):
    if asset_id not in ASSETS:
        raise ValueError("invalid symbol")
    
    asset = ASSETS[asset_id]
    if asset["category"] == "CRYPTO":
        return "OPEN"
        
    now = datetime.utcnow()
    if now.weekday() >= 5: # Weekend
        return "CLOSED"
        
    return "OPEN"

def get_asset_info(asset_id: str):
    if asset_id not in ASSETS:
        raise ValueError("invalid symbol")
    return ASSETS[asset_id]
