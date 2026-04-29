from __future__ import annotations

from typing import Any


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Any] = {}

    def register(self, tool: Any) -> None:
        name = getattr(tool, 'name', None)
        if not isinstance(name, str) or not name.strip():
            raise ValueError('tool must expose a non-empty name')
        self._tools[name] = tool

    def resolve(self, names: list[str] | tuple[str, ...]) -> list[Any]:
        tools = []
        for name in names:
            try:
                tools.append(self._tools[name])
            except KeyError as exc:
                raise KeyError(f'unknown internal tool: {name}') from exc
        return tools
