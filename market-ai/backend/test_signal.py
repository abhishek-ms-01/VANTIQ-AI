import pandas as pd
from strategies.gold_strategy import GoldStrategy

def run_test():
    strategy = GoldStrategy()
    
    # Create mock 15M dataframe
    timestamps = pd.date_range("2026-08-19 14:00:00", periods=50, freq="15min", tz="UTC")
    df = pd.DataFrame(index=timestamps)
    
    # Mock data to create a perfect Breakout Setup
    df['open'] = 4400.0
    df['high'] = 4420.0
    df['low'] = 4390.0
    df['close'] = 4415.0 # Close > EMA21 and Close > VWAP
    
    # Mock Indicators
    df['ema21'] = 4370.0
    df['ema50'] = 4360.0
    df['ema200'] = 4350.0
    df['rsi14'] = 82.5 # High RSI momentum
    df['atr14'] = 10.0
    df['vwap'] = 4405.0 # Price is comfortably above VWAP
    df['candle_size'] = df['high'] - df['low']
    df['macd'] = 5.0
    df['macd_signal'] = 3.0
    df['adx14'] = 35.0
    
    data = {
        '15M': df,
        '1H': df.copy(),
        '4H': df.copy(),
        '1D': df.copy()
    }
    
    # Generate signal directly (skip recalculating indicators in this mock)
    # We monkey-patch calculate_indicators just for this test so it uses our mocked values
    original_calc = strategy.calculate_indicators
    strategy.calculate_indicators = lambda x: x
    
    print("--- MOCKING A PERFECT BREAKOUT SETUP ---")
    print(f"Close: {df['close'].iloc[-1]}, VWAP: {df['vwap'].iloc[-1]}, RSI: {df['rsi14'].iloc[-1]}")
    signal = strategy.generate_signal(data)
    
    import json
    print("\n--- SIGNAL OUTPUT ---")
    print(json.dumps(signal, indent=2))
    print("\n--- EXPLANATION ---")
    print(signal['explanation'])

if __name__ == "__main__":
    run_test()
