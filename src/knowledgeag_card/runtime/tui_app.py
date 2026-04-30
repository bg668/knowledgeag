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
[bold]Commands[/bold]\n
\t/ingest <path>    导入文件或目录\n
\t/review <run_id>  写入任务复盘\n
\t/ask <question>   提问\n
\t/runs             查看最近运行\n
\t/stats            查看统计\n
\t/help             查看帮助\n
\t/quit             退出\n
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
            if text == '/runs':
                self._runs()
                continue
            if text.startswith('/ingest '):
                self._ingest(text.removeprefix('/ingest ').strip())
                continue
            if text.startswith('/review '):
                self._review(text.removeprefix('/review ').strip())
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
        state = _event_state()

        def on_event(event) -> None:
            _update_event_state(state, event)
            live.update(_event_panel(state, title=f'Ingest: {path}'))

        with Live(_event_panel(state, title=f'Ingest: {path}'), console=console, refresh_per_second=10) as live:
            results = self.app.ingest(path, on_event=on_event)
            live.update(_event_panel(state, title=f'Ingest: {path}'))
        table = Table(title=f'Ingested: {path}')
        table.add_column('Source')
        table.add_column('Type')
        table.add_column('Evidences', justify='right')
        table.add_column('Claims', justify='right')
        table.add_column('Cards', justify='right')
        table.add_column('Source Coverage', justify='right')
        table.add_column('Uncovered Sections', justify='right')
        table.add_column('Missing Topics', justify='right')
        for result in results:
            source_coverage = result.source_coverage
            covered_sections = len(source_coverage.covered_sections) if source_coverage else 0
            total_sections = len(source_coverage.source_sections) if source_coverage else 0
            uncovered_sections = len(source_coverage.uncovered_sections) if source_coverage else 0
            table.add_row(
                result.source.title,
                result.source.type.value,
                str(len(result.evidences)),
                str(len(result.claims)),
                str(len(result.cards)),
                f'{covered_sections}/{total_sections}',
                str(uncovered_sections),
                str(len(result.missing_topics)),
            )
        console.print(table)

    def _review(self, run_id: str) -> None:
        result = self.app.review_task(run_id)
        table = Table(title=f'Task Review: {result.source.title}')
        table.add_column('Cards', justify='right')
        table.add_column('Claims', justify='right')
        table.add_column('Evidences', justify='right')
        table.add_column('Card Types')
        table.add_row(
            str(len(result.cards)),
            str(len(result.claims)),
            str(len(result.evidences)),
            ', '.join(card.card_type for card in result.cards),
        )
        console.print(table)

    def _runs(self) -> None:
        runs = self.app.list_runs()
        table = Table(title='Recent Runs')
        table.add_column('Run ID')
        table.add_column('Command')
        table.add_column('Status')
        table.add_column('Started At')
        table.add_column('Ended At')
        for run in runs:
            table.add_row(
                run['run_id'],
                run['command_type'],
                run['status'],
                run['started_at'],
                run.get('ended_at') or '',
            )
        console.print(table)

    def _ask(self, question: str) -> None:
        state = _event_state()

        def on_event(event) -> None:
            _update_event_state(state, event)
            live.update(_event_panel(state, title=f'Q: {question}'))

        with Live(_event_panel(state, title=f'Q: {question}'), console=console, refresh_per_second=10) as live:
            answer = self.app.ask(question, on_event=on_event)
            live.update(_event_panel(state, title=f'Q: {question}'))
        console.print(Panel(answer, title=f'Q: {question}', border_style='blue'))


def main() -> None:
    setup_logging()
    TUI().run()


def _event_state() -> dict:
    return {'run_id': '', 'node': '', 'thinking': '', 'output': ''}


def _update_event_state(state: dict, event) -> None:
    state['run_id'] = event.run_id
    state['node'] = event.node
    if event.kind == 'thinking_delta':
        state['thinking'] = (state['thinking'] + event.text)[-1000:]
    elif event.kind == 'output_delta':
        state['output'] = (state['output'] + event.text)[-1000:]


def _event_panel(state: dict, *, title: str) -> Panel:
    lines = [
        f"[bold]Run[/bold] {state['run_id'] or '-'}",
        f"[bold]Node[/bold] {state['node'] or '-'}",
        '',
        '[bold yellow]Thinking[/bold yellow]',
        state['thinking'] or '[dim]-[/dim]',
        '',
        '[bold cyan]Output[/bold cyan]',
        state['output'] or '[dim]-[/dim]',
    ]
    return Panel('\n'.join(lines), title=title, border_style='cyan')


if __name__ == '__main__':
    main()
