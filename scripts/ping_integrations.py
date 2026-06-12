"""One-shot live check for all marketing data integrations."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import config  # noqa: E402


def main() -> int:
    results = config.ping_all_integrations()
    print(json.dumps(results, indent=2))
    return 0 if all(v.get("ok") for v in results.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
