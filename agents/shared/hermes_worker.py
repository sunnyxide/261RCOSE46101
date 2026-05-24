"""HermesWorker — adapter that runs lab tasks through the local Hermes CLI.

Hermes is the long-running single-agent substrate (see AUTONOMOUS_INTEGRATION.md
section 2.1). This wrapper:

1. Formats the task as a brief that loads the OpenClaw research_v2 5-slot
   spec at the top, then appends the agent's system prompt + task payload.
2. Invokes Hermes with the known-good provider override pattern from the
   feedback-hermes-provider-override memory (`--provider openai -m gpt-5.4`).
3. Captures stdout + parses the `[meta]` footer for verifiability_signal.
4. Returns artifact paths + a self-reported cost estimate.

Uses asyncio.create_subprocess_exec (argv list, not shell string) so command
injection is impossible — there is no shell interpolation step.

The Hermes binary is assumed installed at `hermes` on PATH and configured
via `~/.hermes/.env` (XIAOMI_API_KEY etc.). This module does NOT manage
Hermes config — that's a one-time setup outside the lab.
"""

from __future__ import annotations

import asyncio
import os
import re
import shlex
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from loguru import logger

from orchestrator.budget import BudgetGuard


HERMES_BIN = os.environ.get("HERMES_BIN", "hermes")
# Provider override per feedback-hermes-provider-override memory:
# default localhost Qwen falls back ungracefully if LM Studio is down; pinning
# to OpenAI gpt-5.4 keeps overnight runs robust.
HERMES_DEFAULT_PROVIDER = os.environ.get("HERMES_PROVIDER", "openai")
HERMES_DEFAULT_MODEL = os.environ.get("HERMES_MODEL", "gpt-5.4")

RESEARCH_V2_PROMPT_PATH = Path(
    os.environ.get(
        "RESEARCH_V2_PROMPT_PATH",
        "/Users/orbt/Desktop/orbt/overnight-agents/prompts/openclaw/research_v2.md",
    )
)

HERMES_TASK_TIMEOUT_SEC = int(os.environ.get("HERMES_TASK_TIMEOUT_SEC", "1800"))


@dataclass
class HermesResult:
    artifact_paths: list[str]
    raw_stdout: str
    verifiability_signal: str  # 'high' | 'medium' | 'low' | 'unknown'
    cost_usd_estimate: float
    duration_sec: float
    exit_code: int


