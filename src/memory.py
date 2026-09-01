"""Structured private/shared memory shared by generic and contest runners."""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, replace
from typing import Iterable, Literal

MemoryKind = Literal["note", "tool_observation"]
MemoryScope = Literal["private", "shared", "all"]


@dataclass(frozen=True)
class MemoryItem:
    memory_id: str
    owner: str
    kind: MemoryKind
    content: str
    created_turn: int
    content_hash: str
    shared: bool = False
    source_memory_id: str | None = None


class MemoryStore:
    """Structured private/shared memory extracted from the ICPC rule session."""

    def __init__(self, agent_names: Iterable[str]):
        self.private: dict[str, dict[str, MemoryItem]] = {
            agent_name: {} for agent_name in agent_names
        }
        self.shared: dict[str, MemoryItem] = {}
        self._private_counter = 0
        self._shared_counter = 0

    def _require_agent(self, agent_name: str) -> dict[str, MemoryItem]:
        if agent_name not in self.private:
            raise KeyError(f"Unknown memory owner: {agent_name}")
        return self.private[agent_name]

    def add(
        self,
        agent_name: str,
        content: str,
        *,
        turn: int,
        kind: MemoryKind = "note",
    ) -> MemoryItem:
        memories = self._require_agent(agent_name)
        content = str(content or "").strip()
        if not content:
            raise ValueError("Memory content cannot be empty.")
        self._private_counter += 1
        item = MemoryItem(
            memory_id=f"M{self._private_counter}",
            owner=agent_name,
            kind=kind,
            content=content,
            created_turn=turn,
            content_hash=hashlib.sha256(content.encode("utf-8")).hexdigest(),
        )
        memories[item.memory_id] = item
        return item

    def publish(
        self, agent_name: str, memory_ids: Iterable[str], *, turn: int
    ) -> list[MemoryItem]:
        memories = self._require_agent(agent_name)
        published: list[MemoryItem] = []
        for raw_id in memory_ids:
            memory_id = str(raw_id).strip()
            source = memories.get(memory_id)
            if source is None:
                raise KeyError(f"{agent_name} does not own memory {memory_id!r}.")
            existing = next(
                (
                    item
                    for item in self.shared.values()
                    if item.source_memory_id == source.memory_id
                    and item.owner == agent_name
                    and item.content_hash == source.content_hash
                ),
                None,
            )
            if existing is not None:
                published.append(existing)
                continue
            self._shared_counter += 1
            item = replace(
                source,
                memory_id=f"S{self._shared_counter}",
                created_turn=turn,
                shared=True,
                source_memory_id=source.memory_id,
            )
            self.shared[item.memory_id] = item
            published.append(item)
        return published

    def recall(
        self,
        agent_name: str,
        query: str = "",
        *,
        scope: MemoryScope = "all",
        top_k: int | None = 8,
    ) -> list[MemoryItem]:
        memories = self._require_agent(agent_name)
        candidates: list[MemoryItem] = []
        if scope in {"private", "all"}:
            candidates.extend(memories.values())
        if scope in {"shared", "all"}:
            candidates.extend(self.shared.values())
        terms = {term.lower() for term in query.split() if len(term) > 1}
        candidates.sort(
            key=lambda item: (
                sum(term in item.content.lower() for term in terms),
                item.created_turn,
            ),
            reverse=True,
        )
        selected: list[MemoryItem] = []
        seen: set[str] = set()
        for item in candidates:
            if item.content_hash in seen:
                continue
            selected.append(item)
            seen.add(item.content_hash)
            if top_k is not None and len(selected) >= max(1, int(top_k)):
                break
        return selected

    @staticmethod
    def render(items: Iterable[MemoryItem]) -> str:
        rows = [
            f"[{item.memory_id}] kind={item.kind} owner={item.owner}\n{item.content}"
            for item in items
        ]
        return "\n\n".join(rows) or "(none)"

    def snapshot(self) -> dict:
        return {
            "private": {
                agent_name: [asdict(item) for item in memories.values()]
                for agent_name, memories in self.private.items()
            },
            "shared": [asdict(item) for item in self.shared.values()],
        }
