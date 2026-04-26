from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from knowledge_agent.runtime.agent_app import AgentApp


def main() -> None:
    question = sys.argv[1] if len(sys.argv) > 1 else "系统中心是什么？"
    app = AgentApp()
    print(app.ask(question))


if __name__ == "__main__":
    main()
