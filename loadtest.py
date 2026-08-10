"""Small load generator used to measure the /api/items endpoint."""
import statistics
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

URL = "http://localhost:8085/api/items?count=25000"


def one_call():
    start = time.perf_counter()
    with urllib.request.urlopen(URL, timeout=60) as resp:
        resp.read()
    return (time.perf_counter() - start) * 1000


def run(total, workers):
    with ThreadPoolExecutor(max_workers=workers) as pool:
        wall_start = time.perf_counter()
        latencies = list(pool.map(lambda _: one_call(), range(total)))
        wall = time.perf_counter() - wall_start
    latencies.sort()
    return {
        "requests": total,
        "wall_seconds": round(wall, 2),
        "throughput_rps": round(total / wall, 1),
        "avg_ms": round(statistics.mean(latencies), 1),
        "p50_ms": round(latencies[int(len(latencies) * 0.50)], 1),
        "p95_ms": round(latencies[int(len(latencies) * 0.95)], 1),
        "max_ms": round(latencies[-1], 1),
    }


if __name__ == "__main__":
    phase = sys.argv[1] if len(sys.argv) > 1 else "measure"
    if phase == "warmup":
        run(300, 4)
        print("warmup done")
    else:
        stats = run(1200, 16)
        for key, value in stats.items():
            print(f"{key}={value}")
