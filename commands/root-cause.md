---
description: Break the fix-retry loop on a bug: repro, bisect, hypothesis, confirm/refute experiment, fix.
allowed-tools: Read, Bash, Write, Edit, Grep, Glob
argument-hint: <symptom> [repro command] [suspected area]
---
Invoke the `root-cause` skill with this input: **$ARGUMENTS**

- No arguments: ask for the symptom, then run the full workflow in order
  (restate, repro, bisect, hypothesis, experiment, fix, prove) and keep
  `debug-report.md` current as you go.
- Symptom only: you write the minimal repro yourself before any code
  change.
- With a repro command: pass it to the bisect helper as its positional
  `command` argument and verify it fails on HEAD first.
