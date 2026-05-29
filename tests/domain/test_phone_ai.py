"""Unit tests for the optional AI phone classifier.

These focus on the graceful-degradation contract (no key / no library / model
errors -> ``None``) and the confidence/mapping logic, without making real
network calls.
"""

from assistant_t800.domain.phone_ai import AIPhoneClassification, AIPhoneClassifier
from assistant_t800.domain.phone_validation import PhoneCountry


def test_unavailable_classifier_returns_none(monkeypatch):
    classifier = AIPhoneClassifier(model="")

    assert classifier.available is False
    assert classifier.classify("0001234567") is None


def test_default_model_prefers_google(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "x")
    monkeypatch.delenv("GOOGLE_API_MODEL", raising=False)

    assert AIPhoneClassifier()._model.startswith("google")


def test_default_model_falls_back_to_openai(monkeypatch):
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "x")

    assert "gpt" in AIPhoneClassifier()._model


def test_default_model_empty_without_keys(monkeypatch):
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    assert AIPhoneClassifier(model=None).available is False


def test_classify_skips_non_phone_input():
    classifier = AIPhoneClassifier(model="fake:model")

    assert classifier.classify("not a phone") is None


def test_classify_maps_high_confidence_result(monkeypatch):
    classifier = AIPhoneClassifier(model="fake:model")

    def fake_classify(value: str):
        # Bypass the real agent: simulate _classify's mapping directly.
        ai = AIPhoneClassification(country="UA", operator="Vodafone", confidence=90)
        from assistant_t800.domain.phone_validation import (
            PhoneClassification,
            _to_e164,
            normalize,
        )

        national = normalize(value)

        return PhoneClassification(
            national=national,
            e164=_to_e164(national, PhoneCountry.UA),
            country=PhoneCountry.UA,
            operator=ai.operator,
            is_valid=True,
            looks_like_phone=True,
            source="ai",
        )

    monkeypatch.setattr(classifier, "_classify", fake_classify)

    result = classifier.classify("0501234567")

    assert result is not None
    assert result.source == "ai"
    assert result.operator == "Vodafone"
    assert result.e164 == "+380501234567"


def test_classify_swallows_model_errors(monkeypatch):
    classifier = AIPhoneClassifier(model="fake:model")

    def boom(value: str):
        raise RuntimeError("model exploded")

    monkeypatch.setattr(classifier, "_classify", boom)

    assert classifier.classify("0501234567") is None


def test_ai_phone_classification_defaults():
    model = AIPhoneClassification()

    assert model.country == ""
    assert model.operator == ""
    assert model.confidence == 0.0
