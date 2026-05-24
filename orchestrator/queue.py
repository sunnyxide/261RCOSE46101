"""SQLite-backed task queue with dependency tracking and idempotent dispatch."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from sqlmodel import Field, Session, SQLModel, create_engine, select


class TaskStatus(str, Enum):
    pending = "pending"
    running = "running"
    complete = "complete"
    failed = "failed"
    escalated = "escalated"  # tier permissions denied, needs human
    paused = "paused"


class TaskRow(SQLModel, table=True):
    __tablename__ = "tasks"
    id: str = Field(primary_key=True)
    kind: str
    agent: str
    tier: int
    priority: str
    status: str = Field(default=TaskStatus.pending.value, index=True)
    depends_on: str = ""  # comma-separated task IDs
    payload_json: str = "{}"
    justification: str | None = None
    enqueued_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: datetime | None = None
    completed_at: datetime | None = None
    outcome_json: str | None = None
    error: str | None = None


class AlertRow(SQLModel, table=True):
    __tablename__ = "alerts"
    id: int | None = Field(default=None, primary_key=True)
    severity: str
    message: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    acknowledged: bool = False


@dataclass
class Task:
    id: str
    kind: str
    agent: str
    tier: int
    priority: str
    payload: dict[str, Any] = field(default_factory=dict)
    justification: str | None = None


PRIORITY_RANK = {"critical": 0, "high": 1, "normal": 2, "low": 3}


class TaskQueue:
    def __init__(self, db_url: str) -> None:
        if not db_url.startswith("sqlite"):
            db_url = f"sqlite:///{db_url}"
        self.engine = create_engine(db_url, connect_args={"check_same_thread": False})

    @staticmethod
    def init(db_path: str = "orchestrator/state.db") -> None:
        engine = create_engine(f"sqlite:///{db_path}")
        SQLModel.metadata.create_all(engine)

    async def enqueue(
        self,
        kind: str,
        agent: str,
        tier: int = 1,
        priority: str = "normal",
        payload: dict[str, Any] | None = None,
        depends_on: list[str] | None = None,
        justification: str | None = None,
    ) -> str:
        task_id = str(uuid.uuid4())
        row = TaskRow(
            id=task_id,
            kind=kind,
            agent=agent,
            tier=tier,
            priority=priority,
            depends_on=",".join(depends_on or []),
            payload_json=json.dumps(payload or {}),
            justification=justification,
        )
        with Session(self.engine) as s:
            s.add(row)
            s.commit()
        return task_id

    async def next_runnable(self) -> Task | None:
        with Session(self.engine) as s:
            pending = s.exec(
                select(TaskRow).where(TaskRow.status == TaskStatus.pending.value)
            ).all()
            for t in sorted(pending, key=lambda x: (PRIORITY_RANK[x.priority], x.enqueued_at)):
                if not t.depends_on:
                    return self._to_task(t)
                deps = t.depends_on.split(",")
                resolved = s.exec(
                    select(TaskRow).where(
                        TaskRow.id.in_(deps),  # type: ignore[union-attr]
                        TaskRow.status == TaskStatus.complete.value,
                    )
                ).all()
                if len(resolved) == len(deps):
                    return self._to_task(t)
        return None

    async def mark_running(self, task_id: str) -> None:
        self._update(task_id, status=TaskStatus.running.value, started_at=datetime.now(timezone.utc))

    async def mark_complete(self, task_id: str, outcome: dict[str, Any]) -> None:
        self._update(
            task_id,
            status=TaskStatus.complete.value,
            completed_at=datetime.now(timezone.utc),
            outcome_json=json.dumps(outcome, default=str),
        )

    async def mark_failed(self, task_id: str, error: str) -> None:
        self._update(task_id, status=TaskStatus.failed.value, error=error)

    async def escalate(self, task: Task) -> None:
        self._update(task.id, status=TaskStatus.escalated.value)

    async def pause_all(self) -> int:
        with Session(self.engine) as s:
            running = s.exec(select(TaskRow).where(TaskRow.status == TaskStatus.running.value)).all()
            for t in running:
                t.status = TaskStatus.paused.value
                s.add(t)
            s.commit()
            return len(running)

    async def summary(self) -> list[dict[str, Any]]:
        with Session(self.engine) as s:
            rows = s.exec(select(TaskRow)).all()
        grouped: dict[str, list[TaskRow]] = {}
        for r in rows:
            grouped.setdefault(r.status, []).append(r)
        return [
            {
                "state": k,
                "count": len(v),
                "oldest": min(r.enqueued_at for r in v) if v else None,
                "newest": max(r.enqueued_at for r in v) if v else None,
            }
            for k, v in grouped.items()
        ]

    async def enqueue_alert(self, severity: str, message: str) -> None:
        with Session(self.engine) as s:
            s.add(AlertRow(severity=severity, message=message))
            s.commit()

    # ---- internals ----
    def _update(self, task_id: str, **fields: Any) -> None:
        with Session(self.engine) as s:
            row = s.get(TaskRow, task_id)
            if row is None:
                raise KeyError(task_id)
            for k, v in fields.items():
                setattr(row, k, v)
            s.add(row)
            s.commit()

    def _to_task(self, row: TaskRow) -> Task:
        return Task(
            id=row.id,
            kind=row.kind,
            agent=row.agent,
            tier=row.tier,
            priority=row.priority,
            payload=json.loads(row.payload_json),
            justification=row.justification,
        )


if __name__ == "__main__":
    import typer

    typer.run(lambda: TaskQueue.init())
