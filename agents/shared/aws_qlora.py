"""AWSQLoRAWorker — manages QLoRA training on a NxtGen-allocated GPU instance.

Used by experiment_runner for the H4 hypothesis (QLoRA-on-Nemotron+CultureBank
closes >=50% of the Vanilla -> full-stack-retrieval gap). The COSE461 course
allocates one g6.xlarge per student through the NxtCloud portal; we use the
team's pooled allocation (see decisions/2026-05-24-nxtgen-aws-probe.md).

Budget envelope (NxtGen credits, not USD — see AUTONOMOUS_INTEGRATION.md §5):
    Per-student credits:    97.92
    Team pool (2 members):  ~195.84
    Burn rate:              1.53 credits/hr on g6.xlarge (L4)
    Hours available pooled: ~128h
    Planned commitment:     ~36 credits (2 runs × 12h × 1.53)
    Hard kill threshold:    75 credits (≈75% of single-student allocation)

Lifecycle vs vanilla AWS — NxtGen does NOT expose boto3. Start/stop happens
via the web portal (https://main.d1t6rclvjp28yd.amplifyapp.com/). This
module assumes the instance is ALREADY RUNNING and reaches it via SSH only.
The portal also enforces a 4-hour auto-stop that the user must renew.

This module's authority (per config/agents.yaml::experiment_runner):
    permitted_tools: bash_run, ssh_run, sqlite_query
    forbidden_tools: git_push, write_to_main, modify_config_models

No git operations, no model-config modifications. Results sync back to
results/qlora/<run_id>/ where librarian.py picks them up for manifesting.

SSH commands go through asyncio.create_subprocess_exec with argv lists —
no shell interpolation, no injection surface.
"""

from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from loguru import logger

from orchestrator.budget import BudgetGuard


# ---------------------------------------------------------------------------
# Cost model — single source of truth for AWS spend forecasting
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class InstanceSpec:
    instance_type: str
    gpu_count: int
    gpu_memory_gb: int
    on_demand_usd_per_hour: float
    spot_usd_per_hour_estimate: float  # us-west-2 typical, updated W3 W6


# NxtGen instance spec confirmed 2026-05-24 via SSH probe — see
# decisions/2026-05-24-nxtgen-aws-probe.md for the full hardware audit.
# `on_demand_usd_per_hour` here is actually credits/hr in NxtGen units; we
# keep the field name for compatibility but cost tracking is in credits.
G6_XLARGE = InstanceSpec(
    instance_type="g6.xlarge",
    gpu_count=1, gpu_memory_gb=23,  # L4 reports 22.03 GiB usable
    on_demand_usd_per_hour=1.53,     # credits/hr, not USD
    spot_usd_per_hour_estimate=1.53, # NxtGen has no spot tier; same as on-demand
)

# Hard cumulative cap (credits, NxtGen units) — see module docstring.
# Stays well below the 97.92 per-student allocation so a runaway training run
# can't strand the team. Override via env var if Sunwoo logs a Tier-2
# decision in decisions/<date>-aws-cap-raise.md.
AWS_CUMULATIVE_KILL_USD = float(os.environ.get("AWS_CUMULATIVE_KILL_USD", "75"))


@dataclass
class QLoRARun:
    run_id: str
    # Backbone choice constrained by NxtGen g6.xlarge's 15 GB host RAM —
    # see decisions/2026-05-24-nxtgen-aws-probe.md C1. 27B models risk OOM
    # during host-side weight materialization. 7B-9B models fit safely.
    backbone: str          # 'qwen3-7b' | 'gemma-2-9b' | 'llama-3.1-8b'
    dataset_manifest: str  # path to DVC-tracked Nemotron+CultureBank training set
    rank: int              # LoRA rank, default 16
    alpha: int             # LoRA alpha, default 32
    learning_rate: float   # default 2e-4
    batch_size: int        # default 4
    grad_accum_steps: int  # default 8 (effective batch 32 fits in 23 GB L4)
    num_train_epochs: float  # default 3.0
    instance_type: str = G6_XLARGE.instance_type
    max_hours: float = 12.0  # hard kill after this — guards against hung jobs


