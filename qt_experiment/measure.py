"""Repeatable offscreen cold-process comparison; not a Windows/game benchmark."""
from __future__ import annotations

import os
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import psutil


def measure(candidate, repeats=5):
    results = []
    for _ in range(repeats):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / 'frame.png'
            env = dict(os.environ, QT_QPA_PLATFORM='offscreen', QT_QUICK_BACKEND='software')
            start = time.monotonic()
            process = subprocess.Popen([sys.executable, '-m', 'qt_experiment.' + candidate,
                                        '--screenshot', str(target)], env=env,
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            child = psutil.Process(process.pid)
            peak = 0
            while process.poll() is None:
                try:
                    peak = max(peak, child.memory_info().rss)
                except psutil.NoSuchProcess:
                    break
                time.sleep(.005)
            stdout, stderr = process.communicate()
            elapsed = (time.monotonic() - start) * 1000
            if process.returncode or not target.exists():
                raise RuntimeError(f'{candidate}: {process.returncode}\n{stderr.decode(errors="replace")}')
            results.append((elapsed, peak / 1048576))
    return results


if __name__ == '__main__':
    for name in ('quick', 'widgets'):
        rows = measure(name)
        print(name, 'cold process+frame ms median', round(statistics.median(x[0] for x in rows), 1),
              'range', tuple(round(x, 1) for x in (min(r[0] for r in rows), max(r[0] for r in rows))),
              'observed RSS MiB median', round(statistics.median(x[1] for x in rows), 1),
              'runs', rows)
