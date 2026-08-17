from config import ASSETS
from datetime import datetime
import asyncio
import httpx
import os

_cache = {}
_cache_ttl = 300
_price_cache = {}
_price_cache_ttl = 30

TWELVE_DATA_API_KEY = os.getenv("TWELVE_DATA_API_KEY", "386a97ae541945ec8d77c8479d0453cc")

async def get_live_price(asset_id: str):
    if asset_id not in ASSETS:
        raise ValueError("invalid symbol")
        
    now = datetime.now().timestamp()
    if asset_id in _price_cache:
        cached = _price_cache[asset_id]
        if now - cached['time'] < _price_cache_ttl:
            return cached['data']

    try:
        # Use XAU/USD for accurate Spot Gold pricing
        symbol = "XAU/USD"
        
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"https://api.twelvedata.com/quote?symbol={symbol}&apikey={TWELVE_DATA_API_KEY}", 
                timeout=10.0
            )
            data = resp.json()
            
            if 'code' in data and data['code'] != 200:
                print(f"TwelveData error: {data}")
                return "DATA_UNAVAILABLE"
                
            last = float(data['close'])
            prev = float(data['previous_close'])
            change = float(data['change'])
            change_pct = float(data['percent_change'])
            
            result = {
                "price": last,
                "previous_close": prev,
                "change": change,
                "change_percent": change_pct,
                "timestamp": int(now),
                "source": "TwelveData (XAU/USD)",
                "market_status": "OPEN" if data.get('is_market_open') else "CLOSED"
            }
            _price_cache[asset_id] = {'time': now, 'data': result}
            return result
    except Exception as e:
        print(f"TwelveData price failed for {asset_id}: {e}")
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
        intervals = {
            '5M': '5min',
            '15M': '15min',
            '1H': '1h',
            '4H': '4h',
            '1D': '1day'
        }
        
        if timeframe not in intervals:
            return "DATA_UNAVAILABLE"
            
        symbol = "XAU/USD"
        
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"https://api.twelvedata.com/time_series?symbol={symbol}&interval={intervals[timeframe]}&outputsize=100&apikey={TWELVE_DATA_API_KEY}", 
                timeout=10.0
            )
            data = resp.json()
            
            if data.get('status') != 'ok':
                print(f"TwelveData candles error: {data}")
                return "DATA_UNAVAILABLE"
                
            raw_candles = data['values']
            raw_candles.reverse() # Oldest to newest
            
            candles = []
            for row in raw_candles:
                candles.append({
                    "timestamp": row['datetime'],
                    "open": float(row['open']),
                    "close": float(row['close']),
                    "high": float(row['high']),
                    "low": float(row['low']),
                    "volume": float(row.get('volume', 0))
                })
                
            _cache[cache_key] = {'time': now, 'data': candles}
            return candles
    except Exception as e:
        print(f"TwelveData candles failed for {asset_id}: {e}")
        return "DATA_UNAVAILABLE"

def get_market_status(asset_id: str) -> str:
    return "OPEN"

def get_asset_info(asset_id: str):
    return ASSETS.get(asset_id)