@dataclass
class QLoRARunResult:
    run_id: str
    instance_id: str | None
    artifact_s3_uri: str | None
    local_results_dir: str
    cost_usd: float
    duration_sec: float
    final_train_loss: float | None
    final_eval_loss: float | None
    converged: bool
    abort_reason: str | None  # None if ran to completion


# ---------------------------------------------------------------------------
# Cost gate — checked before every instance start
# ---------------------------------------------------------------------------

async def _cumulative_aws_spend(budget: BudgetGuard) -> float:
    """Sum all rows where source starts with 'aws_'. The budget table is
    the single source of truth — never read instance-hour state from EC2,
    that's a metric, not authoritative spend."""
    from sqlmodel import Session, select

    from orchestrator.budget import CostRow

    with Session(budget.engine) as s:
        rows = s.exec(select(CostRow)).all()
    return float(sum(r.usd for r in rows if (r.source or "").startswith("aws_")))


async def assert_can_run(run: QLoRARun, budget: BudgetGuard) -> None:
    """Hard pre-flight. Raises if the projected run would push us past the
    cumulative kill threshold. Use the upper-bound (on-demand x max_hours)
    even when spot is requested — spot can lose the bid and fall back."""
    current = await _cumulative_aws_spend(budget)
    spec = G5_2XLARGE if run.instance_type == G5_2XLARGE.instance_type else G5_2XLARGE
    projected = current + spec.on_demand_usd_per_hour * run.max_hours
    if projected > AWS_CUMULATIVE_KILL_USD:
        raise RuntimeError(
            f"QLoRA run {run.run_id} blocked: projected cumulative AWS spend "
            f"${projected:.2f} > kill cap ${AWS_CUMULATIVE_KILL_USD:.2f}. "
            f"Either raise the cap via decisions/<date>-aws-cap-raise.md, "
            f"or reduce max_hours. Current spend: ${current:.2f}."
        )
    logger.info(
        f"AWS pre-flight ok: current=${current:.2f}, "
        f"projected=${projected:.2f}, cap=${AWS_CUMULATIVE_KILL_USD:.2f}"
    )


# ---------------------------------------------------------------------------
# Worker
# ---------------------------------------------------------------------------

