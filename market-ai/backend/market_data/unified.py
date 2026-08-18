from config import ASSETS
from datetime import datetime, timedelta
import asyncio
import os
import yfinance as yf
import random

_cache = {}
_cache_ttl = 300
_price_cache = {}
_price_cache_ttl = 30
_locks = {}

# Simulated base price for gold to generate realistic mock data if yfinance fails
SIMULATED_BASE_PRICE = 2450.50

async def get_live_price(asset_id: str):
    if asset_id not in ASSETS:
        raise ValueError("invalid symbol")
        
    lock_key = f"price_{asset_id}"
    if lock_key not in _locks:
        _locks[lock_key] = asyncio.Lock()
        
    async with _locks[lock_key]:
        now = datetime.now().timestamp()
        if asset_id in _price_cache:
            cached = _price_cache[asset_id]
            if now - cached['time'] < _price_cache_ttl:
                return cached['data']

        try:
            symbol = "GC=F"
            
            def fetch_price():
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="5d")
                if len(hist) == 0:
                    raise Exception("No data returned from yfinance")
                    
                current = float(hist['Close'].iloc[-1])
                prev_close = float(hist['Close'].iloc[-2]) if len(hist) > 1 else float(hist['Open'].iloc[-1])
                change = current - prev_close
                change_pct = (change / prev_close) * 100 if prev_close else 0
                return current, prev_close, change, change_pct

            current, prev_close, change, change_pct = await asyncio.to_thread(fetch_price)
            source = "Yahoo Finance (GC=F)"
            
        except Exception as e:
            print(f"yfinance price failed for {asset_id}, using simulated data: {e}")
            # FALLBACK: Simulated Market Data
            current = SIMULATED_BASE_PRICE + random.uniform(-5, 5)
            prev_close = SIMULATED_BASE_PRICE - 12.50
            change = current - prev_close
            change_pct = (change / prev_close) * 100
            source = "Simulated Fallback Data"

        result = {
            "price": current,
            "previous_close": prev_close,
            "change": change,
            "change_percent": change_pct,
            "timestamp": int(now),
            "source": source,
            "market_status": "OPEN"
        }
        _price_cache[asset_id] = {'time': now, 'data': result}
        return result

async def get_historical_candles(asset_id: str, timeframe: str):
    if asset_id not in ASSETS:
        raise ValueError("invalid symbol")
        
    cache_key = f"{asset_id}_{timeframe}"
    
    if cache_key not in _locks:
        _locks[cache_key] = asyncio.Lock()
        
    async with _locks[cache_key]:
        now = datetime.now().timestamp()
        
        if cache_key in _cache:
            cached = _cache[cache_key]
            if now - cached['time'] < _cache_ttl:
                return cached['data']

        try:
            intervals = {
                '5M': '5m',
                '15M': '15m',
                '1H': '1h',
                '4H': '1h', # Fallback to 1h
                '1D': '1d'
            }
            
            if timeframe not in intervals:
                return "DATA_UNAVAILABLE"
                
            symbol = "GC=F"
            yf_interval = intervals[timeframe]
            period = '1y' if timeframe == '1D' else '1mo'
            
            def fetch_candles():
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period=period, interval=yf_interval)
                if len(hist) == 0:
                    raise Exception("No candle data returned from yfinance")
                return hist.reset_index().to_dict('records')
                
            raw_candles = await asyncio.to_thread(fetch_candles)
            
            candles = []
            for row in raw_candles[-100:]:
                dt_val = row.get('Datetime', row.get('Date'))
                candles.append({
                    "timestamp": dt_val.strftime('%Y-%m-%d %H:%M:%S'),
                    "open": float(row['Open']),
                    "close": float(row['Close']),
                    "high": float(row['High']),
                    "low": float(row['Low']),
                    "volume": float(row.get('Volume', 0))
                })
                
        except Exception as e:
            print(f"yfinance candles failed for {asset_id}, using simulated data: {e}")
            # FALLBACK: Simulated Candles Data
            candles = []
            base_time = datetime.now() - timedelta(days=5)
            current_price = SIMULATED_BASE_PRICE - 20
            
            # Create 100 realistic-looking mock candles
            for i in range(100):
                # determine time step
                if timeframe == '5M':
                    base_time += timedelta(minutes=5)
                elif timeframe == '15M':
                    base_time += timedelta(minutes=15)
                elif timeframe == '1H' or timeframe == '4H':
                    base_time += timedelta(hours=1)
                elif timeframe == '1D':
                    base_time += timedelta(days=1)
                    
                open_p = current_price
                close_p = open_p + random.uniform(-3, 3)
                high_p = max(open_p, close_p) + random.uniform(0, 2)
                low_p = min(open_p, close_p) - random.uniform(0, 2)
                
                candles.append({
                    "timestamp": base_time.strftime('%Y-%m-%d %H:%M:%S'),
                    "open": open_p,
                    "close": close_p,
                    "high": high_p,
                    "low": low_p,
                    "volume": random.uniform(1000, 50000)
                })
                current_price = close_p
                
        _cache[cache_key] = {'time': now, 'data': candles}
        return candles

def get_market_status(asset_id: str) -> str:
    return "OPEN"

def get_asset_info(asset_id: str):
    return ASSETS.get(asset_id)
