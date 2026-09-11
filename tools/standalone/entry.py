"""Frozen executable entry point; dispatch spawn workers before the CLI."""

import multiprocessing

if __name__ == "__main__":
    multiprocessing.freeze_support()
    from zencad.__main__ import main

    raise SystemExit(main())
