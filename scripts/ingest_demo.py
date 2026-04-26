from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from knowledge_agent.runtime.agent_app import AgentApp


def main() -> None:
    path = sys.argv[1] if len(sys.argv) > 1 else str(ROOT / "data" / "raw")
    app = AgentApp()
    results = app.ingest(path)
    print(f"Ingested {len(results)} source(s).")
    for result in results:
        print(f"- {result.source.title}: evidences={len(result.evidences)}, claims={len(result.claims)}")


if __name__ == "__main__":
    main()
