import httpx
from config import settings
from datetime import datetime
import time
import asyncio

quote_cache = {}
candle_cache = {}
QUOTE_TTL = 10
CANDLE_TTL = 300

async def get_twelve_data_live_price(symbol: str):
    if not settings.TWELVE_DATA_API_KEY:
        raise ValueError("Configure market data API")
    
    now = time.time()
    if symbol in quote_cache and now - quote_cache[symbol]['time'] < QUOTE_TTL:
        return quote_cache[symbol]['data']
        
    url = f"https://api.twelvedata.com/quote?symbol={symbol}&exchange=OANDA&apikey={settings.TWELVE_DATA_API_KEY}"
    
    for attempt in range(3):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=10.0)
                if response.status_code == 429:
                    await asyncio.sleep(2 ** attempt)
                    continue
                if response.status_code != 200:
                    raise Exception(f"API unavailable: {response.status_code}")
                
                data = response.json()
                
                if "code" in data and data["code"] == 429:
                    await asyncio.sleep(2 ** attempt)
                    continue
                    
                if "symbol" in data:
                    try:
                        price_val = float(data.get("close", 0)) or float(data.get("previous_close", 0))
                    except:
                        price_val = 0.0
                        
                    result = {
                        "price": price_val,
                        "previous_close": float(data.get("previous_close", 0) or 0),
                        "change": float(data.get("change", 0) or 0),
                        "change_percent": float(data.get("percent_change", 0) or 0),
                        "timestamp": data.get("timestamp") or int(datetime.utcnow().timestamp()),
                        "source": "Twelve Data",
                        "market_status": "OPEN" if data.get("is_market_open", False) else "CLOSED"
                    }
                    quote_cache[symbol] = {'time': now, 'data': result}
                    return result
                else:
                    raise Exception(f"invalid response: {data}")
        except httpx.RequestError:
            if attempt == 2:
                raise Exception("API network error")
            await asyncio.sleep(2 ** attempt)

    raise Exception("API unavailable after retries")

async def get_twelve_data_historical_candles(symbol: str, timeframe: str):
    if not settings.TWELVE_DATA_API_KEY:
        raise ValueError("Configure market data API")
        
    cache_key = f"{symbol}_{timeframe}"
    now = time.time()
    if cache_key in candle_cache and now - candle_cache[cache_key]['time'] < CANDLE_TTL:
        return candle_cache[cache_key]['data']
        
    interval_map = {"5M": "5min", "15M": "15min", "1H": "1h", "4H": "4h", "1D": "1day"}
    interval = interval_map.get(timeframe, "1day")
    url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval={interval}&exchange=OANDA&apikey={settings.TWELVE_DATA_API_KEY}&outputsize=100"
    
    for attempt in range(3):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=10.0)
                if response.status_code == 429:
                    await asyncio.sleep(2 ** attempt)
                    continue
                if response.status_code != 200:
                    raise Exception("API unavailable")
                    
                data = response.json()
                
                if "code" in data and data["code"] == 429:
                    await asyncio.sleep(2 ** attempt)
                    continue
                    
                if "values" in data:
                    candles = []
                    for item in data["values"]:
                        candles.append({
                            "timestamp": item["datetime"],
                            "open": float(item["open"]),
                            "high": float(item["high"]),
                            "low": float(item["low"]),
                            "close": float(item["close"]),
                            "volume": float(item.get("volume", 0))
                        })
                    result = candles[::-1]
                    candle_cache[cache_key] = {'time': now, 'data': result}
                    return result
                else:
                    raise Exception("invalid response")
        except httpx.RequestError:
            if attempt == 2:
                raise Exception("API network error")
            await asyncio.sleep(2 ** attempt)
            
    raise Exception("API unavailable after retries")
