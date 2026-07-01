"""Convert a Postman Collection (v2.1) into clean Markdown API docs.

The converter walks the collection tree, turning folders into headings and
requests into documented sections with their URL, headers, body, and example
responses. Output is deterministic so the generated docs diff cleanly in git.
"""

from __future__ import annotations

import json
import re
from typing import Any, Optional

# Heading level used for the first level of folders / top-level requests.
# The collection title is the single H1, so content starts at H2.
_BASE_LEVEL = 2
_MAX_LEVEL = 6


class SlugRegistry:
    """Generates GitHub-style heading anchors, de-duplicating collisions.

    GitHub lowercases a heading, drops anything that is not a word character,
    space, or hyphen, then turns spaces into hyphens. Repeated headings get
    ``-1``, ``-2`` suffixes. Reproducing that here means the table-of-contents
    links actually resolve on GitHub.
    """

    def __init__(self) -> None:
        self._seen: dict[str, int] = {}

    def slug(self, text: str) -> str:
        base = text.strip().lower()
        base = re.sub(r"[^\w\s-]", "", base)
        base = re.sub(r"\s+", "-", base)
        count = self._seen.get(base, 0)
        self._seen[base] = count + 1
        return base if count == 0 else f"{base}-{count}"


def convert(
    collection: dict,
    *,
    include_toc: bool = True,
    title: Optional[str] = None,
) -> str:
    """Render *collection* (a parsed Postman v2.1 dict) as a Markdown string.

    :param collection: The parsed collection JSON.
    :param include_toc: Whether to emit a table of contents after the intro.
    :param title: Override the document title; defaults to the collection name.
    """
    info = collection.get("info", {}) or {}
    doc_title = title or info.get("name") or "API Documentation"

    slugs = SlugRegistry()
    body_lines: list[str] = []
    toc_lines: list[str] = []

    for item in collection.get("item", []) or []:
        _render_item(item, level=_BASE_LEVEL, slugs=slugs, body=body_lines, toc=toc_lines)

    out: list[str] = [f"# {doc_title}", ""]
    description = _description_text(info.get("description"))
    if description:
        out.append(description)
        out.append("")
    if include_toc and toc_lines:
        out.append("## Contents")
        out.append("")
        out.extend(toc_lines)
        out.append("")
    out.extend(body_lines)

    # Collapse trailing blank lines to exactly one terminal newline.
    text = "\n".join(out).rstrip() + "\n"
    return text


def _render_item(
    item: dict,
    *,
    level: int,
    slugs: SlugRegistry,
    body: list[str],
    toc: list[str],
) -> None:
    name = item.get("name", "Unnamed")
    if "item" in item:
        # Folder: heading, optional description, then children one level deeper.
        heading_level = min(level, _MAX_LEVEL)
        slug = slugs.slug(name)
        body.append(f"{'#' * heading_level} {name}")
        body.append("")
        folder_desc = _description_text(item.get("description"))
        if folder_desc:
            body.append(folder_desc)
            body.append("")
        toc.append(f"{'  ' * (level - _BASE_LEVEL)}- [{name}](#{slug})")
        for child in item.get("item", []) or []:
            _render_item(child, level=level + 1, slugs=slugs, body=body, toc=toc)
    elif "request" in item:
        _render_request(item, level=level, slugs=slugs, body=body, toc=toc)


def _render_request(
    item: dict,
    *,
    level: int,
    slugs: SlugRegistry,
    body: list[str],
    toc: list[str],
) -> None:
    name = item.get("name", "Unnamed request")
    request = item.get("request", {}) or {}
    method = (request.get("method") or "GET").upper()
    heading_text = f"{method} {name}"
    heading_level = min(level, _MAX_LEVEL)
    slug = slugs.slug(heading_text)

    body.append(f"{'#' * heading_level} {heading_text}")
    body.append("")
    toc.append(f"{'  ' * (level - _BASE_LEVEL)}- [{heading_text}](#{slug})")

    url = _format_url(request.get("url"))
    if url:
        body.append(f"`{method} {url}`")
        body.append("")

    req_desc = _description_text(request.get("description"))
    if req_desc:
        body.append(req_desc)
        body.append("")

    headers = _enabled_headers(request.get("header"))
    if headers:
        body.append("**Headers**")
        body.append("")
        body.append("| Header | Value |")
        body.append("| --- | --- |")
        for key, value in headers:
            body.append(f"| {key} | {value} |")
        body.append("")

    _render_body(request.get("body"), body)
    _render_responses(item.get("response"), body)


