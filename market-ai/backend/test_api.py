import asyncio
import json
from main import get_strategy

async def test_endpoint():
    print("Testing /api/strategy/GOLD endpoint logic...")
    result = await get_strategy("GOLD")
    print(json.dumps(result, indent=2, default=str))

if __name__ == "__main__":
    asyncio.run(test_endpoint())
