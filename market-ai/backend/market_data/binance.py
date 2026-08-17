import httpx
from datetime import datetime
import time

CANDLE_TTL = 15 # 15 seconds cache for fast updates
candle_cache = {}

async def get_binance_live_price(symbol: str):
    # Map GOLD to PAXGUSDT
    binance_symbol = "PAXGUSDT" if symbol in ["GOLD", "XAU/USD", "XAUUSD"] else symbol
    url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={binance_symbol}"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=5.0)
        data = response.json()
        
        current_price = float(data["lastPrice"])
        prev_close = float(data["prevClosePrice"])
        change = float(data["priceChange"])
        change_pct = float(data["priceChangePercent"])
        
        return {
            "price": current_price,
            "previous_close": prev_close,
            "change": change,
            "change_percent": change_pct,
            "timestamp": int(datetime.utcnow().timestamp()),
            "source": "Binance Live",
            "market_status": "OPEN 24/7"
        }

async def get_binance_historical_candles(symbol: str, timeframe: str):
    binance_symbol = "PAXGUSDT" if symbol in ["GOLD", "XAU/USD", "XAUUSD"] else symbol
    
    cache_key = f"{binance_symbol}_{timeframe}"
    now = time.time()
    if cache_key in candle_cache and now - candle_cache[cache_key]['time'] < CANDLE_TTL:
        return candle_cache[cache_key]['data']
        
    interval_map = {"5M": "5m", "15M": "15m", "1H": "1h", "4H": "4h", "1D": "1d"}
    interval = interval_map.get(timeframe, "1d")
    
    url = f"https://api.binance.com/api/v3/klines?symbol={binance_symbol}&interval={interval}&limit=150"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=5.0)
        data = response.json()
        
        candles = []
        for item in data:
            candles.append({
                "timestamp": datetime.fromtimestamp(item[0]/1000).strftime('%Y-%m-%d %H:%M:%S'),
                "open": float(item[1]),
                "high": float(item[2]),
                "low": float(item[3]),
                "close": float(item[4]),
                "volume": float(item[5])
            })
            
        result = candles # Binance already returns oldest to newest
        candle_cache[cache_key] = {'time': now, 'data': result}
        return result
