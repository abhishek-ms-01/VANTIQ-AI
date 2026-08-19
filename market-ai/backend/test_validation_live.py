import asyncio
import pandas as pd
import json
from market_data.twelve_data import get_twelve_data_historical_candles
from strategies.gold_strategy import GoldStrategy
from risk.trade_validation import validate_and_build_trade_plan

async def run_test():
    strategy = GoldStrategy()
    data = {}
    for tf in ["15M", "1H", "4H", "1D"]:
        candles = await get_twelve_data_historical_candles("XAU/USD", tf)
        df = pd.DataFrame(candles)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        data[tf] = df
        
    data = strategy.calculate_indicators(data)
    signal = strategy.generate_signal(data)
    
    print("--- RAW SIGNAL ---")
    print(json.dumps(signal, indent=2, default=str))
    
    plan = validate_and_build_trade_plan(
        raw_signal=signal,
        data_df=data['15M'],
        min_rr=1.0
    )
    
    print("\n--- VALIDATED PLAN ---")
    print(json.dumps(plan, indent=2, default=str))

if __name__ == "__main__":
    asyncio.run(run_test())
