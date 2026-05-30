"""Phone normalization marker datasets."""

import re
from typing import Final

from assistant_t800.domain.phones import ParsedPhone

PHONE_MIN_DIGITS: Final[int] = 10
PHONE_MAX_DIGITS: Final[int] = 15
UA_COUNTRY_CODE: Final[str] = "38"
UA_INTERNATIONAL_PREFIX: Final[str] = "380"

CLEAN_PHONE_PATTERN: Final[re.Pattern[str]] = re.compile(r"\D")
PHONE_LIKE_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^\+?[\d\s\-().]*\d[\d\s\-().]*$"
)
DATE_SHAPE_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^\d{1,2}[./-]\d{1,2}[./-]\d{4}$"
)


class PhoneMarkers:
    """Static phone markers for deterministic phone normalization."""

    MIN_DIGITS: Final[int] = PHONE_MIN_DIGITS
    MAX_DIGITS: Final[int] = PHONE_MAX_DIGITS

    UA_MOBILE_OPERATORS: Final[dict[str, str]] = {
        "067": "Kyivstar",
        "068": "Kyivstar",
        "096": "Kyivstar",
        "097": "Kyivstar",
        "098": "Kyivstar",
        "050": "Vodafone",
        "066": "Vodafone",
        "095": "Vodafone",
        "099": "Vodafone",
        "063": "lifecell",
        "073": "lifecell",
        "093": "lifecell",
        "091": "3Mob",
        "094": "Intertelecom",
    }

    UA_CITY_CODES: Final[dict[str, str]] = {
        "044": "Kyiv",
        "032": "Lviv",
        "056": "Dnipro",
        "057": "Kharkiv",
        "048": "Odesa",
        "061": "Zaporizhzhia",
        "051": "Mykolaiv",
        "052": "Kropyvnytskyi",
        "053": "Poltava",
        "054": "Sumy",
        "055": "Kherson",
        "031": "Uzhhorod",
        "033": "Lutsk",
        "034": "Ivano-Frankivsk",
        "035": "Ternopil",
        "036": "Rivne",
        "037": "Chernivtsi",
        "038": "Khmelnytskyi",
        "041": "Zhytomyr",
        "043": "Vinnytsia",
        "046": "Chernihiv",
        "047": "Cherkasy",
        "062": "Donetsk",
        "064": "Luhansk",
        "069": "Sevastopol",
    }

    @classmethod
    def clean(cls, value: str) -> str:
        """Return phone digits only."""
        result = CLEAN_PHONE_PATTERN.sub("", value or "")

        return result

    @classmethod
    def looks_like(cls, value: str) -> bool:
        """Return whether value plausibly resembles a phone number."""
        result = False

        if isinstance(value, str):
            candidate = value.strip()

            if candidate and PHONE_LIKE_PATTERN.fullmatch(candidate):
                digits = cls.clean(candidate)
                result = (
                    not DATE_SHAPE_PATTERN.fullmatch(candidate)
                    and PHONE_MIN_DIGITS - 3 <= len(digits) <= PHONE_MAX_DIGITS
                )

        return result

    @classmethod
    def normalize_ukrainian_shape(cls, digits: str) -> str:
        """Normalize common Ukrainian local shapes to international digits."""
        result = digits

        if len(digits) == 10 and digits.startswith("0"):
            result = f"{UA_COUNTRY_CODE}{digits}"
        elif len(digits) == 11 and digits.startswith("80"):
            result = f"3{digits}"

        return result

    @classmethod
    def resolve_ukrainian(cls, digits: str) -> ParsedPhone | None:
        """Resolve known Ukrainian mobile operator or city code."""
        result = None
        normalized = cls.normalize_ukrainian_shape(digits)

        if normalized.startswith(UA_INTERNATIONAL_PREFIX) and len(normalized) == 12:
            national_code = f"0{normalized[3:5]}"
            mobile_operator = cls.UA_MOBILE_OPERATORS.get(national_code)
            city = cls.UA_CITY_CODES.get(national_code)

            if mobile_operator is not None:
                result = ParsedPhone(
                    normalized=normalized,
                    country="Україна",
                    owner=mobile_operator,
                    is_mobile=True,
                    is_valid=True,
                )
            elif city is not None:
                result = ParsedPhone(
                    normalized=normalized,
                    country="Україна",
                    owner=city,
                    is_mobile=False,
                    is_valid=True,
                )

        return result

    @classmethod
    def is_valid_digits(cls, digits: str) -> bool:
        """Return whether digits are acceptable as a normalized phone."""
        result = (
            digits.isdigit()
            and PHONE_MIN_DIGITS <= len(digits) <= PHONE_MAX_DIGITS
            and (len(digits) != 10 or digits.startswith("0"))
        )

        return result
