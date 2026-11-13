"""Synthetic local burst benchmark for incoming CoD2 chat latency.

No internet or user messages. The fixed fake provider models a remote MT
delay so this benchmark only compares queue behaviour; its p50/p95 values
are NOT measurements of live Google or game performance.
"""
from __future__ import annotations

import argparse
import queue
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import ChatMessage, TranslatorWorker, TranslationWorkerSharedState  # noqa: E402


def percentile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    return round(ordered[min(len(ordered) - 1, round((len(ordered)-1) * q))], 1)


def benchmark(workers: int, count: int = 24, fake_network_ms: int = 75) -> dict:
    """Simulate a burst of unambiguous chat texts all requiring network MT."""
    if not 1 <= workers <= 4:
        raise ValueError("workers must be 1..4")
    if count < 1 or not 0 <= fake_network_ms <= 1000:
        raise ValueError("invalid benchmark parameters")
    jobs: queue.Queue[ChatMessage] = queue.Queue(maxsize=max(50, count))
    events: queue.Queue[tuple] = queue.Queue()
    stop = threading.Event()
    shared = TranslationWorkerSharedState()
    pool = []
    for _ in range(workers):
        worker = TranslatorWorker(
            jobs,
            events,
            lambda: "ru",
            lambda: False,
            lambda: False,  # keep provider path for all examples
            lambda: "live",
            stop,
            smart_enabled_getter=lambda: True,
            shared_state=shared,
        )
        def simulated_provider(text, target):
            time.sleep(fake_network_ms / 1000.0)
            return "перевод"
        worker._translate = simulated_provider
        pool.append(worker)
    started = time.monotonic()
    for number in range(count):
        jobs.put(ChatMessage("Synthetic", f"hello test message {number}", enqueued_at=started))
    for worker in pool:
        worker.start()
    jobs.join()
    stop.set()
    for worker in pool:
        worker.join(timeout=3)
        if worker.is_alive():
            raise RuntimeError("Worker failed to stop")
    elapsed_ms = round((time.monotonic()-started)*1000,1)
    arrivals = []
    errors = []
    while not events.empty():
        event = events.get_nowait()
        if event[0] == "translation":
            arrivals.append(event[3])
        else:
            errors.append(event[0])
    if len(arrivals) != count or errors:
        raise AssertionError(f"Missing translations: {len(arrivals)}/{count}, errors={errors}")
    result = shared.snapshot()
    result.update({
        "workers": workers,
        "count": count,
        "fake_provider_ms": fake_network_ms,
        "end_to_end_p50_ms": percentile(arrivals, 0.5),
        "end_to_end_p95_ms": percentile(arrivals, 0.95),
        "elapsed_burst_ms": elapsed_ms,
    })
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=24)
    parser.add_argument("--fake-network-ms", type=int, default=75)
    args = parser.parse_args()
    old = benchmark(1, args.count, args.fake_network_ms)
    improved = benchmark(2, args.count, args.fake_network_ms)
    print("SYNTHETIC burst, no internet/game latency measurements:")
    for label, metrics in (("one_worker", old), ("two_workers", improved)):
        print(f"{label}: {metrics}")
    if old["end_to_end_p95_ms"] > 0:
        reduction = 100 * (
            1 - improved["end_to_end_p95_ms"] / old["end_to_end_p95_ms"]
        )
        print(f"Simulated p95 reduction: {reduction:.1f}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
