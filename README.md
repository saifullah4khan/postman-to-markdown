# postman-to-markdown

Turn a Postman Collection export into clean, committable Markdown API docs.

## The problem

A Postman collection is where an API's real behavior tends to live: the exact
endpoints, headers, request bodies, and the example responses someone actually
captured. The trouble is that it stays locked inside Postman as a big JSON blob.
Teammates who don't use Postman can't read it, and it never shows up in a code
review the way a docs file would.

This tool reads the exported collection and writes a single Markdown file:
folders become sections, each request gets its method, URL, headers, body, and
example responses, and the whole thing is committed alongside your code so it
reviews and diffs like any other file.

## Quickstart

```bash
pip install postman-to-markdown
```

Export a collection from Postman (Collection v2.1), then:

```bash
# Print to stdout
postman-to-markdown my-collection.json

# Write to a file
postman-to-markdown my-collection.json -o API.md

# Skip the table of contents, set a custom title
postman-to-markdown my-collection.json --no-toc --title "Payments API"
```

You can also call it from Python:

```python
from postman_to_markdown import convert_file

markdown = convert_file("my-collection.json")
```

## What the output looks like

For each request the tool emits a heading with the method and name, a code line
with the full URL, the description, an enabled-headers table, a fenced request
body, and any saved example responses. Folders nest as sub-headings and the
table of contents links straight to each one. See the sample in
[`tests/fixtures/sample_collection.json`](tests/fixtures/sample_collection.json)
for the input and run the command above to see the rendered result.

## Design decisions

**It reads the export, not the Postman API.** No account, API key, or network
call is involved. You hand it the JSON file you already exported, which keeps
the tool trivial to run in CI and free of credentials.

**Output is deterministic.** The same collection always produces byte-identical
Markdown, so regenerating docs yields a clean diff instead of noise. That is
what makes it safe to check the generated file into git and even enforce in CI.

**Anchors match GitHub's slug rules.** The table of contents is only useful if
its links resolve, so the slug generator reproduces GitHub's own rules
(lowercase, strip punctuation, spaces to hyphens) and de-duplicates repeated
headings with numeric suffixes exactly as GitHub does.

**Disabled items are dropped.** Postman keeps headers, query parameters, and
form fields that you toggled off. Those are not part of the real request, so
they are excluded from the docs rather than shown as clutter.

**Both URL shapes are handled.** Postman stores a URL as either a plain string
or a structured object with host, path, and query arrays. The tool prefers the
`raw` value when present and reconstructs a readable URL from the parts when it
is not.

**Descriptions are normalized.** A description may be a plain string or an
object with a `content` field depending on how the collection was made. Both
are handled so no text is silently lost.

## Configuration

| Option | Default | Meaning |
| --- | --- | --- |
| `-o`, `--output` | stdout | Write Markdown to this file. |
| `--no-toc` | off | Omit the table of contents. |
| `--title` | collection name | Override the document title. |

## Testing

```bash
pip install -e ".[dev]"
pytest
```

The suite runs the converter against a bundled sample collection (folders,
enabled and disabled headers, a raw JSON body, string and structured URLs, and
an example response) and exercises the CLI end to end, including its error
handling for a missing file and invalid JSON.

## License

MIT. See [LICENSE](LICENSE).
