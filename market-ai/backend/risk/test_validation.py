import pandas as pd
from risk.trade_validation import validate_and_build_trade_plan

def run_test():
    raw_signal = {
        "direction": "LONG",
        "entry": 52480,
        "signal_strength": 84,
        "market_regime": "BULLISH_TREND",
        "invalidation": "15M close below 52350 invalidates the long setup.",
        "reasons": ["15m MACD crossover", "4h trend alignment"]
    }
    
    # Mock dataframe with necessary data
    data = pd.DataFrame({
        'open': [52400],
        'high': [52500],
        'low': [52380],
        'close': [52490],
        'atr14': [100],
        'swing_low': [52350],
        'swing_high': [52740]
    })
    
    # Add another high for TP2
    data_tp2 = pd.DataFrame({
        'open': [52400, 52600],
        'high': [52740, 52950],
        'low': [52350, 52500],
        'close': [52490, 52900],
        'atr14': [100, 100],
        'swing_low': [52350, 52350],
        'swing_high': [52740, 52950]
    })

    print("--- TESTING SUCCESSFUL TRADE ---")
    plan = validate_and_build_trade_plan(raw_signal, data_tp2, atr_multiplier=0.0) # SL at exactly swing low 52350
    for k, v in plan.items():
        print(f"{k}: {v}")
        
    print("\n--- TESTING FAILED RR ---")
    plan2 = validate_and_build_trade_plan(raw_signal, data_tp2, atr_multiplier=0.0, min_rr=3.0)
    for k, v in plan2.items():
        print(f"{k}: {v}")

if __name__ == "__main__":
    run_test()