class HermesWorker:
    def __init__(self, budget: BudgetGuard) -> None:
        self.budget = budget
        if not RESEARCH_V2_PROMPT_PATH.exists():
            logger.warning(
                f"research_v2 prompt not found at {RESEARCH_V2_PROMPT_PATH}; "
                f"writer outputs will not load the 5-slot standard. "
                f"Set RESEARCH_V2_PROMPT_PATH to override."
            )

    async def run(
        self,
        agent_name: str,
        system_prompt: str,
        user_brief: str,
        task_id: str,
        artifact_dir: Path,
        attach_research_v2: bool = True,
        provider: str | None = None,
        model: str | None = None,
        timeout_sec: int | None = None,
    ) -> HermesResult:
        """Dispatch one task through Hermes via argv (no shell)."""
        artifact_dir.mkdir(parents=True, exist_ok=True)
        brief_path = artifact_dir / f"{task_id}-brief.md"
        stdout_path = artifact_dir / f"{task_id}-stdout.md"
        provider = provider or HERMES_DEFAULT_PROVIDER
        model = model or HERMES_DEFAULT_MODEL
        timeout_sec = timeout_sec or HERMES_TASK_TIMEOUT_SEC

        brief_text = self._compose_brief(
            agent_name=agent_name,
            system_prompt=system_prompt,
            user_brief=user_brief,
            attach_research_v2=attach_research_v2,
        )
        brief_path.write_text(brief_text)

        argv = [
            HERMES_BIN, "--yolo", "chat",
            "--provider", provider,
            "-m", model,
            "--brief", str(brief_path),
        ]
        logger.info(f"hermes dispatch task={task_id} argv={shlex.join(argv)}")

        start = datetime.now(timezone.utc)
        # NOTE: create_subprocess_exec takes argv as a list — no shell, no
        # injection surface. Equivalent to execFile in Node.js / posix_spawn.
        proc = await asyncio.create_subprocess_exec(
            *argv,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout_b, stderr_b = await asyncio.wait_for(
                proc.communicate(), timeout=timeout_sec
            )
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            raise TimeoutError(
                f"Hermes task {task_id} exceeded {timeout_sec}s; killed."
            )
        duration = (datetime.now(timezone.utc) - start).total_seconds()

        stdout = stdout_b.decode("utf-8", errors="replace")
        stderr = stderr_b.decode("utf-8", errors="replace")
        stdout_path.write_text(stdout)

        if proc.returncode != 0:
            logger.error(
                f"hermes exit={proc.returncode} task={task_id} stderr_tail="
                f"{stderr[-400:]!r}"
            )

        signal = _parse_verifiability_signal(stdout)
        cost = _estimate_cost_usd(brief_text, stdout)
        self.budget.record(
            source=f"hermes-{provider}", usd=cost, task_id=task_id, agent=agent_name
        )

        return HermesResult(
            artifact_paths=[str(brief_path), str(stdout_path)],
            raw_stdout=stdout,
            verifiability_signal=signal,
            cost_usd_estimate=cost,
            duration_sec=duration,
            exit_code=proc.returncode or 0,
        )

    def _compose_brief(
        self,
        *,
        agent_name: str,
        system_prompt: str,
        user_brief: str,
        attach_research_v2: bool,
    ) -> str:
        parts: list[str] = []
        parts.append(
            f"# Hermes brief — agent={agent_name} "
            f"timestamp={datetime.now(timezone.utc).isoformat()}\n"
        )
        # Anti-tool-call-XML guard from feedback-ralph-loop-tuning memory.
        # Hermes is also completion-style for the Plan endpoint; same risk.
        parts.append(
            "**Output protocol:** You have NO tool access in this completion. "
            "Respond with the full markdown deliverable as plain text. Do not "
            "emit `<tool_call>` XML, do not request reads — the brief below "
            "has everything inlined.\n"
        )
        if attach_research_v2 and RESEARCH_V2_PROMPT_PATH.exists():
            parts.append("## Output standard — OpenClaw research_v2 (inlined)\n")
            parts.append(RESEARCH_V2_PROMPT_PATH.read_text())
            parts.append("\n---\n")
        parts.append("## Agent system prompt\n")
        parts.append(system_prompt.strip() + "\n")
        parts.append("\n---\n")
        parts.append("## Task brief\n")
        parts.append(user_brief.strip() + "\n")
        return "\n".join(parts)


VERIFIABILITY_PATTERN = re.compile(r"^verifiability_signal:\s*(\w+)\s*$", re.MULTILINE)


def _parse_verifiability_signal(stdout: str) -> str:
    """Extract verifiability_signal from the [meta] footer.

    Line-anchored per feedback-ralph-loop-tuning memory — relax this to a
    non-anchored search and we accept signals that happen to appear in
    prose, which is wrong.
    """
    m = VERIFIABILITY_PATTERN.search(stdout)
    if not m:
        return "unknown"
    val = m.group(1).lower()
    if val not in {"high", "medium", "low"}:
        return "unknown"
    return val


def _estimate_cost_usd(brief_text: str, stdout_text: str) -> float:
    """Rough cost estimate using gpt-5.4 pricing ($5/$15 per Mtoken in/out).

    Hermes does not yet report token usage. char count / 4 ≈ token count is
    used as a heuristic; for Korean (1 char ≈ 1 token) this over-estimates,
    which is the safe direction for a budget guard.
    """
    in_tokens = len(brief_text) / 4
    out_tokens = len(stdout_text) / 4
    return (in_tokens * 5 + out_tokens * 15) / 1_000_000


async def dispatch(
    agent_name: str,
    system_prompt: str,
    user_brief: str,
    task_id: str,
    artifact_dir: Path,
    budget: BudgetGuard,
    **kwargs,
) -> HermesResult:
    worker = HermesWorker(budget)
    return await worker.run(
        agent_name=agent_name,
        system_prompt=system_prompt,
        user_brief=user_brief,
        task_id=task_id,
        artifact_dir=artifact_dir,
        **kwargs,
    )


def health_check() -> dict[str, object]:
    """Pre-flight: confirm hermes binary + research_v2 prompt are reachable.

    Returns a dict suitable for inclusion in the lab's preflight smoke test.
    Does NOT call the LLM (zero cost).
    """
    import shutil

    bin_path = shutil.which(HERMES_BIN)
    return {
        "hermes_bin": bin_path,
        "hermes_bin_present": bin_path is not None,
        "research_v2_prompt": str(RESEARCH_V2_PROMPT_PATH),
        "research_v2_present": RESEARCH_V2_PROMPT_PATH.exists(),
        "default_provider": HERMES_DEFAULT_PROVIDER,
        "default_model": HERMES_DEFAULT_MODEL,
        "task_timeout_sec": HERMES_TASK_TIMEOUT_SEC,
    }
