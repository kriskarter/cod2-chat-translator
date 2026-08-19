from __future__ import annotations

import os
import subprocess

import updater as core


_REAL_POPEN = core.subprocess.Popen


def _quiet_popen(*args, **kwargs):
    if os.name == "nt":
        flags = int(getattr(subprocess, "CREATE_NO_WINDOW", 0))
        if flags:
            kwargs.setdefault("creationflags", flags)
    return _REAL_POPEN(*args, **kwargs)


def main() -> int:
    core.subprocess.Popen = _quiet_popen
    return core.main()


if __name__ == "__main__":
    raise SystemExit(main())
