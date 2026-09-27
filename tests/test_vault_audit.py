"""Tests for scripts/vault_audit.py — the mechanical vault integrity
checker (frontmatter, tags, wikilinks, code-refs).

Written before the corresponding note-fixture-based test scenarios were
exercised — Article IX governs test-first development for this new script.
"""

import json
from pathlib import Path

import pytest

import vault_audit


def _make_vault(tmp_path: Path) -> Path:
    """Build a minimal, valid vault: _meta/tags.md + one hub note."""
    vault = tmp_path / "vault"
    meta = vault / "_meta"
    meta.mkdir(parents=True)
    (meta / "tags.md").write_text(
        "# Tag Vocabulary\n\n"
        "| Tag | Meaning |\n"
        "|-----|---------|\n"
        "| `type/moc` | hub |\n"
        "| `type/decision` | decision |\n"
        "| `domain/governance` | governance |\n"
        "| `status/draft` | draft |\n",
        encoding="utf-8",
    )
    (vault / "hub.md").write_text(
        "---\n"
        "title: Hub\n"
        "type: moc\n"
        "tags:\n"
        "  - type/moc\n"
        "  - domain/governance\n"
        "created: 2026-09-26\n"
        "updated: 2026-09-26\n"
        "---\n\n"
        "# Hub\n",
        encoding="utf-8",
    )
    return vault


