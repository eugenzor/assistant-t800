"""Semantic parsing helpers for contact commands."""

import re
from dataclasses import dataclass

from assistant_t800.application.enums import SystemValue
from assistant_t800.localization import ErrorCode, Message
from assistant_t800.application.results import AppResult
from assistant_t800.domain.fields import Birthday, Email, Phone


@dataclass(frozen=True)
class ContactDraft:
    """Parsed contact data before service-level processing."""

    name: str
    phones: tuple[str, ...] = ()
    emails: tuple[str, ...] = ()
    address: str | None = None
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
    def split_multi_values(cls, value: str) -> tuple[str, ...]:
        """Split a multi-value argument by configured separators."""
        pattern = f"[{re.escape(SystemValue.MULTI_VALUE_SEPARATORS.value)}]"
        result = tuple(
            item.strip() for item in re.split(pattern, value) if item.strip()
        )

        return result

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
        address: str | None = None
        birthday: str | None = None
        error: AppResult | None = None

        for token in args[1:]:
            normalized_birthday = cls.normalize_birthday(token)

            if cls._is_phone_collection(token):
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
            elif address is None:
                address = token
            else:
                error = AppResult.fail(
                    ErrorCode.EXTRA_ARGUMENTS,
                    command="add",
                    hint=str(Message.USE_QUOTES_HINT),
                )
                break

        if error is not None:
            result: ContactDraft | AppResult = error
        else:
            result = ContactDraft(
                name=name,
                phones=tuple(phones),
                emails=tuple(emails),
                address=address,
                birthday=birthday,
            )

        return result

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
