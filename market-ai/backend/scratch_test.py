import asyncio
import pandas as pd
from market_data.twelve_data import get_twelve_data_live_price, get_twelve_data_historical_candles
from strategies.gold_strategy import GoldStrategy

async def main():
    try:
        # Fetch data
        print("Fetching data...")
        data = {}
        for tf in ["15M", "1H", "4H", "1D"]:
            candles = await get_twelve_data_historical_candles("XAU/USD", tf)
            df = pd.DataFrame(candles)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
            data[tf] = df
        
        print("Data fetched. Analyzing...")
        strategy = GoldStrategy()
        
        # Manually calculate and print indicators
        data = strategy.calculate_indicators(data)
        
        last15 = data['15M'].iloc[-1]
        prev15 = data['15M'].iloc[-2]
        current_atr = last15['atr14']
        
        print(f"\n--- Current Market State (15M) ---")
        print(f"Timestamp: {data['15M'].index[-1]}")
        print(f"Parsed Hour GMT: {data['15M'].index[-1].hour}")
        print(f"Close: {last15['close']}")
        print(f"EMA21: {last15['ema21']}")
        print(f"EMA50: {last15['ema50']}")
        print(f"EMA200: {last15['ema200']}")
        print(f"VWAP:  {last15['vwap']}")
        print(f"RSI:   {last15['rsi14']} (prev: {prev15['rsi14']})")
        print(f"ATR:   {current_atr}")
        print(f"Distance to EMA50: {abs(last15['close'] - last15['ema50'])}")
        print(f"Pullback threshold (1.5x ATR): {1.5 * current_atr}")
        
        regime = strategy.detect_market_regime(data)
        print(f"\nRegime: {regime}")
        
        signal = strategy.generate_signal(data)
        print("\n--- Signal Output ---")
        import json
        print(json.dumps(signal, indent=2, default=str))

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
