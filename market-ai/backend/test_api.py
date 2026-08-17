import httpx, asyncio
async def f():
    resp = await httpx.AsyncClient().get('https://api.twelvedata.com/quote?symbol=XAU/USD&apikey=386a97ae541945ec8d77c8479d0453cc')
    print(resp.json())
asyncio.run(f())
