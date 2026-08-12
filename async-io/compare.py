"""The same requests done one after another, then all at once.

This is the measurement behind the claim that async helps here.

    python3 compare.py
"""
from __future__ import annotations

import asyncio
import time

import aiohttp

BASE = "https://jsonplaceholder.typicode.com"

# A bigger batch than the five in async_fetch.py. Each response here comes back
# in a few hundredths of a second, so five requests are not enough for the
# difference to be worth measuring.
URLS = [f"{BASE}/posts/{n}" for n in range(1, 21)]


async def get(session: aiohttp.ClientSession, url: str) -> int:
    async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as r:
        await r.json()
        return r.status


async def warm_up() -> None:
    """One request first, so DNS and the TLS handshake are not counted."""
    async with aiohttp.ClientSession() as session:
        await get(session, URLS[0])


async def sequentially() -> float:
    """Each request waits for the one before it to finish."""
    started = time.perf_counter()
    async with aiohttp.ClientSession() as session:
        for url in URLS:
            await get(session, url)
    return time.perf_counter() - started


async def concurrently() -> float:
    """All the requests are in flight at the same time."""
    started = time.perf_counter()
    async with aiohttp.ClientSession() as session:
        await asyncio.gather(*(get(session, url) for url in URLS))
    return time.perf_counter() - started


async def main() -> None:
    print(f"{len(URLS)} requests to jsonplaceholder.typicode.com\n")
    await warm_up()

    one_at_a_time = await sequentially()
    print(f"  one after another   {one_at_a_time:5.2f}s")

    all_together = await concurrently()
    print(f"  all at once         {all_together:5.2f}s")

    print(f"\n  {one_at_a_time / all_together:.1f}x faster, "
          f"{one_at_a_time - all_together:.2f}s saved")
    print("\nThe work itself is the same. The time saved is the waiting that "
          "now overlaps.")


if __name__ == "__main__":
    asyncio.run(main())
