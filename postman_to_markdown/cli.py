"""Command-line entry point: postman-to-markdown collection.json [-o docs.md]."""

from __future__ import annotations

import argparse
import sys

from .converter import convert_file


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="postman-to-markdown",
        description="Turn a Postman Collection (v2.1) export into Markdown API docs.",
    )
    parser.add_argument("collection", help="Path to the exported collection JSON file.")
    parser.add_argument(
        "-o",
        "--output",
        help="Write Markdown to this file instead of standard output.",
    )
    parser.add_argument(
        "--no-toc",
        action="store_true",
        help="Omit the table of contents.",
    )
    parser.add_argument(
        "--title",
        help="Override the document title (defaults to the collection name).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        markdown = convert_file(
            args.collection,
            include_toc=not args.no_toc,
            title=args.title,
        )
    except FileNotFoundError:
        print(f"error: no such file: {args.collection}", file=sys.stderr)
        return 1
    except ValueError as exc:  # json.JSONDecodeError subclasses ValueError
        print(f"error: could not parse collection JSON: {exc}", file=sys.stderr)
        return 1

    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(markdown)
        print(f"Wrote {args.output}", file=sys.stderr)
    else:
        sys.stdout.write(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
