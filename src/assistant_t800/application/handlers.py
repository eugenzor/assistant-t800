"""Application command handlers."""

from collections.abc import Callable, Sequence

from assistant_t800.application.contacts_args import (
    ContactArgumentsParser,
    ContactDraft,
)
from assistant_t800.application.context import AppContext
from assistant_t800.application.results import AppResult
from assistant_t800.domain.contacts import Contact
from assistant_t800.localization import ErrorCode, Message


def show_help(context: AppContext) -> AppResult:
    """Return registered commands for help rendering."""
    return AppResult.ok(Message.HELP, data=context.registry)


def close_app(context: AppContext) -> AppResult:
    """Request application shutdown."""
    return AppResult.ok(Message.GOOD_BYE, should_exit=True)


def list_contacts(context: AppContext) -> AppResult:
    """Return all contacts."""
    contacts = context.contacts.list_contacts()

    if contacts:
        result = AppResult.ok(
            Message.CONTACTS_LISTED,
            data=contacts,
            count=len(contacts),
        )
    else:
        result = AppResult.info(ErrorCode.CONTACTS_NOT_FOUND)

    return result


def get_contact(context: AppContext) -> AppResult:
    """Return one contact by name."""
    name = context.args["name"]

    try:
        contact = context.contacts.get_contact(name)
        result = AppResult.ok(
            Message.CONTACT_FOUND,
            data=contact,
            name=contact.name.value,
        )
    except KeyError:
        result = AppResult.warning(
            ErrorCode.NAME_NOT_FOUND,
            query=name,
        )

    return result


def search_contacts(context: AppContext) -> AppResult:
    """Search contacts by all searchable fields."""
    return _search(
        context=context,
        method=context.contacts.search_contacts,
        error_code=ErrorCode.QUERY_NOT_FOUND,
    )


def search_contacts_by_name(context: AppContext) -> AppResult:
    """Search contacts by name."""
    return _search(
        context=context,
        method=context.contacts.search_contacts_by_name,
        error_code=ErrorCode.NAME_NOT_FOUND,
    )


def search_contacts_by_phone(context: AppContext) -> AppResult:
    """Search contacts by phone."""
    return _search(
        context=context,
        method=context.contacts.search_contacts_by_phone,
        error_code=ErrorCode.PHONE_NOT_FOUND,
    )


def search_contacts_by_email(context: AppContext) -> AppResult:
    """Search contacts by email."""
    return _search(
        context=context,
        method=context.contacts.search_contacts_by_email,
        error_code=ErrorCode.EMAIL_NOT_FOUND,
    )


def search_contacts_by_note(context: AppContext) -> AppResult:
    """Search contacts by note."""
    return _search(
        context=context,
        method=context.contacts.search_contacts_by_note,
        error_code=ErrorCode.NOTE_NOT_FOUND,
    )


def search_contacts_by_tag(context: AppContext) -> AppResult:
    """Search contacts by tag."""
    return _search(
        context=context,
        method=context.contacts.search_contacts_by_tag,
        error_code=ErrorCode.TAG_NOT_FOUND,
    )


def list_upcoming_birthdays(context: AppContext) -> AppResult:
    """Return contacts with upcoming birthday congratulations."""
    raw_days = context.args.get("days", "7")

    try:
        days = int(raw_days)
    except ValueError:
        result = AppResult.fail(ErrorCode.INVALID_DAYS, value=raw_days)
    else:
        if days <= 0:
            result = AppResult.fail(ErrorCode.INVALID_DAYS, value=raw_days)
        else:
            contacts = context.contacts.search_upcoming_birthdays(days)
            code = Message.BIRTHDAYS_FOUND if contacts else Message.NO_BIRTHDAYS
            result = (
                AppResult.ok(
                    code,
                    data=contacts,
                    days=days,
                    count=len(contacts),
                )
                if contacts
                else AppResult.info(Message.NO_BIRTHDAYS, days=days)
            )

    return result


def edit_note(context: AppContext) -> AppResult:
    """Set or replace a contact note."""
    parsed = ContactArgumentsParser.parse_optional_named_value(
        context.raw_args,
        command="edit-note",
        value_name="note",
    )

    if isinstance(parsed, AppResult):
        result = parsed
    else:
        name, note = parsed

        if note is None:
            result = AppResult.fail(
                ErrorCode.MISSING_ARGUMENTS,
                command="edit-note",
                syntax="edit-note <name> [note]",
            )
        else:
            try:
                contact = context.contacts.set_note(name, note)
                result = AppResult.ok(
                    Message.CONTACT_UPDATED,
                    data=contact,
                    name=contact.name.value,
                    field="note",
                )
            except KeyError:
                result = AppResult.warning(ErrorCode.NAME_NOT_FOUND, query=name)
            except ValueError as error:
                contact = None

                try:
                    contact = context.contacts.get_contact(name)
                except KeyError:
                    pass

                result = AppResult.fail(
                    ErrorCode.VALIDATION_ERROR,
                    data=contact,
                    reason=str(error),
                )

    return result


