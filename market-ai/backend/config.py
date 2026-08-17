from pydantic_settings import BaseSettings
from typing import Dict, Any

class Settings(BaseSettings):
    TWELVE_DATA_API_KEY: str = "1542558161bd4b6aa75f68a479b46a69"
    
    class Config:
        env_file = ".env"

settings = Settings()

ASSETS: Dict[str, Dict[str, Any]] = {
    "GOLD": {
        "id": "GOLD",
        "display_name": "XAU/USD",
        "category": "FOREX",
        "provider": "twelve_data",
        "provider_symbol": "XAU/USD",
        "supported_timeframes": ["5M", "15M", "1H", "4H", "1D"],
        "strategy_module": "gold_strategy"
    }
}
