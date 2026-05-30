"""Convert Markdown into an inline Rich ``Text``.

Unlike ``rich.markdown.Markdown`` (which renders block-level elements and so
forces line breaks), this produces a single inline ``Text`` with styles
applied. That keeps chat messages on the same line as their colored sender
label while still rendering ``**bold**``, ``*italic*``, ``code`` and links.
"""

from typing import Final

from markdown_it import MarkdownIt
from rich.text import Text

# Inline token base name -> Rich style applied to its span.
_STYLE_FOR: Final[dict[str, str]] = {
    "strong": "bold",
    "em": "italic",
    "s": "strike",
    "link": "underline",
}

# Style for inline ``code`` spans.
_CODE_STYLE: Final[str] = "cyan"

# A reusable parser limited to inline emphasis features (no block rendering).
_PARSER: Final[MarkdownIt] = MarkdownIt("zero").enable(
    ["emphasis", "backticks", "strikethrough", "link", "newline"]
)


def markdown_to_text(md: str) -> Text:
    """Render inline Markdown ``md`` as a styled Rich ``Text``.

    Only inline formatting is interpreted; block elements (lists, tables,
    headings) are flattened to their text. Returns an empty ``Text`` for empty
    input. Building a ``Text`` rather than a markup string means literal ``[``
    in the data cannot be misparsed as Rich markup.
    """
    result = Text()

    if not md:
        return result

    tokens = _PARSER.parseInline(md)
    if not tokens:
        return result

    style_stack: list[str] = []

    for token in tokens[0].children or []:
        kind = token.type

        match kind:
            case "text":
                result.append(token.content, style=_combine(style_stack))
            case "code_inline":
                result.append(
                    token.content, style=_combine([*style_stack, _CODE_STYLE])
                )
            case "softbreak" | "hardbreak":
                result.append("\n")
            case _ if kind.endswith("_open"):
                style_stack.append(_STYLE_FOR.get(kind[: -len("_open")], ""))
            case _ if kind.endswith("_close") and style_stack:
                style_stack.pop()

    return result


def _combine(styles: list[str]) -> str:
    """Join the active (non-empty) styles into one Rich style string."""
    return " ".join(style for style in styles if style)
