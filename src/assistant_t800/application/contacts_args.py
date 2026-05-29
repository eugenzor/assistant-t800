"""Semantic parsing helpers for contact commands."""

import re
from dataclasses import dataclass

from assistant_t800.application.enums import SystemValue
from assistant_t800.localization import ErrorCode, Message
from assistant_t800.application.results import AppResult
from assistant_t800.domain.fields import AddressInput, Birthday, Email, Phone


_ADDRESS_KEYS: dict[str, str] = {
    "country": "country",
    "країна": "country",
    "city": "city",
    "місто": "city",
    "line": "line",
    "address": "line",
    "адреса": "line",
    "street": "line",
    "вулиця": "line",
    "zip": "zip_code",
    "zip_code": "zip_code",
    "index": "zip_code",
    "індекс": "zip_code",
    "region": "region",
    "регіон": "region",
    "область": "region",
}

_KEY_VALUE_PATTERN = re.compile(r"^([^\s=]+)=(.*)$", re.UNICODE)

_ADDRESS_PREFIXES: tuple[str, ...] = (
    "вул.",
    "вул ",
    "пл.",
    "пл ",
    "пр.",
    "пр ",
    "просп.",
    "просп ",
    "бул.",
    "бул ",
    "м.",
    "м ",
    "с.",
    "с ",
    "ст.",
    "ст ",
    "str.",
    "str ",
    "st.",
    "st ",
    "ave.",
    "ave ",
    "rd.",
    "rd ",
    "blvd.",
    "blvd ",
)


@dataclass(frozen=True)
class ContactDraft:
    """Parsed contact data before service-level processing."""

    name: str
    phones: tuple[str, ...] = ()
    emails: tuple[str, ...] = ()
    address: AddressInput | None = None
    birthday: str | None = None


