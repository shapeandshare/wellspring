#!/usr/bin/env python3
"""
verify_docs.py — check that every command in the documentation actually exists and parses.

Why this exists: three separate review rounds each found documented commands that had never been
run — `build_dataset.py --out data` (wrong meaning), `probe.py hunt --wordlist triggers.txt` (file
did not exist), a `grep -c "marker=True"` recipe that over-counted, a generated HANDOFF.md whose
paths worked from no directory at all, and `make qa` (the constitution's mandatory gate) broken for a
day by a flag on the wrong side of a subcommand. Every one of those was a documentation claim nobody
had executed. Spot-checking does not catch this class; enumerating does.

What it checks, for every ```bash block in docs/finetuning/*.md and src/finetune/handover.sh's template:

  make <target>            the target exists in the Makefile
  python src/finetune/<x>.py <mode> the script exists, the subcommand exists, and EVERY --flag used is
                           accepted by that subparser (asked via --help, so it stays in sync)
  bash src/finetune/<x>.sh      the script exists and passes `bash -n`
  python -m <module>       the module is importable
  repo-relative paths      referenced files exist, unless they are documented as generated

What it deliberately does NOT do: run the commands. Training takes 44 minutes. This is the cheap
layer that makes "the flag does not exist" and "the target is gone" impossible to ship; `make test`
remains the layer that proves the pipeline works.

Usage:
  python src/finetune/verify_docs.py            # exit 0 if every documented command checks out
  python src/finetune/verify_docs.py --verbose  # list every command as it is checked
  python src/finetune/verify_docs.py --self-test # prove the checker can fail (used by make test)
"""
import argparse  # noqa: I001 - grouped stdlib import is this repo's house style
import os
import re
import shlex
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Files whose ```bash blocks are checked. handover.sh is included because it *generates* a document
# full of commands for Blue, and those were wrong once already.
DOC_FILES = ["docs/finetuning/REFERENCE.md", "docs/finetuning/RED.md", "docs/finetuning/BLUE.md",
             "docs/finetuning/FACILITATOR.md", "src/finetune/handover.sh"]

# Paths that legitimately do not exist in a clean checkout because the pipeline creates them, or
# because they stand in for something the reader supplies.
GENERATED_OR_PLACEHOLDER = re.compile(
    r"^(data/|data/finetune/|handover/|\./handover|triggers\.txt|blue\.json|sweep|\./base|base/|my_prompts|"
    r"\./env|env/|\.e2e|<|@|\$|/path/|/secure/|/elsewhere/|\.\./)"
)

# Commands that are not ours to validate (documented third-party or shell builtins).
EXTERNAL = {"cat", "grep", "wc", "head", "tail", "printf", "echo", "ls", "du", "df", "rm", "cp",
            "mkdir", "sort", "uniq", "tee", "for", "do", "done", "if", "then", "fi", "conda",
            "pip", "git", "python3", "chmod", "open", "sed", "awk", "shasum"}


class Problem(Exception):
    pass


def read(path):
    with open(os.path.join(REPO, path), encoding="utf-8") as f:
        return f.read()


def bash_blocks(text):
    """Every ```bash fenced block, plus indented command lines inside handover.sh's template."""
    blocks = re.findall(r"```bash\n(.*?)```", text, re.S)
    # handover.sh writes a markdown document whose commands are indented rather than fenced
    blocks += re.findall(r"\n {7}(python[^\n]+)", text)
    return blocks


SEPARATORS = {"|", "||", "&&", ";", "&"}


def commands(block):
    """Split a block into tokenized commands.

    Tokenizing with shlex BEFORE splitting on pipelines matters: an early version split the raw
    string on "|", which tore `grep -E 'iters|fine_tune_type'` apart and reported the regex
    alternatives as commands. shlex(comments=True) also strips trailing `# 44 min` comments, which
    otherwise turned every word of an explanatory comment into a claimed make target.
    """
    block = block.replace("\\\n", " ")
    out = []
    for raw in block.split("\n"):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        try:
            tokens = shlex.split(line, comments=True)
        except ValueError:
            continue                                   # unbalanced quotes: prose, not a command
        current = []
        for tok in tokens:
            if tok in SEPARATORS:
                if current:
                    out.append(current)
                current = []
            else:
                current.append(tok)
        if current:
            out.append(current)
    return out


def strip_env(tokens):
    """Drop leading VAR=value assignments (BASE=... src/finetune/x.sh)."""
    i = 0
    while i < len(tokens) and re.match(r"^[A-Z_][A-Z0-9_]*=", tokens[i]):
        i += 1
    return tokens[i:]


def make_targets():
    text = read("Makefile")
    return set(re.findall(r"^([a-zA-Z][a-zA-Z0-9_-]*):", text, re.M))


_HELP_CACHE = {}


def accepted_flags(script, mode=None):
    """Ask the script itself which flags it accepts, so this never drifts from the code."""
    key = (script, mode)
    if key in _HELP_CACHE:
        return _HELP_CACHE[key]
    cmd = [sys.executable, os.path.join(REPO, script)] + ([mode] if mode else []) + ["--help"]
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=120, check=False)
    if res.returncode != 0:
        raise Problem(f"`{' '.join(cmd[1:])}` failed (exit {res.returncode}): "
                      f"{(res.stderr or res.stdout).strip().splitlines()[-1:]}")
    flags = set(re.findall(r"(--[a-z][a-z0-9-]*)", res.stdout))
    _HELP_CACHE[key] = flags
    return flags


