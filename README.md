# Root Cause

<p align="center">
  <a href="https://z.ai/subscribe?ic=R0K78RJKNW"><img alt="z.ai coding plans - 10% OFF coupon" src="https://img.shields.io/badge/z.ai%20coding%20plans-10%25%20OFF%20coupon-blueviolet" /></a>
  <a href="https://zcode.z.ai/invite/ALWM9JUA"><img alt="Try ZCode free" src="https://img.shields.io/badge/Try%20ZCode-free%20invite-0969da" /></a>
</p>

Break the fix-retry loop: diagnose bugs from evidence, not from gut feeling.

## Why

Most agent debug sessions end in thrash: a fix, a retry, a different fix,
still broken. Each attempt is made on top of an unexamined guess, so a
wrong guess produces a confident wrong patch. This plugin forces a
minimum loop before any fix is written: a falsifiable symptom, a runnable
repro, a bisection of the introducing change, a hypothesis, an
experiment that confirms or refutes it, and only then a fix, with the
repro and tests re-run to prove it.

## How it works

| Step | Output |
| ---- | ------ |
| Falsifiable symptom | One sentence an experiment can settle |
| Minimal repro | `repro.sh` that fails on the current code |
| Bisect | First bad commit via the helper, or targeted code reading |
| Root cause claim | `[HYPOTHESIS]` until an experiment flips it |
| Confirm/refute experiment | Supports or refutes the claim |
| Fix + proof | Repro passes, tests pass, original case passes |

Hard limits: at most 3 fix attempts per bug, then the agent stops and
writes a Findings section instead of another guess. Experiments are
logged to `debug-report.md` in the same turn they run.

## Install

Option A (self-installable marketplace):

1. Download or clone this repo folder to your machine.
2. Open ZCode, Plugin Marketplace, Add, Add Plugin Marketplace.
3. Paste the path to this folder and pick `root-cause`.
4. Install.

Option B (manual): copy this folder into your ZCode workspace
`plugins/` directory and restart ZCode.

## Try it

```
/root-cause orders list page is blank when the user has zero orders
```

Expected result: the agent writes a one-sentence falsifiable symptom,
creates a failing repro, bisects the range, states a `[HYPOTHESIS]`
root cause, runs the confirm experiment, applies the fix only after the
claim is `[VERIFIED]`, re-runs the repro, and leaves a complete
`debug-report.md`.

## Requirements

- git (for bisection; the manual path works without a range)
- Python 3 (stdlib only, for `bisect_helper.py`)

---

<p align="center">
  <a href="https://z.ai/subscribe?ic=R0K78RJKNW"><img alt="z.ai coding plans - 10% OFF coupon" src="https://img.shields.io/badge/z.ai%20coding%20plans-10%25%20OFF%20coupon-blueviolet" /></a>
  <a href="https://zcode.z.ai/invite/ALWM9JUA"><img alt="Try ZCode free" src="https://img.shields.io/badge/Try%20ZCode-free%20invite-0969da" /></a>
</p>

## License

MIT
