from __future__ import annotations

import sys

from knowledgeag_card.runtime.agent_app import AgentApp


def main() -> None:
    question = sys.argv[1] if len(sys.argv) > 1 else '这个知识库的主对象是什么？'
    app = AgentApp.create()
    print(app.ask(question))


if __name__ == '__main__':
    main()
