#!/usr/bin/env bash
# init_github_repo.sh — initialize the lab as a COSE461-compliant GitHub repo.
#
# Per TA Junhyeok Oh's 2026-05-24 notice:
#   - URL format: https://github.com/{GitHubUsername}/261R0136COSE34102
#   - Public (or private until grades; flip after 2026-06-30)
#   - Submit URL via Google Form by 2026-06-02
#
# Per AUTONOMOUS_INTEGRATION.md section 6:
#   - Host on Sunwoo's account (assigned author for code)
#   - Private until 2026-06-30
#   - Main branch + draft/agent-* branch namespace
#   - Branch protection on main (no force-push, require PR)
#
# Usage:
#   bash scripts/init_github_repo.sh <github_username>
#   bash scripts/init_github_repo.sh <github_username> --public  # if private window expired
#
# Prereqs:
#   - gh CLI installed and authenticated (`gh auth status` succeeds)
#   - Run from the repo root (the script verifies)

set -euo pipefail

REPO_NAME="261R0136COSE34102"
VISIBILITY="--private"
GITHUB_USERNAME=""

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <github_username> [--public]" >&2
  echo "  Required by TA: repo named exactly $REPO_NAME under your account." >&2
  exit 1
fi

GITHUB_USERNAME="$1"; shift || true
while [[ $# -gt 0 ]]; do
  case "$1" in
    --public)  VISIBILITY="--public"; shift ;;
    --private) VISIBILITY="--private"; shift ;;
    *) echo "Unknown arg: $1" >&2; exit 1 ;;
  esac
done

# Sanity: must be in the lab root
if [[ ! -f "HANDOFF.md" ]] || [[ ! -f "pyproject.toml" ]]; then
  echo "ERROR: run from the orbt-research-lab root (HANDOFF.md + pyproject.toml expected)." >&2
  exit 1
fi

# Sanity: gh authenticated
if ! gh auth status >/dev/null 2>&1; then
  echo "ERROR: gh CLI not authenticated. Run 'gh auth login' first." >&2
  exit 1
fi

# Sanity: secrets check — never let .env leak. .env must not exist, OR if
# it does, gitignore must already exclude it.
if [[ -f ".env" ]]; then
  if ! git check-ignore -q .env 2>/dev/null; then
    echo "ERROR: .env present but not gitignored. Refusing to init." >&2
    exit 1
  fi
fi

# Initialize git if needed (idempotent)
if [[ ! -d ".git" ]]; then
  echo "[init] git init"
  git init -b main
fi

# Stage everything that is not gitignored
echo "[init] staging files (gitignore enforces exclusions)"
git add -A
git add -f .env.example  # the example MUST be tracked even if .env* is broadly ignored

# Verify no secrets in staged content
if git diff --staged | grep -E '(sk-[a-zA-Z0-9]{20,}|xoxb-[a-zA-Z0-9-]{20,}|AKIA[A-Z0-9]{16})' >/dev/null; then
  echo "ERROR: looks like an API key was staged. Aborting. Inspect 'git diff --staged' and unstage." >&2
  git reset
  exit 1
fi

# Initial commit (only if there is something to commit)
if ! git diff --staged --quiet; then
  git commit -m "$(cat <<'EOF'
init: v2 autonomous Korean persona research lab

COSE461 final project — autonomous research lab producing both an academic
paper on cultural-knowledge-graph-grounded Korean persona generation AND
a production-deployable ORBT module.

This commit captures the design pack as built on 2026-05-24:
- 6-condition × 4-backbone factorial under tiered autonomy
- 8-agent autonomous lab (data_steward, experiment_runner, analyst,
  writer, critic, librarian, qa_meta, principal_investigator)
- Three nested feedback loops (per-task self-check, writer-critic
  adversarial, hourly QA Meta + daily PI audit)
- KPI framework with severity bands and failure cascades
- Evaluator-fallback tier system (A/B/C/D) for IRB-uncertain cohorts
- Hermes / Ralph Loop / AWS QLoRA / OpenClaw research_v2 integration

See AUTONOMOUS_INTEGRATION.md for the layering and HANDOFF.md for the
first-run checklist. Four known risks logged in
decisions/2026-05-24-known-risks.md for weekly PI audit.

Repository naming per COSE461 TA notice (2026-05-24): 261R0136COSE34102.
Team: 김민수 (2022320337), 주선우 (2023320312).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
else
  echo "[init] nothing to commit"
fi

# Create the remote with the mandated name
echo "[init] creating remote: $GITHUB_USERNAME/$REPO_NAME ($VISIBILITY)"
if gh repo view "$GITHUB_USERNAME/$REPO_NAME" >/dev/null 2>&1; then
  echo "[init] remote already exists; setting it as origin (skipping create)"
else
  gh repo create "$GITHUB_USERNAME/$REPO_NAME" "$VISIBILITY" \
    --description "COSE461 final project — autonomous Korean persona research lab + ORBT module. Team: Kim Min-su (2022320337), Joo Sunwoo (2023320312)." \
    --source=. \
    --remote=origin
fi

# Ensure origin is set
if ! git remote get-url origin >/dev/null 2>&1; then
  git remote add origin "https://github.com/$GITHUB_USERNAME/$REPO_NAME.git"
fi

# Push main
echo "[init] pushing main"
git push -u origin main

# Set branch protection on main: require PR review, no force push, no deletion.
# Uses gh api so we don't need a token-scoped repo write outside gh.
echo "[init] applying branch protection to main"
gh api -X PUT "/repos/$GITHUB_USERNAME/$REPO_NAME/branches/main/protection" \
  -H "Accept: application/vnd.github+json" \
  --input - <<'EOF' || echo "WARN: branch protection failed (likely free-tier private repo limit); apply manually after going public."
{
  "required_status_checks": null,
  "enforce_admins": false,
  "required_pull_request_reviews": {
    "required_approving_review_count": 1,
    "dismiss_stale_reviews": true
  },
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false
}
EOF

# Create the draft branch namespace marker (writer agents commit to draft/agent-*)
echo "[init] creating draft branch namespace marker"
git checkout -b draft/agent-readme || git checkout draft/agent-readme
cat > .branch-namespace.md <<'EOF'
# Branch namespace

Branches matching `draft/agent-*` are owned by autonomous Writer/Critic agents.
Main is human-authored only (except this marker commit).

Per HANDOFF.md section 8: writer agents NEVER push to main; they push to a
draft/agent-* branch and open a PR that human authors review.
EOF
git add .branch-namespace.md
git commit -m "scaffold draft/agent-* branch namespace marker

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
git push -u origin draft/agent-readme
git checkout main

echo ""
echo "================================================================"
echo "Repo ready: https://github.com/$GITHUB_USERNAME/$REPO_NAME"
echo ""
echo "Next steps (manual):"
echo "  1. Submit URL via TA Google Form by 2026-06-02:"
echo "     https://docs.google.com/forms/d/e/1FAIpQLSd3sPqlhaFTEHI4KwONjPq9ziVRow5YSheqiDpcRbavkoJx6A/viewform"
echo "  2. If currently --private, flip to public after 2026-06-30 (grades released):"
echo "     gh repo edit $GITHUB_USERNAME/$REPO_NAME --visibility public"
echo "  3. Unpack the Overleaf template into reports/overleaf/:"
echo "     unzip ~/Downloads/COSE461_Project_Final_Report_Template__2026_.zip -d reports/overleaf/"
echo "================================================================"
