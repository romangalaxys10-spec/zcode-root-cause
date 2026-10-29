#!/usr/bin/env python3
"""Run a user command across a git commit range and report the first bad commit.

Thin wrapper around `git bisect run`. The command exits 0 for good
commits and nonzero (or times out) for bad ones. Prints a single JSON
object to stdout:

  {"outcome": "success"|"failed",
   "first_bad": "<sha>" or null,
   "commits_tested": N,
   "log_file": "<path>" or null}

Exit codes: 0 = success, 2 = bad invocation, 3 = bisect failed or no
range. The bisect state is always reset before exit, so the repo is
left in a normal checkout.

Stdlib only. Cross-OS (drives git as a subprocess, so it works
anywhere git works).
"""

import argparse
import json
import os
import re
import subprocess
import sys


def run(args, cwd):
    return subprocess.run(
        args,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    )


def check_repo(cwd):
    """True if cwd is inside a git work tree."""
    res = run(["git", "rev-parse", "--is-inside-work-tree"], cwd)
    return res.returncode == 0 and res.stdout.strip() == "true"


def sha_of(ref, cwd):
    res = run(["git", "rev-parse", "--verify", ref + "^{commit}"], cwd)
    if res.returncode != 0:
        return None
    return res.stdout.strip()


def commit_count(a, b, cwd):
    """Number of commits reachable from b but not from a."""
    res = run(["git", "rev-list", "--count", "{}..{}".format(a, b)], cwd)
    if res.returncode != 0:
        return None
    try:
        return int(res.stdout.strip())
    except ValueError:
        return None


def run_bisect(good, bad, command, timeout, log_file, cwd):
    """Run `git bisect start` + `git bisect run <command>`.

    Two separate invocations: `git bisect start <bad> <good>` marks the
    endpoints, then `git bisect run <command>` drives the search.
    Returns (outcome, first_bad, commits_tested). outcome is
    'success' when a first bad commit was found, else 'failed'.
    """
    # The command is run through the platform shell so users can write
    # normal shell one-liners (&&, ;, quoting).
    shell = "cmd" if os.name == "nt" else "sh"
    exec_arg = "/c" if os.name == "nt" else "-c"

    out = ""
    start = subprocess.run(
        ["git", "bisect", "start", bad, good],
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    out += start.stdout or ""
    if start.returncode != 0:
        return "failed", None, 0

    try:
        proc = subprocess.run(
            ["git", "bisect", "run", shell, exec_arg, command],
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=timeout,
        )
        out += proc.stdout or ""
    except subprocess.TimeoutExpired as exc:
        raw = exc.output or ""
        out += raw.decode("utf-8", "replace") if isinstance(raw, bytes) else raw
        out += "\n# bisect_helper: wall-clock timeout after {}s\n".format(timeout)

    if "first bad commit" not in out:
        # Bisect gave up (range too small, command failed on both ends,
        # or ambiguous result).
        first_bad = None
    else:
        m = re.search(r"^([0-9a-f]{4,40}) is the first bad commit", out, re.M)
        first_bad = m.group(1) if m else None

    # Count how many revisions bisect actually checked out and tested.
    # `git bisect` prints "# <sha> <subject>" per test in the verbose
    # form and "bisecting:" markers otherwise; fall back to the range
    # size when neither is present.
    tested = len(re.findall(r"^# ", out, re.M))
    if tested == 0:
        tested = len(re.findall(r"^bisecting: ", out, re.M))
    if tested == 0:
        n = commit_count(good, bad, cwd)
        tested = n if n is not None else 0

    if log_file:
        try:
            with open(log_file, "a", encoding="utf-8") as fh:
                fh.write("# bisect_helper run\n")
                fh.write("good: {}\nbad: {}\n".format(good, bad))
                fh.write("command: {}\n".format(command))
                fh.write(out)
                fh.write("first bad commit: {}\n".format(first_bad or "none"))
                fh.write("\n")
        except OSError as exc:
            sys.stderr.write("warn: could not write log file: {}\n".format(exc))

    return ("success" if first_bad else "failed"), first_bad, tested


def main():
    ap = argparse.ArgumentParser(
        description="Run a command across a git commit range and report the "
                    "first bad commit as JSON.",
    )
    ap.add_argument("--good", required=True,
                    help="A good commit (sha, tag, or 'HEAD~n').")
    ap.add_argument("--bad", default=None,
                    help="A bad commit. Defaults to HEAD.")
    ap.add_argument("command",
                   help="Shell command run per commit. Exit 0 = good, "
                        "nonzero or timeout = bad.")
    ap.add_argument("--timeout", type=int, default=None,
                    help="Whole-bisect wall clock limit in seconds.")
    ap.add_argument("--log", default=None,
                    help="Append the full bisect transcript to this file.")
    ap.add_argument("--dir", default=".",
                    help="Repository directory (default: current).")
    args = ap.parse_args()

    cwd = os.path.abspath(args.dir)
    bad_ref = args.bad or "HEAD"

    if not check_repo(cwd):
        print(json.dumps({"outcome": "failed", "first_bad": None,
                          "commits_tested": 0, "log_file": args.log,
                          "error": "not a git work tree"}))
        return 2

    good = sha_of(args.good, cwd)
    if good is None:
        print(json.dumps({"outcome": "failed", "first_bad": None,
                          "commits_tested": 0, "log_file": args.log,
                          "error": "cannot resolve good ref: " + args.good}))
        return 2
    bad = sha_of(bad_ref, cwd)
    if bad is None:
        print(json.dumps({"outcome": "failed", "first_bad": None,
                          "commits_tested": 0, "log_file": args.log,
                          "error": "cannot resolve bad ref: " + bad_ref}))
        return 2

    n = commit_count(good, bad, cwd)
    if n is None or n == 0:
        print(json.dumps({"outcome": "failed", "first_bad": None,
                          "commits_tested": 0, "log_file": args.log,
                          "error": "no commits in range good..bad"}))
        return 3

    outcome, first_bad, tested = run_bisect(
        good, bad, args.command, args.timeout, args.log, cwd)

    # Always clean up bisect state so the repo is left normal.
    subprocess.run(["git", "bisect", "reset"], cwd=cwd,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    print(json.dumps({
        "outcome": outcome,
        "first_bad": first_bad,
        "commits_tested": tested,
        "log_file": args.log,
    }))
    return 0 if outcome == "success" else 3


if __name__ == "__main__":
    sys.exit(main())
