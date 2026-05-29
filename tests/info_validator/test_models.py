"""Unit tests for info validator models."""

from assistant_t800.info_validator.models import (
    EntityKind,
    EntitySource,
    InfoResult,
    ValidatedEntity,
)


def _entity(kind, raw, value):
    return ValidatedEntity(kind=kind, raw=raw, value=value)


def test_validated_entity_resolved_when_kind_and_value_present():
    entity = _entity(EntityKind.PHONE, "0501234567", "0501234567")

    assert entity.resolved


def test_validated_entity_unresolved_when_unknown():
    entity = ValidatedEntity(
        kind=EntityKind.UNKNOWN, raw="x", value=None, source=EntitySource.NONE
    )

    assert not entity.resolved


def test_validated_entity_default_metadata_is_empty_dict():
    entity = _entity(EntityKind.EMAIL, "a@b.com", "a@b.com")

    assert entity.metadata == {}


def test_info_result_buckets_by_kind():
    result = InfoResult(
        entities=(
            _entity(EntityKind.PHONE, "0501234567", "0501234567"),
            _entity(EntityKind.EMAIL, "a@b.com", "a@b.com"),
            _entity(EntityKind.BIRTHDAY, "01.01.1990", "01.01.1990"),
            _entity(EntityKind.ADDRESS, "Kyiv", "Kyiv"),
            ValidatedEntity(
                kind=EntityKind.UNKNOWN,
                raw="?",
                value=None,
                source=EntitySource.NONE,
            ),
        )
    )

    assert len(result.phones) == 1
    assert len(result.emails) == 1
    assert len(result.birthdays) == 1
    assert len(result.addresses) == 1
    assert len(result.unknown) == 1


def test_info_result_as_dict_shape():
    result = InfoResult(
        entities=(
            _entity(EntityKind.PHONE, "0501234567", "0501234567"),
            _entity(EntityKind.PHONE, "0671234567", "0671234567"),
            _entity(EntityKind.EMAIL, "a@b.com", "a@b.com"),
            _entity(EntityKind.ADDRESS, "Kyiv", "Kyiv"),
            ValidatedEntity(
                kind=EntityKind.UNKNOWN,
                raw="junk",
                value=None,
                source=EntitySource.NONE,
            ),
        )
    )

    assert result.as_dict() == {
        "phones": ["0501234567", "0671234567"],
        "emails": ["a@b.com"],
        "birthdays": [],
        "address": "Kyiv",
        "unknown": ["junk"],
    }


def test_info_result_as_dict_address_none_when_absent():
    result = InfoResult(
        entities=(_entity(EntityKind.PHONE, "0501234567", "0501234567"),)
    )

    assert result.as_dict()["address"] is None


def test_info_result_preserves_order_within_kind():
    result = InfoResult(
        entities=(
            _entity(EntityKind.PHONE, "0501234567", "0501234567"),
            _entity(EntityKind.EMAIL, "a@b.com", "a@b.com"),
            _entity(EntityKind.PHONE, "0671234567", "0671234567"),
        )
    )

    assert [e.value for e in result.phones] == ["0501234567", "0671234567"]
