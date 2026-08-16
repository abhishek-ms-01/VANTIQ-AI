import yfinance as yf
import pandas as pd
from typing import Dict
from strategies.banknifty_strategy import BankNiftyStrategy
from strategies.sensex_strategy import SensexStrategy
from strategies.gold_strategy import GoldStrategy
from strategies.eurusd_strategy import EurUsdStrategy
from strategies.btc_strategy import BtcStrategy
from strategies.eth_strategy import EthStrategy

def format_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [col.lower() for col in df.columns]
    # Keep only open, high, low, close, volume
    if 'volume' not in df.columns:
        df['volume'] = 0
    return df[['open', 'high', 'low', 'close', 'volume']]

def fetch_data(symbol: str, interval: str, period: str = "60d") -> pd.DataFrame:
    print(f"Fetching {symbol} - {interval}...")
    df = yf.download(symbol, interval=interval, period=period, progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return format_data(df)

def run_tests():
    # Asset Symbols
    assets = {
        'Bank Nifty': {'symbol': '^NSEBANK', 'strategy': BankNiftyStrategy()},
        'Sensex': {'symbol': '^BSESN', 'strategy': SensexStrategy()},
        'Gold': {'symbol': 'GC=F', 'strategy': GoldStrategy()},
        'EUR/USD': {'symbol': 'EURUSD=X', 'strategy': EurUsdStrategy()},
        'BTC': {'symbol': 'BTC-USD', 'strategy': BtcStrategy()},
        'ETH': {'symbol': 'ETH-USD', 'strategy': EthStrategy()}
    }

    # Common timeframes to fetch based on strategy needs
    intervals = {
        '5M': '5m',
        '15M': '15m',
        '1H': '1h',
        '4H': '1h', # Since yfinance doesn't natively do 4h, we'll resample 1h to 4h
        '1D': '1d'
    }

    for name, info in assets.items():
        symbol = info['symbol']
        strategy = info['strategy']
        print(f"\n{'='*50}\nTesting Strategy: {name}\n{'='*50}")
        
        # Prepare data dict
        data_dict = {}
        for tf in strategy.timeframes:
            if tf == '4H':
                # Resample 1H to 4H
                df_1h = fetch_data(symbol, '1h', '60d')
                if not df_1h.empty:
                    # Resampling logic
                    resampled = df_1h.resample('4H').agg({
                        'open': 'first',
                        'high': 'max',
                        'low': 'min',
                        'close': 'last',
                        'volume': 'sum'
                    }).dropna()
                    data_dict['4H'] = resampled
                else:
                    data_dict['4H'] = pd.DataFrame()
            else:
                period = "60d" if tf in ['5M', '15M'] else ("730d" if tf == '1H' else "max")
                data_dict[tf] = fetch_data(symbol, intervals[tf], period)

        # Handle missing data test (simulate empty dataframe for a timeframe)
        try:
            print("Running indicators and signal generation...")
            signal = strategy.generate_signal(data_dict)
            print("Signal Result:")
            for k, v in signal.items():
                print(f"  {k}: {v}")
        except Exception as e:
            print(f"Error running strategy: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    run_tests()
