"""Tests for the command-line entry point."""

from __future__ import annotations

import os

from postman_to_markdown.cli import main

FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures", "sample_collection.json")


def test_cli_writes_to_stdout(capsys):
    exit_code = main([FIXTURE])
    assert exit_code == 0
    out = capsys.readouterr().out
    assert out.startswith("# Widget API")


def test_cli_writes_to_output_file(tmp_path):
    target = tmp_path / "docs.md"
    exit_code = main([FIXTURE, "-o", str(target)])
    assert exit_code == 0
    assert target.read_text(encoding="utf-8").startswith("# Widget API")


def test_cli_no_toc_flag(capsys):
    main([FIXTURE, "--no-toc"])
    assert "## Contents" not in capsys.readouterr().out


def test_cli_missing_file_returns_error(capsys):
    exit_code = main(["does-not-exist.json"])
    assert exit_code == 1
    assert "no such file" in capsys.readouterr().err


def test_cli_invalid_json_returns_error(tmp_path, capsys):
    bad = tmp_path / "bad.json"
    bad.write_text("{ not valid json", encoding="utf-8")
    exit_code = main([str(bad)])
    assert exit_code == 1
    assert "could not parse" in capsys.readouterr().err
