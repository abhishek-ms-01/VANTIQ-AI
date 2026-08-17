from config import ASSETS
from datetime import datetime
import yfinance as yf
import pandas as pd
import asyncio

_cache = {}
_cache_ttl = 15 # 15 seconds TTL for candles
_price_cache = {}
_price_cache_ttl = 5 # 5 seconds TTL for live price

async def get_live_price(asset_id: str):
    if asset_id not in ASSETS:
        raise ValueError("invalid symbol")
        
    now = datetime.now().timestamp()
    if asset_id in _price_cache:
        cached = _price_cache[asset_id]
        if now - cached['time'] < _price_cache_ttl:
            return cached['data']

    try:
        yf_sym = 'GC=F' if asset_id == 'GOLD' else ASSETS[asset_id]["provider_symbol"]
        
        df = await asyncio.to_thread(yf.download, yf_sym, period="2d", interval="5m", progress=False)
        if df.empty:
            return "DATA_UNAVAILABLE"
            
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        df.columns = [col.lower() for col in df.columns]
        
        last = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else last
        
        result = {
            "price": float(last['close']),
            "previous_close": float(prev['close']),
            "change": float(last['close'] - prev['close']),
            "change_percent": float(((last['close'] - prev['close']) / prev['close']) * 100),
            "timestamp": int(datetime.utcnow().timestamp()),
            "source": "Yahoo Finance (Futures)",
            "market_status": "OPEN"
        }
        _price_cache[asset_id] = {'time': now, 'data': result}
        return result
    except Exception as e:
        print(f"YF price failed for {asset_id}: {e}")
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

    try:
        yf_sym = 'GC=F' if asset_id == 'GOLD' else ASSETS[asset_id]["provider_symbol"]
        
        intervals = {
            '5M': '5m',
            '15M': '15m',
            '1H': '1h',
            '4H': '1h', # resample below
            '1D': '1d'
        }
        
        if timeframe not in intervals:
            return "DATA_UNAVAILABLE"
            
        period = "60d" if timeframe in ['5M', '15M'] else "730d"
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
        print(f"YF candles failed for {asset_id}: {e}")
        return "DATA_UNAVAILABLE"

def get_market_status(asset_id: str) -> str:
    return "OPEN"

def get_asset_info(asset_id: str):
    return ASSETS.get(asset_id)
