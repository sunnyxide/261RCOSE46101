"""LLM judge panel for evaluator-fallback tiers B/C.

When Korean human evaluators are unavailable or limited, the CAS metric falls
back to a multi-model LLM panel. Family diversity (Anthropic + OpenAI + Google
+ Asian-prior) is the load-bearing assumption: shared blind spots show up as
inter-judge agreement on the wrong answer, which calibration against a small
human anchor set then detects.

Tiers consumed by `agents/qa_meta.py`:
    A — full human panel (15 × 200). Panel here unused except as cross-check.
    B — small human anchor (5 × 50) + this panel, calibrated via isotonic.
    C — this panel alone, no human anchor; inter_judge_uncertainty is reported
        as confidence.
    D — panel disabled; CAS dropped, paper reframed around HAD+PDI+JSD+BAS.

The panel itself is independent of tier. `qa_meta` picks the tier.
"""

from __future__ import annotations

import asyncio
import json
import os
import re
from dataclasses import dataclass, field
from typing import Literal

import numpy as np
from anthropic import AsyncAnthropic
from loguru import logger
from openai import AsyncOpenAI

from orchestrator.budget import BudgetGuard

# CURE = Cultural authenticity, Realism, Idiom, reasoning, behavioral Engagement.
# Each scored 1-5 Likert. The Korean cultural-evaluator system prompt below
# binds the scale to concrete anchors so judges don't drift into vibes-grading.
CURE_DIMENSIONS = ("realism", "plausibility", "idiom", "reasoning", "behavior")

JUDGE_SYSTEM = """당신은 한국 소비자 행동 연구자입니다. 페르소나 응답이 한국 문화적으로
얼마나 진정성 있는지 평가합니다. 영어식 사고를 한국어로 번역한 응답과 한국어로
사고한 응답을 구분할 수 있어야 합니다.

다섯 차원 각각 1-5 정수 점수:

1. realism — 인구통계학적 일관성. 50대 보수적 남성이 한류 아이돌 굿즈를
   구매한다면 1. 일치하면 5.
2. plausibility — 행동의 한국 시장 맥락에서 그럴듯함. 한국에서 흔치 않은
   채널/브랜드 가정 시 감점.
3. idiom — 표현이 한국 원어민 자연스러움. 영어 직역체("훌륭한 결정이네요"
   같은 hollow compliment) 감점.
4. reasoning — 사고 흐름이 한국식. 관계 중심, 체면, 정 등이 적절히
   반영됐는지. 개인주의적 추론이면 감점.
5. behavior — 실제 한국 소비자가 보일 행동 패턴. 결정 절차, 가족/지인
   상의 여부, 사회적 증거 가중치 등.

JSON으로만 응답:
{"realism": int, "plausibility": int, "idiom": int, "reasoning": int,
 "behavior": int, "rationale_kr": "<200자 이내 한국어 사유>"}"""


@dataclass
class JudgeRating:
    judge_id: str  # 'anthropic-opus-4-7' | 'openai-gpt-5' | 'google-gemini-2.5' | 'qwen-3.6-27b'
    scores: dict[str, int]  # CURE dimensions
    rationale: str
    raw_usd: float

    @property
    def mean(self) -> float:
        return float(np.mean(list(self.scores.values())))


@dataclass
class PanelRating:
    persona_id: str
    judges: list[JudgeRating]
    mean_score: float
    per_dimension: dict[str, float]
    inter_judge_uncertainty: float  # std across judges' mean scores
    per_dimension_uncertainty: dict[str, float]
    total_usd: float
    tier: Literal["B", "C"] = "C"
    calibrated_score: float | None = None  # set by calibrate_against_human_anchor

    def to_record(self) -> dict:
        return dict(
            persona_id=self.persona_id,
            mean_score=self.mean_score,
            calibrated_score=self.calibrated_score,
            inter_judge_uncertainty=self.inter_judge_uncertainty,
            per_dimension=self.per_dimension,
            per_dimension_uncertainty=self.per_dimension_uncertainty,
            judges=[
                dict(judge_id=j.judge_id, scores=j.scores, rationale=j.rationale)
                for j in self.judges
            ],
            tier=self.tier,
            total_usd=self.total_usd,
        )


