#!/usr/bin/env python3
"""Cross-evaluation matrix across every model and dataset (thesis Table 6.1).

Thin entry point; the implementation lives in :mod:`itaf.stages.reporting`.

    uv run python scripte/02_single_turn/comparision_eval.py
    uv run python scripte/02_single_turn/comparision_eval.py --worst 10 --no-plots

Equivalent: ``uv run itaf report matrix``
"""

import sys

from itaf.stages.reporting import matrix_main

if __name__ == "__main__":
    sys.exit(matrix_main())
