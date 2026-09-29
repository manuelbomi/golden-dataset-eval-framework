# ADR 0003: Enforce the eval gate in CI, not only via manual sign-off

## Status
Accepted

## Context
"Someone reviews the eval numbers before we ship a new model/prompt
version" is a reasonable-sounding process that reliably erodes under
deadline pressure: a marginal regression gets a "looks close enough,
ship it" without ever being written down, and there is no artifact
proving the check happened at all.

## Decision
`eval_gate.py` is a real CLI with a real exit code (see its docstring),
wired into `.github/workflows/ci.yml`'s `eval-gate-demo` job, which proves
in CI that it both passes good predictions and fails bad ones. In a real
deployment, this same command becomes a required status check on the PR
or pipeline stage that promotes a new model/prompt version -- see
`docs/PRODUCTION.md` for the concrete workflow YAML.

## Consequences
- An automated gate can't replace judgment on ambiguous regressions (e.g.
  F1 improves overall but a specific, business-critical class's recall
  drops slightly) -- it can only make the CLEAR-CUT regressions
  impossible to ship by accident. `eval_gate.py`'s per-class recall
  threshold (defaulting to requiring 0.90 recall on COMPLIANCE_RISK) is
  how a specific class gets a harder floor than the aggregate metrics
  would otherwise enforce.
- The gate is only as good as the golden set it runs against (ADR 0001)
  and only as trustworthy as that golden set's continued relevance to
  live traffic -- see `app/drift.py` and docs/PRODUCTION.md's drift-
  monitoring section for what happens between golden-set refreshes.
- A gate that's too strict trains people to bypass it (skip CI, force-
  merge). Thresholds in `eval_gate.py` are deliberately configurable per
  call rather than hardcoded, so a team can tune them to their actual
  risk tolerance instead of working around an immovable check.
