"""Localized message enums."""

from enum import auto, Enum
from importlib.metadata import PackageNotFoundError, version
from typing import Final

from assistant_t800.localization.multilang import MultiLang

try:
    APP_VERSION = version("assistant-t800")
except PackageNotFoundError:
    APP_VERSION = "1.0.0"

ASCII_APP_LOGO: Final[str] = r"""       ______   
     <((((((\\\ 
     /      . }\
     ;--..--._|}
     '--/\--'  )
     | '-'  :'| 
     . -==- .-| 
      \.__.'    
                """


class MultiLangEnum(Enum):
    """Enum base class with localized string conversion."""

    @property
    def text(self) -> str:
        """Return localized enum text."""
        return MultiLang.get(self)

    def render(self, **params: object) -> str:
        """Return localized text formatted with parameters."""
        return self.text.format(**params)

    def confirm_render(self, **params: object) -> str:
        """Return localized confirmation prompt."""
        return f"{self.render(**params)} ({Message.YES}/{Message.NO}): "

    def confirm_check(self, answer: str) -> bool:
        """Return True when the answer confirms the action."""
        return answer.strip().lower() in {
            str(Message.YES).lower(),
            str(Message.YES)[0].lower(),
            "yes",
            "y",
        }

    def __str__(self) -> str:
        return self.text


class Message(MultiLangEnum):
    """Localized application and UI messages."""

    PROMPT = auto()
    EDITABLE_PROMPT = auto()
    YES = auto()
    NO = auto()

    WELCOME = auto()
    WELCOME_TITLE = auto()
    WELCOME_SUBTITLE = auto()
    WELCOME_HINTS_TITLE = auto()
    WELCOME_QUOTES_HINT = auto()
    WELCOME_MULTI_VALUE_HINT = auto()
    WELCOME_REMOVE_HINT = auto()
    WELCOME_HELP_HINT = auto()
    GOOD_BYE = auto()
    HELP = auto()
    HELP_CONTACTS = auto()
    HELP_NOTES = auto()
    HELP_BIRTHDAYS = auto()
    HELP_OTHER = auto()

    COMMAND_SUGGESTION_CONFIRM = auto()
    COMMAND_SUGGESTION_RUN = auto()

    CONTACT_ADDED = auto()
    CONTACT_UPDATED = auto()
    CONTACT_TAGS_UPDATED = auto()
    CONTACT_FOUND = auto()
    CONTACTS_FOUND = auto()
    CONTACTS_LISTED = auto()
    BIRTHDAYS_FOUND = auto()
    NO_BIRTHDAYS = auto()
    BIRTHDAY_LIST_ITEM = auto()

    OPERATION_CANCELLED = auto()

    CONFIRM_REMOVE_CONTACT = auto()
    CONFIRM_REMOVE_ADDRESS = auto()
    CONFIRM_REMOVE_BIRTHDAY = auto()
    CONFIRM_REMOVE_NOTE = auto()
    CONFIRM_REMOVE_PHONE = auto()
    CONFIRM_REMOVE_EMAIL = auto()
    CONFIRM_REMOVE_TAGS = auto()
    CONFIRM_REMOVE_ALL_PHONES = auto()
    CONFIRM_REMOVE_ALL_EMAILS = auto()
    CONFIRM_SUFFIX = auto()
    REMOVED_CONTACT = auto()
    REMOVED_ADDRESS = auto()
    REMOVED_BIRTHDAY = auto()
    REMOVED_NOTE = auto()
    REMOVED_PHONE = auto()
    REMOVED_EMAIL = auto()
    REMOVED_TAGS = auto()

    NO_CONTACTS = auto()
    USE_QUOTES_HINT = auto()
    BIRTHDAY_ONCE_HINT = auto()

    CONTACT_NAME = auto()
    CONTACT_PHONE = auto()
    CONTACT_EMAIL = auto()
    CONTACT_ADDRESS = auto()
    CONTACT_BIRTHDAY = auto()
    CONTACT_NOTE = auto()
    CONTACT_TAGS = auto()

    HELP_DESCRIPTION = auto()
    EXIT_DESCRIPTION = auto()
    ADD_DESCRIPTION = auto()
    CONTACTS_DESCRIPTION = auto()
    GET_DESCRIPTION = auto()
    SEARCH_DESCRIPTION = auto()
    SEARCH_NAME_DESCRIPTION = auto()
    SEARCH_PHONE_DESCRIPTION = auto()
    SEARCH_EMAIL_DESCRIPTION = auto()
    SEARCH_NOTE_DESCRIPTION = auto()
    SEARCH_TAG_DESCRIPTION = auto()
    BIRTHDAYS_DESCRIPTION = auto()
    SET_ADDRESS_DESCRIPTION = auto()
    SET_BIRTHDAY_DESCRIPTION = auto()
    ADD_PHONE_DESCRIPTION = auto()
    ADD_EMAIL_DESCRIPTION = auto()
    REMOVE_DESCRIPTION = auto()
    REMOVE_ADDRESS_DESCRIPTION = auto()
    REMOVE_BIRTHDAY_DESCRIPTION = auto()
    REMOVE_PHONE_DESCRIPTION = auto()
    REMOVE_EMAIL_DESCRIPTION = auto()
    EDIT_NOTE_DESCRIPTION = auto()
    EDIT_NOTE_INPUT_TITLE = auto()
    EDIT_NOTE_INPUT_HINT = auto()
    EDIT_NOTE_INPUT_PROMPT = auto()
    REMOVE_NOTE_DESCRIPTION = auto()
    EDIT_TAGS_DESCRIPTION = auto()
    EDIT_TAGS_INPUT_HINT = auto()
    SUGGEST_TAGS_DESCRIPTION = auto()
    SUGGEST_TAGS_NONE = auto()


class ErrorCode(MultiLangEnum):
    """Localized application error codes."""

    UNKNOWN_INTERFACE_MODE = auto()
    UNKNOWN_COMMAND = auto()
    EMPTY_COMMAND = auto()
    INVALID_COMMAND_SYNTAX = auto()
    INVALID_QUOTES_SYNTAX = auto()
    COMMAND_PARSE_ERROR = auto()

    MISSING_ARGUMENTS = auto()
    EXTRA_ARGUMENTS = auto()
    INCORRECT_ARGUMENTS = auto()

    VALIDATION_ERROR = auto()
    CONTACT_NOT_FOUND = auto()
    CONTACTS_NOT_FOUND = auto()
    NAME_NOT_FOUND = auto()
    QUERY_NOT_FOUND = auto()
    EMAIL_NOT_FOUND = auto()
    PHONE_NOT_FOUND = auto()
    TAG_NOT_FOUND = auto()
    NOTE_NOT_FOUND = auto()
    CONTACT_ALREADY_EXISTS = auto()
    CONTACT_VALUE_NOT_FOUND = auto()
    CONTACT_FIELD_EMPTY = auto()
    INVALID_DAYS = auto()
    EMPTY_NAME = auto()
    INVALID_PHONE = auto()
    INVALID_EMAIL = auto()
    EMPTY_ADDRESS = auto()
    INVALID_BIRTHDAY_FORMAT = auto()
    FUTURE_BIRTHDAY = auto()
    INVALID_PHONE_DIGITS_RANGE = auto()
    PHONE_NOT_RECOGNIZED = auto()
    SUGGEST_TAGS_FAILED = auto()
    SUGGEST_TAGS_INTERACTIVE_ONLY = auto()
    NOT_IMPLEMENTED = auto()
    UNEXPECTED_ERROR = auto()
