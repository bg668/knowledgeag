from __future__ import annotations

from pathlib import Path

from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from knowledgeag_card.app.logging import setup_logging
from knowledgeag_card.runtime.agent_app import AgentApp

console = Console()

HELP = """
[bold]Commands[/bold]
/ingest <path>    导入文件或目录
/ask <question>   提问
/stats            查看统计
/help             查看帮助
/quit             退出
"""


class TUI:
    def __init__(self) -> None:
        self.app = AgentApp.create()

    def run(self) -> None:
        console.print(Panel.fit('KnowledgeCard-first knowledgeag', border_style='cyan'))
        console.print(Markdown(HELP))
        while True:
            try:
                text = Prompt.ask('[bold green]knowledgeag-card[/bold green]').strip()
            except (KeyboardInterrupt, EOFError):
                console.print('\nBye')
                return
            if not text:
                continue
            if text == '/quit':
                console.print('Bye')
                return
            if text == '/help':
                console.print(Markdown(HELP))
                continue
            if text == '/stats':
                self._stats()
                continue
            if text.startswith('/ingest '):
                self._ingest(text.removeprefix('/ingest ').strip())
                continue
            if text.startswith('/ask '):
                self._ask(text.removeprefix('/ask ').strip())
                continue
            self._ask(text)

    def _stats(self) -> None:
        stats = self.app.stats()
        table = Table(title='Storage Stats')
        table.add_column('Metric')
        table.add_column('Value', justify='right')
        table.add_row('Sources', str(stats.sources))
        table.add_row('Evidences', str(stats.evidences))
        table.add_row('Claims', str(stats.claims))
        table.add_row('Cards', str(stats.cards))
        console.print(table)

    def _ingest(self, path: str) -> None:
        if not Path(path).exists():
            console.print(Panel.fit(f'Path not found: {path}', border_style='red'))
            return
        results = self.app.ingest(path)
        table = Table(title=f'Ingested: {path}')
        table.add_column('Source')
        table.add_column('Type')
        table.add_column('Evidences', justify='right')
        table.add_column('Claims', justify='right')
        table.add_column('Cards', justify='right')
        for result in results:
            table.add_row(
                result.source.title,
                result.source.type.value,
                str(len(result.evidences)),
                str(len(result.claims)),
                str(len(result.cards)),
            )
        console.print(table)

    def _ask(self, question: str) -> None:
        buffer: list[str] = []
        placeholder = '[dim]Thinking...[/dim]'

        def on_delta(delta: str) -> None:
            buffer.append(delta)
            live.update(Panel(''.join(buffer) or placeholder, title=f'Q: {question}', border_style='cyan'))

        with Live(Panel(placeholder, title=f'Q: {question}', border_style='cyan'), console=console, refresh_per_second=10) as live:
            answer = self.app.ask(question, on_delta=on_delta if self.app.backend_name == 'paimon' else None)
            if self.app.backend_name != 'paimon':
                live.update(Panel(answer, title=f'Q: {question}', border_style='blue'))
        console.print(Panel(answer, title=f'Q: {question}', border_style='blue'))


def main() -> None:
    setup_logging()
    TUI().run()


if __name__ == '__main__':
    main()