class ContactArgumentsParser:
    """Parse raw contact command arguments into semantic payloads."""

    @classmethod
    def parse_add(cls, args: tuple[str, ...]) -> ContactDraft | AppResult:
        """Parse arguments for the ``add`` command."""
        if not args:
            result: ContactDraft | AppResult = AppResult.fail(
                ErrorCode.MISSING_ARGUMENTS,
                command="add",
                syntax="add <name> [phone] [email] [address] [birthday]",
            )
        else:
            result = cls._parse_contact_draft(args)

        return result

    @classmethod
    def parse_values(
        cls,
        args: tuple[str, ...],
        *,
        command: str,
        value_name: str,
    ) -> tuple[str, tuple[str, ...]] | AppResult:
        """Parse ``<name> <value>`` commands with multi-value support."""
        if len(args) < 2:
            result: tuple[str, tuple[str, ...]] | AppResult = AppResult.fail(
                ErrorCode.MISSING_ARGUMENTS,
                command=command,
                syntax=f"{command} <name> <{value_name}>",
            )
        elif len(args) > 2:
            result = AppResult.fail(
                ErrorCode.EXTRA_ARGUMENTS,
                command=command,
                hint=str(Message.USE_QUOTES_HINT),
            )
        else:
            result = args[0], cls.split_multi_values(args[1])

        return result

    @classmethod
    def parse_optional_values(
        cls,
        args: tuple[str, ...],
        *,
        command: str,
        value_name: str,
    ) -> tuple[str, tuple[str, ...]] | AppResult:
        """Parse ``<name> [value]`` commands with multi-value support."""
        if not args:
            result: tuple[str, tuple[str, ...]] | AppResult = AppResult.fail(
                ErrorCode.MISSING_ARGUMENTS,
                command=command,
                syntax=f"{command} <name> [{value_name}]",
            )
        elif len(args) > 2:
            result = AppResult.fail(
                ErrorCode.EXTRA_ARGUMENTS,
                command=command,
                hint=str(Message.USE_QUOTES_HINT),
            )
        else:
            values = cls.split_multi_values(args[1]) if len(args) == 2 else ()
            result = args[0], values

        return result

    @classmethod
    def parse_named_value(
        cls,
        args: tuple[str, ...],
        *,
        command: str,
        value_name: str,
    ) -> tuple[str, str] | AppResult:
        """Parse ``<name> <value>`` commands with a single value."""
        if len(args) < 2:
            result: tuple[str, str] | AppResult = AppResult.fail(
                ErrorCode.MISSING_ARGUMENTS,
                command=command,
                syntax=f"{command} <name> <{value_name}>",
            )
        elif len(args) > 2:
            result = AppResult.fail(
                ErrorCode.EXTRA_ARGUMENTS,
                command=command,
                hint=str(Message.USE_QUOTES_HINT),
            )
        else:
            result = args[0], args[1]

        return result

    @classmethod
    def parse_optional_named_value(
        cls,
        args: tuple[str, ...],
        *,
        command: str,
        value_name: str,
    ) -> tuple[str, str | None] | AppResult:
        """Parse ``<name> [value]`` commands with a single optional value."""
        if not args:
            result: tuple[str, str | None] | AppResult = AppResult.fail(
                ErrorCode.MISSING_ARGUMENTS,
                command=command,
                syntax=f"{command} <name> [{value_name}]",
            )
        elif len(args) > 2:
            result = AppResult.fail(
                ErrorCode.EXTRA_ARGUMENTS,
                command=command,
                hint=str(Message.USE_QUOTES_HINT),
            )
        else:
            result = args[0], args[1] if len(args) == 2 else None

        return result

    @classmethod
    def split_multi_values(cls, value: str) -> tuple[str, ...]:
        """Split a multi-value argument by configured separators."""
        pattern = f"[{re.escape(SystemValue.MULTI_VALUE_SEPARATORS.value)}]"
        result = tuple(
            item.strip() for item in re.split(pattern, value) if item.strip()
        )

        return result

    @classmethod
    def parse_set_address(
        cls, args: tuple[str, ...]
    ) -> tuple[str, AddressInput] | AppResult:
        """Parse ``set-address <name> key=value ...``."""
        if len(args) < 2:
            return AppResult.fail(
                ErrorCode.MISSING_ARGUMENTS,
                command="set-address",
                syntax="set-address <name> country=<...> city=<...> line=<...> "
                "[zip=<...>] [region=<...>]",
            )

        name = args[0]
        parsed = cls.parse_address_kwargs(args[1:])

        if isinstance(parsed, AppResult):
            return parsed

        return name, parsed

    @classmethod
    def is_address_kwarg(cls, token: str) -> bool:
        match = _KEY_VALUE_PATTERN.match(token)

        return bool(match) and match.group(1).strip().casefold() in _ADDRESS_KEYS

    @classmethod
    def parse_address_kwargs(cls, tokens: tuple[str, ...]) -> AddressInput | AppResult:
        """Build an :class:`AddressInput` from ``key=value`` tokens."""
        fields: dict[str, str] = {}

        for token in tokens:
            match = _KEY_VALUE_PATTERN.match(token)

            if not match:
                return AppResult.fail(
                    ErrorCode.VALIDATION_ERROR,
                    reason=(
                        f"set-address: очікується формат key=value, отримано {token!r}"
                    ),
                )

            key = match.group(1).strip().casefold()
            field_name = _ADDRESS_KEYS.get(key)

            if field_name is None:
                return AppResult.fail(
                    ErrorCode.VALIDATION_ERROR,
                    reason=(f"set-address: невідоме поле адреси {match.group(1)!r}"),
                )

            fields[field_name] = match.group(2).strip()

        missing = [
            label
            for label, key in (
                ("country", "country"),
                ("city", "city"),
                ("line", "line"),
            )
            if not fields.get(key)
        ]

        if missing:
            return AppResult.fail(
                ErrorCode.MISSING_ARGUMENTS,
                command="set-address",
                syntax="обов'язкові поля: " + ", ".join(missing),
            )

        return AddressInput(
            country=fields["country"],
            city=fields["city"],
            line=fields["line"],
            zip_code=fields.get("zip_code"),
            region=fields.get("region"),
        )

    @classmethod
    def looks_like_address(cls, token: str) -> bool:
        """Return whether a bare token plausibly resembles an address."""
        if not isinstance(token, str):
            return False

        candidate = token.strip()

        if not candidate:
            return False

        if any(ch in candidate for ch in " ,."):
            return True

        prefixed = candidate.casefold()

        return any(prefixed.startswith(prefix) for prefix in _ADDRESS_PREFIXES)

    @classmethod
    def normalize_birthday(cls, value: str) -> str:
        """Normalize supported date separators to the domain date separator."""
        result = value.strip()

        for separator in SystemValue.DATE_VALUE_SEPARATORS.value:
            result = result.replace(separator, ".")

        return result

    @classmethod
    def _parse_contact_draft(cls, args: tuple[str, ...]) -> ContactDraft | AppResult:
        """Parse contact creation payload."""
        name = args[0]
        phones: list[str] = []
        emails: list[str] = []
        address_kwargs: dict[str, str] = {}
        address_legacy: str | None = None
        birthday: str | None = None
        error: AppResult | None = None

        for token in args[1:]:
            normalized_birthday = cls.normalize_birthday(token)

            if cls.is_address_kwarg(token):
                match = _KEY_VALUE_PATTERN.match(token)
                field_name = _ADDRESS_KEYS[match.group(1).strip().casefold()]
                address_kwargs[field_name] = match.group(2).strip()
            elif cls._is_phone_collection(token):
                phones.extend(cls.split_multi_values(token))
            elif cls._is_email_collection(token):
                emails.extend(cls.split_multi_values(token))
            elif Phone.looks_like(token):
                phones.append(token)
            elif Email.looks_like(token):
                emails.append(token)
            elif Birthday.looks_like(token):
                if birthday is None:
                    birthday = normalized_birthday
                else:
                    error = AppResult.fail(
                        ErrorCode.EXTRA_ARGUMENTS,
                        command="add",
                        hint=str(Message.BIRTHDAY_ONCE_HINT),
                    )
                    break
            elif address_legacy is None and not address_kwargs:
                address_legacy = token
            else:
                error = AppResult.fail(
                    ErrorCode.EXTRA_ARGUMENTS,
                    command="add",
                    hint=str(Message.USE_QUOTES_HINT),
                )
                break

        if error is not None:
            return error

        address = cls._build_draft_address(address_kwargs, address_legacy)

        if isinstance(address, AppResult):
            return address

        return ContactDraft(
            name=name,
            phones=tuple(phones),
            emails=tuple(emails),
            address=address,
            birthday=birthday,
        )

    @classmethod
    def _build_draft_address(
        cls, address_kwargs: dict[str, str], address_legacy: str | None
    ) -> AddressInput | None | AppResult:
        if address_kwargs:
            missing = [
                label
                for label in ("country", "city", "line")
                if not address_kwargs.get(label)
            ]

            if missing:
                return AppResult.fail(
                    ErrorCode.MISSING_ARGUMENTS,
                    command="add",
                    syntax="обов'язкові поля адреси: " + ", ".join(missing),
                )

            return AddressInput(
                country=address_kwargs["country"],
                city=address_kwargs["city"],
                line=address_kwargs["line"],
                zip_code=address_kwargs.get("zip_code"),
                region=address_kwargs.get("region"),
            )

        if address_legacy is None:
            return None

        if not cls.looks_like_address(address_legacy):
            return AppResult.fail(
                ErrorCode.VALIDATION_ERROR,
                reason=(
                    f"Не вдалося розпізнати токен {address_legacy!r}. "
                    f"Якщо це адреса — використайте формат "
                    f"country=... city=... line=..."
                ),
            )

        return AddressInput.from_legacy_string(address_legacy)

    @classmethod
    def _is_phone_collection(cls, value: str) -> bool:
        """Return ``True`` when all separated values look like phones."""
        values = cls.split_multi_values(value)
        result = len(values) > 1 and all(Phone.looks_like(item) for item in values)

        return result

    @classmethod
    def _is_email_collection(cls, value: str) -> bool:
        """Return ``True`` when all separated values look like emails."""
        values = cls.split_multi_values(value)
        result = len(values) > 1 and all(Email.looks_like(item) for item in values)

        return result
