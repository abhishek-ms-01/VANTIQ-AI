from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from config import ASSETS, settings
from market_data.unified import get_live_price, get_historical_candles, get_market_status, get_asset_info
import pandas as pd
from strategies.banknifty_strategy import BankNiftyStrategy
from strategies.sensex_strategy import SensexStrategy
from strategies.gold_strategy import GoldStrategy
from strategies.eurusd_strategy import EurUsdStrategy
from strategies.btc_strategy import BtcStrategy
from strategies.eth_strategy import EthStrategy
from risk.trade_validation import validate_and_build_trade_plan

strategy_map = {
    "BANK_NIFTY": BankNiftyStrategy(),
    "SENSEX": SensexStrategy(),
    "GOLD": GoldStrategy(),
    "EURUSD": EurUsdStrategy(),
    "BTC": BtcStrategy(),
    "ETH": EthStrategy()
}

async def get_strategy_data(asset: str):
    if asset not in ASSETS:
        raise HTTPException(status_code=404, detail="invalid symbol")
    
    strategy = strategy_map.get(asset)
    if not strategy:
        raise HTTPException(status_code=500, detail="strategy not found")
        
    data_dict = {}
    for tf in strategy.timeframes:
        candles = await get_historical_candles(asset, tf)
        if candles != "DATA_UNAVAILABLE" and isinstance(candles, list) and len(candles) > 0:
            df = pd.DataFrame(candles)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
            data_dict[tf] = df
        else:
            data_dict[tf] = pd.DataFrame()
            
    return strategy, data_dict

app = FastAPI(title="MARKET AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
async def health_check():
    provider_status = {
        "twelve_data": "configured" if settings.TWELVE_DATA_API_KEY else "missing_key",
        "upstox": "configured" if settings.UPSTOX_ACCESS_TOKEN else "missing_key"
    }
    
    return {
        "status": "online",
        "backend": "FastAPI",
        "timestamp": datetime.utcnow().isoformat(),
        "data_provider_status": provider_status
    }

@app.get("/api/assets")
async def get_assets():
    return list(ASSETS.values())

@app.get("/api/market/{asset}")
async def get_market(asset: str):
    if asset not in ASSETS:
        raise HTTPException(status_code=404, detail="invalid symbol")
    
    price_data = await get_live_price(asset)
    if price_data == "DATA_UNAVAILABLE":
        return {"status": "DATA_UNAVAILABLE", "message": "Market data unavailable"}
        
    return {
        "asset": asset,
        "symbol": ASSETS[asset]["provider_symbol"],
        "price": price_data.get("price"),
        "previous_close": price_data.get("previous_close"),
        "change": price_data.get("change"),
        "change_percent": price_data.get("change_percent"),
        "timestamp": price_data.get("timestamp"),
        "source": price_data.get("source"),
        "market_status": price_data.get("market_status")
    }

@app.get("/api/candles/{asset}/{timeframe}")
async def get_candles(asset: str, timeframe: str):
    if asset not in ASSETS:
        raise HTTPException(status_code=404, detail="invalid symbol")
        
    if timeframe not in ASSETS[asset]["supported_timeframes"]:
        raise HTTPException(status_code=400, detail="invalid timeframe")
        
    candles = await get_historical_candles(asset, timeframe)
    if candles == "DATA_UNAVAILABLE":
        return {"status": "DATA_UNAVAILABLE", "message": "Market data unavailable"}
        
    return {
        "asset": asset,
        "timeframe": timeframe,
        "candles": candles
    }

@app.get("/api/analysis/{asset}")
async def get_analysis(asset: str):
    try:
        strategy, data_dict = await get_strategy_data(asset)
        
        # We need to calculate indicators for all timeframes
        data_dict = strategy.calculate_indicators(data_dict)
        base_tf = strategy.timeframes[0]
        df = data_dict[base_tf]
        
        if df.empty:
            return {"status": "DATA_UNAVAILABLE"}
            
        latest = df.iloc[-1]
        
        # Simple extraction for Technical Panel
        def fmt(val):
            return str(round(val, 2)) if not pd.isna(val) else "N/A"
            
        trend = "BULLISH" if latest.get('ema_20', 0) > latest.get('ema_50', 0) else "BEARISH"
        
        return {
            "asset": asset,
            "trend": trend,
            "ema": f"{fmt(latest.get('ema_20'))} / {fmt(latest.get('ema_50'))}",
            "rsi": fmt(latest.get('rsi')),
            "macd": fmt(latest.get('macd')),
            "adx": fmt(latest.get('adx')),
            "atr": fmt(latest.get('atr')),
            "vwap": fmt(latest.get('vwap')),
            "volume": fmt(latest.get('volume')),
            "support": fmt(latest.get('support')),
            "resistance": fmt(latest.get('resistance')),
            "message": f"Real-time {base_tf} Technicals"
        }
    except Exception as e:
        print(f"Error in analysis: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/api/strategy/{asset}")
async def get_strategy(asset: str):
    try:
        strategy, data_dict = await get_strategy_data(asset)
        
        # Generate signal
        signal = strategy.generate_signal(data_dict)
        
        # Validate trade plan
        plan = validate_and_build_trade_plan(
            asset_id=asset,
            direction=signal.get("direction", "NO_TRADE"),
            entry_price=signal.get("entry", 0),
            stop_loss=signal.get("stop_loss", 0),
            target_1=signal.get("target_1", 0),
            target_2=signal.get("target_2", 0),
            signal_strength=signal.get("signal_strength", 0),
            trade_quality=100 if signal.get("trade_quality") == "HIGH" else (50 if signal.get("trade_quality") == "MEDIUM" else 0),
            invalidation_level=signal.get("invalidation", ""),
            reasons=signal.get("reasons", []),
            warnings=signal.get("warnings", []),
            min_rr=1.0 # Lowered slightly for demonstration
        )
        
        plan['strategy_name'] = strategy.__class__.__name__
        plan['market_regime'] = signal.get("market_regime", "UNKNOWN")
        plan['timeframes'] = signal.get("timeframes", strategy.timeframes)
        
        return plan
    except Exception as e:
        print(f"Error in strategy: {e}")
        return {"status": "error", "message": str(e)}
