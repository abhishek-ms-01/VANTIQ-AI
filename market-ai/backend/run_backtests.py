import yfinance as yf
import pandas as pd
from backtest import BacktestEngine
from strategies.banknifty_strategy import BankNiftyStrategy
from strategies.sensex_strategy import SensexStrategy
from strategies.gold_strategy import GoldStrategy
from strategies.eurusd_strategy import EurUsdStrategy
from strategies.btc_strategy import BtcStrategy
from strategies.eth_strategy import EthStrategy

def format_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [col.lower() for col in df.columns]
    if 'volume' not in df.columns:
        df['volume'] = 0
    return df[['open', 'high', 'low', 'close', 'volume']]

def fetch_data(symbol: str, interval: str, period: str = "60d") -> pd.DataFrame:
    df = yf.download(symbol, interval=interval, period=period, progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return format_data(df)

def run_all_backtests():
    assets = {
        'BANK NIFTY': {'symbol': '^NSEBANK', 'strategy': BankNiftyStrategy()},
        'SENSEX': {'symbol': '^BSESN', 'strategy': SensexStrategy()},
        'GOLD': {'symbol': 'GC=F', 'strategy': GoldStrategy()},
        'EUR/USD': {'symbol': 'EURUSD=X', 'strategy': EurUsdStrategy()},
        'BTC': {'symbol': 'BTC-USD', 'strategy': BtcStrategy()},
        'ETH': {'symbol': 'ETH-USD', 'strategy': EthStrategy()}
    }

    intervals = {
        '5M': '5m',
        '15M': '15m',
        '1H': '1h',
        '1D': '1d'
    }

    print("\n" + "="*50)
    print("STRATEGY REPORT (FINAL UNSEEN TEST DATA)")
    print("="*50)

    for name, info in assets.items():
        symbol = info['symbol']
        strategy = info['strategy']
        
        # Prepare data dict
        data_dict = {}
        for tf in strategy.timeframes:
            if tf == '4H':
                # Resample 1H to 4H
                df_1h = fetch_data(symbol, '1h', '60d')
                if not df_1h.empty:
                    resampled = df_1h.resample('4h').agg({
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

        # Run Backtest Engine on TEST set (last 20%)
        engine = BacktestEngine(strategy=strategy, name=name, data_dict=data_dict)
        try:
            metrics = engine.run_backtest(split_type='TEST')
            
            print(f"\n{name}")
            print("-" * 12)
            print(f"Test signals:\n{metrics['total_signals']}")
            print(f"\nTotal trades executed:\n{metrics['total_trades']}")
            print(f"No-trade count (filtered):\n{metrics['no_trade_count']}")
            print(f"\nDirectional accuracy:\n{metrics['directional_accuracy']}%")
            print(f"\nWin rate:\n{metrics['win_rate']}%")
            print(f"\nProfit factor:\n{metrics['profit_factor']}")
            print(f"\nMax drawdown (R):\n{metrics['max_drawdown']}")
            print(f"\nAverage R:\n{metrics['average_r']}")
        except Exception as e:
            print(f"\n{name}")
            print("-" * 12)
            print(f"Error running backtest: {e}")

if __name__ == "__main__":
    run_all_backtests()
