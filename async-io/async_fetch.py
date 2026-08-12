"""Fetches several API endpoints at the same time with asyncio and aiohttp.

    python3 async_fetch.py
"""
from __future__ import annotations

import asyncio
import time

import aiohttp

BASE = "https://jsonplaceholder.typicode.com"

URLS = [
    f"{BASE}/posts/1",
    f"{BASE}/posts/2",
    f"{BASE}/users/1",
    f"{BASE}/todos/1",
    f"{BASE}/comments/1",
]


async def fetch_data(session: aiohttp.ClientSession, url: str) -> dict:
    """Send a GET request and return the decoded JSON body.

    await hands control back to the event loop while the network is busy, which
    is what lets the other requests run during this one's waiting time.
    """
    started = time.perf_counter()
    async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
        response.raise_for_status()
        data = await response.json()
    elapsed = time.perf_counter() - started
    print(f"  {response.status}  {elapsed:5.2f}s  {url}")
    return data


async def main() -> None:
    print(f"Fetching {len(URLS)} endpoints concurrently\n")
    started = time.perf_counter()

    async with aiohttp.ClientSession() as session:
        # One coroutine per URL, then gather runs them together and gives the
        # results back in the order the URLs were listed.
        tasks = [fetch_data(session, url) for url in URLS]
        results = await asyncio.gather(*tasks)

    total = time.perf_counter() - started

    print(f"\nGot {len(results)} responses in {total:.2f}s\n")
    for url, data in zip(URLS, results):
        label = url.rsplit("/", 2)[-2]
        title = data.get("title") or data.get("name") or data.get("body", "")
        print(f"  {label:9} id={data.get('id')}  {title[:46].strip()}")


if __name__ == "__main__":
    asyncio.run(main())
