"""Budget guard — tracks LLM and compute spend, hard-kills if daily cap breached.

Costs are recorded by each agent at the end of every task; the guard
aggregates them and compares against thresholds set in .env. AWS instance
hours are sampled hourly from the EC2 API.

This is a load-bearing safety component — keep it boring and well-tested.
"""

from __future__ import annotations

import os
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlmodel import Field, Session, SQLModel, create_engine, select


class CostRow(SQLModel, table=True):
    __tablename__ = "costs"
    id: int | None = Field(default=None, primary_key=True)
    when: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)
    source: str  # 'openai' | 'anthropic' | 'aws_ec2' | 'huggingface' | etc.
    task_id: str | None = None
    agent: str | None = None
    usd: float


@dataclass
class BudgetReport:
    today_usd: float
    week_usd: float
    total_usd: float
    daily_limit: float
    weekly_limit: float
    total_limit: float

    @property
    def headroom_today(self) -> float:
        return self.daily_limit - self.today_usd


class BudgetGuard:
    def __init__(self) -> None:
        db = os.environ["ORCHESTRATOR_DB"]
        if not db.startswith("sqlite"):
            db = f"sqlite:///{db}"
        self.engine = create_engine(db, connect_args={"check_same_thread": False})
        self.daily_limit = float(os.environ["DAILY_BUDGET_LIMIT"])
        self.weekly_limit = float(os.environ["WEEKLY_BUDGET_LIMIT"])
        self.total_limit = float(os.environ["TOTAL_BUDGET_LIMIT"])
        self.emergency_threshold = float(os.environ.get("EMERGENCY_STOP_THRESHOLD", "0.90"))

    @staticmethod
    def init() -> None:
        db = os.environ["ORCHESTRATOR_DB"]
        engine = create_engine(f"sqlite:///{db}")
        SQLModel.metadata.create_all(engine)

    def record(self, source: str, usd: float, task_id: str | None = None, agent: str | None = None) -> None:
        with Session(self.engine) as s:
            s.add(CostRow(source=source, usd=usd, task_id=task_id, agent=agent))
            s.commit()

    async def is_within_daily_limit(self) -> bool:
        return (await self.report()).today_usd < self.daily_limit

    async def assert_within_limits(self) -> None:
        r = await self.report()
        assert r.today_usd < self.daily_limit, f"Daily limit breached: ${r.today_usd:.2f}"
        assert r.total_usd < self.total_limit, f"Total limit breached: ${r.total_usd:.2f}"

    async def report(self) -> BudgetReport:
        now = datetime.now(timezone.utc)
        with Session(self.engine) as s:
            rows = s.exec(select(CostRow)).all()
        today = sum(r.usd for r in rows if r.when.date() == now.date())
        week = sum(r.usd for r in rows if r.when >= now - timedelta(days=7))
        total = sum(r.usd for r in rows)
        return BudgetReport(
            today_usd=today,
            week_usd=week,
            total_usd=total,
            daily_limit=self.daily_limit,
            weekly_limit=self.weekly_limit,
            total_limit=self.total_limit,
        )

    async def report_text(self) -> str:
        r = await self.report()
        return (
            f"Budget: today ${r.today_usd:.2f}/${r.daily_limit:.0f}  "
            f"week ${r.week_usd:.2f}/${r.weekly_limit:.0f}  "
            f"total ${r.total_usd:.2f}/${r.total_limit:.0f}"
        )
