from config import ASSETS
from datetime import datetime
import asyncio
import httpx

_cache = {}
_cache_ttl = 15
_price_cache = {}
_price_cache_ttl = 5

KUCOIN_SYMBOL = "PAXG-USDT"

async def get_live_price(asset_id: str):
    if asset_id not in ASSETS:
        raise ValueError("invalid symbol")
        
    now = datetime.now().timestamp()
    if asset_id in _price_cache:
        cached = _price_cache[asset_id]
        if now - cached['time'] < _price_cache_ttl:
            return cached['data']

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"https://api.kucoin.com/api/v1/market/stats?symbol={KUCOIN_SYMBOL}", timeout=10.0)
            data = resp.json()
            
            if data['code'] != '200000':
                return "DATA_UNAVAILABLE"
                
            stats = data['data']
            last = float(stats['last'])
            change = float(stats['changePrice'])
            change_pct = float(stats['changeRate']) * 100
            
            result = {
                "price": last,
                "previous_close": last - change,
                "change": change,
                "change_percent": change_pct,
                "timestamp": int(now),
                "source": "KuCoin (PAXG)",
                "market_status": "OPEN"
            }
            _price_cache[asset_id] = {'time': now, 'data': result}
            return result
    except Exception as e:
        print(f"KuCoin price failed for {asset_id}: {e}")
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
            '1H': '1hour',
            '4H': '4hour',
            '1D': '1day'
        }
        
        if timeframe not in intervals:
            return "DATA_UNAVAILABLE"
            
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"https://api.kucoin.com/api/v1/market/candles?type={intervals[timeframe]}&symbol={KUCOIN_SYMBOL}", timeout=10.0)
            data = resp.json()
            
            if data['code'] != '200000' or not data['data']:
                return "DATA_UNAVAILABLE"
                
            raw_candles = data['data']
            raw_candles.reverse() # KuCoin returns newest first, we want oldest first
            
            candles = []
            for row in raw_candles:
                candles.append({
                    "timestamp": datetime.fromtimestamp(int(row[0])).isoformat(),
                    "open": float(row[1]),
                    "close": float(row[2]),
                    "high": float(row[3]),
                    "low": float(row[4]),
                    "volume": float(row[5])
                })
                
            _cache[cache_key] = {'time': now, 'data': candles}
            return candles
    except Exception as e:
        print(f"KuCoin candles failed for {asset_id}: {e}")
        return "DATA_UNAVAILABLE"

def get_market_status(asset_id: str) -> str:
    return "OPEN"

def get_asset_info(asset_id: str):
    return ASSETS.get(asset_id)
