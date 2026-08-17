from config import ASSETS
from market_data.binance import get_binance_live_price, get_binance_historical_candles
from datetime import datetime

_cache = {}
_cache_ttl = 15 # 15 seconds TTL for candles
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

    try:
        data = await get_binance_live_price(symbol)
        _price_cache[asset_id] = {'time': now, 'data': data}
        return data
    except Exception as e:
        print(f"Binance price failed for {asset_id}: {e}")
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
        data = await get_binance_historical_candles(ASSETS[asset_id]["provider_symbol"], timeframe)
        _cache[cache_key] = {'time': now, 'data': data}
        return data
    except Exception as e:
        print(f"Binance candles failed for {asset_id}: {e}")
        return "DATA_UNAVAILABLE"

def get_market_status(asset_id: str) -> str:
    return "OPEN 24/7"

def get_asset_info(asset_id: str):
    return ASSETS.get(asset_id)