def remove_note(context: AppContext) -> AppResult:
    """Remove contact note after confirmation."""
    return _remove_field(
        context=context,
        confirm_message=Message.CONFIRM_REMOVE_NOTE,
        success_message=Message.REMOVED_NOTE,
        action=lambda: context.contacts.remove_note(context.args["name"]),
    )


def edit_tags(context: AppContext) -> AppResult:
    """Replace or clear contact tags."""
    parsed = ContactArgumentsParser.parse_optional_named_value(
        context.raw_args,
        command="edit-tags",
        value_name="tags",
    )

    if isinstance(parsed, AppResult):
        result = parsed
    else:
        name, raw_tags = parsed

        if raw_tags is None:
            result = AppResult.fail(
                ErrorCode.MISSING_ARGUMENTS,
                command="edit-tags",
                syntax="edit-tags <name> [tags]",
            )
        elif not raw_tags.strip() and not context.confirmed:
            result = AppResult.confirm(
                Message.CONFIRM_REMOVE_TAGS,
                name=name,
            )
        else:
            message = (
                Message.REMOVED_TAGS
                if not raw_tags.strip()
                else Message.CONTACT_TAGS_UPDATED
            )
            result = _mutate_contact(
                context=context,
                action=lambda: context.contacts.set_tags_from_text(name, raw_tags),
                message_code=message,
                field="tags",
            )

    return result


def add_contact(context: AppContext) -> AppResult:
    """Create a contact from raw contact arguments."""
    parsed = ContactArgumentsParser.parse_add(context.raw_args)

    if isinstance(parsed, AppResult):
        result = parsed
    else:
        result = _create_contact(context, parsed)

    return result


def set_address(context: AppContext) -> AppResult:
    """Set or replace a contact address from ``key=value`` arguments."""
    parsed = ContactArgumentsParser.parse_set_address(context.raw_args)

    if isinstance(parsed, AppResult):
        return parsed

    name, address = parsed

    return _mutate_contact(
        context=context,
        action=lambda: context.contacts.set_address(name, address),
        message_code=Message.CONTACT_UPDATED,
        field="address",
    )


def set_birthday(context: AppContext) -> AppResult:
    """Set or replace a contact birthday."""
    birthday = ContactArgumentsParser.normalize_birthday(context.args["birthday"])

    return _mutate_contact(
        context=context,
        action=lambda: context.contacts.set_birthday(
            context.args["name"],
            birthday,
        ),
        message_code=Message.CONTACT_UPDATED,
        field="birthday",
    )


def add_phone(context: AppContext) -> AppResult:
    """Add one or more phones to a contact."""
    parsed = ContactArgumentsParser.parse_values(
        context.raw_args,
        command="add-phone",
        value_name="phone",
    )

    result = (
        parsed
        if isinstance(parsed, AppResult)
        else _add_values(
            name=parsed[0],
            values=parsed[1],
            method=context.contacts.add_phones,
        )
    )

    return result


def add_email(context: AppContext) -> AppResult:
    """Add one or more emails to a contact."""
    parsed = ContactArgumentsParser.parse_values(
        context.raw_args,
        command="add-email",
        value_name="email",
    )

    result = (
        parsed
        if isinstance(parsed, AppResult)
        else _add_values(
            name=parsed[0],
            values=parsed[1],
            method=context.contacts.add_emails,
        )
    )

    return result


def remove_contact(context: AppContext) -> AppResult:
    """Remove a whole contact after confirmation."""
    name = context.args["name"]

    if not context.confirmed:
        result = AppResult.confirm(
            Message.CONFIRM_REMOVE_CONTACT,
            name=name,
        )
    else:
        try:
            contact = context.contacts.remove_contact(name)
            result = AppResult.ok(
                Message.REMOVED_CONTACT,
                name=contact.name.value,
            )
        except KeyError:
            result = AppResult.fail(ErrorCode.CONTACT_NOT_FOUND, name=name)

    return result


