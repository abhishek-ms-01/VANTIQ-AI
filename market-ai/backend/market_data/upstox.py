import httpx
from config import settings
import urllib.parse
import time
import asyncio
from datetime import datetime

quote_cache = {}
candle_cache = {}
QUOTE_TTL = 10
CANDLE_TTL = 300

async def get_upstox_live_price(symbol: str):
    if not settings.UPSTOX_ACCESS_TOKEN:
        raise ValueError("Configure market data API")
    
    now = time.time()
    if symbol in quote_cache and now - quote_cache[symbol]['time'] < QUOTE_TTL:
        return quote_cache[symbol]['data']
        
    encoded_symbol = urllib.parse.quote(symbol)
    url = f"https://api.upstox.com/v2/market-quote/quotes?instrument_key={encoded_symbol}"
    
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {settings.UPSTOX_ACCESS_TOKEN}"
    }
    
    for attempt in range(3):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, timeout=10.0)
                if response.status_code == 429:
                    await asyncio.sleep(2 ** attempt)
                    continue
                if response.status_code != 200:
                    raise Exception(f"API unavailable: {response.status_code}")
                
                data = response.json()
                if "data" in data and symbol in data["data"]:
                    instrument_data = data["data"][symbol]
                    
                    price = float(instrument_data.get("last_price", 0))
                    prev_close = float(instrument_data.get("ohlc", {}).get("close", 0))
                    change = float(instrument_data.get("net_change", price - prev_close))
                    change_percent = (change / prev_close * 100) if prev_close != 0 else 0
                    
                    timestamp_val = instrument_data.get("last_trade_time") or instrument_data.get("timestamp")
                    if timestamp_val and isinstance(timestamp_val, str) and timestamp_val.isdigit():
                        ts = int(int(timestamp_val)/1000)
                    elif timestamp_val and isinstance(timestamp_val, (int, float)):
                        ts = int(timestamp_val/1000) if timestamp_val > 9999999999 else int(timestamp_val)
                    else:
                        ts = int(time.time())
                        
                    result = {
                        "price": price,
                        "previous_close": prev_close,
                        "change": change,
                        "change_percent": change_percent,
                        "timestamp": ts,
                        "source": "Upstox",
                        "market_status": "OPEN" # Detailed status needs different API, assuming open for now
                    }
                    quote_cache[symbol] = {'time': now, 'data': result}
                    return result
                else:
                    raise Exception("invalid response")
        except httpx.RequestError:
            if attempt == 2:
                raise Exception("API network error")
            await asyncio.sleep(2 ** attempt)
            
    raise Exception("API unavailable after retries")

async def get_upstox_historical_candles(symbol: str, timeframe: str):
    if not settings.UPSTOX_ACCESS_TOKEN:
        raise ValueError("Configure market data API")
        
    cache_key = f"{symbol}_{timeframe}"
    now = time.time()
    if cache_key in candle_cache and now - candle_cache[cache_key]['time'] < CANDLE_TTL:
        return candle_cache[cache_key]['data']
        
    interval_map = {"5M": "5minute", "15M": "15minute", "1H": "60minute", "4H": "240minute", "1D": "day"}
    interval = interval_map.get(timeframe, "day")
    encoded_symbol = urllib.parse.quote(symbol)
    
    # Calculate date range for historical API
    to_date = datetime.now().strftime("%Y-%m-%d")
    # For simplicity, pulling from a fixed date or dynamic based on timeframe
    from_date = "2024-01-01" 
    
    url = f"https://api.upstox.com/v2/historical-candle/{encoded_symbol}/{interval}/{to_date}/{from_date}" 
    
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {settings.UPSTOX_ACCESS_TOKEN}"
    }
    
    for attempt in range(3):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, timeout=10.0)
                if response.status_code == 429:
                    await asyncio.sleep(2 ** attempt)
                    continue
                if response.status_code != 200:
                    raise Exception(f"API unavailable: {response.status_code}")
                    
                data = response.json()
                if "data" in data and data["data"] and data["data"]["candles"]:
                    candles = []
                    for item in data["data"]["candles"]:
                        # Upstox format: [timestamp, open, high, low, close, volume, oi]
                        candles.append({
                            "timestamp": item[0],
                            "open": float(item[1]),
                            "high": float(item[2]),
                            "low": float(item[3]),
                            "close": float(item[4]),
                            "volume": float(item[5])
                        })
                    result = candles[::-1]  # Return in chronological order
                    candle_cache[cache_key] = {'time': now, 'data': result}
                    return result
                else:
                    raise Exception("invalid response")
        except httpx.RequestError:
            if attempt == 2:
                raise Exception("API network error")
            await asyncio.sleep(2 ** attempt)
            
    raise Exception("API unavailable after retries")