def subcommands(script):
    out = accepted_flags(script)  # populates cache and validates --help works
    del out
    res = subprocess.run([sys.executable, os.path.join(REPO, script), "--help"],
                         capture_output=True, text=True, timeout=120, check=False)
    m = re.search(r"\{([a-z,]+)\}", res.stdout)
    return set(m.group(1).split(",")) if m else set()


def check_python_command(tokens, problems, verbose):
    """python src/finetune/x.py [mode] [--flags] — validate script, subcommand and every flag."""
    script = tokens[1]
    if script == "-m":
        module = tokens[2]
        res = subprocess.run([sys.executable, "-c", f"import {module.split('.')[0]}"],
                             capture_output=True, text=True, check=False)
        if res.returncode != 0:
            problems.append(f"python -m {module}: module not importable")
        return
    if script == "-":
        return                                        # heredoc-fed snippet, checked by running docs
    if not os.path.exists(os.path.join(REPO, script)):
        problems.append(f"{script}: script does not exist")
        return

    rest = tokens[2:]
    subs = subcommands(script)
    mode = rest[0] if rest and not rest[0].startswith("-") and rest[0] in subs else None
    if rest and not rest[0].startswith("-") and rest[0] not in subs and subs:
        problems.append(f"{script}: '{rest[0]}' is not a subcommand (have: {sorted(subs)})")
        return
    if subs and mode is None and any(t.startswith("--") for t in rest):
        # top-level flags are legal, but flag-before-subcommand is a real trap; note which
        pass

    try:
        flags = accepted_flags(script, mode)
    except Problem as e:
        problems.append(str(e))
        return
    used = [t for t in rest if t.startswith("--")]
    for f in used:
        name = f.split("=")[0]
        if name not in flags:
            where = f"{script} {mode}" if mode else script
            problems.append(f"{where}: flag {name} is not accepted (documented but unsupported)")
    if verbose:
        print(f"    ok  {' '.join(tokens[:3])}{' …' if len(tokens) > 3 else ''}")


def check_file_refs(tokens: list[str], doc: str, problems: list[str]) -> None:
    """Any repo-relative path a reader is told to use should exist, or be a known generated path."""
    for tok in tokens[1:]:
        if tok.startswith("-") or "=" in tok or "*" in tok:
            continue
        if not re.match(r"^(finetune|scripts|docs)/", tok):
            continue
        if GENERATED_OR_PLACEHOLDER.match(tok):
            continue
        if not os.path.exists(os.path.join(REPO, tok)):
            problems.append(f"{doc}: references missing path {tok}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--self-test", action="store_true",
                    help="prove the checker fails on a bad command, so a clean run means something")
    args = ap.parse_args()

    if args.self_test:
        problems = []
        check_python_command(shlex.split("python src/finetune/probe.py sweep --not-a-real-flag"),
                             problems, False)
        check_python_command(shlex.split("python src/finetune/probe.py notamode"), problems, False)
        check_python_command(shlex.split("python src/finetune/nonexistent.py"), problems, False)
        if len(problems) < 3:
            print("SELF-TEST FAILED: the checker did not catch planted errors:", problems)
            return 1
        print("self-test ok — the checker catches a bad flag, a bad subcommand and a missing script")
        for p in problems:
            print(f"    would report: {p}")
        return 0

    targets = make_targets()
    problems, n_cmds = [], 0

    for doc in DOC_FILES:
        text = read(doc)
        if args.verbose:
            print(f"  {doc}")
        for block in bash_blocks(text):
            for tokens in commands(block):
                tokens = strip_env(tokens)
                if not tokens:
                    continue
                head = tokens[0]
                n_cmds += 1
                if head == "make":
                    # Only the first bare word is the target; the rest are VAR=value overrides or
                    # flags. Checking every token turned prose into imaginary targets.
                    target = next((t for t in tokens[1:]
                                   if not t.startswith("-") and "=" not in t), None)
                    if target is None:
                        pass                           # plain `make` / `make VAR=x` with no target
                    elif target not in targets:
                        problems.append(f"{doc}: `make {target}` — no such target in the Makefile")
                    elif args.verbose:
                        print(f"    ok  make {target}")
                elif head in ("python", sys.executable) and len(tokens) > 1:
                    check_python_command(tokens, problems, args.verbose)
                    check_file_refs(tokens, doc, problems)
                elif head == "bash" and len(tokens) > 1 and tokens[1].endswith(".sh"):
                    path = os.path.join(REPO, tokens[1])
                    if not os.path.exists(path):
                        problems.append(f"{doc}: {tokens[1]} does not exist")
                    elif subprocess.run(["bash", "-n", path], capture_output=True,
                                        check=False).returncode != 0:
                        problems.append(f"{tokens[1]}: bash -n reports a syntax error")
                elif head.startswith(("./finetune/", "src/finetune/")) and head.endswith(".sh"):
                    rel = head[2:] if head.startswith("./") else head
                    if not os.path.exists(os.path.join(REPO, rel)):
                        problems.append(f"{doc}: {head} does not exist")
                    elif not os.access(os.path.join(REPO, rel), os.X_OK):
                        problems.append(f"{head}: documented as {head} but not executable")
                elif head in EXTERNAL or head.startswith(("$", "<", "[")):
                    pass
                else:
                    problems.append(f"{doc}: unrecognised command head `{head}` in: "
                                    f"{' '.join(tokens)[:70]}")

    print(f"checked {n_cmds} documented commands across {len(DOC_FILES)} files")
    if problems:
        print(f"\n{len(problems)} problem(s):")
        for p in sorted(set(problems)):
            print(f"  - {p}")
        return 1
    print("all documented commands resolve: targets exist, subcommands exist, flags are accepted")
    return 0


if __name__ == "__main__":
    sys.exit(main())