def remove_address(context: AppContext) -> AppResult:
    """Remove contact address after confirmation."""
    return _remove_field(
        context=context,
        confirm_message=Message.CONFIRM_REMOVE_ADDRESS,
        success_message=Message.REMOVED_ADDRESS,
        action=lambda: context.contacts.remove_address(context.args["name"]),
    )


def remove_birthday(context: AppContext) -> AppResult:
    """Remove contact birthday after confirmation."""
    return _remove_field(
        context=context,
        confirm_message=Message.CONFIRM_REMOVE_BIRTHDAY,
        success_message=Message.REMOVED_BIRTHDAY,
        action=lambda: context.contacts.remove_birthday(context.args["name"]),
    )


def remove_phone(context: AppContext) -> AppResult:
    """Remove one, many, or all phones from a contact after confirmation."""
    parsed = ContactArgumentsParser.parse_optional_values(
        context.raw_args,
        command="remove-phone",
        value_name="phone",
    )

    result = (
        parsed
        if isinstance(parsed, AppResult)
        else _remove_optional_values(
            context=context,
            name=parsed[0],
            values=parsed[1],
            current_values=lambda contact: tuple(item.value for item in contact.phones),
            confirm_value_message=Message.CONFIRM_REMOVE_PHONE,
            confirm_all_message=Message.CONFIRM_REMOVE_ALL_PHONES,
            success_message=Message.REMOVED_PHONE,
            remove_values=context.contacts.remove_phones,
            remove_all=context.contacts.remove_all_phones,
            empty_field="phone",
        )
    )

    return result


def remove_email(context: AppContext) -> AppResult:
    """Remove one, many, or all emails from a contact after confirmation."""
    parsed = ContactArgumentsParser.parse_optional_values(
        context.raw_args,
        command="remove-email",
        value_name="email",
    )

    result = (
        parsed
        if isinstance(parsed, AppResult)
        else _remove_optional_values(
            context=context,
            name=parsed[0],
            values=parsed[1],
            current_values=lambda contact: tuple(item.value for item in contact.emails),
            confirm_value_message=Message.CONFIRM_REMOVE_EMAIL,
            confirm_all_message=Message.CONFIRM_REMOVE_ALL_EMAILS,
            success_message=Message.REMOVED_EMAIL,
            remove_values=context.contacts.remove_emails,
            remove_all=context.contacts.remove_all_emails,
            empty_field="email",
        )
    )

    return result


def _create_contact(context: AppContext, draft: ContactDraft) -> AppResult:
    """Create a contact from parsed draft."""
    try:
        contact = context.contacts.add_contact(
            draft.name,
            phones=draft.phones,
            emails=draft.emails,
            address=draft.address,
            birthday=draft.birthday,
        )
        result = AppResult.ok(
            Message.CONTACT_ADDED,
            data=contact,
            name=contact.name.value,
        )
    except ValueError as error:
        result = AppResult.fail(
            ErrorCode.VALIDATION_ERROR,
            reason=str(error),
        )

    return result


def _search(
    *,
    context: AppContext,
    method: Callable[[str], list[object]],
    error_code: ErrorCode,
) -> AppResult:
    """Run a search command."""
    query = context.args["query"]
    contacts = method(query)

    if contacts:
        result = AppResult.ok(
            Message.CONTACTS_FOUND,
            data=contacts,
            query=query,
            count=len(contacts),
        )
    else:
        result = AppResult.warning(error_code, query=query)

    return result


def _mutate_contact(
    *,
    context: AppContext,
    action: Callable[[], object],
    message_code: Message,
    field: str,
) -> AppResult:
    """Run a contact mutation and convert known errors to app results."""
    try:
        contact = action()
        result = AppResult.ok(
            message_code,
            data=contact,
            name=contact.name.value,
            field=field,
        )
    except KeyError:
        result = AppResult.fail(
            ErrorCode.CONTACT_NOT_FOUND,
            name=context.args.get("name", ""),
        )
    except ValueError as error:
        result = AppResult.fail(
            ErrorCode.VALIDATION_ERROR,
            reason=str(error),
        )

    return result


def _add_values(
    *,
    name: str,
    values: Sequence[str],
    method: Callable[[str, Sequence[str]], object],
) -> AppResult:
    """Add collection values to a contact."""
    try:
        contact = method(name, values)
        result = AppResult.ok(
            Message.CONTACT_UPDATED,
            data=contact,
            name=contact.name.value,
            values=";".join(values),
        )
    except KeyError:
        result = AppResult.fail(ErrorCode.CONTACT_NOT_FOUND, name=name)
    except ValueError as error:
        result = AppResult.fail(ErrorCode.VALIDATION_ERROR, reason=str(error))

    return result


