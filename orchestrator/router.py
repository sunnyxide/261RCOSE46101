"""Resource router — decides whether a task runs on Mac Mini or AWS, and which AWS account.

Heuristics:
- Anything tagged 'gpu_heavy' → AWS g6e.xlarge.
- Anything tagged 'io_bound' or 'orchestration' → Mac Mini.
- Default → Mac Mini, since it's free.
- AWS instances are spun up on-demand and stopped after the queue empties.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

import boto3

from orchestrator.queue import Task


# Tag conventions per task kind (extend as new kinds are added)
TASK_KIND_TAGS = {
    "layer1_data_collection": {"io_bound", "orchestration"},
    "build_kg": {"io_bound", "compute_medium"},
    "qlora_train": {"gpu_heavy"},
    "batch_inference": {"gpu_heavy"},
    "oasis_simulation": {"orchestration"},  # API calls dominate, not local GPU
    "metric_compute": {"compute_light"},
    "report_draft": {"orchestration"},
    "critic_review": {"orchestration"},
}


@dataclass
class ComputeTarget:
    name: str
    cost_per_hour: float
    notes: str


MAC_MINI = ComputeTarget(name="mac_mini", cost_per_hour=0.0, notes="M4 Pro 48GB, always-on")
AWS_ACCOUNT_A = ComputeTarget(name="aws_account_a", cost_per_hour=1.86, notes="g6e.xlarge L40S")
AWS_ACCOUNT_B = ComputeTarget(name="aws_account_b", cost_per_hour=1.86, notes="g6e.xlarge L40S")


class ResourceRouter:
    def __init__(self) -> None:
        self.region = os.environ.get("AWS_REGION", "us-east-1")
        self._aws_state: dict[str, str] = {}  # account → 'stopped' | 'running'

    def pick(self, task: Task) -> str:
        tags = TASK_KIND_TAGS.get(task.kind, set())
        if "gpu_heavy" in tags:
            return self._pick_aws_account()
        return MAC_MINI.name

    def _pick_aws_account(self) -> str:
        # Simple round-robin between Sunwoo's and Josh's accounts to use both credits.
        # In a fancier version, pick based on remaining credit per account.
        last = self._aws_state.get("last_picked", AWS_ACCOUNT_B.name)
        nxt = AWS_ACCOUNT_A.name if last == AWS_ACCOUNT_B.name else AWS_ACCOUNT_B.name
        self._aws_state["last_picked"] = nxt
        return nxt

    def start_aws_instance(self, account: str) -> None:
        profile = os.environ[f"{account.upper()}_PROFILE"]
        instance_id = os.environ[f"{account.upper()}_INSTANCE_ID"]
        session = boto3.Session(profile_name=profile, region_name=self.region)
        ec2 = session.client("ec2")
        ec2.start_instances(InstanceIds=[instance_id])

    def stop_aws_instance(self, account: str) -> None:
        profile = os.environ[f"{account.upper()}_PROFILE"]
        instance_id = os.environ[f"{account.upper()}_INSTANCE_ID"]
        session = boto3.Session(profile_name=profile, region_name=self.region)
        ec2 = session.client("ec2")
        ec2.stop_instances(InstanceIds=[instance_id])

    def stop_all_aws_instances(self) -> int:
        n = 0
        for account in [AWS_ACCOUNT_A.name, AWS_ACCOUNT_B.name]:
            try:
                self.stop_aws_instance(account)
                n += 1
            except Exception:
                pass
        return n
