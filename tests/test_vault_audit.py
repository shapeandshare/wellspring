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
        "tags:\n  - type/decision\n"
        "created: not-iso\n"
        "updated: 2026-09-26\n"
        "---\n\n# Warn Only\n",
        encoding="utf-8",
    )
    # add type/reference and type/decision to the vocab so only the date warns
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