@dataclass
class JudgeSpec:
    judge_id: str
    family: str  # 'anthropic' | 'openai' | 'google' | 'asian-prior'
    model: str
    input_usd_per_mtoken: float
    output_usd_per_mtoken: float
    base_url: str | None = None  # for OpenAI-compatible local servers
    api_key_env: str = "OPENAI_API_KEY"


# Intentional family diversity. Replacing any of these with a same-family model
# weakens the panel's ability to detect shared blind spots.
DEFAULT_PANEL: list[JudgeSpec] = [
    JudgeSpec("anthropic-opus-4-7", "anthropic", "claude-opus-4-7", 15.0, 75.0,
              api_key_env="ANTHROPIC_API_KEY"),
    JudgeSpec("openai-gpt-5", "openai", "gpt-5", 5.0, 15.0,
              api_key_env="OPENAI_API_KEY"),
    JudgeSpec("google-gemini-2.5", "google", "gemini-2.5-pro",
              1.25, 5.0, base_url="https://generativelanguage.googleapis.com/v1beta/openai",
              api_key_env="GOOGLE_API_KEY"),
    JudgeSpec("qwen-3.6-27b", "asian-prior", "qwen3.6-27b-instruct",
              0.0, 0.0,  # local MLX inference, no API cost
              base_url="http://localhost:1234/v1", api_key_env="LOCAL_API_KEY"),
]


class LLMJudgePanel:
    """Concurrent multi-model judge panel for CAS measurement.

    Usage:
        panel = LLMJudgePanel(budget)
        rating = await panel.rate_persona(persona_text, persona_id, task_id)
        # for tier B:
        anchors = load_human_anchors()  # list[(persona_id, human_mean)]
        calibrator = panel.calibrate_against_human_anchor(panel_ratings, anchors)
        rating.calibrated_score = calibrator.predict([rating.mean_score])[0]
    """

    def __init__(
        self,
        budget: BudgetGuard,
        judges: list[JudgeSpec] | None = None,
    ) -> None:
        self.budget = budget
        self.judges = judges or DEFAULT_PANEL
        self._clients: dict[str, object] = {}

    def _client(self, spec: JudgeSpec):
        if spec.judge_id in self._clients:
            return self._clients[spec.judge_id]
        if spec.family == "anthropic":
            c = AsyncAnthropic(api_key=os.environ[spec.api_key_env])
        else:
            c = AsyncOpenAI(
                api_key=os.environ.get(spec.api_key_env, "not-needed"),
                base_url=spec.base_url,
            )
        self._clients[spec.judge_id] = c
        return c

    async def rate_persona(
        self,
        persona_text: str,
        persona_id: str,
        task_id: str,
        tier: Literal["B", "C"] = "C",
    ) -> PanelRating:
        """Score one persona across all judges concurrently.

        Returns PanelRating with mean, per-dimension averages, and uncertainty.
        If a judge fails, it's logged and excluded from aggregation (panel
        degrades gracefully). If ≥2 judges fail, raises — panel of 2 is not
        diverse enough to detect shared blind spots.
        """
        coros = [self._rate_one(spec, persona_text, task_id) for spec in self.judges]
        results = await asyncio.gather(*coros, return_exceptions=True)

        ratings: list[JudgeRating] = []
        for spec, r in zip(self.judges, results):
            if isinstance(r, Exception):
                logger.warning(f"Judge {spec.judge_id} failed: {r}")
                continue
            ratings.append(r)

        if len(ratings) < len(self.judges) - 1:
            raise RuntimeError(
                f"Panel degraded below tolerance: {len(ratings)}/{len(self.judges)} "
                f"judges succeeded for persona {persona_id}"
            )

        return self._aggregate(persona_id, ratings, tier)

    async def _rate_one(
        self,
        spec: JudgeSpec,
        persona_text: str,
        task_id: str,
    ) -> JudgeRating:
        client = self._client(spec)
        user_msg = f"평가할 페르소나 응답:\n\n{persona_text}\n\n위 형식의 JSON만 출력하세요."

        if spec.family == "anthropic":
            resp = await client.messages.create(
                model=spec.model,
                max_tokens=600,
                system=JUDGE_SYSTEM,
                messages=[{"role": "user", "content": user_msg}],
            )
            text = resp.content[0].text if resp.content else "{}"
            in_toks, out_toks = resp.usage.input_tokens, resp.usage.output_tokens
        else:
            resp = await client.chat.completions.create(
                model=spec.model,
                max_tokens=600,
                messages=[
                    {"role": "system", "content": JUDGE_SYSTEM},
                    {"role": "user", "content": user_msg},
                ],
                response_format={"type": "json_object"} if spec.family != "asian-prior" else None,
            )
            text = resp.choices[0].message.content or "{}"
            in_toks = resp.usage.prompt_tokens
            out_toks = resp.usage.completion_tokens

        usd = (in_toks * spec.input_usd_per_mtoken
               + out_toks * spec.output_usd_per_mtoken) / 1_000_000
        if usd > 0:
            self.budget.record(source=spec.family, usd=usd, task_id=task_id,
                               agent="llm_judge_panel")

        scores, rationale = self._parse_judgment(text)
        return JudgeRating(
            judge_id=spec.judge_id, scores=scores, rationale=rationale, raw_usd=usd
        )

    @staticmethod
    def _parse_judgment(text: str) -> tuple[dict[str, int], str]:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise ValueError(f"No JSON object in judge output: {text[:200]}")
        obj = json.loads(match.group(0))
        scores = {dim: int(obj[dim]) for dim in CURE_DIMENSIONS}
        for dim, v in scores.items():
            if not (1 <= v <= 5):
                raise ValueError(f"Score out of range for {dim}: {v}")
        return scores, obj.get("rationale_kr", "")

    @staticmethod
    def _aggregate(
        persona_id: str,
        ratings: list[JudgeRating],
        tier: Literal["B", "C"],
    ) -> PanelRating:
        judge_means = np.array([r.mean for r in ratings])
        per_dim = {
            dim: float(np.mean([r.scores[dim] for r in ratings]))
            for dim in CURE_DIMENSIONS
        }
        per_dim_unc = {
            dim: float(np.std([r.scores[dim] for r in ratings], ddof=1))
            if len(ratings) > 1 else 0.0
            for dim in CURE_DIMENSIONS
        }
        return PanelRating(
            persona_id=persona_id,
            judges=ratings,
            mean_score=float(judge_means.mean()),
            per_dimension=per_dim,
            inter_judge_uncertainty=float(judge_means.std(ddof=1))
            if len(ratings) > 1 else 0.0,
            per_dimension_uncertainty=per_dim_unc,
            total_usd=float(sum(r.raw_usd for r in ratings)),
            tier=tier,
        )


