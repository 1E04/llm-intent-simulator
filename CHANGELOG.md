## [1.0.0] - 2026-08-05

### Added
- **Multi-Turn Dialogue Harness:** Added `scripte/multi-turn-simulator.py` to support automated multi-turn testing for Banking77 intent recognition. Features `UserSimulator` (persona-driven testing), `TargetVoiceBot`, and `MultiTurnTestHarness` with automatic token logging and incremented run output tracking.
- **Environment & Dependency Management:** Integrated `python-dotenv` and generated `uv.lock` for reproducible dependency management. Added core data and plotting dependencies (`matplotlib`, `openai`, `pandas`, `seaborn`) to `pyproject.toml`.
- **Git Ignore Safeguards:** Updated `.gitignore` to protect `.env` secrets and exclude auxiliary evaluation scripts (`judge_llm.py`, `evaluate_jsonl.py`, `comparision_eval.py`, `add_uuid_to_dataset.py`, `main.py`).

### Changed
- **Repository Setup & README:** Restructured `README.md` to feature the project title (*Master's Thesis: LLM-Based Testing System*) and provided a comprehensive setup guide for secure local configuration using environment variables.

## [0.1.0] - 2026-08-03

### Added
- **Initial Repository Setup:** Created the foundational repository structure for the Master's thesis project focusing on the conceptual design of an LLM-based testing system.
- **Datasets:** Added initial single-turn datasets based on Banking77, including:
  - `banking77_test.csv`: Base testing dataset.
  - `banking77_test_with_uuid.csv`: Testing dataset extended with unique identifiers.
  - `banking77_personas_gpt-oss:120b.csv`: A generated dataset containing over 2,300 persona-driven variations (e.g., *angry_layperson*, *panicking_emergency*, *polite_expert*, *gen_z_slang*, *non_native_speaker*, *short_wording*) mapped to Banking77 intents.
- **Project Configurations:** 
  - Added `.python-version` specifying Python 3.14.
  - Added `.gitignore` to exclude standard Python build artifacts, virtual environments (`.venv`), and local testing/result directories (`pics`, `results`, specific generator scripts).
- **Documentation:** Created the initial `README.md` outlining the thesis title and repository purpose.