def _render_body(request_body: Any, body: list[str]) -> None:
    if not isinstance(request_body, dict):
        return
    mode = request_body.get("mode")
    if mode == "raw":
        raw = request_body.get("raw", "")
        if not raw:
            return
        language = ""
        options = request_body.get("options", {}) or {}
        raw_options = options.get("raw", {}) or {}
        if raw_options.get("language"):
            language = raw_options["language"]
        body.append("**Request body**")
        body.append("")
        body.append(f"```{language}".rstrip())
        body.append(raw)
        body.append("```")
        body.append("")
    elif mode in ("urlencoded", "formdata"):
        rows = request_body.get(mode) or []
        enabled = [r for r in rows if not r.get("disabled")]
        if not enabled:
            return
        label = "Form data" if mode == "formdata" else "URL-encoded body"
        body.append(f"**Request body ({label})**")
        body.append("")
        body.append("| Key | Value |")
        body.append("| --- | --- |")
        for row in enabled:
            body.append(f"| {row.get('key', '')} | {row.get('value', '')} |")
        body.append("")


def _render_responses(responses: Any, body: list[str]) -> None:
    if not isinstance(responses, list) or not responses:
        return
    body.append("**Example responses**")
    body.append("")
    for response in responses:
        if not isinstance(response, dict):
            continue
        name = response.get("name", "Example")
        code = response.get("code")
        status = response.get("status", "")
        label = name
        if code is not None:
            status_part = f" {status}" if status else ""
            label += f" ({code}{status_part})"
        body.append(f"- {label}")
        response_body = response.get("body")
        if response_body:
            body.append("")
            body.append("```json")
            body.append(response_body)
            body.append("```")
            body.append("")
    if body and body[-1] != "":
        body.append("")


def _format_url(url: Any) -> str:
    """Return a printable URL from either a string or Postman's URL object."""
    if isinstance(url, str):
        return url
    if not isinstance(url, dict):
        return ""
    if url.get("raw"):
        return url["raw"]
    host = url.get("host")
    host_str = ".".join(host) if isinstance(host, list) else (host or "")
    path = url.get("path")
    path_str = "/".join(path) if isinstance(path, list) else (path or "")
    combined = host_str
    if path_str:
        combined = f"{combined}/{path_str}" if combined else path_str
    query = url.get("query") or []
    enabled_query = [q for q in query if not q.get("disabled")]
    if enabled_query:
        pairs = "&".join(
            f"{q.get('key', '')}={q.get('value', '')}" for q in enabled_query
        )
        combined = f"{combined}?{pairs}"
    return combined


def _enabled_headers(headers: Any) -> list[tuple[str, str]]:
    if not isinstance(headers, list):
        return []
    return [
        (h.get("key", ""), h.get("value", ""))
        for h in headers
        if isinstance(h, dict) and not h.get("disabled")
    ]


def _description_text(description: Any) -> str:
    """Postman descriptions are sometimes a string, sometimes {content: ...}."""
    if isinstance(description, str):
        return description.strip()
    if isinstance(description, dict):
        return str(description.get("content", "")).strip()
    return ""


def convert_file(path: str, **kwargs) -> str:
    """Read a collection JSON file at *path* and return Markdown."""
    with open(path, "r", encoding="utf-8") as handle:
        collection = json.load(handle)
    return convert(collection, **kwargs)
