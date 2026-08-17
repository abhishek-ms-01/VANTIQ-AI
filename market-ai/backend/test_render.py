import httpx, asyncio, json
async def f():
    resp = await httpx.AsyncClient().get('https://vantiq-ai-1.onrender.com/api/market/GOLD')
    print(resp.json())
asyncio.run(f())
