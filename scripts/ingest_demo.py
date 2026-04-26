from __future__ import annotations

import sys

from knowledgeag_card.runtime.agent_app import AgentApp


def main() -> None:
    path = sys.argv[1] if len(sys.argv) > 1 else 'data/raw'
    app = AgentApp.create()
    results = app.ingest(path)
    for result in results:
        print(result.source.title, len(result.evidences), len(result.claims), len(result.cards))


if __name__ == '__main__':
    main()