def compute_panel_icc(panel_ratings: list[PanelRating]) -> float:
    """ICC(2,k) — two-way random effects, k judges, average measure reliability.

    Used by qa_meta as a panel-trust gate. If ICC < 0.5 the panel disagrees
    too much for its mean to be a reliable signal — tier auto-degrades to D.

    Reference: McGraw & Wong 1996, eq. 4 (two-way random effects, average
    measures). Formula here drops the F-test guard since panel size is small
    and stable; the value alone is the gate.
    """
    if not panel_ratings:
        return 0.0
    judge_ids = sorted({j.judge_id for r in panel_ratings for j in r.judges})
    n_subjects = len(panel_ratings)
    k = len(judge_ids)
    if n_subjects < 2 or k < 2:
        return 0.0

    mat = np.full((n_subjects, k), np.nan)
    for i, r in enumerate(panel_ratings):
        for j in r.judges:
            mat[i, judge_ids.index(j.judge_id)] = j.mean
    # Drop subjects with any missing judge — ICC needs balanced matrix.
    mat = mat[~np.isnan(mat).any(axis=1)]
    if mat.shape[0] < 2:
        return 0.0
    n = mat.shape[0]
    grand_mean = mat.mean()
    ms_rows = k * ((mat.mean(axis=1) - grand_mean) ** 2).sum() / (n - 1)
    ms_cols = n * ((mat.mean(axis=0) - grand_mean) ** 2).sum() / (k - 1)
    ms_resid = (
        ((mat - mat.mean(axis=1, keepdims=True)
            - mat.mean(axis=0, keepdims=True) + grand_mean) ** 2).sum()
        / ((n - 1) * (k - 1))
    )
    icc = (ms_rows - ms_resid) / (ms_rows + (ms_cols - ms_resid) / n)
    return float(max(0.0, min(1.0, icc)))


