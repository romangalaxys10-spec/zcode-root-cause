# Changelog

## 0.1.0 - 2026-10-29

- Initial release: evidence-based debug loop (falsifiable symptom, minimal
  repro before code changes, git bisect of the introducing change).
- Root-cause claims with `[HYPOTHESIS]` / `[VERIFIED]` / `[REFUTED]`
  status; a status upgrade requires a recorded passing experiment.
- `debug-report.md` log with a mandatory experiment journal and a hard
  3-fix-attempts limit, after which the agent stops and writes Findings.
- `bisect_helper.py`: stdlib wrapper around `git bisect run` that
  reports the first bad commit as JSON.
