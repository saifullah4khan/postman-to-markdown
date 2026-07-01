"""postman-to-markdown: turn a Postman Collection export into Markdown API docs."""

from __future__ import annotations

from .converter import convert, convert_file

__all__ = ["convert", "convert_file"]
