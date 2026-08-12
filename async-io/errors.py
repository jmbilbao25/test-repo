"""What happens when some of the endpoints fail.

By default asyncio.gather stops at the first exception and the results that did
succeed are lost. return_exceptions=True keeps every slot, so a failure becomes a
value you can inspect instead of something that cancels the batch.

    python3 errors.py
"""
from __future__ import annotations

import asyncio

import aiohttp

BASE = "https://jsonplaceholder.typicode.com"

# url, timeout in seconds, what it is meant to show
TARGETS = [
    (f"{BASE}/posts/1", 10.0, "a normal request"),
    (f"{BASE}/posts/99999999", 10.0, "a path that does not exist"),
    ("https://no-such-host.invalid/data", 10.0, "a host that does not resolve"),
    (f"{BASE}/todos/1", 0.001, "a real endpoint, impossible timeout"),
    (f"{BASE}/users/1", 10.0, "a normal request"),
]


async def fetch_data(session: aiohttp.ClientSession, url: str,
                     timeout: float) -> dict:
    async with session.get(
        url, timeout=aiohttp.ClientTimeout(total=timeout)
    ) as response:
        response.raise_for_status()
        return await response.json()


def coroutines(session: aiohttp.ClientSession):
    return (fetch_data(session, url, timeout) for url, timeout, _ in TARGETS)


async def main() -> None:
    for url, timeout, note in TARGETS:
        print(f"  {note:38} timeout {timeout}s")

    print("\nDefault gather: the first failure ends the batch\n")
    async with aiohttp.ClientSession() as session:
        try:
            await asyncio.gather(*coroutines(session))
        except Exception as exc:
            print(f"  raised {type(exc).__name__}: {str(exc)[:52]}")
            print("  the responses that did arrive are thrown away")

    print("\nreturn_exceptions=True: every slot comes back\n")
    async with aiohttp.ClientSession() as session:
        results = await asyncio.gather(*coroutines(session),
                                       return_exceptions=True)

    ok = 0
    for (url, _timeout, _note), result in zip(TARGETS, results):
        if isinstance(result, Exception):
            reason = str(result).split(",")[0][:40] or "no message"
            print(f"  FAILED  {type(result).__name__:24} {reason}")
        else:
            ok += 1
            print(f"  ok      id={result.get('id'):<21} {url}")

    print(f"\n  {ok} succeeded, {len(results) - ok} failed, "
          "and the batch still finished")


if __name__ == "__main__":
    asyncio.run(main())
