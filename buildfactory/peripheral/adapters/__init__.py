"""Per-source adapters. Each module exposes `SOURCE: str` and
`to_ime(native: dict) -> dict` (a dumb, no-LLM transform: native signal → IME)."""