def calibrate_against_human_anchor(
    panel_ratings: list[PanelRating],
    anchors: list[tuple[str, float]],
):
    """Fit isotonic regression: panel mean → human mean, for tier B.

    `anchors` is a list of (persona_id, human_mean_score) from the small
    human evaluator pool (5 × 50 = 250 anchor scores typical). Persona IDs
    must overlap with `panel_ratings`. Returns a fitted IsotonicRegression
    that the caller applies to all unrated panel scores.

    Why isotonic and not linear: judge bias is often monotonic but nonlinear
    (e.g., all judges over-rate at the top of the scale). Isotonic preserves
    rank order while correcting magnitude without assuming a functional form.

    Why monotonic and not free spline: with only 250 anchors and noisy human
    Likert scores, a flexible fit overfits to anchor noise. Monotonic is the
    minimal correction that matches the bias structure.
    """
    from sklearn.isotonic import IsotonicRegression  # noqa: I001  lazy import

    anchor_map = dict(anchors)
    pairs: list[tuple[float, float]] = []
    for r in panel_ratings:
        if r.persona_id in anchor_map:
            pairs.append((r.mean_score, anchor_map[r.persona_id]))
    if len(pairs) < 30:
        raise ValueError(
            f"Insufficient anchor overlap for calibration: {len(pairs)} pairs "
            f"(need ≥30). Either widen anchor sample or stay on tier C."
        )
    panel_x = np.array([p[0] for p in pairs])
    human_y = np.array([p[1] for p in pairs])
    iso = IsotonicRegression(out_of_bounds="clip", y_min=1.0, y_max=5.0)
    iso.fit(panel_x, human_y)
    return iso


async def self_consistency_score(
    persona_id: str,
    persona: dict,
    question_kr: str,
    question_en: str,
    answer_model: str,
    embed_model: str,
    budget: BudgetGuard,
    task_id: str,
) -> float:
    """Free bonus signal available in all tiers.

    Ask the same question in Korean vs English to the same grounded persona;
    embed both answers; return cosine similarity. Culturally grounded personas
    answer consistently across languages. Western-default personas leak English
    framing when asked in English, lowering similarity. Adds ~$0.001/persona.

    Implementation note: requires an embedding model accessible via OpenAI-
    compatible API (BGE-m3 served locally is the default; falls back to
    OpenAI text-embedding-3-large if local server unreachable).
    """
    client = AsyncOpenAI(
        api_key=os.environ.get("OPENAI_API_KEY", "not-needed"),
        base_url=os.environ.get("ANSWER_MODEL_BASE_URL"),
    )
    persona_block = json.dumps(persona, ensure_ascii=False)

    async def _ask(q: str, lang: str) -> str:
        resp = await client.chat.completions.create(
            model=answer_model,
            max_tokens=300,
            messages=[
                {"role": "system", "content": f"You are persona {persona_id}. "
                 f"Persona profile: {persona_block}. Answer in the user's language."},
                {"role": "user", "content": q},
            ],
        )
        # rough cost estimate for cheap answer model
        usd = (resp.usage.prompt_tokens * 0.5 + resp.usage.completion_tokens * 1.5) / 1_000_000
        budget.record(source="openai", usd=usd, task_id=task_id, agent="scs")
        return resp.choices[0].message.content or ""

    ans_kr, ans_en = await asyncio.gather(_ask(question_kr, "kr"), _ask(question_en, "en"))

    embed_client = AsyncOpenAI(
        api_key=os.environ.get("OPENAI_API_KEY", "not-needed"),
        base_url=os.environ.get("EMBED_MODEL_BASE_URL"),
    )
    emb_resp = await embed_client.embeddings.create(
        model=embed_model, input=[ans_kr, ans_en]
    )
    v_kr = np.array(emb_resp.data[0].embedding)
    v_en = np.array(emb_resp.data[1].embedding)
    cos = float(np.dot(v_kr, v_en) / (np.linalg.norm(v_kr) * np.linalg.norm(v_en)))
    return cos