def _remove_field(
    *,
    context: AppContext,
    confirm_message: Message,
    success_message: Message,
    action: Callable[[], object],
) -> AppResult:
    """Remove a scalar contact field after confirmation."""
    name = context.args["name"]

    if not context.confirmed:
        result = AppResult.confirm(
            confirm_message,
            name=name,
        )
    else:
        result = _remove_confirmed_field(
            context=context,
            action=action,
            message_code=success_message,
        )

    return result


def _remove_optional_values(
    *,
    context: AppContext,
    name: str,
    values: Sequence[str],
    current_values: Callable[[Contact], tuple[str, ...]],
    confirm_value_message: Message,
    confirm_all_message: Message,
    success_message: Message,
    remove_values: Callable[[str, Sequence[str]], Contact],
    remove_all: Callable[[str], Contact],
    empty_field: str,
) -> AppResult:
    """Remove explicit values or all values when no value is provided."""
    if values:
        result = _remove_values(
            context=context,
            name=name,
            values=values,
            confirm_message=confirm_value_message,
            success_message=success_message,
            method=remove_values,
        )
    else:
        result = _remove_all_or_single_value(
            context=context,
            name=name,
            current_values=current_values,
            confirm_value_message=confirm_value_message,
            confirm_all_message=confirm_all_message,
            success_message=success_message,
            remove_values=remove_values,
            remove_all=remove_all,
            empty_field=empty_field,
        )

    return result


def _remove_all_or_single_value(
    *,
    context: AppContext,
    name: str,
    current_values: Callable[[Contact], tuple[str, ...]],
    confirm_value_message: Message,
    confirm_all_message: Message,
    success_message: Message,
    remove_values: Callable[[str, Sequence[str]], Contact],
    remove_all: Callable[[str], Contact],
    empty_field: str,
) -> AppResult:
    """Remove one existing value or ask whether all values should be removed."""
    try:
        contact = context.contacts.get_contact(name)
        values = current_values(contact)

        if not values:
            result = AppResult.fail(
                ErrorCode.CONTACT_FIELD_EMPTY,
                field=empty_field,
            )
        elif not context.confirmed:
            confirm_message = (
                confirm_value_message if len(values) == 1 else confirm_all_message
            )
            params = {"name": name}

            if len(values) == 1:
                params["value"] = values[0]

            result = AppResult.confirm(confirm_message, **params)
        elif len(values) == 1:
            result = _remove_values(
                context=context,
                name=name,
                values=values,
                confirm_message=confirm_value_message,
                success_message=success_message,
                method=remove_values,
            )
        else:
            updated_contact = remove_all(name)
            result = AppResult.ok(
                success_message,
                data=updated_contact,
                name=updated_contact.name.value,
            )
    except KeyError:
        result = AppResult.fail(ErrorCode.CONTACT_NOT_FOUND, name=name)
    except ValueError as error:
        result = AppResult.fail(ErrorCode.VALIDATION_ERROR, reason=str(error))

    return result


def _remove_values(
    *,
    context: AppContext,
    name: str,
    values: Sequence[str],
    confirm_message: Message,
    success_message: Message,
    method: Callable[[str, Sequence[str]], object],
) -> AppResult:
    """Remove collection values from a contact after confirmation."""
    joined_values = ";".join(values)

    if not context.confirmed:
        result = AppResult.confirm(
            confirm_message,
            name=name,
            value=joined_values,
        )
    else:
        try:
            contact = method(name, values)
            result = AppResult.ok(
                success_message,
                data=contact,
                name=contact.name.value,
                value=joined_values,
            )
        except KeyError:
            result = AppResult.fail(ErrorCode.CONTACT_NOT_FOUND, name=name)
        except ValueError as error:
            result = AppResult.fail(ErrorCode.VALIDATION_ERROR, reason=str(error))

    return result


def _remove_confirmed_field(
    *,
    context: AppContext,
    action: Callable[[], object],
    message_code: Message,
) -> AppResult:
    """Run confirmed scalar field removal."""
    try:
        contact = action()
        result = AppResult.ok(
            message_code,
            data=contact,
            name=contact.name.value,
        )
    except KeyError:
        result = AppResult.fail(
            ErrorCode.CONTACT_NOT_FOUND,
            name=context.args.get("name", ""),
        )
    except ValueError as error:
        result = AppResult.fail(
            ErrorCode.VALIDATION_ERROR,
            reason=str(error),
        )

    return result
