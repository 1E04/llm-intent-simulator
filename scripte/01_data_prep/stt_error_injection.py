#!/usr/bin/env python3
"""Inject simulated STT transcription errors into a dataset (thesis 4.3.4).

Thin entry point; the implementation lives in :mod:`itaf.stages.data_prep`.

    uv run python scripte/01_data_prep/stt_error_injection.py \\
        --input dataset/single-turn/banking77_personas_phi4:14b_clean.csv \\
        --output dataset/single-turn/banking77_personas_phi4:14b_stt_degraded.csv

Applies phonetic confusion, punctuation and casing loss, and character-level
edits, then reports the mean Word Error Rate (Eq. 4.7) of the result -- which
nothing in the pipeline previously measured. The degradation rates are now
flags, and ``--seed`` makes runs reproducible; the earlier version had neither.
"""

import sys

from itaf.stages.data_prep import stt_inject_main

if __name__ == "__main__":
    sys.exit(stt_inject_main())
