"""Unit tests for the country resolver."""

import pytest

from assistant_t800.domain.country import is_known_country, resolve_country


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("UA", "UA"),
        ("ua", "UA"),
        ("Ukraine", "UA"),
        ("Україна", "UA"),
        ("україна", "UA"),
        ("  de  ", "DE"),
        ("Poland", "PL"),
        ("сша", "US"),
        ("uk", "GB"),
    ],
)
def test_resolve_country_table_and_aliases(raw, expected):
    assert resolve_country(raw) == expected


def test_resolve_bare_alpha2_passthrough():
    # A two-letter token not in the table is accepted as an ISO code as-is.
    assert resolve_country("fr") == "FR"


@pytest.mark.parametrize("raw", ["", "   ", "Narnia", "Atlantis"])
def test_resolve_country_unresolved_returns_none(raw):
    assert resolve_country(raw) is None


def test_resolve_country_rejects_non_string():
    assert resolve_country(123) is None  # type: ignore[arg-type]


def test_resolve_country_uses_ai_fallback_when_table_misses():
    calls: list[str] = []

    def ai(value: str):
        calls.append(value)
        return "AT"

    assert resolve_country("Atlantis", ai_fallback=ai) == "AT"
    assert calls == ["Atlantis"]


def test_resolve_country_skips_ai_when_table_hits():
    def ai(value: str):
        raise AssertionError("AI must not be called when the table resolves")

    assert resolve_country("Ukraine", ai_fallback=ai) == "UA"


def test_resolve_country_ignores_invalid_ai_output():
    # AI returns something that is not a 2-letter code -> treated as unresolved.
    assert resolve_country("Atlantis", ai_fallback=lambda v: "nonsense") is None


def test_is_known_country():
    assert is_known_country("Ukraine")
    assert is_known_country("ua")
    assert not is_known_country("Narnia")
    assert not is_known_country("fr")  # alpha-2 shortcut is not "known" via table
