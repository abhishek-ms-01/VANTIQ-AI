from pydantic_settings import BaseSettings
from typing import Dict, Any

class Settings(BaseSettings):
    TWELVE_DATA_API_KEY: str = ""
    UPSTOX_API_KEY: str = ""
    UPSTOX_API_SECRET: str = ""
    UPSTOX_ACCESS_TOKEN: str = ""
    
    class Config:
        env_file = ".env"

settings = Settings()

ASSETS: Dict[str, Dict[str, Any]] = {
    "BANK_NIFTY": {
        "id": "BANK_NIFTY",
        "display_name": "BANK NIFTY",
        "category": "INDIAN",
        "provider": "upstox",
        "provider_symbol": "NSE_INDEX|Nifty Bank",
        "supported_timeframes": ["5M", "15M", "1H", "4H", "1D"],
        "strategy_module": "banknifty_strategy"
    },
    "SENSEX": {
        "id": "SENSEX",
        "display_name": "SENSEX",
        "category": "INDIAN",
        "provider": "upstox",
        "provider_symbol": "BSE_INDEX|SENSEX",
        "supported_timeframes": ["5M", "15M", "1H", "4H", "1D"],
        "strategy_module": "sensex_strategy"
    },
    "GOLD": {
        "id": "GOLD",
        "display_name": "XAU/USD",
        "category": "FOREX",
        "provider": "twelve_data",
        "provider_symbol": "XAU/USD",
        "supported_timeframes": ["5M", "15M", "1H", "4H", "1D"],
        "strategy_module": "gold_strategy"
    },
    "EURUSD": {
        "id": "EURUSD",
        "display_name": "EUR/USD",
        "category": "FOREX",
        "provider": "twelve_data",
        "provider_symbol": "EUR/USD",
        "supported_timeframes": ["5M", "15M", "1H", "4H", "1D"],
        "strategy_module": "eurusd_strategy"
    },
    "BTC": {
        "id": "BTC",
        "display_name": "BTC/USD",
        "category": "CRYPTO",
        "provider": "twelve_data",
        "provider_symbol": "BTC/USD",
        "supported_timeframes": ["5M", "15M", "1H", "4H", "1D"],
        "strategy_module": "btc_strategy"
    },
    "ETH": {
        "id": "ETH",
        "display_name": "ETH/USD",
        "category": "CRYPTO",
        "provider": "twelve_data",
        "provider_symbol": "ETH/USD",
        "supported_timeframes": ["5M", "15M", "1H", "4H", "1D"],
        "strategy_module": "eth_strategy"
    }
}
