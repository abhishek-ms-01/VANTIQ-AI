from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from config import ASSETS, settings
from market_data.unified import get_live_price, get_historical_candles, get_market_status, get_asset_info
import pandas as pd
from strategies.gold_strategy import GoldStrategy
from risk.trade_validation import validate_and_build_trade_plan
from notifications import check_and_send_alert
import asyncio

strategy_map = {
    "GOLD": GoldStrategy()
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

async def autonomous_trading_loop():
    print("Starting Autonomous Trade Evaluator...")
    while True:
        try:
            # Check market every 5 minutes
            await asyncio.sleep(300)
            strategy, data_dict = await get_strategy_data("GOLD")
            signal = strategy.generate_signal(data_dict)
            plan = validate_and_build_trade_plan(
                raw_signal=signal,
                data_df=data_dict[strategy.timeframes[0]],
                min_rr=1.0
            )
            plan['regime'] = signal.get("market_regime", "UNKNOWN")
            plan['score'] = signal.get("signal_strength", 0)
            plan['session_tier'] = signal.get("session_tier", "UNKNOWN")
            plan['lots'] = signal.get("lots", 0)
            check_and_send_alert(plan)
        except Exception as e:
            print(f"Autonomous loop error: {e}")

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(autonomous_trading_loop())

@app.get("/api/health")
async def health_check():
    provider_status = {
        "twelve_data": "configured" if settings.TWELVE_DATA_API_KEY else "missing_key"
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
            
        trend = "BULLISH" if latest.get('ema21', 0) > latest.get('ema50', 0) else "BEARISH"
        
        return {
            "asset": asset,
            "trend": trend,
            "ema": f"{fmt(latest.get('ema21'))} / {fmt(latest.get('ema50'))}",
            "rsi": fmt(latest.get('rsi14')),
            "macd": fmt(latest.get('macd')),
            "adx": fmt(latest.get('adx14')),
            "atr": fmt(latest.get('atr14')),
            "vwap": fmt(latest.get('vwap')),
            "volume": fmt(latest.get('volume')),
            "support": "N/A", # Support/Resistance not calculated natively yet, can be added later
            "resistance": "N/A",
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
            raw_signal=signal,
            data_df=data_dict[strategy.timeframes[0]],
            min_rr=1.0
        )
        
        plan['strategy_name'] = strategy.__class__.__name__
        plan['market_regime'] = signal.get("market_regime", "UNKNOWN")
        plan['regime'] = signal.get("market_regime", "UNKNOWN")
        plan['score'] = signal.get("signal_strength", 0)
        plan['session_tier'] = signal.get("session_tier", "UNKNOWN")
        plan['lots'] = signal.get("lots", 0)
        plan['timeframes'] = signal.get("timeframes", strategy.timeframes)
        
        check_and_send_alert(plan)
        
        return plan
    except Exception as e:
        print(f"Error in strategy: {e}")
        return {"status": "error", "message": str(e)}
