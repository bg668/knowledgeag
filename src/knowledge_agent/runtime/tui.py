from __future__ import annotations

from pathlib import Path

from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from knowledge_agent.app.logging import setup_logging
from knowledge_agent.runtime.agent_app import AgentApp

console = Console()


HELP_TEXT = """
[bold]Commands[/bold]
/help               查看帮助
/ingest <path>      导入文件或目录
/ask <question>     提问
/stats              查看统计
/quit               退出

直接输入普通文本，也会按问题处理。
"""


def render_welcome(app: AgentApp) -> None:
    console.print(
        Panel.fit(
            (
                "[bold cyan]Knowledge Agent[/bold cyan]\n"
                "最小闭环 TUI：导入资料、检索 Claim、回拉 Evidence、输出答案\n"
                f"当前后端：[bold]{app.backend_name}[/bold]"
            ),
            border_style="cyan",
        )
    )
    console.print(Markdown(HELP_TEXT))


class TUI:
    def __init__(self) -> None:
        self.app = AgentApp()

    def run(self) -> None:
        render_welcome(self.app)
        while True:
            try:
                text = Prompt.ask("[bold green]knowledge-agent[/bold green]").strip()
            except (KeyboardInterrupt, EOFError):
                console.print("\n👋 Bye")
                return

            if not text:
                continue

            if text == "/quit":
                console.print("👋 Bye")
                return
            if text == "/help":
                console.print(Markdown(HELP_TEXT))
                continue
            if text == "/stats":
                self._show_stats()
                continue
            if text.startswith("/ingest "):
                self._ingest(text.removeprefix("/ingest ").strip())
                continue
            if text.startswith("/ask "):
                self._ask(text.removeprefix("/ask ").strip())
                continue

            self._ask(text)

    def _show_stats(self) -> None:
        stats = self.app.stats()
        table = Table(title="Storage Stats")
        table.add_column("Metric")
        table.add_column("Value", justify="right")
        table.add_row("Sources", str(stats.sources))
        table.add_row("Evidences", str(stats.evidences))
        table.add_row("Claims", str(stats.claims))
        console.print(table)

    def _ingest(self, path: str) -> None:
        path_obj = Path(path)
        if not path_obj.exists():
            console.print(Panel.fit(f"路径不存在：{path}", border_style="red"))
            return
        results = self.app.ingest(path)
        table = Table(title=f"Ingested: {path}")
        table.add_column("Source")
        table.add_column("Type")
        table.add_column("Evidences", justify="right")
        table.add_column("Claims", justify="right")
        for result in results:
            table.add_row(
                result.source.title,
                result.source.type.value,
                str(len(result.evidences)),
                str(len(result.claims)),
            )
        console.print(table)

    def _ask(self, question: str) -> None:
        if self.app.backend_name != "paimonsdk":
            answer = self.app.ask(question)
            console.print(Panel(answer, title=f"Q: {question}", border_style="blue"))
            return

        buffer: list[str] = []
        placeholder = "[dim]Thinking...[/dim]"

        def on_delta(delta: str) -> None:
            buffer.append(delta)
            live.update(
                Panel(
                    "".join(buffer) or placeholder,
                    title=f"Q: {question}",
                    border_style="cyan",
                )
            )

        with Live(
            Panel(placeholder, title=f"Q: {question}", border_style="cyan"),
            console=console,
            refresh_per_second=12,
        ) as live:
            answer = self.app.ask(question, on_delta=on_delta)

        console.print(Panel(answer, title=f"Q: {question}", border_style="blue"))


def main() -> None:
    setup_logging()
    TUI().run()


if __name__ == "__main__":
    main()
