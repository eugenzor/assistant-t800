"""Interactive edit command resolvers."""

import shlex
from typing import TYPE_CHECKING

from assistant_t800.application.context import AppContext
from assistant_t800.application.enums import SystemValue
from assistant_t800.application.results import AppResult
from assistant_t800.interfaces.cli.prompting import EditableInputFunc, TextInputFunc
from assistant_t800.localization import ErrorCode, Message

if TYPE_CHECKING:
    from assistant_t800.interfaces.cli.presenter import CliPresenter


class NoteEditResolver:
    """Resolve interactive note editing commands before dispatch."""

    EDIT_NOTE_COMMAND = "edit-note"

    def __init__(
        self,
        *,
        context: AppContext,
        presenter: "CliPresenter",
        text_input_func: TextInputFunc | None,
    ) -> None:
        self._context = context
        self._presenter = presenter
        self._text_input_func = text_input_func

    def resolve(self, raw_input: str) -> str | AppResult:
        """Return resolved command input or direct app result when needed."""
        note_owner = self._resolve_owner(raw_input)

        if note_owner is None or self._text_input_func is None:
            result = raw_input
        else:
            result = self._resolve_note_edit(note_owner)

        return result

    def _resolve_note_edit(self, name: str) -> str | AppResult:
        """Run interactive note editor for one contact."""
        try:
            contact = self._context.contacts.get_contact(name)
        except KeyError:
            result = AppResult.warning(ErrorCode.NAME_NOT_FOUND, query=name)
        else:
            current_note = self._normalize_note(contact.note)
            edited_note = self._presenter.request_note_edit(
                contact=contact,
                current_note=current_note,
                text_input_func=self._text_input_func,
            )

            if edited_note is None:
                result = AppResult.ok(data=contact)
            else:
                result = self._build_input(self.EDIT_NOTE_COMMAND, name, edited_note)

        return result

    def _resolve_owner(self, raw_input: str) -> str | None:
        """Return contact name when input requests interactive note editing."""
        result = _resolve_interactive_owner(
            raw_input=raw_input,
            registry=self._context.registry,
            command_name=self.EDIT_NOTE_COMMAND,
        )

        return result

    @staticmethod
    def _normalize_note(note: str) -> str:
        """Return user-editable note text."""
        result = "" if note == SystemValue.EMPTY_TEXT.value else note

        return result

    @staticmethod
    def _build_input(command_name: str, name: str, value: str) -> str:
        """Build canonical command input."""
        result = f"{command_name} {_quote_arg(name)} {_quote_arg(value)}"

        return result


class TagEditResolver:
    """Resolve interactive tag editing commands before dispatch."""

    EDIT_TAGS_COMMAND = "edit-tags"

    def __init__(
        self,
        *,
        context: AppContext,
        presenter: "CliPresenter",
        editable_func: EditableInputFunc | None,
    ) -> None:
        self._context = context
        self._presenter = presenter
        self._editable_func = editable_func

    def resolve(self, raw_input: str) -> str | AppResult:
        """Return resolved command input or direct app result when needed."""
        tag_owner = self._resolve_owner(raw_input)

        if tag_owner is None or self._editable_func is None:
            result = raw_input
        else:
            result = self._resolve_tag_edit(tag_owner)

        return result

    def _resolve_tag_edit(self, name: str) -> str | AppResult:
        """Run inline tag editor for one contact."""
        try:
            contact = self._context.contacts.get_contact(name)
        except KeyError:
            result = AppResult.warning(ErrorCode.NAME_NOT_FOUND, query=name)
        else:
            current_tags = self._context.contacts.format_tags(contact.tags)
            edited_tags = self._presenter.request_tag_edit(
                contact=contact,
                current_tags=current_tags,
                editable_func=self._editable_func,
            )

            if edited_tags is None:
                result = AppResult.ok(data=contact)
            else:
                result = self._build_input(self.EDIT_TAGS_COMMAND, name, edited_tags)

        return result

    def _resolve_owner(self, raw_input: str) -> str | None:
        """Return contact name when input requests interactive tag editing."""
        result = _resolve_interactive_owner(
            raw_input=raw_input,
            registry=self._context.registry,
            command_name=self.EDIT_TAGS_COMMAND,
        )

        return result

    @staticmethod
    def _build_input(command_name: str, name: str, value: str) -> str:
        """Build canonical command input."""
        result = f"{command_name} {_quote_arg(name)} {_quote_arg(value)}"

        return result


