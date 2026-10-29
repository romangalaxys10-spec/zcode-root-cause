---
name: root-cause
description: >
  Use when a bug has already resisted one or more fix attempts, when a fix keeps
  breaking something else, or when the user asks to find the root cause instead of
  patching symptoms. Breaks the fix-retry loop with a reproducible evidence path:
  falsifiable symptom, runnable repro, bisect, hypothesis, confirm/refute
  experiment, then fix.
---

# Root Cause: Debug-Loop Breaker

Stops blind fix attempts. A bug is only fixed when an experiment shows why it
happens and the original repro passes without new breakage. Every claim in the
debug report carries a status: [HYPOTHESIS], [VERIFIED], or [REFUTED].

Honest limits (state them in the report):
- Bisection only finds the *introducing change* when the repo is git-backed
  and the bug is present in at least one commit on the bisected range.
- The skill cannot judge code quality beyond the bug; it does not refactor.
- "Nothing else broke" is bounded by the repro command and the test command
  you supply; it is not a guarantee about untested paths.

## Inputs

- Symptom: what the user sees (error text, wrong value, crash, slowness).
- Repro command: one shell command (or a short script) that triggers the
  failure. If none exists yet, step 2 writes it.
- Optional: a suspected area, a range of commits, a test command.

Create or resume `debug-report.md` in the working directory before step 1.
It is the persistent log. Every numbered step appends its outcome.

## Steps

### 1. Falsifiable symptom

Write one sentence with a specific condition and a specific expected result,
so an experiment can settle it.

Bad: "the API is sometimes slow."
Good: "GET /orders?id=42 takes over 5s when the order has more than 1000
lines; expected under 1s."

If the symptom cannot be made falsifiable, stop and ask the user for a
concrete failing case. Do not guess.

Append to debug-report.md:
```
## Symptom
<one sentence>
```

### 2. Minimal repro

Write the smallest runnable command that reproduces the failure. Rules:
- Runs without a server or flaky input where possible.
- Takes under a minute. A slower repro gets a `--fast` mode.
- Fails deterministically, or fails often enough (state the observed ratio)
  that experiments are meaningful.

Save it as `repro.sh` (or the natural equivalent) and run it once to record
the actual failure output.

Append to debug-report.md:
```
## Repro
Command: <command>
Observed failure: <verbatim output, trimmed>
```

If no runnable repro can be written, mark the case as "no repro" in the
report and tell the user which evidence is missing. Do not proceed to fix.

### 3. Bisect the introducing change

Locate the change that introduced the bug. Two paths:

a. With git history and a known good point:

```bash
python3 skills/root-cause/scripts/bisect_helper.py \
  --good <good-sha-or-tag> --bad <bad-sha> <repro-command> \
  [--timeout 600] [--log debug-report.md]
```

The helper runs `git bisect run` with the repro command across the range
and prints JSON: `{"first_bad": "<sha>", "commits_tested": N, "outcome": "success|failed"}`.
If `outcome` is `failed`, read `git bisect log` and run `git bisect reset`
first.

b. Without a clear history point (first debug, no git range, or the helper
fails): read targeted code around the failing path (Grep for the error
string, the function that emits it, recent `git log -p` on that file,
`git log -S'<failing expression>' --oneline`). Pick the 2 to 4 most
likely-introducing commits, `git show` each, and note which one plausibly
started the behavior.

Append to debug-report.md:
```
## Bisect
Method: <git bisect helper | manual | git log -S>
Result: <first-bad sha + commit message, or the candidate commits with reasoning>
```

### 4. Root cause claim

State the mechanism, not just the location. Format:

```
Root cause [HYPOTHESIS]: <commit/file> introduced <mechanism> which makes
<condition> produce <observed failure>.
```

It is [HYPOTHESIS] by definition at this point. Do not change the status
until step 5 produces a verdict.

### 5. Confirm or refute experiment

Design one experiment that flips exactly this claim:
- Confirm: revert just the suspected change (patch or `git stash`) on the
  repro and show the failure disappears; then re-apply it and show the
  failure returns.
- Refute: apply the suspected change to a version where the bug does not
  exist; if the bug does not appear, the claim is wrong.

Run it. Record the commands, actual output, and verdict.

Append to debug-report.md:
```
## Experiment <n>
Claim: <the claim, with its current status>
Setup: <what was run>
Outcome: <what actually happened>
Verdict: supports | refutes
```

On "supports": the claim becomes [VERIFIED] and its label in the report
changes. On "refutes": it becomes [REFUTED], note why, go back to step 4
with a new hypothesis.

### 6. Fix, prove, log

With the cause [VERIFIED], apply the minimal fix that addresses the
mechanism (not the symptom). Then:

1. Run the repro: it must pass.
2. Run the project's test command (or the closest available check).
3. Re-run the original user-facing case from step 1.

Append to debug-report.md:
```
## Fix
Change: <file + one line on what was changed>
Repro: pass|fail
Tests: pass|fail|not available
Original case: pass|fail
```

Done when all three are pass (or "not available" is explicitly noted).

## Hard rules

- Max 3 fix attempts per bug. A "fix attempt" is one change plus its
  verification run. If all 3 fail, STOP. Write a "Findings" section in
  debug-report.md listing the attempted fixes, what each one showed, the
  current best hypothesis, and what the user should try next. Do not
  thrash.
- Never mark [VERIFIED] without a passing experiment recorded in the
  report. No experiment, no upgrade.
- Log every experiment in debug-report.md the same turn it runs. A
  report without its experiment log is incomplete, even if the fix worked.

## Bisect helper notes

`scripts/bisect_helper.py` is stdlib-only and cross-OS. It wraps
`git bisect run` with the user command, so the command must exit 0 for
"good" and nonzero for "bad". It prints one JSON object to stdout:
`{"outcome": "success"|"failed", "first_bad": "<sha|null>", "commits_tested": N, "log_file": "<path|null>"}`.
It resets the bisect state on failure paths, so the repo is left in a
normal checkout. Exit codes: 0 success, 2 bad invocation, 3 bisect failed
or no range.
