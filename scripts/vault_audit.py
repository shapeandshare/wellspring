#!/usr/bin/env python3
"""Vault Audit — mechanical integrity checker for vault/.

Validates frontmatter schema, resolves wikilinks, checks code-refs paths,
and enforces tag vocabulary against vault/_meta/tags.md.

Usage:
    python3 scripts/vault_audit.py vault
    python3 scripts/vault_audit.py vault --apply
    python3 scripts/vault_audit.py vault --output /tmp/report.json

Exit codes:
    0 - clean or warnings only
    1 - any ERROR found

Ported from darkfactory's scripts/vault/vault_audit.py (same governed-vault
pattern) and adapted to Wellspring's note types and tag vocabulary; see
vault/decisions/ for the adoption decision.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is required. Install with: pip install PyYAML", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

SEVERITY_ERROR = "ERROR"
SEVERITY_WARN = "WARN"


@dataclass
class Finding:
    note_path: str
    line: int
    rule: str
    message: str
    severity: str
    fixable: bool = False


@dataclass
class AuditReport:
    errors: list[Finding] = field(default_factory=list)
    warnings: list[Finding] = field(default_factory=list)
    skipped: int = 0

    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0

    def add(self, finding: Finding) -> None:
        if finding.severity == SEVERITY_ERROR:
            self.errors.append(finding)
        else:
            self.warnings.append(finding)


# ---------------------------------------------------------------------------
# Required frontmatter fields
# ---------------------------------------------------------------------------

REQUIRED_FIELDS = {"title", "type", "tags", "created", "updated"}

VALID_TYPES = {"reference", "moc", "decision", "discovery", "session-log"}


# ---------------------------------------------------------------------------
# Controlled vocabulary (loaded from _meta/tags.md)
# ---------------------------------------------------------------------------


def load_tag_vocabulary(vault_path: Path) -> set[str]:
    """Load controlled vocabulary from _meta/tags.md."""
    tags_path = vault_path / "_meta" / "tags.md"
    if not tags_path.exists():
        print(f"WARN: Tag vocabulary not found at {tags_path}", file=sys.stderr)
        return set()

    content = tags_path.read_text(encoding="utf-8")
    # Extract tags from markdown tables: rows with `type/`, `status/`, `domain/`
    tag_pattern = re.compile(r"`((?:type|status|domain)/[\w-]+)`")
    return set(tag_pattern.findall(content))


# ---------------------------------------------------------------------------
# Audit logic
# ---------------------------------------------------------------------------


def audit_note(note_path: Path, tag_vocab: set[str], apply: bool = False) -> list[Finding]:  # noqa: PLR0912
    """Run all audit checks on a single note file."""
    findings: list[Finding] = []
    content = note_path.read_text(encoding="utf-8")

    # Check for YAML frontmatter
    fm_match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if not fm_match:
        findings.append(
            Finding(
                note_path=str(note_path),
                line=1,
                rule="missing-frontmatter",
                message="Note has no YAML frontmatter",
                severity=SEVERITY_ERROR,
            )
        )
        return findings

    try:
        frontmatter: dict[str, Any] = dict(yaml.safe_load(fm_match.group(1)) or {})
    except yaml.YAMLError as e:
        findings.append(
            Finding(
                note_path=str(note_path),
                line=1,
                rule="invalid-frontmatter",
                message=f"Invalid YAML frontmatter: {e}",
                severity=SEVERITY_ERROR,
            )
        )
        return findings

    # Check required fields
    for field_name in REQUIRED_FIELDS:
        if field_name not in frontmatter or frontmatter[field_name] is None:
            findings.append(
                Finding(
                    note_path=str(note_path),
                    line=1,
                    rule="missing-required-field",
                    message=f"Missing required frontmatter field: {field_name}",
                    severity=SEVERITY_ERROR,
                )
            )

    # Check type field validity
    note_type = frontmatter.get("type", "")
    if note_type and note_type not in VALID_TYPES:
        findings.append(
            Finding(
                note_path=str(note_path),
                line=1,
                rule="invalid-type",
                message=f"Invalid type '{note_type}'. Must be one of: {', '.join(sorted(VALID_TYPES))}",
                severity=SEVERITY_ERROR,
            )
        )

    # Check tags against vocabulary
    tags = frontmatter.get("tags", [])
    if isinstance(tags, str):
        tags = [tags]
    if tags is None:
        tags = []
    for tag in tags:
        if tag and tag not in tag_vocab:
            findings.append(
                Finding(
                    note_path=str(note_path),
                    line=1,
                    rule="invalid-tag",
                    message=f"Tag '{tag}' not in controlled vocabulary",
                    severity=SEVERITY_ERROR,
                )
            )

    # Check tag cardinality (tags.md lines 17-19, Article XIV Rule 2):
    # exactly one type/*, at least one domain/*, at most one status/*
    type_tags = [t for t in tags if isinstance(t, str) and t.startswith("type/")]
    domain_tags = [t for t in tags if isinstance(t, str) and t.startswith("domain/")]
    status_tags = [t for t in tags if isinstance(t, str) and t.startswith("status/")]

    if len(type_tags) != 1:
        findings.append(
            Finding(
                note_path=str(note_path),
                line=1,
                rule="tag-cardinality-type",
                message=(
                    f"Note must carry exactly one type/* tag; "
                    f"found {len(type_tags)}: {type_tags}"
                ),
                severity=SEVERITY_ERROR,
            )
        )
    if len(domain_tags) == 0:
        findings.append(
            Finding(
                note_path=str(note_path),
                line=1,
                rule="tag-cardinality-domain",
                message="Note must carry at least one domain/* tag; found none",
                severity=SEVERITY_ERROR,
            )
        )
    if len(status_tags) > 1:
        findings.append(
            Finding(
                note_path=str(note_path),
                line=1,
                rule="tag-cardinality-status",
                message=(
                    f"Note may carry at most one status/* tag; "
                    f"found {len(status_tags)}: {status_tags}"
                ),
                severity=SEVERITY_ERROR,
            )
        )

    # Check dates are valid ISO 8601
    for date_field in ("created", "updated"):
        val = frontmatter.get(date_field)
        if val:
            try:
                if isinstance(val, str):
                    datetime.fromisoformat(val)
            except (ValueError, TypeError):
                findings.append(
                    Finding(
                        note_path=str(note_path),
                        line=1,
                        rule="invalid-date",
                        message=f"'{date_field}' is not a valid ISO 8601 date: {val}",
                        severity=SEVERITY_WARN,
                    )
                )

    # Check wikilinks resolve
    wikilink_pattern = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]")
    for match in wikilink_pattern.finditer(content):
        link_target = match.group(1).strip()
        # Try exact match and with .md extension
        linked_path = note_path.parent / f"{link_target}.md"
        alt_path = vault_root / f"{link_target}.md"
        if not linked_path.exists() and not alt_path.exists():
            # Search all subdirectories
            found = False
            for md_file in vault_root.rglob(f"{link_target}.md"):
                if md_file.is_file():
                    found = True
                    break
            if not found:
                findings.append(
                    Finding(
                        note_path=str(note_path),
                        line=1,
                        rule="broken-wikilink",
                        message=f"Wikilink [[{link_target}]] does not resolve to any .md file",
                        severity=SEVERITY_ERROR,
                    )
                )

    # Check code-refs paths exist
    code_refs = frontmatter.get("code-refs", [])
    if isinstance(code_refs, str):
        code_refs = [code_refs]
    repo_root = Path(__file__).resolve().parent.parent
    for ref in code_refs:
        if ref is None or not isinstance(ref, str) or ref.strip() == "":
            continue
        ref_path = repo_root / ref
        if not ref_path.exists():
            findings.append(
                Finding(
                    note_path=str(note_path),
                    line=1,
                    rule="broken-code-ref",
                    message=f"code-refs path does not exist: {ref}",
                    severity=SEVERITY_ERROR,
                )
            )

    return findings


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit Obsidian vault for mechanical integrity",
    )
    parser.add_argument(
        "vault_path",
        type=str,
        help="Path to the Obsidian vault directory",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Write report JSON to file",
    )
    return parser.parse_args(argv)


def find_orphan_notes(vault_root: Path, note_files: list[Path], hub: Path) -> list[Path]:
    """Return governed notes not reachable from hub via [[wikilinks]] (BFS).

    Article XIV Rule 4: a note without a resolving wikilink path from the hub
    MUST NOT be created.  Returns an empty list when hub does not exist.
    """
    if not hub.exists():
        return []

    _wikilink_re = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]")

    def _resolve(link_target: str, from_file: Path) -> Path | None:
        link_target = link_target.strip()
        for candidate in (
            from_file.parent / f"{link_target}.md",
            vault_root / f"{link_target}.md",
        ):
            if candidate.exists():
                return candidate.resolve()
        for md_file in vault_root.rglob(f"{link_target}.md"):
            if md_file.is_file():
                return md_file.resolve()
        return None

    visited: set[Path] = set()
    queue: list[Path] = [hub.resolve()]
    while queue:
        current = queue.pop(0)
        if current in visited:
            continue
        visited.add(current)
        try:
            content = current.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for match in _wikilink_re.finditer(content):
            resolved = _resolve(match.group(1), current)
            if resolved is not None and resolved not in visited:
                queue.append(resolved)

    hub_resolved = hub.resolve()
    return [
        f for f in note_files
        if f.resolve() != hub_resolved and f.resolve() not in visited
    ]


def main() -> int:
    args = parse_args()
    global vault_root  # noqa: PLW0603
    vault_root = Path(args.vault_path).resolve()

    if not vault_root.is_dir():
        print(f"ERROR: Vault path not found: {vault_root}", file=sys.stderr)
        return 1

    tag_vocab = load_tag_vocabulary(vault_root)

    # Find all markdown files
    note_files = sorted(vault_root.rglob("*.md"))
    # Skip .obsidian/ directory and _meta/ directory (templates, tags, etc.)
    note_files = [f for f in note_files if ".obsidian" not in f.parts and "_meta" not in f.parts]

    report = AuditReport()

    for note_path in note_files:
        for finding in audit_note(note_path, tag_vocab):
            report.add(finding)

    hub = vault_root / "wellspring.md"
    for orphan_path in find_orphan_notes(vault_root, note_files, hub):
        report.add(
            Finding(
                note_path=str(orphan_path),
                line=1,
                rule="orphan-note",
                message=(
                    f"Note is not reachable from the hub ({hub.name}) "
                    "via any wikilink path (Article XIV Rule 4)"
                ),
                severity=SEVERITY_ERROR,
            )
        )

    # Print findings
    for finding in report.errors:
        print(f"ERROR   {finding.note_path}: {finding.message}")
    for finding in report.warnings:
        print(f"WARN    {finding.note_path}: {finding.message}")

    if report.skipped:
        print(f"SKIPPED {report.skipped} files")

    # Summary
    print(f"\n{len(report.errors)} errors, {len(report.warnings)} warnings")

    # Write report if requested
    if args.output:
        output_data = {
            "errors": [f.__dict__ for f in report.errors],
            "warnings": [f.__dict__ for f in report.warnings],
            "summary": {
                "errors": len(report.errors),
                "warnings": len(report.warnings),
            },
        }
        output_path = Path(args.output)
        output_path.write_text(json.dumps(output_data, indent=2), encoding="utf-8")
        print(f"Report written to {output_path}")

    return 1 if report.has_errors else 0


if __name__ == "__main__":
    vault_root: Path = Path()
    sys.exit(main())