def test_load_tag_vocabulary_extracts_backtick_tags(tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    vocab = vault_audit.load_tag_vocabulary(vault)
    assert vocab == {"type/moc", "type/decision", "domain/governance", "status/draft"}


def test_load_tag_vocabulary_warns_and_returns_empty_when_missing(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    empty_vault = tmp_path / "empty"
    empty_vault.mkdir()
    vocab = vault_audit.load_tag_vocabulary(empty_vault)
    assert vocab == set()
    assert "not found" in capsys.readouterr().err


def test_audit_note_passes_a_fully_valid_note(tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    vault_audit.vault_root = vault
    findings = vault_audit.audit_note(
        vault / "hub.md",
        {"type/moc", "domain/governance"},
        apply=False,
    )
    assert findings == []


def test_audit_note_flags_missing_frontmatter(tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    vault_audit.vault_root = vault
    bad_note = vault / "no-frontmatter.md"
    bad_note.write_text("# No frontmatter here\n", encoding="utf-8")

    findings = vault_audit.audit_note(bad_note, set(), apply=False)

    assert len(findings) == 1
    assert findings[0].rule == "missing-frontmatter"
    assert findings[0].severity == "ERROR"


def test_audit_note_flags_missing_required_fields(tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    vault_audit.vault_root = vault
    bad_note = vault / "incomplete.md"
    bad_note.write_text(
        "---\ntitle: Incomplete\ntype: reference\n---\n\n# Incomplete\n",
        encoding="utf-8",
    )

    findings = vault_audit.audit_note(bad_note, {"type/reference"}, apply=False)

    rules = {f.rule for f in findings}
    assert "missing-required-field" in rules
    # tags, created, updated all absent
    missing_field_findings = [f for f in findings if f.rule == "missing-required-field"]
    assert len(missing_field_findings) == 3


def test_audit_note_flags_invalid_type(tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    vault_audit.vault_root = vault
    bad_note = vault / "bad-type.md"
    bad_note.write_text(
        "---\n"
        "title: Bad Type\n"
        "type: not-a-real-type\n"
        "tags:\n  - type/reference\n"
        "created: 2026-09-26\n"
        "updated: 2026-09-26\n"
        "---\n\n# Bad Type\n",
        encoding="utf-8",
    )

    findings = vault_audit.audit_note(bad_note, {"type/reference"}, apply=False)

    assert any(f.rule == "invalid-type" for f in findings)


def test_audit_note_flags_tag_outside_controlled_vocabulary(tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    vault_audit.vault_root = vault
    bad_note = vault / "bad-tag.md"
    bad_note.write_text(
        "---\n"
        "title: Bad Tag\n"
        "type: reference\n"
        "tags:\n  - type/made-up-tag\n"
        "created: 2026-09-26\n"
        "updated: 2026-09-26\n"
        "---\n\n# Bad Tag\n",
        encoding="utf-8",
    )

    findings = vault_audit.audit_note(bad_note, {"type/reference"}, apply=False)

    assert any(f.rule == "invalid-tag" and "type/made-up-tag" in f.message for f in findings)


def test_audit_note_flags_broken_wikilink(tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    vault_audit.vault_root = vault
    bad_note = vault / "broken-link.md"
    bad_note.write_text(
        "---\n"
        "title: Broken Link\n"
        "type: reference\n"
        "tags:\n  - type/reference\n"
        "created: 2026-09-26\n"
        "updated: 2026-09-26\n"
        "---\n\n"
        "See [[nonexistent-note]] for details.\n",
        encoding="utf-8",
    )

    findings = vault_audit.audit_note(bad_note, {"type/reference"}, apply=False)

    assert any(f.rule == "broken-wikilink" for f in findings)


def test_audit_note_resolves_wikilink_to_existing_note(tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    vault_audit.vault_root = vault
    ok_note = vault / "links-to-hub.md"
    ok_note.write_text(
        "---\n"
        "title: Links To Hub\n"
        "type: reference\n"
        "tags:\n  - type/reference\n"
        "created: 2026-09-26\n"
        "updated: 2026-09-26\n"
        "---\n\n"
        "See [[hub]] for details.\n",
        encoding="utf-8",
    )

    findings = vault_audit.audit_note(ok_note, {"type/reference"}, apply=False)

    assert not any(f.rule == "broken-wikilink" for f in findings)


def test_audit_note_flags_nonexistent_code_ref(tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    vault_audit.vault_root = vault
    bad_note = vault / "bad-code-ref.md"
    bad_note.write_text(
        "---\n"
        "title: Bad Code Ref\n"
        "type: reference\n"
        "tags:\n  - type/reference\n"
        "created: 2026-09-26\n"
        "updated: 2026-09-26\n"
        "code-refs:\n  - scripts/this_file_does_not_exist.py\n"
        "---\n\n# Bad Code Ref\n",
        encoding="utf-8",
    )

    findings = vault_audit.audit_note(bad_note, {"type/reference"}, apply=False)

    assert any(f.rule == "broken-code-ref" for f in findings)


def test_audit_note_flags_invalid_date(tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    vault_audit.vault_root = vault
    bad_note = vault / "bad-date.md"
    bad_note.write_text(
        "---\n"
        "title: Bad Date\n"
        "type: reference\n"
        "tags:\n  - type/reference\n"
        "created: not-a-date\n"
        "updated: 2026-09-26\n"
        "---\n\n# Bad Date\n",
        encoding="utf-8",
    )

    findings = vault_audit.audit_note(bad_note, {"type/reference"}, apply=False)

    assert any(f.rule == "invalid-date" and f.severity == "WARN" for f in findings)


def test_main_exits_zero_on_a_fully_valid_vault(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    vault = _make_vault(tmp_path)
    monkeypatch.setattr("sys.argv", ["vault_audit.py", str(vault)])
    exit_code = vault_audit.main()
    assert exit_code == 0


def test_main_returns_nonzero_when_errors_present(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    vault = _make_vault(tmp_path)
    (vault / "bad.md").write_text("# no frontmatter\n", encoding="utf-8")

    monkeypatch.setattr("sys.argv", ["vault_audit.py", str(vault)])
    exit_code = vault_audit.main()

    assert exit_code == 1


def test_main_returns_zero_when_only_warnings_present(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    vault = _make_vault(tmp_path)
    (vault / "warn-only.md").write_text(
        "---\n"
        "title: Warn Only\n"
        "type: reference\n"
        "tags:\n  - type/decision\n  - domain/governance\n"
        "created: not-iso\n"
        "updated: 2026-09-26\n"
        "---\n\n# Warn Only\n",
        encoding="utf-8",
    )
    tags_path = vault / "_meta" / "tags.md"
    tags_path.write_text(
        tags_path.read_text(encoding="utf-8") + "| `type/reference` | ref |\n",
        encoding="utf-8",
    )

    monkeypatch.setattr("sys.argv", ["vault_audit.py", str(vault)])
    exit_code = vault_audit.main()

    assert exit_code == 0


def test_main_writes_json_report_when_output_given(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    vault = _make_vault(tmp_path)
    report_path = tmp_path / "report.json"

    monkeypatch.setattr(
        "sys.argv", ["vault_audit.py", str(vault), "--output", str(report_path)]
    )
    exit_code = vault_audit.main()

    assert exit_code == 0
    assert report_path.exists()
    data = json.loads(report_path.read_text(encoding="utf-8"))
    assert data["summary"]["errors"] == 0


def test_main_fails_fast_on_nonexistent_vault_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    monkeypatch.setattr("sys.argv", ["vault_audit.py", str(tmp_path / "does-not-exist")])
    exit_code = vault_audit.main()

    assert exit_code == 1
    assert "not found" in capsys.readouterr().err


def test_audit_note_flags_zero_type_tags(tmp_path: Path) -> None:
    """A note with no type/* tags must emit tag-cardinality-type ERROR."""
    vault = _make_vault(tmp_path)
    vault_audit.vault_root = vault
    note = vault / "no-type.md"
    note.write_text(
        "---\n"
        "title: No Type\n"
        "type: reference\n"
        "tags:\n  - domain/governance\n"
        "created: 2026-09-26\n"
        "updated: 2026-09-26\n"
        "---\n\n# No Type\n",
        encoding="utf-8",
    )
    findings = vault_audit.audit_note(note, {"domain/governance"}, apply=False)
    assert any(f.rule == "tag-cardinality-type" and f.severity == "ERROR" for f in findings)


def test_audit_note_flags_two_type_tags(tmp_path: Path) -> None:
    """A note with two type/* tags must emit tag-cardinality-type ERROR."""
    vault = _make_vault(tmp_path)
    vault_audit.vault_root = vault
    note = vault / "two-types.md"
    note.write_text(
        "---\n"
        "title: Two Types\n"
        "type: decision\n"
        "tags:\n  - type/decision\n  - type/moc\n  - domain/governance\n"
        "created: 2026-09-26\n"
        "updated: 2026-09-26\n"
        "---\n\n# Two Types\n",
        encoding="utf-8",
    )
    findings = vault_audit.audit_note(
        note, {"type/decision", "type/moc", "domain/governance"}, apply=False
    )
    assert any(f.rule == "tag-cardinality-type" and f.severity == "ERROR" for f in findings)


def test_audit_note_flags_zero_domain_tags(tmp_path: Path) -> None:
    """A note with no domain/* tags must emit tag-cardinality-domain ERROR."""
    vault = _make_vault(tmp_path)
    vault_audit.vault_root = vault
    note = vault / "no-domain.md"
    note.write_text(
        "---\n"
        "title: No Domain\n"
        "type: decision\n"
        "tags:\n  - type/decision\n"
        "created: 2026-09-26\n"
        "updated: 2026-09-26\n"
        "---\n\n# No Domain\n",
        encoding="utf-8",
    )
    findings = vault_audit.audit_note(note, {"type/decision"}, apply=False)
    assert any(f.rule == "tag-cardinality-domain" and f.severity == "ERROR" for f in findings)


def test_audit_note_flags_two_status_tags(tmp_path: Path) -> None:
    """A note with two status/* tags must emit tag-cardinality-status ERROR."""
    vault = _make_vault(tmp_path)
    vault_audit.vault_root = vault
    note = vault / "two-statuses.md"
    note.write_text(
        "---\n"
        "title: Two Statuses\n"
        "type: decision\n"
        "tags:\n"
        "  - type/decision\n"
        "  - domain/governance\n"
        "  - status/draft\n"
        "  - status/reviewed\n"
        "created: 2026-09-26\n"
        "updated: 2026-09-26\n"
        "---\n\n# Two Statuses\n",
        encoding="utf-8",
    )
    findings = vault_audit.audit_note(
        note,
        {"type/decision", "domain/governance", "status/draft", "status/reviewed"},
        apply=False,
    )
    assert any(f.rule == "tag-cardinality-status" and f.severity == "ERROR" for f in findings)


def test_audit_note_valid_cardinality_produces_no_cardinality_findings(tmp_path: Path) -> None:
    """One type/*, >=1 domain/*, and 0-1 status/* produces no cardinality findings."""
    vault = _make_vault(tmp_path)
    vault_audit.vault_root = vault
    note = vault / "valid-cardinality.md"
    note.write_text(
        "---\n"
        "title: Valid Cardinality\n"
        "type: decision\n"
        "tags:\n  - type/decision\n  - domain/governance\n  - status/draft\n"
        "created: 2026-09-26\n"
        "updated: 2026-09-26\n"
        "---\n\n# Valid Cardinality\n",
        encoding="utf-8",
    )
    findings = vault_audit.audit_note(
        note, {"type/decision", "domain/governance", "status/draft"}, apply=False
    )
    cardinality_rules = {
        "tag-cardinality-type",
        "tag-cardinality-domain",
        "tag-cardinality-status",
    }
    assert not any(f.rule in cardinality_rules for f in findings)


def test_parse_args_does_not_accept_apply_flag() -> None:
    """After removing --apply, parse_args(['vault', '--apply']) must raise SystemExit."""
    with pytest.raises(SystemExit):
        vault_audit.parse_args(["vault", "--apply"])


def _make_vault_with_wellspring_hub(tmp_path: Path) -> Path:
    """Build a vault with wellspring.md as the hub (for orphan-detection tests)."""
    vault = tmp_path / "vault"
    meta = vault / "_meta"
    meta.mkdir(parents=True)
    (meta / "tags.md").write_text(
        "# Tag Vocabulary\n\n"
        "| Tag | Meaning |\n"
        "|-----|---------|\n"
        "| `type/moc` | hub |\n"
        "| `type/decision` | decision |\n"
        "| `domain/governance` | governance |\n"
        "| `status/draft` | draft |\n",
        encoding="utf-8",
    )
    (vault / "wellspring.md").write_text(
        "---\n"
        "title: Hub\n"
        "type: moc\n"
        "tags:\n"
        "  - type/moc\n"
        "  - domain/governance\n"
        "created: 2026-09-26\n"
        "updated: 2026-09-26\n"
        "---\n\n"
        "# Hub\n",
        encoding="utf-8",
    )
    return vault


def _note_files(vault: Path) -> list[Path]:
    """Return governed note files (mirrors main()'s filter)."""
    return sorted(
        f
        for f in vault.rglob("*.md")
        if ".obsidian" not in f.parts and "_meta" not in f.parts
    )


def test_find_orphan_notes_flags_unlinked_note(tmp_path: Path) -> None:
    """A note not reachable from the hub (directly or transitively) is an orphan."""
    vault = _make_vault_with_wellspring_hub(tmp_path)
    orphan = vault / "unlinked.md"
    orphan.write_text(
        "---\ntitle: Unlinked\ntype: decision\n"
        "tags:\n  - type/decision\n  - domain/governance\n"
        "created: 2026-09-26\nupdated: 2026-09-26\n---\n\n# Unlinked\n",
        encoding="utf-8",
    )
    hub = vault / "wellspring.md"
    orphans = vault_audit.find_orphan_notes(vault, _note_files(vault), hub)
    assert orphan in orphans


def test_find_orphan_notes_does_not_flag_transitively_linked_note(tmp_path: Path) -> None:
    """A note linked transitively (hub -> A -> B) must NOT be flagged as orphan."""
    vault = _make_vault_with_wellspring_hub(tmp_path)
    hub = vault / "wellspring.md"
    # A: directly linked from hub
    note_a = vault / "linked-a.md"
    note_a.write_text(
        "---\ntitle: A\ntype: decision\n"
        "tags:\n  - type/decision\n  - domain/governance\n"
        "created: 2026-09-26\nupdated: 2026-09-26\n---\n\n"
        "[[linked-b]]\n",
        encoding="utf-8",
    )
    # B: linked from A only, not from hub
    note_b = vault / "linked-b.md"
    note_b.write_text(
        "---\ntitle: B\ntype: decision\n"
        "tags:\n  - type/decision\n  - domain/governance\n"
        "created: 2026-09-26\nupdated: 2026-09-26\n---\n\n# B\n",
        encoding="utf-8",
    )
    # Update hub to link to A
    hub.write_text(
        "---\ntitle: Hub\ntype: moc\n"
        "tags:\n  - type/moc\n  - domain/governance\n"
        "created: 2026-09-26\nupdated: 2026-09-26\n---\n\n"
        "[[linked-a]]\n",
        encoding="utf-8",
    )
    orphans = vault_audit.find_orphan_notes(vault, _note_files(vault), hub)
    assert note_b not in orphans


def test_find_orphan_notes_does_not_flag_hub_itself(tmp_path: Path) -> None:
    """The hub note itself must never be reported as an orphan."""
    vault = _make_vault_with_wellspring_hub(tmp_path)
    hub = vault / "wellspring.md"
    orphans = vault_audit.find_orphan_notes(vault, _note_files(vault), hub)
    assert hub not in orphans


def test_main_flags_orphan_note_as_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """main() reports orphan-note ERROR for a note not reachable from wellspring.md."""
    vault = _make_vault_with_wellspring_hub(tmp_path)
    orphan = vault / "orphan.md"
    orphan.write_text(
        "---\ntitle: Orphan\ntype: decision\n"
        "tags:\n  - type/decision\n  - domain/governance\n"
        "created: 2026-09-26\nupdated: 2026-09-26\n---\n\n# Orphan\n",
        encoding="utf-8",
    )
    monkeypatch.setattr("sys.argv", ["vault_audit.py", str(vault)])
    exit_code = vault_audit.main()
    assert exit_code == 1
