import httpx, asyncio, json
async def f():
    resp = await httpx.AsyncClient().get('https://api.twelvedata.com/time_series?symbol=XAU/USD&interval=15min&outputsize=1&apikey=386a97ae541945ec8d77c8479d0453cc')
    with open('out.json', 'w') as f:
        json.dump(resp.json(), f)
asyncio.run(f())
