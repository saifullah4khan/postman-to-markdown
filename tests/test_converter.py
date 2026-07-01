"""Tests for the Postman-to-Markdown converter."""

from __future__ import annotations

import os

import pytest

from postman_to_markdown import convert, convert_file
from postman_to_markdown.converter import SlugRegistry, _format_url

FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures", "sample_collection.json")


@pytest.fixture
def markdown():
    return convert_file(FIXTURE)


def test_title_and_description(markdown):
    assert markdown.startswith("# Widget API")
    assert "A small sample API" in markdown


def test_table_of_contents_links(markdown):
    assert "## Contents" in markdown
    # A request TOC entry links to a GitHub-style anchor.
    assert "- [GET List widgets](#get-list-widgets)" in markdown


def test_folders_become_headings(markdown):
    assert "## Widgets" in markdown
    assert "Endpoints for managing widgets." in markdown


def test_request_shows_method_and_url(markdown):
    assert "`GET https://api.example.com/widgets?limit=10`" in markdown


def test_disabled_header_is_omitted(markdown):
    assert "Authorization" in markdown
    assert "X-Debug" not in markdown  # disabled header must not appear


def test_raw_body_becomes_fenced_json(markdown):
    assert "**Request body**" in markdown
    assert "```json" in markdown
    assert '"name": "Sprocket"' in markdown


def test_example_response_is_rendered(markdown):
    assert "**Example responses**" in markdown
    assert "OK (200 OK)" in markdown


def test_string_url_request(markdown):
    assert "`GET https://api.example.com/health`" in markdown


def test_toc_can_be_disabled():
    md = convert_file(FIXTURE, include_toc=False)
    assert "## Contents" not in md


def test_title_override():
    md = convert_file(FIXTURE, title="Custom Title")
    assert md.startswith("# Custom Title")


def test_output_is_deterministic():
    assert convert_file(FIXTURE) == convert_file(FIXTURE)


def test_empty_collection_still_produces_a_title():
    md = convert({"info": {"name": "Empty"}, "item": []})
    assert md.strip() == "# Empty"


def test_format_url_reconstructs_from_parts():
    url = {"host": ["api", "example", "com"], "path": ["v1", "users"], "query": [{"key": "q", "value": "x"}]}
    assert _format_url(url) == "api.example.com/v1/users?q=x"


def test_slug_registry_dedupes_collisions():
    reg = SlugRegistry()
    assert reg.slug("Get user") == "get-user"
    assert reg.slug("Get user") == "get-user-1"
    assert reg.slug("Get user") == "get-user-2"