class SuggestTagsResolver:
    """Resolve interactive AI tag suggestion commands before dispatch."""

    SUGGEST_TAGS_COMMAND = "suggest-tags"
    EDIT_TAGS_COMMAND = "edit-tags"

    def __init__(
        self,
        *,
        context: AppContext,
        presenter: "CliPresenter",
        editable_func: EditableInputFunc | None,
    ) -> None:
        self._context = context
        self._presenter = presenter
        self._editable_func = editable_func

    def resolve(self, raw_input: str) -> str | AppResult:
        """Return resolved edit-tags input or direct app result."""
        owner = self._resolve_owner(raw_input)

        if owner is None or self._editable_func is None:
            result = raw_input
        else:
            result = self._resolve_tag_suggestions(owner)

        return result

    def _resolve_tag_suggestions(self, name: str) -> str | AppResult:
        """Suggest tags with AI and pass them through the tag editor."""
        try:
            contact = self._context.contacts.get_contact(name)
        except KeyError:
            result = AppResult.warning(ErrorCode.NAME_NOT_FOUND, query=name)
        else:
            try:
                suggested_tags = self._suggest_tags(name)
            except Exception as error:
                result = AppResult.fail(
                    ErrorCode.SUGGEST_TAGS_FAILED,
                    data=contact,
                    reason=str(error),
                )
            else:
                if not suggested_tags:
                    result = AppResult.info(
                        Message.SUGGEST_TAGS_NONE,
                        data=contact,
                        name=contact.name.value,
                    )
                else:
                    default_tags = self._merge_tags(contact.tags, suggested_tags)
                    edited_tags = self._presenter.request_tag_edit(
                        contact=contact,
                        current_tags=default_tags,
                        editable_func=self._editable_func,
                    )

                    if edited_tags is None:
                        result = AppResult.ok(data=contact)
                    else:
                        result = self._build_input(
                            self.EDIT_TAGS_COMMAND,
                            name,
                            edited_tags,
                        )

        return result

    def _suggest_tags(self, name: str) -> list[str]:
        """Call AI tag suggestion and clean the raw result."""
        from assistant_t800.ai.tag_suggester import suggest_tags

        snapshot = self._context.contacts.tag_suggestion_snapshot(name)
        raw_tags = suggest_tags(snapshot)
        result = self._context.contacts.clean_suggested_tags(raw_tags, name)

        return result

    def _resolve_owner(self, raw_input: str) -> str | None:
        """Return contact name when input requests AI tag suggestions."""
        result = _resolve_interactive_owner(
            raw_input=raw_input,
            registry=self._context.registry,
            command_name=self.SUGGEST_TAGS_COMMAND,
        )

        return result

    @staticmethod
    def _merge_tags(existing_tags: set[str], suggested_tags: list[str]) -> str:
        """Return editable tag text with manual tags first."""
        separator = f"{SystemValue.MULTI_VALUE_SEPARATORS.value[0]} "
        ordered_tags = [*sorted(existing_tags), *suggested_tags]
        result = separator.join(ordered_tags)

        return result

    @staticmethod
    def _build_input(command_name: str, name: str, value: str) -> str:
        """Build canonical command input."""
        result = f"{command_name} {_quote_arg(name)} {_quote_arg(value)}"

        return result


def _resolve_interactive_owner(
    *,
    raw_input: str,
    registry: dict,
    command_name: str,
) -> str | None:
    """Resolve an interactive command owner from a raw CLI input."""
    try:
        parts = shlex.split(raw_input)
    except ValueError:
        result = None
    else:
        result = _resolve_owner_from_parts(
            parts=parts,
            registry=registry,
            command_name=command_name,
        )

    return result


def _resolve_owner_from_parts(
    *,
    parts: list[str],
    registry: dict,
    command_name: str,
) -> str | None:
    """Resolve command aliases and return one owner argument."""
    result: str | None = None

    for index in range(len(parts), 0, -1):
        candidate = " ".join(parts[:index]).strip().lower()
        command = registry.get(candidate)

        if command is not None and command.name == command_name:
            command_args = parts[index:]
            result = command_args[0] if len(command_args) == 1 else None
            break

    return result


def _quote_arg(value: str) -> str:
    """Quote a command argument for shlex-based dispatch."""
    result = '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'

    return result
