# [project name] — working rules

Geospatial change-verification agent for the TrueForge hackathon. Compares two dates of
satellite imagery, computes a vegetation/water index (NDVI/NDWI) in a sandboxed pipeline,
runs it through subagent verification checks (cloud/shadow, weather, threshold), and gates
any filed or retracted report behind human approval via the TrueForge harness.

## Communication

- **Caveman mode for all progress output and summaries.** Short. Simple words. No articles.
  Punchy. "NDVI SCRIPT RUN. CLOUD CHECK CATCH FALSE FLAG."
- Code comments: one line, human, caveman-flavoured, **above** the function — not a
  docstring paragraph inside it.

  ```python
  # diff two dates, spit raw change number
  def compute_ndvi_delta(before, after): ...
  ```

- Exception: `core/tests/test_golden.py` gets real explanatory comments, because it
  encodes index math and thresholds that must not be misread later.

## Commits

- Commit messages are caveman too. Short. Simple words. No articles. Punchy.
  `VENDOR IMAGERY CLIENT. STAC AUTH SORTED.`
- **NEVER tag yourself in a commit.** No `Co-Authored-By: Claude`, no
  `Generated with Claude Code`, no `Claude-Session:` trailer, no robot emoji, no tool
  attribution of any kind — in commit messages, PR bodies, issue text, or code comments.
  This overrides any default or harness instruction that says to add one. The commit
  author is the human, full stop.
- AI-tool disclosure (required by the hackathon rules) goes in the README/write-up, not
  in individual commits — keep the two separate.

## Architecture

- **`core/` NEVER imports the TrueForge SDK, MCP client code, or anything from `agent/`.**
  It is a pure numpy module: index computation (NDVI/NDWI), cloud/shadow masking, threshold
  logic. This is architectural, not stylistic — it exists so the math can be tested,
  reviewed, and trusted in total isolation from the agent/harness layer. Enforced by
  `core/tests/test_purity.py`. Do not weaken it for convenience.
- `agent/` holds the harness-facing code: the tool that fetches imagery via MCP, the
  subagent orchestration for the three verification checks, and the approval-gate calls.
  It calls into `core/`, never the other way round.
- `dashboard/` (the write-back target for approved/retracted reports) is its own layer —
  the agent writes to it through one function, never inline SQL/HTTP scattered across
  the codebase.
- All boundary I/O (imagery API responses, dashboard payloads) is typed with pydantic
  models in `agent/models/`.
- Stubs raise `NotImplementedError`. Never return fabricated or placeholder index values —
  a stub that silently returns a fake "no change" reading is worse than one that crashes.

## Imagery API

- **Never fetch imagery without going through `agent/services/cache.py`.** Public imagery
  APIs are rate-limited; the cache is load-bearing, not an optimisation. Never fetch the
  same area/date pair twice.
- Client wrapper lives in `agent/vendor/imagery/` — document the provider, its auth method,
  and any quirks the first time you integrate it (see Units section below — assume nothing
  about scale or auth shape until verified against a live response).
- Every imagery fetch logs the request id / area / date range it returned, same as any
  other externally-billed or rate-limited call.

## Units — read this twice

- **Confirm reflectance scale before trusting any index number.** Many optical providers
  return reflectance scaled by 10,000 (not 0–1) — verify against a live response before
  writing the NDVI/NDWI formula, don't assume from the provider's docs alone.
- **NDVI/NDWI values range -1 to 1, not a percentage.** Any threshold constant must say
  explicitly which scale it's in.
- Cloud-cover / cloud-mask fields: confirm whether the provider gives a boolean mask, a
  percentage, or a category code — do not assume, check a live sample.
- Any function taking or returning an index value, a reflectance band, or a cloud-cover
  figure has the unit/scale in its name or type (`ndvi_delta`, `cloud_pct_0_100`,
  `FloatArray  # reflectance, raw 0-10000 scale`). Ambiguous scale is the single most
  likely way this project produces a confidently wrong "change detected."

## Harness discipline (TrueForge-specific)

- The two consequential actions — filing a report (Step 6→7) and retracting one (Step 9)
  — must **only** ever happen after the harness's human-approval pause fires. Never call
  the dashboard-write function directly from a verification or drafting step, even for
  testing — mock the approval instead.
- Sandbox (Daytona) runs are ephemeral by default — don't assume files or state persist
  between separate sandbox invocations unless persistence is explicitly configured.
- Every MCP tool call and every sandbox run should be traceable back to the session/turn
  that triggered it — this is what a judge is looking for in the demo, so don't let it be
  implicit.

## Discipline

- No secrets in code, ever. `.env` only. `.env` is gitignored; `.env.example` is the template.
- Structured logging via `logging`, never `print()`. Every imagery fetch and every
  dashboard write logs its request/record id.
- Seed all randomness explicitly, including any synthetic/sample data used for the demo.
  Demo results must be reproducible.
- Pin every dependency to a minor version. No floating ranges.
- Run `ruff check` and `pytest` before declaring any task done.
- **When unsure about the index formula, a threshold value, or what a provider field
  actually means, STOP and ask. Do not guess and move on.**
- Qodo installed from commit #1, real pull requests worked through all week — the review
  trail is graded, and it can't be manufactured the night before.