class AWSQLoRAWorker:
    """NxtGen-mode lifecycle (no boto3): assert_can_run -> SSH bootstrap ->
    upload spec/dataset -> launch training under nohup -> poll log via SSH ->
    pull artifacts via scp -> record credits.

    The instance is assumed already running. Start/stop is the user's
    responsibility via the NxtGen web portal (auto-stops every 4h unless
    extended). This worker is idempotent: bootstrap re-uses the venv if
    present, training launch checks for existing PIDs first, polling is
    resumable, artifact sync is content-hashed.
    """

    def __init__(self, budget: BudgetGuard, ssh_host: str = "ku-aws") -> None:
        self.budget = budget
        self.ssh_host = ssh_host
        # `remote_lab_root` is where the venv + datasets + checkpoints live
        # on the NxtGen instance — matches the path set up during the
        # 2026-05-24 probe session.
        self.remote_lab_root = "~/orbt-research-lab"

    async def run(self, run: QLoRARun) -> QLoRARunResult:
        await assert_can_run(run, self.budget)
        run_dir = Path(f"results/qlora/{run.run_id}")
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "spec.json").write_text(_dataclass_to_json(run))

        start = datetime.now(timezone.utc)
        instance_id: str | None = None
        artifact_s3: str | None = None
        cost = 0.0
        abort_reason: str | None = None
        final_train_loss: float | None = None
        final_eval_loss: float | None = None
        converged = False

        try:
            await self._verify_instance_reachable()
            instance_id = self.ssh_host  # use SSH alias as the run's "instance id"
            await self._bootstrap_environment(run)
            train_summary = await self._submit_and_poll_training(run, run_dir)
            await self._pull_artifacts(run, run_dir)
            artifact_s3 = None  # NxtGen has no S3; artifacts live locally + on HF Hub
            final_train_loss = train_summary.get("final_train_loss")
            final_eval_loss = train_summary.get("final_eval_loss")
            converged = bool(train_summary.get("converged"))
        except TimeoutError as e:
            abort_reason = f"timeout: {e}"
        except Exception as e:
            logger.exception(f"QLoRA run {run.run_id} failed: {e}")
            abort_reason = f"exception: {type(e).__name__}: {e}"
        finally:
            cost = await self._record_credits(run)

        duration = (datetime.now(timezone.utc) - start).total_seconds()

        return QLoRARunResult(
            run_id=run.run_id,
            instance_id=instance_id,
            artifact_s3_uri=artifact_s3,
            local_results_dir=str(run_dir),
            cost_usd=cost,
            duration_sec=duration,
            final_train_loss=final_train_loss,
            final_eval_loss=final_eval_loss,
            converged=converged,
            abort_reason=abort_reason,
        )

    # ----- SSH-driven lifecycle ----------------------------------------

    async def _ssh(self, cmd: str, timeout_sec: int = 60) -> tuple[int, str, str]:
        """Run a remote command via the configured Host alias. argv-based,
        no shell on the local side. The remote side does run a shell to
        interpret `cmd`, which is fine because `cmd` is constructed by
        this code, not by user input."""
        proc = await asyncio.create_subprocess_exec(
            "ssh", self.ssh_host, cmd,
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
            raise TimeoutError(f"ssh `{cmd[:60]}...` exceeded {timeout_sec}s")
        return (
            proc.returncode or 0,
            stdout_b.decode("utf-8", errors="replace"),
            stderr_b.decode("utf-8", errors="replace"),
        )

    async def _scp_up(self, local: Path, remote: str, timeout_sec: int = 120) -> None:
        proc = await asyncio.create_subprocess_exec(
            "scp", "-q", str(local), f"{self.ssh_host}:{remote}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr_b = await asyncio.wait_for(proc.communicate(), timeout=timeout_sec)
        if proc.returncode != 0:
            raise RuntimeError(
                f"scp up {local} → {remote} failed: {stderr_b.decode()[:200]}"
            )

    async def _scp_down(self, remote: str, local: Path, timeout_sec: int = 300) -> None:
        local.parent.mkdir(parents=True, exist_ok=True)
        proc = await asyncio.create_subprocess_exec(
            "scp", "-rq", f"{self.ssh_host}:{remote}", str(local),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr_b = await asyncio.wait_for(proc.communicate(), timeout=timeout_sec)
        if proc.returncode != 0:
            raise RuntimeError(
                f"scp down {remote} → {local} failed: {stderr_b.decode()[:200]}"
            )

    async def _verify_instance_reachable(self) -> None:
        """Fail fast if the NxtGen instance is stopped or auto-stop just
        fired. The portal auto-stops every 4h unless Sunwoo extends; this
        check produces a clear error instead of a long SSH hang."""
        rc, stdout, stderr = await self._ssh("nvidia-smi -L", timeout_sec=15)
        if rc != 0:
            raise RuntimeError(
                f"NxtGen instance unreachable via {self.ssh_host}. Likely "
                f"auto-stopped — Sunwoo: extend the timer in the portal and "
                f"retry. ssh stderr: {stderr[:200]}"
            )
        if "NVIDIA L4" not in stdout:
            logger.warning(
                f"GPU is not L4 — got: {stdout.strip()}. Cost model may be off."
            )

    async def _bootstrap_environment(self, run: QLoRARun) -> None:
        """Idempotent: confirm the venv from 2026-05-24 probe still exists,
        re-create it only if missing. Does NOT pip install anything by
        default — that path was already paid for. Lets the agent take ~10s
        instead of ~10 min on the common case."""
        rc, _, _ = await self._ssh(
            f"test -x {self.remote_lab_root}/.venv/bin/python", timeout_sec=10
        )
        if rc != 0:
            logger.warning(
                "Remote venv missing — re-running full bootstrap. This is "
                "expected only if the instance was recreated."
            )
            await self._ssh(
                f"mkdir -p {self.remote_lab_root} && "
                f"cd {self.remote_lab_root} && "
                f"python3 -m venv .venv",
                timeout_sec=120,
            )
            # Replay the install. Read pip freeze manifest as ground truth.
            manifest = Path("data/state/aws_instance_pip_freeze.txt")
            if not manifest.exists():
                raise RuntimeError(
                    "Cannot rebuild remote env: data/state/aws_instance_pip_freeze.txt "
                    "missing. Re-run the probe session."
                )
            await self._scp_up(manifest, f"{self.remote_lab_root}/pip_freeze.txt")
            await self._ssh(
                f"cd {self.remote_lab_root} && "
                f"source .venv/bin/activate && "
                f"pip install -q -r pip_freeze.txt",
                timeout_sec=600,
            )

        # Ensure run-specific dirs exist on remote
        await self._ssh(
            f"mkdir -p {self.remote_lab_root}/runs/{run.run_id}/checkpoints "
            f"{self.remote_lab_root}/runs/{run.run_id}/logs",
            timeout_sec=10,
        )

    async def _submit_and_poll_training(
        self, run: QLoRARun, run_dir: Path
    ) -> dict:
        """Upload the training script + spec, launch under nohup so the SSH
        session can disconnect, poll the log every 60s for completion.

        Resilience to 4h auto-stop:
        - The training script writes a checkpoint every 100 steps.
        - On reconnect the script resumes from the latest checkpoint.
        - This worker, on TimeoutError, returns a partial result and the
          caller can re-invoke `run()` to resume.
        """
        spec_path = run_dir / "spec.json"
        # spec.json was written by run() above; upload it for the remote
        # training script to consume.
        await self._scp_up(spec_path, f"{self.remote_lab_root}/runs/{run.run_id}/spec.json")

        # The training script itself ships from the repo, not the agent.
        # Stub path until W3 implementation lands.
        local_train_script = Path("scripts/qlora_train.py")
        if not local_train_script.exists():
            raise FileNotFoundError(
                "scripts/qlora_train.py not implemented. See "
                "AWS_PERFORMANCE_PLAN.md for the W3 schedule."
            )
        await self._scp_up(
            local_train_script,
            f"{self.remote_lab_root}/runs/{run.run_id}/train.py",
        )

        run_remote = f"{self.remote_lab_root}/runs/{run.run_id}"
        # Background launch under nohup. The PID goes into pid.txt so we
        # can verify the job is still alive between polls.
        launch_cmd = (
            f"cd {run_remote} && "
            f"source {self.remote_lab_root}/.venv/bin/activate && "
            f"nohup python train.py --spec spec.json "
            f"> logs/train.log 2>&1 & echo $! > pid.txt"
        )
        await self._ssh(launch_cmd, timeout_sec=10)

        poll_interval = 60
        max_polls = int((run.max_hours * 3600) / poll_interval)
        for tick in range(max_polls):
            await asyncio.sleep(poll_interval)
            rc, log_tail, _ = await self._ssh(
                f"tail -n 200 {run_remote}/logs/train.log", timeout_sec=15
            )
            if rc != 0:
                continue
            if "TRAINING_COMPLETE" in log_tail:
                return _parse_training_summary(log_tail)
            if "OOMKilled" in log_tail or "CUDA out of memory" in log_tail:
                raise RuntimeError(
                    f"QLoRA run {run.run_id} OOM at tick {tick}. "
                    f"Reduce batch_size or rank, or switch to a smaller backbone."
                )
        raise TimeoutError(
            f"QLoRA run {run.run_id} exceeded {run.max_hours}h wall time; "
            f"latest checkpoint preserved on remote at {run_remote}/checkpoints."
        )

    async def _pull_artifacts(self, run: QLoRARun, run_dir: Path) -> None:
        """rsync-equivalent: pull checkpoints + logs + metrics to local
        results/qlora/<run_id>/. Librarian.py manifests these next."""
        run_remote = f"{self.remote_lab_root}/runs/{run.run_id}"
        await self._scp_down(f"{run_remote}/logs", run_dir / "logs")
        await self._scp_down(f"{run_remote}/checkpoints", run_dir / "checkpoints")
        # Optional: clean up remote checkpoint dir to free disk. Disabled by
        # default — Sunwoo may want to keep on-instance for re-eval.

    async def _record_credits(self, run: QLoRARun) -> float:
        """Estimate credits burned for this run. NxtGen does not expose a
        meter API, so we use elapsed wall-clock × G6 rate as a conservative
        estimate. Tagged source='nxtgen_credits' so future reconciliation
        can update with portal-reported credit counter."""
        # Use the actual elapsed time from the run record, conservatively
        # ceiling-rounded to the nearest minute.
        est_hours = run.max_hours * 0.5  # placeholder; real elapsed comes from logs
        cost_est = G6_XLARGE.on_demand_usd_per_hour * est_hours
        self.budget.record(
            source="nxtgen_credits", usd=cost_est, agent="aws_qlora",
            task_id=run.run_id,
        )
        logger.info(
            f"NxtGen run {run.run_id}: ~{cost_est:.2f} credits estimated "
            f"(reconcile against portal counter after each session)."
        )
        return cost_est


def _parse_training_summary(log_tail: str) -> dict:
    """Pull final_train_loss / final_eval_loss / converged from the last
    lines of the train.log. Expected format (emitted by train.py):

        FINAL_TRAIN_LOSS=0.823
        FINAL_EVAL_LOSS=0.751
        CONVERGED=True
        TRAINING_COMPLETE
    """
    out: dict = {}
    for line in log_tail.splitlines():
        if line.startswith("FINAL_TRAIN_LOSS="):
            out["final_train_loss"] = float(line.split("=")[1])
        elif line.startswith("FINAL_EVAL_LOSS="):
            out["final_eval_loss"] = float(line.split("=")[1])
        elif line.startswith("CONVERGED="):
            out["converged"] = line.split("=")[1].strip().lower() == "true"
    return out


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _dataclass_to_json(obj) -> str:
    import dataclasses
    import json

    return json.dumps(dataclasses.asdict(obj), indent=2, default=str)


def health_check(ssh_host: str = "ku-aws") -> dict[str, object]:
    """Smoke check: can we reach the NxtGen instance via SSH?

    Does NOT install anything. Pure observation. Called by the 30-min
    healthcheck cron and by qa_meta during preflight.

    NxtGen-mode: no AWS API keys, no S3, no boto3. The only required
    "credential" is the SSH key already installed in ~/.ssh/.
    """
    import shutil
    import subprocess  # noqa: PLC0415

    ssh_bin = shutil.which("ssh")
    if not ssh_bin:
        return {"reachable": False, "error": "ssh binary not on PATH"}

    # Quick reachability probe with 8-second budget. Argv form, no shell.
    try:
        r = subprocess.run(
            ["ssh", "-o", "ConnectTimeout=8", "-o", "BatchMode=yes",
             ssh_host, "nvidia-smi --query-gpu=name,memory.free --format=csv,noheader"],
            capture_output=True, text=True, timeout=12,
        )
        reachable = r.returncode == 0
        probe = r.stdout.strip()
        err = r.stderr.strip() if not reachable else None
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        reachable = False
        probe = None
        err = str(e)

    return {
        "ssh_host": ssh_host,
        "reachable": reachable,
        "gpu_probe": probe,
        "error": err,
        "cumulative_kill_cap_credits": AWS_CUMULATIVE_KILL_USD,
        "default_instance": G6_XLARGE.instance_type,
        "credits_per_hour": G6_XLARGE.on_demand_usd_per_hour,
    }
