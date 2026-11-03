"""`python -m devsecops_dojo.hooks <nom> ...` : appelé par les scripts de `hooks/` (AD-9)."""

from __future__ import annotations

import sys

from devsecops_dojo.hooks import main

if __name__ == "__main__":
    sys.stderr.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    sys.exit(main(sys.argv[1:]))
