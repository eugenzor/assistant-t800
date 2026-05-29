"""Unit tests for the InfoValidator facade."""

from assistant_t800.info_validator.models import (
    EntityKind,
    EntitySource,
    ValidatedEntity,
)
from assistant_t800.info_validator.service import InfoValidator


def test_validate_single_token_phone():
    result = InfoValidator().validate("0671234567")

    assert result.as_dict()["phones"] == ["+380671234567"]


def test_validate_batch_buckets_all_kinds():
    result = InfoValidator().validate(
        [
            "+38 (050) 123-45-67",
            "ivan@example.com",
            "01/01/1990",
            "Київ, Хрещатик 1",
        ]
    )

    data = result.as_dict()
    assert data["phones"] == ["+380501234567"]
    assert data["emails"] == ["ivan@example.com"]
    assert data["birthdays"] == ["01.01.1990"]
    assert data["address"] == "Київ, Хрещатик 1"
    assert data["unknown"] == []


def test_unknown_promoted_to_address_by_default():
    result = InfoValidator().validate(["0671234567", "somewhere street 5"])

    assert result.as_dict()["address"] == "somewhere street 5"
    assert result.unknown == ()


def test_only_first_unknown_promoted_to_address():
    result = InfoValidator().validate(["first place", "second place"])

    data = result.as_dict()
    assert data["address"] == "first place"
    assert data["unknown"] == ["second place"]


def test_promotion_disabled_keeps_unknown():
    result = InfoValidator(promote_unknown_to_address=False).validate(["???"])

    assert result.as_dict()["address"] is None
    assert result.as_dict()["unknown"] == ["???"]


def test_facade_ai_receives_only_unresolved_tokens():
    calls: list[list[str]] = []

    def ai(unresolved):
        calls.append(list(unresolved))
        return {
            "mystery": ValidatedEntity(
                kind=EntityKind.ADDRESS,
                raw="mystery",
                value="Resolved Place",
                source=EntitySource.AI,
            )
        }

    result = InfoValidator(ai_fallback=ai, promote_unknown_to_address=False).validate(
        ["0671234567", "ivan@x.com", "mystery"]
    )

    assert calls == [["mystery"]]
    assert result.as_dict()["address"] == "Resolved Place"


def test_facade_ai_not_called_when_everything_resolved():
    calls: list[list[str]] = []

    def ai(unresolved):
        calls.append(list(unresolved))
        return {}

    InfoValidator(ai_fallback=ai).validate(["0671234567", "ivan@x.com"])

    assert calls == []


def test_facade_ai_exception_does_not_break_validation():
    def ai(unresolved):
        raise RuntimeError("boom")

    result = InfoValidator(ai_fallback=ai, promote_unknown_to_address=False).validate(
        ["0671234567", "???"]
    )

    # Phone still resolved; unknown stays unknown rather than crashing.
    assert result.as_dict()["phones"] == ["+380671234567"]
    assert result.as_dict()["unknown"] == ["???"]


def test_facade_ai_returning_empty_keeps_originals():
    def ai(unresolved):
        return {}

    result = InfoValidator(ai_fallback=ai, promote_unknown_to_address=False).validate(
        ["???"]
    )

    assert result.as_dict()["unknown"] == ["???"]


# ---------- validate_address ----------


def test_facade_validate_address_returns_entity_for_valid_input():
    entity = InfoValidator().validate_address(
        {
            "country": "Ukraine",
            "city": "Київ",
            "line": "вул. Хрещатик 1",
            "zip_code": "01001",
            "region": "Київська обл.",
        }
    )

    assert entity is not None
    assert entity.value == "UA, 01001, Київ, Київська обл., вул. Хрещатик 1"
    assert entity.metadata["country"] == "UA"


def test_facade_validate_address_returns_none_for_invalid():
    facade = InfoValidator()

    assert facade.validate_address({}) is None
    assert facade.validate_address({"country": "UA", "city": "X"}) is None
    assert (
        facade.validate_address({"country": "Narnia", "city": "X", "line": "Y"}) is None
    )
